from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from utils.jwt import decode_access_token
from models.database import get_db
from models.user import Utilisateur
from controllers.user import read_user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Utilisateur:
    # Decoder le JWT puis retrouver l'utilisateur courant
    try:
        payload = decode_access_token(token)
        username = payload.get("username")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No username",
            )
        user = read_user(db, username)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user",
            )
        return user
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is wrong",
            
        )

def require_role(*roles):
    # Verifier que le role de l'utilisateur est autorise
    def role_checker(current_user: Utilisateur = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="Accès interdit : Permission insuffisante."
            )
        return current_user
    return role_checker