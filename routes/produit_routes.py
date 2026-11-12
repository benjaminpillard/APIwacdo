from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from utils.auth import require_role
from utils.docs import AUTH, erreurs

from models.user import Utilisateur
from models.database import get_db
from schemas.produit import ProduitCreate, ProduitOut, ProduitUpdate

from controllers.produit import produit_controller

produit_router = APIRouter(
    prefix="/produits",
    tags=["Produits"]
)

ID_PRODUIT = Path(description="Identifiant du produit", ge=1)


@produit_router.get(
    "/",
    response_model=list[ProduitOut],
    summary="Lister les produits",
    responses=erreurs(*AUTH),
)
def list_produits_route(
    skip: int = Query(0, ge=0, description="Nombre de produits à sauter (pagination)"),
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum de produits renvoyés"),
    categorie_id: int | None = Query(None, description="Ne garder que les produits de cette catégorie"),
    disponible: bool | None = Query(None, description="true : seulement les disponibles, false : seulement les indisponibles"),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """Liste des produits triée par nom, filtrable par catégorie et par disponibilité.

    **Rôles :** tous.
    """
    return produit_controller.lister_filtre(db, skip, limit, categorie_id, disponible)


@produit_router.get(
    "/search",
    response_model=list[ProduitOut],
    summary="Rechercher des produits par nom",
    responses=erreurs(*AUTH, 404),
)
def search_produits_route(
    title: str = Query(min_length=1, description="Tout ou partie du nom (insensible à la casse)", examples=["burger"]),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """Renvoie les produits dont le nom contient le texte recherché.

    **Rôles :** tous. Renvoie 404 si aucun produit ne correspond.
    """
    return produit_controller.rechercher(db, title)


@produit_router.get(
    "/{produit_id}",
    response_model=ProduitOut,
    summary="Détail d'un produit",
    responses=erreurs(*AUTH, 404),
)
def get_produit_route(
    produit_id: int = ID_PRODUIT,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """**Rôles :** tous."""
    return produit_controller.get(db, produit_id)


@produit_router.post(
    "/",
    response_model=ProduitOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un produit",
    responses=erreurs(*AUTH, 404),
)
def create_produit_route(
    produit: ProduitCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Ajoute un produit au catalogue.

    **Rôle :** administrateur. Renvoie 404 si la catégorie indiquée n'existe pas.
    """
    return produit_controller.create(db, produit)


@produit_router.put(
    "/{produit_id}",
    response_model=ProduitOut,
    summary="Modifier un produit (toutes les informations)",
    responses=erreurs(*AUTH, 404),
)
def update_produit_route(
    produit: ProduitCreate,
    produit_id: int = ID_PRODUIT,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Remplace toutes les informations du produit (les champs absents reprennent leur valeur par défaut).

    **Rôle :** administrateur.
    """
    produit_existant = produit_controller.get(db, produit_id)
    return produit_controller.update(db, produit_existant, produit, partiel=False)


@produit_router.patch(
    "/{produit_id}",
    response_model=ProduitOut,
    summary="Modifier une partie d'un produit",
    responses=erreurs(*AUTH, 404),
)
def patch_produit_route(
    produit: ProduitUpdate,
    produit_id: int = ID_PRODUIT,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Seuls les champs envoyés sont modifiés.
    Exemple pour rendre un produit indisponible : `{"disponible": false}`.

    **Rôle :** administrateur.
    """
    produit_existant = produit_controller.get(db, produit_id)
    return produit_controller.update(db, produit_existant, produit, partiel=True)


@produit_router.delete(
    "/{produit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un produit",
    responses=erreurs(*AUTH, 404, 409),
)
def delete_produit_route(
    produit_id: int = ID_PRODUIT,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Supprime un produit jamais utilisé.

    Renvoie **409** si le produit a déjà été commandé ou s'il fait partie d'un menu :
    pour préserver l'historique, il faut alors le rendre indisponible.

    **Rôle :** administrateur.
    """
    produit_controller.delete(db, produit_controller.get(db, produit_id))
    return None
