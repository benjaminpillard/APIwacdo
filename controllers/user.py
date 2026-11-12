import secrets
from typing import cast

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.user import Utilisateur
from models.commande import Commande
from schemas.user import UserCreate, UserUpdate, Role

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
        raise HTTPException(status_code=409, detail="Nom d'utilisateur ou email déjà utilisé")
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


def list_users(db: Session):
    return db.execute(select(Utilisateur).order_by(Utilisateur.username)).scalars().all()


def get_user_by_id(db: Session, user_id: int) -> Utilisateur:
    user = db.get(Utilisateur, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
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


def delete_user(db: Session, user: Utilisateur) -> None:
    """Droit à l'effacement (RGPD).

    - Sans commande : le compte est réellement supprimé.
    - Avec des commandes : on ne peut pas le supprimer sans casser l'historique
      (chaque commande garde son auteur). On l'anonymise donc : toutes les données
      personnelles sont remplacées et le compte ne peut plus se connecter,
      mais les commandes restent cohérentes.
    """
    # On ne supprime jamais le dernier administrateur : plus personne ne pourrait gérer l'application
    if user.role == Role.administrateur.value:
        nb_admins = db.execute(
            select(func.count()).select_from(Utilisateur)
            .where(Utilisateur.role == Role.administrateur.value)
        ).scalar_one()
        if nb_admins <= 1:
            raise HTTPException(
                status_code=409,
                detail="Impossible de supprimer le dernier administrateur",
            )

    a_des_commandes = db.execute(
        select(Commande.id).where(Commande.utilisateur_id == user.id).limit(1)
    ).first() is not None

    if a_des_commandes:
        user.username = f"supprime_{user.id}"
        user.email = f"supprime_{user.id}@example.com"   # domaine réservé, n'appartient à personne
        # Mot de passe aléatoire jamais communiqué : plus aucune connexion possible
        user.password = hash_password(secrets.token_urlsafe(32))
    else:
        db.delete(user)

    db.commit()
