from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from utils.jwt import decode_access_token
from models.database import get_db
from models.user import Utilisateur
from utils.logger import audit


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

def _non_authentifie(detail: str) -> HTTPException:
    # 401 + en-tête WWW-Authenticate, comme le prévoit la norme OAuth2
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> Utilisateur:
    # Décoder le JWT puis retrouver l'utilisateur courant grâce à son id (champ « sub »)
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError):
        # Signature invalide, token modifié, expiré ou incomplet
        raise _non_authentifie("Token invalide ou expiré")

    user = db.get(Utilisateur, user_id)
    if user is None or not user.actif:
        # Compte supprimé ou anonymisé depuis la création du token
        raise _non_authentifie("Compte introuvable ou désactivé : reconnectez-vous")

    return user


def require_role(*roles):
    # Verifier que le role de l'utilisateur est autorise
    # Le rôle est aussi écrit dans le token (utile au front pour adapter l'affichage),
    # mais on vérifie celui de la base : un rôle retiré par l'admin s'applique immédiatement,
    # sans attendre l'expiration du token.
    def role_checker(current_user: Utilisateur = Depends(get_current_user)):
        if current_user.role not in roles:
            audit.warning(
                "Accès refusé : utilisateur=%s rôle=%s rôles requis=%s",
                current_user.username, current_user.role, ",".join(roles),
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Accès interdit : permission insuffisante pour votre rôle"
            )
        return current_user
    return role_checker