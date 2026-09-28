from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from fastapi import HTTPException

from models.menu import Menu, MenuGroupe, MenuGroupeProduit
from models.produit import Produit
from models.commande import LigneCommande, LigneCommandeChoix
from schemas.menu import MenuCreate, GroupeCreate, OptionCreate
from models.categorie import Categorie


def _requete_menu():
    # Charge d'un coup le plat principal, les groupes, leurs options,
    # leur catégorie et les produits de cette catégorie
    return select(Menu).options(
        selectinload(Menu.produit_principal),
        selectinload(Menu.groupes)
        .selectinload(MenuGroupe.options)
        .selectinload(MenuGroupeProduit.produit),
        selectinload(Menu.groupes)
        .selectinload(MenuGroupe.categorie)
        .selectinload(Categorie.produits),
    )

def _verifier_produit(db: Session, produit_id: int):
    produit = db.get(Produit, produit_id)
    if produit is None:
        raise HTTPException(status_code=404, detail="Produit introuvable")
    return produit


def _get_groupe(db: Session, groupe_id: int) -> MenuGroupe:
    groupe = db.get(MenuGroupe, groupe_id)
    if groupe is None:
        raise HTTPException(status_code=404, detail="Groupe introuvable")
    return groupe


# ---------- Menus ----------

def create_menu(db: Session, menu: MenuCreate):
    _verifier_produit(db, menu.produit_principal_id)

    menu_to_create = Menu(**menu.model_dump())
    db.add(menu_to_create)
    db.commit()

    return get_menu_by_id(menu_to_create.id, db)


def list_menus(skip: int, limit: int, db: Session, disponible: bool | None = None):
    stmt = _requete_menu()

    if disponible is not None:
        stmt = stmt.where(Menu.disponible == disponible)

    stmt = stmt.order_by(Menu.nom).offset(skip).limit(limit)
    return db.execute(stmt).scalars().all()


def get_menu_by_id(menu_id: int, db: Session):
    stmt = _requete_menu().where(Menu.id == menu_id)
    menu = db.execute(stmt).scalars().first()

    if menu is None:
        raise HTTPException(status_code=404, detail="Menu introuvable")

    return menu


def get_menu_by_nom(nom: str, db: Session):
    stmt = _requete_menu().where(Menu.nom.ilike(f"%{nom}%")).order_by(Menu.nom)
    menus = db.execute(stmt).scalars().all()

    if not menus:
        raise HTTPException(status_code=404, detail="Aucun menu trouvé")

    return menus


def update_menu(db: Session, menu_id: int, data: MenuCreate):
    menu = get_menu_by_id(menu_id, db)
    _verifier_produit(db, data.produit_principal_id)

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(menu, key, value)

    db.commit()

    return get_menu_by_id(menu_id, db)


def delete_menu(db: Session, menu_id: int):
    menu = get_menu_by_id(menu_id, db)

    # On garde l'historique : impossible de supprimer un menu déjà commandé
    deja_commande = db.execute(
        select(LigneCommande.id).where(LigneCommande.menu_id == menu_id).limit(1)
    ).first()
    if deja_commande is not None:
        raise HTTPException(
            status_code=409,
            detail="Impossible de supprimer : ce menu a déjà été commandé (désactivez-le plutôt)",
        )

    db.delete(menu)
    db.commit()


# ---------- Groupes de choix (Boisson, Accompagnement, Sauce...) ----------

def add_groupe(db: Session, menu_id: int, data: GroupeCreate):
    menu = get_menu_by_id(menu_id, db)

    if data.categorie_id is not None and db.get(Categorie, data.categorie_id) is None:
        raise HTTPException(status_code=404, detail="Catégorie introuvable")

    groupe = MenuGroupe(menu_id=int(menu.id), **data.model_dump())
    db.add(groupe)
    db.commit()

    return get_menu_by_id(menu_id, db)

def delete_groupe(db: Session, groupe_id: int):
    groupe = _get_groupe(db, groupe_id)
    menu_id = groupe.menu_id

    deja_choisi = db.execute(
        select(LigneCommandeChoix.id)
        .where(LigneCommandeChoix.groupe_id == groupe_id)
        .limit(1)
    ).first()
    if deja_choisi is not None:
        raise HTTPException(
            status_code=409,
            detail="Impossible de supprimer : ce groupe a déjà été utilisé dans une commande",
        )

    db.delete(groupe)
    db.commit()

    return get_menu_by_id(menu_id, db)


# ---------- Options d'un groupe (Frites, Coca, Ketchup...) ----------

def add_option(db: Session, groupe_id: int, data: OptionCreate):
    groupe = _get_groupe(db, groupe_id)
    menu_id = groupe.menu_id
    if groupe.categorie_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Ce groupe est lié à une catégorie : ses produits viennent de la catégorie",
        )
    _verifier_produit(db, data.produit_id)

    deja_present = db.execute(
        select(MenuGroupeProduit.id).where(
            MenuGroupeProduit.groupe_id == groupe_id,
            MenuGroupeProduit.produit_id == data.produit_id,
        )
    ).first()
    if deja_present is not None:
        raise HTTPException(status_code=409, detail="Ce produit est déjà dans ce groupe")

    option = MenuGroupeProduit(groupe_id=groupe_id, **data.model_dump())
    db.add(option)
    db.commit()

    return get_menu_by_id(menu_id, db)


def remove_option(db: Session, groupe_id: int, produit_id: int):
    groupe = _get_groupe(db, groupe_id)
    menu_id = groupe.menu_id

    option = db.execute(
        select(MenuGroupeProduit).where(
            MenuGroupeProduit.groupe_id == groupe_id,
            MenuGroupeProduit.produit_id == produit_id,
        )
    ).scalars().first()
    if option is None:
        raise HTTPException(status_code=404, detail="Ce produit n'est pas dans ce groupe")

    db.delete(option)
    db.commit()

    return get_menu_by_id(menu_id, db)