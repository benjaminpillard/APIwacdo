from fastapi import APIRouter, HTTPException, Depends, Path, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from utils.jwt import create_access_token
from utils.auth import get_current_user, require_role
from utils.docs import AUTH, erreurs
from utils.limiter import limiter
from utils.logger import audit
from utils.setting import settings

from schemas.user import UserCreate, UserOut, UserUpdate
from schemas.token import Token
from controllers.user import utilisateur_controller

from models.database import get_db
from models.user import Utilisateur


utilisateur_route = APIRouter(
    prefix="/users",
    tags=["Utilisateurs"]
)


@utilisateur_route.post(
    "/login",
    response_model=Token,
    summary="Se connecter (obtenir un token)",
    responses=erreurs(401, 429),
)
@limiter.limit(settings.LOGIN_RATE_LIMIT)   # anti brute-force : nombre d'essais limité par IP
def login(
    request: Request,   # requis par slowapi pour connaître l'IP
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """OAuth2 Password Flow : envoie `username` et `password` (formulaire), renvoie un token JWT.

    Le token s'utilise ensuite dans l'en-tête `Authorization: Bearer <token>`
    (dans Swagger : bouton **Authorize**).

    Le nombre de tentatives est limité par adresse IP (**429** au-delà).
    """
    user = utilisateur_controller.authentifier(db, form_data.username, form_data.password)
    ip = request.client.host if request.client else "inconnue"

    if not user:
        audit.warning("Connexion échouée : identifiant=%s ip=%s", form_data.username, ip)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # « sub » (subject) = identifiant stable de l'utilisateur, standard des JWT.
    # Pas d'email dans le token : un JWT est seulement encodé, pas chiffré (lisible par tous).
    token = create_access_token({
        "sub": str(user.id),
        "username": user.username,
        "role": user.role,
    })
    audit.info("Connexion réussie : utilisateur=%s ip=%s", user.username, ip)

    return Token(access_token=token, token_type="bearer")


@utilisateur_route.post(
    "/register",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un compte employé",
    responses=erreurs(*AUTH, 409),
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur")),
):
    """Le mot de passe est haché (Argon2) avant d'être enregistré, jamais stocké en clair.

    Renvoie **409** si le nom d'utilisateur ou l'email est déjà pris.

    **Rôle :** administrateur.
    """
    return utilisateur_controller.create(db, user)


@utilisateur_route.get(
    "/me",
    response_model=UserOut,
    summary="Consulter mes données (RGPD)",
    responses=erreurs(401),
)
def read_users_me(current_user: Utilisateur = Depends(get_current_user)):
    """Droit d'accès : renvoie les données du compte connecté. **Rôles :** tous."""
    return current_user


@utilisateur_route.patch(
    "/me",
    response_model=UserOut,
    summary="Modifier mes données (RGPD)",
    responses=erreurs(401, 409),
)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Droit de rectification : nom d'utilisateur, email et/ou mot de passe.
    Le rôle ne peut pas être modifié ici (on ne s'attribue pas de droits soi-même).

    **Rôles :** tous.
    """
    return utilisateur_controller.update(db, current_user, data)


@utilisateur_route.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer mon compte (RGPD)",
    responses=erreurs(401, 409),
)
def delete_me(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    """Droit à l'effacement.
    - Sans commande saisie : le compte est supprimé.
    - Avec des commandes : le compte est **anonymisé** et désactivé, pour garder
      un historique des commandes sans donnée personnelle.

    Renvoie **409** pour le dernier administrateur.

    **Rôles :** tous.
    """
    utilisateur_controller.delete(db, current_user)
    return None


@utilisateur_route.get(
    "/all",
    response_model=list[UserOut],
    summary="Lister les comptes",
    responses=erreurs(*AUTH),
)
def read_all_users(
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """**Rôle :** administrateur."""
    return utilisateur_controller.lister_tous(db)


@utilisateur_route.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un compte",
    responses=erreurs(*AUTH, 404, 409),
)
def delete_user(
    user_id: int = Path(description="Identifiant du compte", ge=1),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    """Même règle que `DELETE /users/me` : suppression, ou anonymisation si le compte
    a saisi des commandes.

    **Rôle :** administrateur.
    """
    utilisateur_controller.delete(db, utilisateur_controller.get(db, user_id))
    return None
