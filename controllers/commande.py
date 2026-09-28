from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from controllers.menu import get_menu_by_id
from models.commande import Commande, LigneCommande, LigneCommandeChoix
from models.enums import StatutCommande, ModeCommande
from models.produit import Produit
from schemas.commande import CommandeCreate, LigneCreate, ChoixCreate

# Les changements de statut autorisés : on ne peut pas sauter d'étape ni revenir en arrière
TRANSITIONS = {
    StatutCommande.saisie: {StatutCommande.preparee},
    StatutCommande.preparee: {StatutCommande.livree},
    StatutCommande.livree: set(),
}


def _dec(valeur) -> Decimal:
    # Convertit proprement en Decimal (évite les erreurs d'arrondi des float)
    return Decimal(str(valeur))


def _requete_commande():
    # Charge d'un coup les lignes, leurs produits/menus et leurs choix
    return select(Commande).options(
        selectinload(Commande.lignes).selectinload(LigneCommande.produit),
        selectinload(Commande.lignes).selectinload(LigneCommande.menu),
        selectinload(Commande.lignes)
        .selectinload(LigneCommande.choix)
        .selectinload(LigneCommandeChoix.groupe),
        selectinload(Commande.lignes)
        .selectinload(LigneCommande.choix)
        .selectinload(LigneCommandeChoix.produit),
    )


def _get_produit_disponible(db: Session, produit_id: int) -> Produit:
    produit = db.get(Produit, produit_id)
    if produit is None:
        raise HTTPException(status_code=404, detail=f"Produit {produit_id} introuvable")
    if not produit.disponible:
        raise HTTPException(status_code=400, detail=f"« {produit.nom} » n'est plus disponible")
    return produit


def _verifier_choix(menu, choix: list[ChoixCreate]) -> Decimal:
    """Vérifie les choix faits dans un menu et renvoie le total des suppléments."""
    groupes = {int(g.id): g for g in menu.groupes}
    nb_par_groupe: dict[int, int] = {}
    supplements = Decimal("0")

    for c in choix:
        groupe = groupes.get(c.groupe_id)
        if groupe is None:
            raise HTTPException(
                status_code=400,
                detail=f"Le groupe {c.groupe_id} ne fait pas partie de ce menu",
            )

        proposes = {int(p.id) for p in groupe.produits_proposes}
        if c.produit_id not in proposes:
            raise HTTPException(
                status_code=400,
                detail=f"Le produit {c.produit_id} n'est pas proposé (ou plus disponible) dans « {groupe.nom} »",
            )

        nb_par_groupe[c.groupe_id] = nb_par_groupe.get(c.groupe_id, 0) + 1

        # Supplément de prix : seulement pour les groupes remplis à la main
        if groupe.categorie_id is None:
            for option in groupe.options:
                if option.produit_id == c.produit_id:
                    supplements += _dec(option.supplement)

    for groupe in menu.groupes:
        nb = nb_par_groupe.get(int(groupe.id), 0)
        if groupe.obligatoire and nb == 0:
            raise HTTPException(status_code=400, detail=f"Choix obligatoire manquant : « {groupe.nom} »")
        if nb > groupe.max_choix:
            raise HTTPException(
                status_code=400,
                detail=f"« {groupe.nom} » : {groupe.max_choix} choix maximum",
            )

    return supplements


def _construire_ligne_menu(db: Session, ligne: LigneCreate) -> LigneCommande:
    menu = get_menu_by_id(int(ligne.menu_id), db)  # 404 si le menu n'existe pas

    if not menu.disponible or not menu.produit_principal.disponible:
        raise HTTPException(status_code=400, detail=f"« {menu.nom} » n'est plus disponible")

    supplements = _verifier_choix(menu, ligne.choix)

    ligne_db = LigneCommande(
        menu_id=int(menu.id),
        quantite=ligne.quantite,
        prix_unitaire=_dec(menu.prix) + supplements,  # prix figé à la commande
    )
    for c in ligne.choix:
        ligne_db.choix.append(
            LigneCommandeChoix(groupe_id=c.groupe_id, produit_id=c.produit_id)
        )
    return ligne_db


def create_commande(db: Session, data: CommandeCreate, utilisateur_id: int):
    existe = db.execute(
        select(Commande.id).where(Commande.numero == data.numero)
    ).first()
    if existe is not None:
        raise HTTPException(status_code=409, detail="Ce numéro de commande existe déjà")

    commande = Commande(
        numero=data.numero,
        mode=data.mode,
        heure_livraison=data.heure_livraison,
        statut=StatutCommande.saisie,   # une commande naît toujours « saisie »
        utilisateur_id=utilisateur_id,  # vient du token, pas du client
        total=Decimal("0"),
    )

    total = Decimal("0")
    for ligne in data.lignes:
        if ligne.produit_id is not None:
            produit = _get_produit_disponible(db, ligne.produit_id)
            ligne_db = LigneCommande(
                produit_id=int(produit.id),
                quantite=ligne.quantite,
                prix_unitaire=_dec(produit.prix),  # prix figé à la commande
            )
        else:
            ligne_db = _construire_ligne_menu(db, ligne)

        commande.lignes.append(ligne_db)
        total += _dec(ligne_db.prix_unitaire) * ligne.quantite

    commande.total = total  # calculé par l'API, jamais envoyé par le client

    db.add(commande)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ce numéro de commande existe déjà")

    return get_commande(db, int(commande.id))


def list_commandes(
    skip: int,
    limit: int,
    db: Session,
    statut: StatutCommande | None = None,
    mode: ModeCommande | None = None,
):
    stmt = _requete_commande()

    if statut is not None:
        stmt = stmt.where(Commande.statut == statut)
    if mode is not None:
        stmt = stmt.where(Commande.mode == mode)

    # Heure de livraison croissante (celles sans heure à la fin), puis ordre d'arrivée
    stmt = (
        stmt.order_by(Commande.heure_livraison.asc().nulls_last(), Commande.created_at.asc())
        .offset(skip)
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


def get_commande(db: Session, commande_id: int):
    stmt = _requete_commande().where(Commande.id == commande_id)
    commande = db.execute(stmt).scalars().first()

    if commande is None:
        raise HTTPException(status_code=404, detail="Commande introuvable")

    return commande


def changer_statut(db: Session, commande_id: int, nouveau: StatutCommande):
    commande = get_commande(db, commande_id)

    if nouveau not in TRANSITIONS[commande.statut]:
        raise HTTPException(
            status_code=409,
            detail=f"Passage de « {commande.statut.value} » à « {nouveau.value} » impossible",
        )

    commande.statut = nouveau
    db.commit()

    return get_commande(db, commande_id)


def delete_commande(db: Session, commande_id: int):
    commande = get_commande(db, commande_id)

    db.delete(commande)  # les lignes et leurs choix partent avec (cascade)
    db.commit()