from fastapi import APIRouter

from schemas.confidentialite import PolitiqueConfidentialite
from controllers import confidentialite as confidentialite_controller

confidentialite_router = APIRouter(
    prefix="/confidentialite",
    tags=["RGPD"]
)


# Route publique : on doit pouvoir lire la politique AVANT de se connecter
@confidentialite_router.get(
    "/",
    response_model=PolitiqueConfidentialite,
    summary="Politique de confidentialité",
)
def politique_confidentialite():
    """Informe sur les données personnelles stockées, leur usage, leur durée de conservation,
    leurs destinataires et les droits de l'utilisateur.

    **Route publique** : lisible sans être connecté.
    """
    return confidentialite_controller.get_politique()
