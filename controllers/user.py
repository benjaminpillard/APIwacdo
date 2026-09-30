from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import cast
from fastapi import HTTPException


from models.user import Utilisateur 
from schemas.user import UserCreate, UserUpdate

from utils.hash import hash_password, verify_password


def create_user(user: UserCreate, db: Session) -> Utilisateur:
    user_to_create = Utilisateur(
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=user.role.value,   # .value : on stocke la chaîne, pas l'enum
    )
    db.add(user_to_create)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("Nom d'utilisateur ou email déjà utilisé")
    db.refresh(user_to_create)
    return user_to_create


def authenticate(db: Session, username: str, password: str) -> Utilisateur | None:
    stmt = select(Utilisateur).where(Utilisateur.username == username)
    user = db.execute(stmt).scalars().first()

    if not user:
        return None

    if verify_password(cast(str, user.password), password):
        return user

    return None


def read_user(db: Session, username: str) -> Utilisateur | None:
    stmt = select(Utilisateur).where(Utilisateur.username == username)
    user = db.execute(stmt).scalars().first()

    return user


def update_user(db: Session, user: Utilisateur, data: UserUpdate) -> Utilisateur:
    changements = data.model_dump(exclude_unset=True)

    if "password" in changements:
        changements["password"] = hash_password(changements["password"])

    for key, value in changements.items():
        setattr(user, key, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Nom d'utilisateur ou email déjà utilisé")
    db.refresh(user)

    return user