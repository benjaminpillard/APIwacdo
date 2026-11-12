from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

from schemas.produit import ProduitOut


# --- Les produits proposés dans un groupe (ex. Frites, Potatoes) ---

class OptionCreate(BaseModel):
    produit_id: int = Field(description="Produit à proposer dans le groupe", examples=[3])
    supplement: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=8, decimal_places=2,
        description="Supplément ajouté au prix du menu si ce produit est choisi", examples=["0.50"],
    )


class OptionOut(BaseModel):
    id: int = Field(description="Identifiant de l'option")
    supplement: Decimal = Field(description="Supplément en euros")
    produit: ProduitOut

    model_config = {"from_attributes": True}


# --- Les groupes de choix d'un menu (ex. Boisson, Sauce) ---

class GroupeCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=50, description="Nom du groupe de choix", examples=["Boisson"])
    obligatoire: bool = Field(default=True, description="Le client doit-il obligatoirement choisir dans ce groupe ?")
    max_choix: int = Field(default=1, ge=1, description="Nombre maximum de produits à choisir", examples=[1])
    categorie_id: Optional[int] = Field(
        default=None,
        description="Si renseigné, tous les produits disponibles de cette catégorie sont proposés",
        examples=[2],
    )


class GroupeOut(GroupeCreate):
    id: int = Field(description="Identifiant du groupe")
    options: list[OptionOut] = Field(default=[], description="Produits ajoutés à la main (groupe sans catégorie)")
    produits_proposes: list[ProduitOut] = Field(
        default=[], description="Produits que le client peut réellement choisir (disponibles uniquement)",
    )

    model_config = {"from_attributes": True}


# --- Le menu lui-même ---

class MenuCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100, description="Nom du menu", examples=["Menu Big Mac"])
    description: Optional[str] = Field(default=None, max_length=500, description="Texte de présentation")
    prix: Decimal = Field(
        gt=0, max_digits=8, decimal_places=2,
        description="Prix de base du menu en euros (hors suppléments)", examples=["8.90"],
    )
    image_url: Optional[str] = Field(default=None, max_length=255, description="Adresse de l'image du menu")
    disponible: bool = Field(default=True, description="false : le menu ne peut plus être commandé")
    produit_principal_id: int = Field(description="Le plat fixe du menu (ex. le burger)", examples=[1])


class MenuOut(MenuCreate):
    id: int = Field(description="Identifiant du menu")
    produit_principal: ProduitOut
    groupes: list[GroupeOut] = Field(default=[], description="Groupes de choix du menu")

    model_config = {"from_attributes": True}
