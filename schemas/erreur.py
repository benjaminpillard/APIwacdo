from pydantic import BaseModel, Field


class ErreurOut(BaseModel):
    """Format commun de toutes les erreurs renvoyées par l'API."""
    detail: str = Field(
        description="Message d'erreur lisible, en français",
        examples=["Produit introuvable"],
    )
