from pydantic import BaseModel, Field


class CategorieCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=50, description="Nom unique de la catégorie", examples=["Boissons"])


class CategorieOut(CategorieCreate):
    id: int = Field(description="Identifiant de la catégorie")

    model_config = {"from_attributes": True}
