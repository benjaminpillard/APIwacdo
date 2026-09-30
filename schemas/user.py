from enum import Enum
from pydantic import BaseModel, EmailStr, Field
from typing import  Optional


class Role(str, Enum):
    administrateur = "administrateur"
    preparateur = "preparateur"
    accueil = "accueil"


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: Role = Role.accueil


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: Role

    model_config = {"from_attributes": True}

class UserUpdate(BaseModel):
    # Tous les champs sont facultatifs : on ne modifie que ce qu'on envoie.
    # Pas de "role" ici : on ne se donne pas ses propres droits soi-même.
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)