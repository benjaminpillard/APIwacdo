from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from schemas.categorie import CategorieCreate
from models.categorie import Categorie
from models.produit import Produit


def create_categorie(db: Session, categorie: CategorieCreate):
    categorie_to_create = Categorie(**categorie.model_dump())

    db.add(categorie_to_create)
    try:
        db.commit()
    except IntegrityError:
        # Le nom est unique dans la base : deux catégories ne peuvent pas avoir le même
        db.rollback()
        raise HTTPException(status_code=409, detail="Cette catégorie existe déjà")
    db.refresh(categorie_to_create)

    return categorie_to_create


def list_categories(db: Session):
    # Tri par nom pour un affichage stable
    stmt = select(Categorie).order_by(Categorie.nom)
    return db.execute(stmt).scalars().all()


def get_categorie_by_id(categorie_id: int, db: Session):
    categorie = db.get(Categorie, categorie_id)

    if categorie is None:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")

    return categorie


def update_categorie(db: Session, categorie_id: int, data: CategorieCreate):
    categorie = get_categorie_by_id(categorie_id, db)
    for key, value in data.model_dump().items():
        setattr(categorie, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Cette catégorie existe déjà")
    db.refresh(categorie)

    return categorie


def delete_categorie(db: Session, categorie_id: int):
    categorie = get_categorie_by_id(categorie_id, db)

    # On refuse de supprimer une catégorie qui contient encore des produits
    produit_lie = db.execute(
        select(Produit.id).where(Produit.categorie_id == categorie_id).limit(1)
    ).first()
    if produit_lie is not None:
        raise HTTPException(
            status_code=409,
            detail="Impossible de supprimer : des produits utilisent cette catégorie",
        )

    db.delete(categorie)
    db.commit()