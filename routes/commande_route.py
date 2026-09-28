from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from models.database import get_db
from models.enums import StatutCommande, ModeCommande
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
    limit: int = 20,
    statut: StatutCommande | None = None,
    mode: ModeCommande | None = None,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    # Ex. le préparateur appelle /commandes/?statut=saisie : les commandes à préparer,
    # triées par heure de livraison croissante
    return commande_controller.list_commandes(skip, limit, db, statut, mode)


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
    current_user: Utilisateur = Depends(require_role("administrateur", "accueil"))
):
    # L'auteur de la commande est la personne connectée, pas une valeur envoyée par le client
    return commande_controller.create_commande(db, commande, int(current_user.id))


@commande_router.post("/{commande_id}/preparer", response_model=CommandeOut)
def preparer_commande_route(
    commande_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur"))
):
    # saisie -> preparee
    return commande_controller.changer_statut(db, commande_id, StatutCommande.preparee)


@commande_router.post("/{commande_id}/livrer", response_model=CommandeOut)
def livrer_commande_route(
    commande_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "accueil"))
):
    # preparee -> livree
    return commande_controller.changer_statut(db, commande_id, StatutCommande.livree)


@commande_router.delete("/{commande_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_commande_route(
    commande_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    commande_controller.delete_commande(db, commande_id)
    return None