from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(description="Token JWT à envoyer dans l'en-tête Authorization")
    token_type: str = Field(description="Toujours « bearer »", examples=["bearer"])
