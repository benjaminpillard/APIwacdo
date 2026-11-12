from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from utils.jwt import decode_access_token
from models.database import get_db
from models.user import Utilisateur
from controllers.user import read_user


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def _non_authentifie(detail: str) -> HTTPException:
    # 401 + en-tête WWW-Authenticate, comme le prévoit la norme OAuth2
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Utilisateur:
    # Decoder le JWT puis retrouver l'utilisateur courant
    try:
        payload = decode_access_token(token)
    except InvalidTokenError:
        # Signature invalide, token modifié ou expiré
        raise _non_authentifie("Token invalide ou expiré")

    username = payload.get("username")
    if username is None:
        raise _non_authentifie("Token invalide : utilisateur non précisé")

    user = read_user(db, username)
    if user is None:
        raise _non_authentifie("Utilisateur introuvable : reconnectez-vous")

    return user

def require_role(*roles):
    # Verifier que le role de l'utilisateur est autorise
    def role_checker(current_user: Utilisateur = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès interdit : permission insuffisante pour votre rôle"
            )
        return current_user
    return role_checker