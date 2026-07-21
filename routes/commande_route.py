from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from models.database import get_db
from models.user import Utilisateur
from utils.auth import require_role

from schemas.commande import CommandeCreate, CommandeOut

from controllers import commande as commande_controller

commande_router = APIRouter(
    prefix="/commandes",
    tags=["Commandes"]
)

@commande_router.get("/", response_model=list[CommandeOut])
def list_commandes_route(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return commande_controller.list_commandes(skip, limit, db)


@commande_router.get("/{commande_id}", response_model=CommandeOut)
def get_commande_route(
    commande_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    return commande_controller.get_commande(db, commande_id)


@commande_router.post("/", response_model=CommandeOut, status_code=status.HTTP_201_CREATED)
def create_commande_route(
    commande: CommandeCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "accueil"))
):
    return commande_controller.create_commande(db, commande)


@commande_router.put("/{commande_id}", response_model=CommandeOut)
def update_commande_route(
    commande_id: int,
    commande: CommandeCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur"))
):
    return commande_controller.update_commande(db, commande_id, commande)


@commande_router.delete("/{commande_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_commande_route(
    commande_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    commande_controller.delete_commande(db, commande_id)
    return None


@commande_router.post("/{commande_id}/produits/{produit_id}", response_model=CommandeOut)
def add_produit_to_commande_route(
    commande_id: int,
    produit_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur"))
):
    return commande_controller.add_produit_to_commande(db, commande_id, produit_id)


@commande_router.delete("/{commande_id}/produits/{produit_id}", response_model=CommandeOut)
def remove_produit_from_commande_route(
    commande_id: int,
    produit_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur"))
):
    return commande_controller.remove_produit_from_commande(db, commande_id, produit_id)