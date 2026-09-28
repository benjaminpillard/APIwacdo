from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from schemas.produit import ProduitCreate
from models.produit import Produit
from schemas.produit import ProduitCreate, ProduitUpdate


def create_produit(db: Session, produit: ProduitCreate):
    # Construire puis enregistrer un produit
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

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(produit, key, value)

    db.commit()
    db.refresh(produit)

    return produit


def delete_produit(db: Session, produit_id: int):
    # Supprimer un produit par son id
    produit = get_produit_by_id(produit_id, db)

    db.delete(produit)
    db.commit()

    return produit