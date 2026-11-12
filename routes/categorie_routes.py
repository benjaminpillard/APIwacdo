from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from utils.auth import require_role
from utils.docs import AUTH, erreurs

from models.user import Utilisateur
from models.database import get_db

from schemas.categorie import CategorieCreate, CategorieOut

from controllers import categorie as categorie_controller

categorie_router = APIRouter(
    prefix="/categories",
    tags=["Catégories"]
)

ID_CATEGORIE = Path(description="Identifiant de la catégorie", ge=1)


@categorie_router.get(
    "/",
    response_model=list[CategorieOut],
    summary="Lister les catégories",
    responses=erreurs(*AUTH),
)
def list_categories_route(
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """Liste triée par nom. **Rôles :** tous."""
    return categorie_controller.list_categories(db)


@categorie_router.get(
    "/{categorie_id}",
    response_model=CategorieOut,
    summary="Détail d'une catégorie",
    responses=erreurs(*AUTH, 404),
)
def get_categorie_route(
    categorie_id: int = ID_CATEGORIE,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """**Rôles :** tous."""
    return categorie_controller.get_categorie_by_id(categorie_id, db)


@categorie_router.post(
    "/",
    response_model=CategorieOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer une catégorie",
    responses=erreurs(*AUTH, 409),
)
def create_categorie_route(
    categorie: CategorieCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Renvoie **409** si une catégorie porte déjà ce nom.

    **Rôle :** administrateur.
    """
    return categorie_controller.create_categorie(db, categorie)


@categorie_router.put(
    "/{categorie_id}",
    response_model=CategorieOut,
    summary="Renommer une catégorie",
    responses=erreurs(*AUTH, 404, 409),
)
def update_categorie_route(
    categorie: CategorieCreate,
    categorie_id: int = ID_CATEGORIE,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """**Rôle :** administrateur."""
    return categorie_controller.update_categorie(db, categorie_id, categorie)


@categorie_router.delete(
    "/{categorie_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer une catégorie",
    responses=erreurs(*AUTH, 404, 409),
)
def delete_categorie_route(
    categorie_id: int = ID_CATEGORIE,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Renvoie **409** si des produits ou un groupe de menu utilisent encore la catégorie.

    **Rôle :** administrateur.
    """
    categorie_controller.delete_categorie(db, categorie_id)
    return None
