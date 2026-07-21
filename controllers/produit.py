from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException


from schemas.produit import ProduitCreate
from models.produit import Produit
from models.menu import Menu
from models.commande import Commande

def create_produit(db: Session, produit: ProduitCreate):
    produit_to_create = Produit(
        produit=produit.produit,
        price=produit.price,
        user_id=produit.user_id
    )

    db.add(produit_to_create)
    db.commit()
    db.refresh(produit_to_create)
    return produit_to_create

def list_produits(skip: int, limit: int, db: Session):
    stmt = select(Produit).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()

def get_produit(db: Session, produit_id: int):
    stmt = select(Produit).where(Produit.id == produit_id)
    produit = db.execute(stmt).scalars().first()

    if produit is None:
        raise HTTPException(
            status_code=404,
            detail="Produit introuvable"
        )

    return produit

def update_produit(db: Session, produit_id: int, data: ProduitCreate):
    produit = get_produit(db, produit_id)

    for key, value in data.model_dump().items():
        if value is not None:
            setattr(produit, key, value)

    db.commit()
    db.refresh(produit)

    return produit


def delete_produit(db: Session, produit_id: int):
    produit = get_produit(db, produit_id)

    db.delete(produit)
    db.commit()

    return produit

def add_menu_to_produit(db: Session, produit_id: int, menu_id: int):
    produit = get_produit(db, produit_id)
    menu = db.get(Menu, menu_id)

    if menu is None:
        raise HTTPException(
            status_code=404,
            detail="Menu introuvable"
        )

    if menu not in produit.menus:
        produit.menus.append(menu)
        db.commit()
        db.refresh(produit)

    return produit

def remove_menu_from_produit(db: Session, produit_id: int, menu_id: int):
    produit = get_produit(db, produit_id)
    menu = db.get(Menu, menu_id)

    if menu is None:
        raise HTTPException(
            status_code=404,
            detail="Menu introuvable"
        )

    if menu in produit.menus:
        produit.menus.remove(menu)
        db.commit()
        db.refresh(produit)

    return produit

def add_commande_to_produit(db: Session, produit_id: int, commande_id: int):
    produit = get_produit(db, produit_id)
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise HTTPException(
            status_code=404,
            detail="Commande introuvable"
        )

    if commande not in produit.commandes:
        produit.commandes.append(commande)
        db.commit()
        db.refresh(produit)

    return produit

def remove_commande_from_produit(db: Session, produit_id: int, commande_id: int):
    produit = get_produit(db, produit_id)
    commande = db.get(Commande, commande_id)

    if commande is None:
        raise HTTPException(
            status_code=404,
            detail="Commande introuvable"
        )

    if commande in produit.commandes:
        produit.commandes.remove(commande)
        db.commit()
        db.refresh(produit)

    return produit
