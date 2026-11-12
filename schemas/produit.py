from decimal import Decimal
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProduitCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100, description="Nom affiché du produit", examples=["Big Mac"])
    description: Optional[str] = Field(
        default=None, max_length=500, description="Texte de présentation",
        examples=["Deux steaks, sauce spéciale, salade, fromage"],
    )
    prix: Decimal = Field(
        gt=0, max_digits=8, decimal_places=2,
        description="Prix unitaire en euros (2 décimales max)", examples=["5.90"],
    )
    image_url: Optional[str] = Field(
        default=None, max_length=255, description="Adresse de l'image du produit",
        examples=["https://exemple.fr/images/big-mac.png"],
    )
    disponible: bool = Field(default=True, description="false : le produit ne peut plus être commandé")
    categorie_id: Optional[int] = Field(default=None, description="Catégorie du produit (facultative)", examples=[1])


class ProduitOut(ProduitCreate):
    id: int = Field(description="Identifiant du produit")
    created_at: Optional[datetime] = Field(default=None, description="Date de création")
    updated_at: Optional[datetime] = Field(default=None, description="Date de dernière modification")

    model_config = {"from_attributes": True}


class ProduitUpdate(BaseModel):
    # Tous les champs sont facultatifs : on n'envoie que ce qui change
    nom: Optional[str] = Field(default=None, min_length=1, max_length=100, description="Nouveau nom")
    description: Optional[str] = Field(default=None, max_length=500, description="Nouvelle description")
    prix: Optional[Decimal] = Field(default=None, gt=0, max_digits=8, decimal_places=2, description="Nouveau prix en euros")
    image_url: Optional[str] = Field(default=None, max_length=255, description="Nouvelle image")
    disponible: Optional[bool] = Field(default=None, description="Rendre le produit disponible ou non", examples=[False])
    categorie_id: Optional[int] = Field(default=None, description="Nouvelle catégorie")
