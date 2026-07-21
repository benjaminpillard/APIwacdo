from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from utils.auth import require_role

from models.user import Utilisateur
from models.database import get_db

from schemas.menu import MenuCreate, MenuOut

from controllers import menu as menu_controller


menu_router = APIRouter(
    prefix="/menus",
    tags=["Menus"]
)


@menu_router.get("/", response_model=list[MenuOut])
def list_menus_route(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return menu_controller.list_menus(skip, limit, db)


@menu_router.get("/search", response_model=list[MenuOut])
def search_menu_route(
    nom: str,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return menu_controller.get_menu_by_nom(nom, db)


@menu_router.get("/{menu_id}", response_model=MenuOut)
def get_menu_route(
    menu_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return menu_controller.get_menu_by_id(menu_id, db)


@menu_router.post("/", response_model=MenuOut, status_code=status.HTTP_201_CREATED)
def create_menu_route(
    menu: MenuCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    return menu_controller.create_menu(db, menu)


@menu_router.put("/{menu_id}", response_model=MenuOut)
def update_menu_route(
    menu_id: int,
    menu: MenuCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    return menu_controller.update_menu(db, menu_id, menu)


@menu_router.delete("/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_route(
    menu_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    menu_controller.delete_menu(db, menu_id)
    return None


@menu_router.post("/{menu_id}/produits/{produit_id}", response_model=MenuOut)
def add_produit_to_menu_route(
    menu_id: int,
    produit_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    return menu_controller.add_produit_to_menu(db, menu_id, produit_id)


@menu_router.delete("/{menu_id}/produits/{produit_id}", response_model=MenuOut)
def remove_produit_from_menu_route(
    menu_id: int,
    produit_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    return menu_controller.remove_produit_from_menu(db, menu_id, produit_id)