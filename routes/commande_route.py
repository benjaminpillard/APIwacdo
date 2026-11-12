from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from models.database import get_db
from models.enums import StatutCommande, ModeCommande
from models.user import Utilisateur
from utils.auth import require_role
from utils.docs import AUTH, erreurs

from schemas.commande import CommandeCreate, CommandeOut

from controllers import commande as commande_controller

commande_router = APIRouter(
    prefix="/commandes",
    tags=["Commandes"]
)

ID_COMMANDE = Path(description="Identifiant de la commande", ge=1)


@commande_router.get(
    "/",
    response_model=list[CommandeOut],
    summary="Lister les commandes",
    responses=erreurs(*AUTH),
)
def list_commandes_route(
    skip: int = Query(0, ge=0, description="Nombre de commandes à sauter (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Nombre maximum de commandes renvoyées"),
    statut: StatutCommande | None = Query(None, description="Filtrer sur le statut"),
    mode: ModeCommande | None = Query(None, description="Filtrer sur le mode de prise de commande"),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """Commandes triées par **heure de livraison croissante** (celles sans heure en dernier),
    puis par ordre d'arrivée.

    - Préparation : `?statut=saisie` donne les commandes **à préparer**.
    - Accueil : `?statut=preparee` donne les commandes **à remettre au client**.

    **Rôles :** tous.
    """
    return commande_controller.list_commandes(skip, limit, db, statut, mode)


@commande_router.get(
    "/{commande_id}",
    response_model=CommandeOut,
    summary="Détail d'une commande",
    responses=erreurs(*AUTH, 404),
)
def get_commande_route(
    commande_id: int = ID_COMMANDE,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """Lignes, produits, menus et choix faits dans chaque menu. **Rôles :** tous."""
    return commande_controller.get_commande(db, commande_id)


@commande_router.post(
    "/",
    response_model=CommandeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Saisir une commande",
    responses=erreurs(*AUTH, 400, 404, 409),
)
def create_commande_route(
    commande: CommandeCreate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("administrateur", "accueil"))
):
    """Saisie d'une commande au comptoir ou par téléphone. Elle est créée au statut **saisie**.

    - Les **prix sont figés** au moment de la commande et le **total est calculé par l'API**.
    - Pour un menu, les choix (boisson, accompagnement...) sont vérifiés : groupes obligatoires
      remplis, nombre maximum respecté, produits proposés et disponibles.
    - L'auteur est l'utilisateur connecté.

    Erreurs : **400** produit indisponible ou choix invalide, **404** produit ou menu inconnu,
    **409** numéro de ticket déjà utilisé.

    **Rôles :** accueil, administrateur.
    """
    return commande_controller.create_commande(db, commande, int(current_user.id))


@commande_router.post(
    "/{commande_id}/preparer",
    response_model=CommandeOut,
    summary="Déclarer une commande préparée",
    responses=erreurs(*AUTH, 404, 409),
)
def preparer_commande_route(
    commande_id: int = ID_COMMANDE,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("administrateur", "preparateur"))
):
    """Passe la commande de **saisie** à **preparee** : elle peut alors être remise au client.

    Renvoie **409** si la commande n'est pas au statut « saisie ».

    **Rôles :** préparateur, administrateur.
    """
    return commande_controller.changer_statut(
        db, commande_id, StatutCommande.preparee, str(current_user.username)
    )


@commande_router.post(
    "/{commande_id}/livrer",
    response_model=CommandeOut,
    summary="Remettre une commande au client",
    responses=erreurs(*AUTH, 404, 409),
)
def livrer_commande_route(
    commande_id: int = ID_COMMANDE,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("administrateur", "accueil"))
):
    """Passe la commande de **preparee** à **livree**.

    Renvoie **409** si la commande n'a pas encore été préparée (on ne saute pas d'étape).

    **Rôles :** accueil, administrateur.
    """
    return commande_controller.changer_statut(
        db, commande_id, StatutCommande.livree, str(current_user.username)
    )


@commande_router.delete(
    "/{commande_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une commande",
    responses=erreurs(*AUTH, 404),
)
def delete_commande_route(
    commande_id: int = ID_COMMANDE,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("administrateur"))
):
    """Supprime la commande avec ses lignes et ses choix. **Rôle :** administrateur."""
    commande_controller.delete_commande(db, commande_id, str(current_user.username))
    return None
