from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from models.enums import StatutCommande, ModeCommande
from schemas.produit import ProduitOut


# ---------- Ce que l'accueil envoie pour saisir une commande ----------

class ChoixCreate(BaseModel):
    """Un choix dans un menu : dans tel groupe, le client a pris tel produit."""
    groupe_id: int
    produit_id: int


class LigneCreate(BaseModel):
    """Une ligne du ticket : soit un produit seul, soit un menu avec ses choix."""
    produit_id: Optional[int] = None
    menu_id: Optional[int] = None
    quantite: int = Field(default=1, ge=1, le=50)
    choix: list[ChoixCreate] = []

    @model_validator(mode="after")
    def verifier_produit_ou_menu(self):
        if (self.produit_id is None) == (self.menu_id is None):
            raise ValueError("Une ligne doit contenir un produit OU un menu, pas les deux")
        if self.produit_id is not None and self.choix:
            raise ValueError("Les choix ne concernent que les menus")
        return self


class CommandeCreate(BaseModel):
    numero: str = Field(min_length=1, max_length=20)
    mode: ModeCommande
    heure_livraison: Optional[datetime] = None
    lignes: list[LigneCreate] = Field(min_length=1)


# ---------- Ce que l'API renvoie ----------

class GroupeRef(BaseModel):
    id: int
    nom: str

    model_config = {"from_attributes": True}


class MenuRef(BaseModel):
    id: int
    nom: str

    model_config = {"from_attributes": True}


class ChoixOut(BaseModel):
    groupe: GroupeRef
    produit: ProduitOut

    model_config = {"from_attributes": True}


class LigneOut(BaseModel):
    id: int
    quantite: int
    prix_unitaire: Decimal
    produit: Optional[ProduitOut] = None
    menu: Optional[MenuRef] = None
    choix: list[ChoixOut] = []

    model_config = {"from_attributes": True}


class CommandeOut(BaseModel):
    id: int
    numero: str
    statut: StatutCommande
    mode: ModeCommande
    heure_livraison: Optional[datetime] = None
    total: Decimal
    utilisateur_id: int
    created_at: Optional[datetime] = None
    lignes: list[LigneOut] = []

    model_config = {"from_attributes": True}