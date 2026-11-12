"""Outils pour la documentation Swagger / OpenAPI.

`erreurs(401, 403, 404)` documente les réponses d'erreur possibles d'une route,
avec leur description et le format renvoyé (schéma ErreurOut).
L'erreur 422 (données invalides) est documentée automatiquement par FastAPI.
"""
from schemas.erreur import ErreurOut

_DESCRIPTIONS = {
    400: "Requête refusée par une règle métier (ex. produit indisponible, choix de menu invalide)",
    401: "Non authentifié : token absent, invalide ou expiré",
    403: "Accès interdit : rôle insuffisant pour cette action",
    404: "Ressource introuvable",
    409: "Conflit : doublon, ou action impossible dans l'état actuel des données",
    429: "Trop de tentatives : réessayer plus tard",
}

# Raccourci pour toutes les routes protégées
AUTH = (401, 403)


def erreurs(*codes: int) -> dict:
    return {code: {"model": ErreurOut, "description": _DESCRIPTIONS[code]} for code in codes}
