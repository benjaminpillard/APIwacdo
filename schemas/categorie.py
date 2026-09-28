from pydantic import BaseModel, Field


class CategorieCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=50)


class CategorieOut(CategorieCreate):
    id: int

    model_config = {"from_attributes": True}