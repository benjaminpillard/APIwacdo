from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from models.menu import Menu
from models.produit import Produit
from schemas import menu, produit
from schemas.menu import MenuCreate


def create_menu(db: Session, menu: MenuCreate):
    menu_to_create = Menu(
        nom=menu.nom,
        price=menu.price
    )

    db.add(menu_to_create)
    db.commit()
    db.refresh(menu_to_create)

    return menu_to_create


def list_menu(skip: int, limit: int, db: Session):
    stmt = select(Menu).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()


def get_menu(db: Session, menu_id: int):
    stmt = select(Menu).where(Menu.id == menu_id)
    menu = db.execute(stmt).scalars().first()

    if menu is None:
        raise HTTPException(
            status_code=404,
            detail="Menu introuvable"
        )

    return menu


def update_menu(db: Session, menu_id: int, data: MenuCreate):
    menu = get_menu(db, menu_id)

    for key, value in data.model_dump().items():
        if value is not None:
            setattr(menu, key, value)

    db.commit()
    db.refresh(menu)

    return menu


def delete_menu(db: Session, menu_id: int):
    menu = get_menu(db, menu_id)

    db.delete(menu)
    db.commit()

    return menu

def add_produit_to_menu(db: Session, menu_id: int, produit_id: int):
    menu = get_menu(db, menu_id)
    produit = db.get(Produit, produit_id)

    if produit is None:
        raise HTTPException(
            status_code=404,
            detail="Produit introuvable"
        )

    if produit not in menu.produits:
        menu.produits.append(produit)
        db.commit()
        db.refresh(menu)

    return menu

def remove_produit_from_menu(db: Session, menu_id: int, produit_id: int):
    menu = get_menu(db, menu_id)
    produit = db.get(Produit, produit_id)

    if produit is None:
        raise HTTPException(
            status_code=404,
            detail="Produit introuvable"
        )

    if produit in menu.produits:
        menu.produits.remove(produit)
        db.commit()
        db.refresh(menu)

    return menu
