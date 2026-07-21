from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from utils.jwt import create_access_token
from utils.auth import get_current_user

from schemas.user import UserCreate, UserOut
from schemas.token import Token

from models.database import get_db
from models.user import Utilisateur

from utils.auth import require_role

from controllers.user import  create_user , authenticate

utilisateur_route = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@utilisateur_route.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    try:
        new_user = create_user(user, db)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return new_user


@utilisateur_route.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate(db, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    token = create_access_token({
        "username": user.username,
        "email": user.email
    })

    return Token(access_token=token, token_type="bearer")


@utilisateur_route.get("/me", response_model=UserOut)
def read_users_me(current_user: Utilisateur = Depends(get_current_user)):
    return current_user


@utilisateur_route.get("/all", response_model=list[UserOut])
def read_all_users(
    db: Session = Depends(get_db),
    current_user: Utilisateur = Depends(require_role("administrateur"))
):
    users = db.query(Utilisateur).all()
    return users

@utilisateur_route.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_role("administrateur"))
):
    user = db.query(Utilisateur).filter(Utilisateur.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=404,
            detail="Utilisateur introuvable"
        )

    db.delete(user)
    db.commit()

    return None