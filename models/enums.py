import enum


class StatutCommande(str, enum.Enum):
    saisie = "saisie"
    preparee = "preparee"
    livree = "livree"


class ModeCommande(str, enum.Enum):
    comptoir = "comptoir"
    telephone = "telephone"