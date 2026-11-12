from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field, model_validator

from models.enums import StatutCommande, ModeCommande
from schemas.produit import ProduitOut


# ---------- Ce que l'accueil envoie pour saisir une commande ----------

class ChoixCreate(BaseModel):
    """Un choix dans un menu : dans tel groupe, le client a pris tel produit."""
    groupe_id: int = Field(description="Groupe du menu (ex. « Boisson »)", examples=[1])
    produit_id: int = Field(description="Produit choisi dans ce groupe (ex. Coca)", examples=[2])


class LigneCreate(BaseModel):
    """Une ligne du ticket : soit un produit seul, soit un menu avec ses choix."""
    produit_id: Optional[int] = Field(default=None, description="Produit commandé seul (exclusif avec menu_id)")
    menu_id: Optional[int] = Field(default=None, description="Menu commandé (exclusif avec produit_id)", examples=[1])
    quantite: int = Field(default=1, ge=1, le=50, description="Quantité (1 à 50)")
    choix: list[ChoixCreate] = Field(default=[], description="Choix faits dans le menu (uniquement pour un menu)")

    @model_validator(mode="after")
    def verifier_produit_ou_menu(self):
        if (self.produit_id is None) == (self.menu_id is None):
            raise ValueError("Une ligne doit contenir un produit OU un menu, pas les deux")
        if self.produit_id is not None and self.choix:
            raise ValueError("Les choix ne concernent que les menus")
        return self


class CommandeCreate(BaseModel):
    numero: str = Field(
        min_length=1, max_length=20,
        description="Numéro du ticket, unique (identifie la commande, pas de paiement)", examples=["A042"],
    )
    mode: ModeCommande = Field(description="comptoir ou telephone")
    heure_livraison: Optional[datetime] = Field(
        default=None, description="Heure à laquelle la commande doit être prête (sert au tri de la préparation)",
    )
    lignes: list[LigneCreate] = Field(min_length=1, description="Au moins une ligne")


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
    prix_unitaire: Decimal = Field(description="Prix figé au moment de la commande (suppléments compris)")
    produit: Optional[ProduitOut] = None
    menu: Optional[MenuRef] = None
    choix: list[ChoixOut] = []

    model_config = {"from_attributes": True}


class CommandeOut(BaseModel):
    id: int
    numero: str
    statut: StatutCommande = Field(description="saisie → preparee → livree")
    mode: ModeCommande
    heure_livraison: Optional[datetime] = None
    total: Decimal = Field(description="Total calculé par l'API")
    utilisateur_id: int = Field(description="Employé qui a saisi la commande")
    created_at: Optional[datetime] = None
    lignes: list[LigneOut] = []

    model_config = {"from_attributes": True}
