from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from utils.jwt import create_access_token
from utils.auth import get_current_user

from schemas.user import UserCreate, UserOut, UserUpdate
from controllers import user as user_controller
from controllers.user import create_user, authenticate, update_user
from schemas.token import Token

from models.database import get_db
from models.user import Utilisateur

from utils.auth import require_role


utilisateur_route = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@utilisateur_route.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur")),
):
    return create_user(user, db)


@utilisateur_route.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiant ou mot de passe incorrect",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token({
        "username": user.username,
        "email": user.email
    })

    return Token(access_token=token, token_type="bearer")


@utilisateur_route.get("/me", response_model=UserOut)
def read_users_me(current_user: Utilisateur = Depends(get_current_user)):
    return current_user

@utilisateur_route.patch("/me", response_model=UserOut)
def update_me(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    return update_user(db, current_user, data)


@utilisateur_route.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(get_current_user)
):
    # Supprime le compte, ou l'anonymise s'il a saisi des commandes (voir le controller)
    user_controller.delete_user(db, current_user)
    return None


@utilisateur_route.get("/all", response_model=list[UserOut])
def read_all_users(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("administrateur"))
):
    return user_controller.list_users(db)

@utilisateur_route.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    user = user_controller.get_user_by_id(db, user_id)
    user_controller.delete_user(db, user)
    return None