from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload

from controllers.base import CRUDBase
from controllers.menu import menu_controller
from models.commande import Commande, LigneCommande, LigneCommandeChoix
from models.enums import StatutCommande, ModeCommande
from models.menu import Menu
from models.produit import Produit
from schemas.commande import CommandeCreate, LigneCreate, ChoixCreate
from utils.logger import audit

# Les changements de statut autorisés : on ne peut pas sauter d'étape ni revenir en arrière
TRANSITIONS = {
    StatutCommande.saisie: {StatutCommande.preparee},
    StatutCommande.preparee: {StatutCommande.livree},
    StatutCommande.livree: set(),
}


def _dec(valeur) -> Decimal:
    # Convertit proprement en Decimal (évite les erreurs d'arrondi des float)
    return Decimal(str(valeur))


class CommandeController(CRUDBase[Commande]):
    message_introuvable = "Commande introuvable"
    message_doublon = "Ce numéro de commande existe déjà"

    def requete(self) -> Select:
        # Surcharge : charge d'un coup les lignes, leurs produits/menus et leurs choix
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

    def lister_filtre(
        self,
        db: Session,
        skip: int,
        limit: int,
        statut: StatutCommande | None = None,
        mode: ModeCommande | None = None,
    ):
        filtres = []
        if statut is not None:
            filtres.append(Commande.statut == statut)
        if mode is not None:
            filtres.append(Commande.mode == mode)
        # Heure de livraison croissante (celles sans heure à la fin), puis ordre d'arrivée
        tri = [Commande.heure_livraison.asc().nulls_last(), Commande.created_at.asc()]
        return self.lister(db, skip=skip, limit=limit, filtres=filtres, tri=tri)

    def saisir(self, db: Session, donnees: CommandeCreate, utilisateur_id: int) -> Commande:
        """Création spécifique (pas le create générique) : chaque ligne est vérifiée
        et son prix figé, puis le total est calculé par l'API."""
        if db.execute(select(Commande.id).where(Commande.numero == donnees.numero)).first():
            raise HTTPException(status_code=409, detail=self.message_doublon)

        commande = Commande(
            numero=donnees.numero,
            mode=donnees.mode,
            heure_livraison=donnees.heure_livraison,
            statut=StatutCommande.saisie,   # une commande naît toujours « saisie »
            utilisateur_id=utilisateur_id,  # vient du token, pas du client
            total=Decimal("0"),
        )

        total = Decimal("0")
        for ligne in donnees.lignes:
            if ligne.produit_id is not None:
                ligne_db = self._ligne_produit(db, ligne)
            else:
                ligne_db = self._ligne_menu(db, ligne)
            commande.lignes.append(ligne_db)
            total += _dec(ligne_db.prix_unitaire) * ligne.quantite

        commande.total = total  # calculé par l'API, jamais envoyé par le client

        db.add(commande)
        self._commit(db)   # 409 si le numéro a été pris entre-temps
        audit.info(
            "Commande créée : numéro=%s mode=%s total=%s utilisateur_id=%s",
            commande.numero, commande.mode.value, commande.total, utilisateur_id,
        )
        return self.get(db, commande.id)

    def changer_statut(self, db: Session, commande_id: int, nouveau: StatutCommande, auteur: str = "?") -> Commande:
        commande = self.get(db, commande_id)

        if nouveau not in TRANSITIONS[commande.statut]:
            raise HTTPException(
                status_code=409,
                detail=f"Passage de « {commande.statut.value} » à « {nouveau.value} » impossible",
            )

        ancien = commande.statut
        commande.statut = nouveau
        db.commit()
        audit.info(
            "Statut de commande : numéro=%s %s -> %s par=%s",
            commande.numero, ancien.value, nouveau.value, auteur,
        )
        return self.get(db, commande_id)

    def supprimer(self, db: Session, commande_id: int, auteur: str = "?") -> None:
        commande = self.get(db, commande_id)
        numero = commande.numero
        super().delete(db, commande)   # les lignes et leurs choix partent avec (cascade)
        audit.info("Commande supprimée : numéro=%s par=%s", numero, auteur)

    # ---------- Construction des lignes ----------

    def _ligne_produit(self, db: Session, ligne: LigneCreate) -> LigneCommande:
        produit = db.get(Produit, ligne.produit_id)
        if produit is None:
            raise HTTPException(status_code=404, detail=f"Produit {ligne.produit_id} introuvable")
        if not produit.disponible:
            raise HTTPException(status_code=400, detail=f"« {produit.nom} » n'est plus disponible")
        return LigneCommande(
            produit_id=produit.id,
            quantite=ligne.quantite,
            prix_unitaire=_dec(produit.prix),  # prix figé à la commande
        )

    def _ligne_menu(self, db: Session, ligne: LigneCreate) -> LigneCommande:
        menu = menu_controller.get(db, ligne.menu_id)  # 404 si le menu n'existe pas

        if not menu.disponible or not menu.produit_principal.disponible:
            raise HTTPException(status_code=400, detail=f"« {menu.nom} » n'est plus disponible")

        supplements = self._verifier_choix(menu, ligne.choix)

        ligne_db = LigneCommande(
            menu_id=menu.id,
            quantite=ligne.quantite,
            prix_unitaire=_dec(menu.prix) + supplements,  # prix figé à la commande
        )
        for c in ligne.choix:
            ligne_db.choix.append(LigneCommandeChoix(groupe_id=c.groupe_id, produit_id=c.produit_id))
        return ligne_db

    def _verifier_choix(self, menu: Menu, choix: list[ChoixCreate]) -> Decimal:
        """Vérifie les choix faits dans un menu et renvoie le total des suppléments."""
        groupes = {g.id: g for g in menu.groupes}
        nb_par_groupe: dict[int, int] = {}
        supplements = Decimal("0")

        for c in choix:
            groupe = groupes.get(c.groupe_id)
            if groupe is None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Le groupe {c.groupe_id} ne fait pas partie de ce menu",
                )

            proposes = {p.id for p in groupe.produits_proposes}
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
            nb = nb_par_groupe.get(groupe.id, 0)
            if groupe.obligatoire and nb == 0:
                raise HTTPException(status_code=400, detail=f"Choix obligatoire manquant : « {groupe.nom} »")
            if nb > groupe.max_choix:
                raise HTTPException(
                    status_code=400,
                    detail=f"« {groupe.nom} » : {groupe.max_choix} choix maximum",
                )

        return supplements


commande_controller = CommandeController(Commande)
