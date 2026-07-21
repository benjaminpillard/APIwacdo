from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ProduitCreate(BaseModel):
    title: str
    price: float
    currency: str = "EUR"

class ProduitOut(BaseModel):
    id: int
    title: str
    price: float
    currency: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        