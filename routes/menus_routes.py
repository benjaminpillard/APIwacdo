from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from utils.auth import require_role
from utils.docs import AUTH, erreurs

from models.user import Utilisateur
from models.database import get_db

from schemas.menu import MenuCreate, MenuOut, GroupeCreate, OptionCreate

from controllers import menu as menu_controller


menu_router = APIRouter(
    prefix="/menus",
    tags=["Menus"]
)

ID_MENU = Path(description="Identifiant du menu", ge=1)
ID_GROUPE = Path(description="Identifiant du groupe de choix (ex. « Boisson »)", ge=1)


# ---------- Menus ----------

@menu_router.get(
    "/",
    response_model=list[MenuOut],
    summary="Lister les menus (avec leur composition)",
    responses=erreurs(*AUTH),
)
def list_menus_route(
    skip: int = Query(0, ge=0, description="Nombre de menus à sauter (pagination)"),
    limit: int = Query(10, ge=1, le=100, description="Nombre maximum de menus renvoyés"),
    disponible: bool | None = Query(None, description="Filtrer sur la disponibilité"),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """Liste détaillée des menus, triée par nom : produit principal, groupes de choix
    (boisson, accompagnement...) et produits proposés dans chaque groupe.

    **Rôles :** tous.
    """
    return menu_controller.list_menus(skip, limit, db, disponible)


@menu_router.get(
    "/search",
    response_model=list[MenuOut],
    summary="Rechercher des menus par nom",
    responses=erreurs(*AUTH, 404),
)
def search_menu_route(
    nom: str = Query(min_length=1, description="Tout ou partie du nom (insensible à la casse)", examples=["big"]),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """**Rôles :** tous. Renvoie 404 si aucun menu ne correspond."""
    return menu_controller.get_menu_by_nom(nom, db)


@menu_router.get(
    "/{menu_id}",
    response_model=MenuOut,
    summary="Détail d'un menu",
    responses=erreurs(*AUTH, 404),
)
def get_menu_route(
    menu_id: int = ID_MENU,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur", "preparateur", "accueil"))
):
    """**Rôles :** tous."""
    return menu_controller.get_menu_by_id(menu_id, db)


@menu_router.post(
    "/",
    response_model=MenuOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un menu",
    responses=erreurs(*AUTH, 404),
)
def create_menu_route(
    menu: MenuCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Crée un menu autour d'un produit principal. Les groupes de choix
    s'ajoutent ensuite avec `POST /menus/{menu_id}/groupes`.

    **Rôle :** administrateur. Renvoie 404 si le produit principal n'existe pas.
    """
    return menu_controller.create_menu(db, menu)


@menu_router.put(
    "/{menu_id}",
    response_model=MenuOut,
    summary="Modifier un menu",
    responses=erreurs(*AUTH, 404),
)
def update_menu_route(
    menu: MenuCreate,
    menu_id: int = ID_MENU,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """**Rôle :** administrateur."""
    return menu_controller.update_menu(db, menu_id, menu)


@menu_router.delete(
    "/{menu_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un menu",
    responses=erreurs(*AUTH, 404, 409),
)
def delete_menu_route(
    menu_id: int = ID_MENU,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Renvoie **409** si le menu a déjà été commandé : il faut alors le rendre indisponible.

    **Rôle :** administrateur.
    """
    menu_controller.delete_menu(db, menu_id)
    return None


# ---------- Groupes de choix d'un menu ----------

@menu_router.post(
    "/{menu_id}/groupes",
    response_model=MenuOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter un groupe de choix à un menu",
    responses=erreurs(*AUTH, 404),
)
def add_groupe_route(
    groupe: GroupeCreate,
    menu_id: int = ID_MENU,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Ajoute un groupe (ex. « Boisson ») au menu. Deux façons de le remplir :
    - **lié à une catégorie** (`categorie_id`) : tous les produits disponibles de la catégorie sont proposés ;
    - **sans catégorie** : on ajoute les produits un par un avec `POST /menus/groupes/{groupe_id}/produits`.

    **Rôle :** administrateur. Renvoie le menu complet mis à jour.
    """
    return menu_controller.add_groupe(db, menu_id, groupe)


@menu_router.delete(
    "/groupes/{groupe_id}",
    response_model=MenuOut,
    summary="Supprimer un groupe de choix",
    responses=erreurs(*AUTH, 404, 409),
)
def delete_groupe_route(
    groupe_id: int = ID_GROUPE,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Renvoie **409** si le groupe a déjà servi dans une commande.

    **Rôle :** administrateur.
    """
    return menu_controller.delete_groupe(db, groupe_id)


# ---------- Produits proposés dans un groupe ----------

@menu_router.post(
    "/groupes/{groupe_id}/produits",
    response_model=MenuOut,
    status_code=status.HTTP_201_CREATED,
    summary="Proposer un produit dans un groupe",
    responses=erreurs(*AUTH, 404, 409),
)
def add_option_route(
    option: OptionCreate,
    groupe_id: int = ID_GROUPE,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Ajoute un produit au groupe, avec un éventuel supplément de prix
    (ex. Potatoes à +0,50 €).

    Renvoie **409** si le produit est déjà dans le groupe, ou si le groupe est lié
    à une catégorie (ses produits viennent alors de la catégorie).

    **Rôle :** administrateur.
    """
    return menu_controller.add_option(db, groupe_id, option)


@menu_router.delete(
    "/groupes/{groupe_id}/produits/{produit_id}",
    response_model=MenuOut,
    summary="Retirer un produit d'un groupe",
    responses=erreurs(*AUTH, 404),
)
def remove_option_route(
    groupe_id: int = ID_GROUPE,
    produit_id: int = Path(description="Identifiant du produit à retirer", ge=1),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """**Rôle :** administrateur."""
    return menu_controller.remove_option(db, groupe_id, produit_id)
