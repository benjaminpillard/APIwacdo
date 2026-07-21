from typing import Optional
from pydantic import BaseModel

class CommandeCreer(BaseModel):
    numero: int
    statut: str
    total: float
    utilisateur_id: Optional[int] = None

class CommandeSupprimer(CommandeCreer):
    id: int

    class Config:
        orm_mode = True