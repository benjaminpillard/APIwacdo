from pydantic import BaseModel
from typing import Optional
from schemas.produit import ProduitOut

class MenuCreate(BaseModel):
    nom: str
    price: float

class MenuOut(MenuCreate):
    id: int
    produits: list[ProduitOut] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        from_attributes = True
        