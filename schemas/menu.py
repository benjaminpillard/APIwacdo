from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from schemas.produit import ProduitOut


# --- Les produits proposés dans un groupe (ex. Frites, Potatoes) ---

class OptionCreate(BaseModel):
    produit_id: int
    supplement: Decimal = Field(default=Decimal("0"), ge=0, max_digits=8, decimal_places=2)


class OptionOut(BaseModel):
    id: int
    supplement: Decimal
    produit: ProduitOut

    model_config = {"from_attributes": True}


# --- Les groupes de choix d'un menu (ex. Boisson, Sauce) ---

class GroupeCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=50)
    obligatoire: bool = True
    max_choix: int = Field(default=1, ge=1)
    categorie_id: Optional[int] = None   # nouveau : lier le groupe à une catégorie


class GroupeOut(GroupeCreate):
    id: int
    options: list[OptionOut] = []
    produits_proposes: list[ProduitOut] = []   # nouveau

    model_config = {"from_attributes": True}

# --- Le menu lui-même ---

class MenuCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    prix: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    image_url: Optional[str] = Field(default=None, max_length=255)
    disponible: bool = True
    produit_principal_id: int


class MenuOut(MenuCreate):
    id: int
    produit_principal: ProduitOut
    groupes: list[GroupeOut] = []

    model_config = {"from_attributes": True}