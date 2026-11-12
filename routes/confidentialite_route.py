from fastapi import APIRouter

from schemas.confidentialite import PolitiqueConfidentialite
from controllers import confidentialite as confidentialite_controller

confidentialite_router = APIRouter(
    prefix="/confidentialite",
    tags=["RGPD"]
)


# Route publique : on doit pouvoir lire la politique AVANT de se connecter
@confidentialite_router.get("/", response_model=PolitiqueConfidentialite)
def politique_confidentialite():
    return confidentialite_controller.get_politique()
