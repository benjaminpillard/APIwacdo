from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException

from schemas.produit import ProduitCreate
from models.produit import Produit
from models.menu import Menu
from models.commande import Commande


def create_produit(db: Session, produit: ProduitCreate):
    produit_to_create = Produit(
        title=produit.title,
        price=produit.price,
        currency=produit.currency
    )

    db.add(produit_to_create)
    db.commit()
    db.refresh(produit_to_create)

    return produit_to_create


def list_produits(skip: int, limit: int, db: Session):
    stmt = select(Produit).offset(skip).limit(limit)
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
        .filter(Produit.title.ilike(f"%{title}%"))
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
    data: ProduitCreate
):
    produit = get_produit_by_id(produit_id, db)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(produit, key, value)

    db.commit()
    db.refresh(produit)

    return produit


def delete_produit(db: Session, produit_id: int):
    produit = get_produit_by_id(produit_id, db)

    db.delete(produit)
    db.commit()

    return produit


def add_menu_to_produit(
    db: Session,
    produit_id: int,
    menu_id: int
):
    produit = get_produit_by_id(produit_id, db)
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


def remove_menu_from_produit(
    db: Session,
    produit_id: int,
    menu_id: int
):
    produit = get_produit_by_id(produit_id, db)
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


def add_commande_to_produit(
    db: Session,
    produit_id: int,
    commande_id: int
):
    produit = get_produit_by_id(produit_id, db)
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


def remove_commande_from_produit(
    db: Session,
    produit_id: int,
    commande_id: int
):
    produit = get_produit_by_id(produit_id, db)
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