from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from utils.auth import require_role

from models.user import Utilisateur
from models.database import get_db

from schemas.categorie import CategorieCreate, CategorieOut

from controllers import categorie as categorie_controller

categorie_router = APIRouter(
    prefix="/categories",
    tags=["Catégories"]
)


@categorie_router.get("/", response_model=list[CategorieOut])
def list_categories_route(
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return categorie_controller.list_categories(db)


@categorie_router.get("/{categorie_id}", response_model=CategorieOut)
def get_categorie_route(
    categorie_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return categorie_controller.get_categorie_by_id(categorie_id, db)


@categorie_router.post("/", response_model=CategorieOut, status_code=status.HTTP_201_CREATED)
def create_categorie_route(
    categorie: CategorieCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    return categorie_controller.create_categorie(db, categorie)


@categorie_router.put("/{categorie_id}", response_model=CategorieOut)
def update_categorie_route(
    categorie_id: int,
    categorie: CategorieCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    return categorie_controller.update_categorie(db, categorie_id, categorie)


@categorie_router.delete("/{categorie_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_categorie_route(
    categorie_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    categorie_controller.delete_categorie(db, categorie_id)
    return None