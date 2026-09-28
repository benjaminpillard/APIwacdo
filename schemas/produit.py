from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProduitCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    prix: Decimal = Field(gt=0, max_digits=8, decimal_places=2)
    image_url: Optional[str] = Field(default=None, max_length=255)
    disponible: bool = True
    categorie_id: Optional[int] = None


class ProduitOut(ProduitCreate):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class ProduitUpdate(BaseModel):
    # Tous les champs sont facultatifs : on n'envoie que ce qui change
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    prix: Optional[Decimal] = Field(default=None, gt=0, max_digits=8, decimal_places=2)
    image_url: Optional[str] = Field(default=None, max_length=255)
    disponible: Optional[bool] = None
    categorie_id: Optional[int] = None