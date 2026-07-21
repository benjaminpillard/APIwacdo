from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProduitCreate(BaseModel):
    produit: str
    price: float
    user_id: Optional[int] = None

class ProduitOut(BaseModel):
    id: int
    produit: str
    price: float
    user_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        