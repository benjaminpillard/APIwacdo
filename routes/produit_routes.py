from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from utils.auth import require_role

from models.user import Utilisateur
from models.database import get_db
from schemas.produit import ProduitCreate, ProduitOut, ProduitUpdate

from controllers import produit as produit_controller

produit_router = APIRouter(
    prefix="/produits",
    tags=["Produits"]
)


@produit_router.get("/", response_model=list[ProduitOut])
def list_produits_route(
    skip: int = 0,
    limit: int = 10,
    categorie_id: int | None = None,
    disponible: bool | None = None,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return produit_controller.list_produits(skip, limit, db, categorie_id, disponible)


@produit_router.get("/search", response_model=list[ProduitOut])
def search_produits_route(
    title: str,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return produit_controller.get_produit_by_title(title, db)


@produit_router.get("/{produit_id}", response_model=ProduitOut)
def get_produit_route(
    produit_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return produit_controller.get_produit_by_id(produit_id, db)


@produit_router.post("/", response_model=ProduitOut, status_code=status.HTTP_201_CREATED)
def create_produit_route(
    produit: ProduitCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    return produit_controller.create_produit(db, produit)


@produit_router.put("/{produit_id}", response_model=ProduitOut)
def update_produit_route(
    produit_id: int,
    produit: ProduitCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    return produit_controller.update_produit(db, produit_id, produit)

@produit_router.patch("/{produit_id}", response_model=ProduitOut)
def patch_produit_route(
    produit_id: int,
    produit: ProduitUpdate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    return produit_controller.update_produit(db, produit_id, produit)

@produit_router.delete("/{produit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_produit_route(
    produit_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    produit_controller.delete_produit(db, produit_id)
    return None