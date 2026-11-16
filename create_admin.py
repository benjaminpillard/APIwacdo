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
from controllers.user import utilisateur_controller

username = input("Username : ")
email = input("Email : ")
# Rien ne s'affiche pendant la saisie : c'est normal (le mot de passe reste invisible)
password = getpass.getpass("Mot de passe (invisible pendant la saisie, 8 caractères minimum) : ")

db = SessionLocal()
try:
    admin = utilisateur_controller.create(
        db,
        UserCreate(username=username, email=email, password=password, role=Role.administrateur),
    )
    print(f"Admin créé : {admin.username}")
except ValidationError as e:
    # On n'affiche que le champ et la règle, jamais la valeur saisie (ce peut être le mot de passe)
    for erreur in e.errors():
        print(f"Données invalides : {'.'.join(map(str, erreur['loc']))} : {erreur['msg']}")
except HTTPException as e:
    print(f"Erreur : {e.detail}")
finally:
    db.close()
