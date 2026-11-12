from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from models.produit import Produit
from models.categorie import Categorie
from models.menu import Menu, MenuGroupeProduit
from models.commande import LigneCommande, LigneCommandeChoix
from schemas.produit import ProduitCreate, ProduitUpdate


def _verifier_categorie(db: Session, categorie_id: int | None):
    # Une catégorie inexistante donnerait une erreur de clé étrangère : on renvoie une 404 claire
    if categorie_id is not None and db.get(Categorie, categorie_id) is None:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")


def create_produit(db: Session, produit: ProduitCreate):
    # Construire puis enregistrer un produit
    _verifier_categorie(db, produit.categorie_id)
    produit_to_create = Produit(**produit.model_dump())

    db.add(produit_to_create)
    db.commit()
    db.refresh(produit_to_create)

    return produit_to_create


def list_produits(
    skip: int,
    limit: int,
    db: Session,
    categorie_id: int | None = None,
    disponible: bool | None = None,
):
    # Filtres facultatifs : on ne les applique que s'ils sont fournis
    stmt = select(Produit)

    if categorie_id is not None:
        stmt = stmt.where(Produit.categorie_id == categorie_id)
    if disponible is not None:
        stmt = stmt.where(Produit.disponible == disponible)

    # Tri par nom, puis pagination
    stmt = stmt.order_by(Produit.nom).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()

def get_produit_by_id(produit_id: int, db: Session):
    produit = db.get(Produit, produit_id)

    if produit is None:
        raise HTTPException(
            status_code=404,
            detail="Produit introuvable"
        )

    return produit


def get_produit_by_title(title: str, db: Session):
    produits = (
        db.query(Produit)
        .filter(Produit.nom.ilike(f"%{title}%"))
        .all()
    )

    if not produits:
        raise HTTPException(
            status_code=404,
            detail="Aucun produit trouvé"
        )

    return produits


def update_produit(
    db: Session,
    produit_id: int,
    data: ProduitCreate | ProduitUpdate
):
    # Mettre a jour les champs recus
    produit = get_produit_by_id(produit_id, db)
    changements = data.model_dump(exclude_unset=True)

    if "categorie_id" in changements:
        _verifier_categorie(db, changements["categorie_id"])

    for key, value in changements.items():
        setattr(produit, key, value)

    db.commit()
    db.refresh(produit)

    return produit


def delete_produit(db: Session, produit_id: int):
    # Supprimer un produit par son id
    produit = get_produit_by_id(produit_id, db)

    # On garde l'historique et la cohérence des menus : un produit déjà utilisé
    # ne peut pas être supprimé, on le rend indisponible à la place.
    utilisations = [
        (select(LigneCommande.id).where(LigneCommande.produit_id == produit_id),
         "il a déjà été commandé"),
        (select(LigneCommandeChoix.id).where(LigneCommandeChoix.produit_id == produit_id),
         "il a déjà été choisi dans un menu commandé"),
        (select(Menu.id).where(Menu.produit_principal_id == produit_id),
         "il est le produit principal d'un menu"),
        (select(MenuGroupeProduit.id).where(MenuGroupeProduit.produit_id == produit_id),
         "il est proposé dans un menu"),
    ]
    for requete, raison in utilisations:
        if db.execute(requete.limit(1)).first() is not None:
            raise HTTPException(
                status_code=409,
                detail=f"Impossible de supprimer : {raison} (rendez-le indisponible plutôt)",
            )

    db.delete(produit)
    db.commit()

    return produit