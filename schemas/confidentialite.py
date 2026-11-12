from pydantic import BaseModel


class DonneeCollectee(BaseModel):
    donnee: str
    finalite: str


class DroitUtilisateur(BaseModel):
    droit: str
    comment: str


class PolitiqueConfidentialite(BaseModel):
    responsable: str
    personnes_concernees: str
    donnees_collectees: list[DonneeCollectee]
    base_legale: str
    duree_conservation: str
    destinataires: str
    securite: list[str]
    droits: list[DroitUtilisateur]
    contact: str
