from datetime import datetime, timedelta, timezone
import jwt
from utils.setting import settings



def create_access_token(data: dict, expires_delta: timedelta | None = None):
    # Creer un token avec une date d'expiration
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str):
    # Decoder et valider le token signe
    # Lève InvalidTokenError (ou ExpiredSignatureError) si le token est faux ou expiré
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
