"""Crée un compte administrateur.

Prérequis : la base doit être à jour (alembic upgrade head).
Usage : python create_admin.py
"""
import getpass

from fastapi import HTTPException
from pydantic import ValidationError

import models  # charge tous les modèles (relations entre tables)
from models.database import SessionLocal
from schemas.user import UserCreate, Role
from controllers.user import create_user

username = input("Username : ")
email = input("Email : ")
password = getpass.getpass("Mot de passe : ")

db = SessionLocal()
try:
    admin = create_user(
        UserCreate(username=username, email=email, password=password, role=Role.administrateur),
        db,
    )
    print(f"Admin créé : {admin.username}")
except ValidationError as e:
    print(f"Données invalides : {e}")
except HTTPException as e:
    print(f"Erreur : {e.detail}")
finally:
    db.close()
