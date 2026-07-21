from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from models.commande import Commande
from models.produit import Produit
from schemas.commande import CommandeCreate


def create_commande(db: Session, commande: CommandeCreate):
    commande_to_create = Commande(
        numero=commande.numero,
        statut=commande.statut,
        total=commande.total,
        user_id=commande.user_id
    )

    db.add(commande_to_create)
    db.commit()
    db.refresh(commande_to_create)

    return commande_to_create


def list_commandes(skip: int, limit: int, db: Session):
    stmt = select(Commande).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()


def get_commande(db: Session, commande_id: int):
    stmt = select(Commande).where(Commande.id == commande_id)
    commande = db.execute(stmt).scalars().first()

    if commande is None:
        raise HTTPException(
            status_code=404,
            detail="Commande introuvable"
        )

    return commande


def update_commande(db: Session, commande_id: int, data: CommandeCreate):
    commande = get_commande(db, commande_id)

    for key, value in data.model_dump().items():
        if value is not None:
            setattr(commande, key, value)

    db.commit()
    db.refresh(commande)

    return commande


def delete_commande(db: Session, commande_id: int):
    commande = get_commande(db, commande_id)

    db.delete(commande)
    db.commit()

    return commande

def add_produit_to_commande(db: Session, commande_id: int, produit_id: int):
    commande = get_commande(db, commande_id)
    produit = db.get(Produit, produit_id)

    if produit is None:
        raise HTTPException(
            status_code=404,
            detail="Produit introuvable"
        )

    if produit not in commande.produits:
        commande.produits.append(produit)
        db.commit()
        db.refresh(commande)

    return commande

def remove_produit_from_commande(db: Session, commande_id: int, produit_id: int):
    commande = get_commande(db, commande_id)
    produit = db.get(Produit, produit_id)

    if produit is None:
        raise HTTPException(
            status_code=404,
            detail="Produit introuvable"
        )

    if produit in commande.produits:
        commande.produits.remove(produit)
        db.commit()
        db.refresh(commande)

    return commande
