from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class Role(str, Enum):
    administrateur = "administrateur"
    preparateur = "preparateur"
    accueil = "accueil"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, description="Identifiant de connexion, unique", examples=["julie.m"])
    email: EmailStr = Field(description="Email professionnel, unique", examples=["julie@wacdo.fr"])
    password: str = Field(
        min_length=8, max_length=128,
        description="Mot de passe (8 caractères minimum), haché avant enregistrement",
        examples=["MotDePasse123!"],
    )
    role: Role = Field(default=Role.accueil, description="Poste de l'employé, qui détermine ses droits")


class UserOut(BaseModel):
    # Jamais de mot de passe (même haché) dans une réponse
    id: int = Field(description="Identifiant du compte")
    username: str
    email: EmailStr
    role: Role
    actif: bool = Field(description="false : compte supprimé et anonymisé")

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    # Tous les champs sont facultatifs : on ne modifie que ce qu'on envoie.
    # Pas de "role" ici : on ne se donne pas ses propres droits soi-même.
    username: Optional[str] = Field(default=None, min_length=3, max_length=50, description="Nouvel identifiant")
    email: Optional[EmailStr] = Field(default=None, description="Nouvel email")
    password: Optional[str] = Field(default=None, min_length=8, max_length=128, description="Nouveau mot de passe")
