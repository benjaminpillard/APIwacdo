import time

import jwt
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from sqlalchemy.exc import IntegrityError

from routes.produit_routes import produit_router
from routes.menus_routes import menu_router
from routes.user_route import utilisateur_route
from routes.commande_route import commande_router
from routes.categorie_routes import categorie_router
from routes.confidentialite_route import confidentialite_router

from utils.limiter import limiter
from utils.logger import configurer_logs, logger, audit
from utils.setting import settings


configurer_logs()

DESCRIPTION = """
API du **back-office Wacdo** : gestion du catalogue (produits, menus), des commandes
et des comptes employés.

## Authentification
1. Se connecter avec `POST /users/login` (ou le bouton **Authorize** ci-dessous).
2. Le token JWT obtenu est envoyé dans l'en-tête `Authorization: Bearer <token>`.

## Rôles
| Rôle | Peut... |
|---|---|
| **administrateur** | tout faire : catalogue, comptes, commandes |
| **preparateur** | voir les commandes et les déclarer préparées |
| **accueil** | saisir une commande et la remettre au client |

## Cycle d'une commande
`saisie` → `preparee` (préparateur) → `livree` (accueil)

## Erreurs
Toutes les erreurs ont la forme `{"detail": "message"}`.
"""

TAGS = [
    {"name": "Utilisateurs", "description": "Connexion, comptes employés et données personnelles (RGPD)."},
    {"name": "Produits", "description": "Catalogue : nom, description, prix, image, disponibilité."},
    {"name": "Catégories", "description": "Classement des produits (Burgers, Boissons...)."},
    {"name": "Menus", "description": "Menus et leur composition : groupes de choix et produits proposés."},
    {"name": "Commandes", "description": "Saisie, préparation et remise des commandes."},
    {"name": "RGPD", "description": "Information sur le traitement des données personnelles."},
    {"name": "Santé", "description": "Vérification que l'API est en ligne."},
]

# Les tables sont créées et mises à jour par Alembic (alembic upgrade head)
app = FastAPI(
    title="API Wacdo — Back-office",
    description=DESCRIPTION,
    version="1.0.0",
    openapi_tags=TAGS,
)
app.state.limiter = limiter

# Brancher les routes de l'API
app.include_router(produit_router)
app.include_router(menu_router)
app.include_router(utilisateur_route)
app.include_router(commande_router)
app.include_router(categorie_router)
app.include_router(confidentialite_router)

# Autoriser les origines front configurees
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------- Traçabilité : une ligne de log par requête ----------

def _utilisateur_du_token(request: Request) -> str:
    # Lecture du token uniquement pour le log : la vraie vérification est faite par get_current_user
    entete = request.headers.get("authorization", "")
    if not entete.lower().startswith("bearer "):
        return "anonyme"
    try:
        payload = jwt.decode(entete[7:], settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return str(payload.get("username", payload.get("sub", "?")))
    except jwt.InvalidTokenError:
        return "token-invalide"


@app.middleware("http")
async def journaliser_requetes(request: Request, call_next):
    debut = time.perf_counter()
    response = await call_next(request)
    duree_ms = (time.perf_counter() - debut) * 1000

    # Ex. : POST /commandes/ -> 201 (12 ms) utilisateur=julie ip=1.2.3.4
    niveau = 30 if response.status_code >= 400 else 20   # WARNING si erreur, sinon INFO
    logger.log(
        niveau,
        "%s %s -> %s (%.0f ms) utilisateur=%s ip=%s",
        request.method, request.url.path, response.status_code, duree_ms,
        _utilisateur_du_token(request), request.client.host if request.client else "?",
    )
    return response


# ---------- Gestion globale des erreurs ----------
# Filet de sécurité : les cas prévus sont traités dans les controllers (404, 409...).
# Ces gestionnaires évitent qu'un cas oublié remonte en erreur 500 brute.

@app.exception_handler(RateLimitExceeded)
async def trop_de_requetes(request: Request, exc: RateLimitExceeded):
    audit.warning(
        "Limite de débit atteinte : %s ip=%s",
        request.url.path, request.client.host if request.client else "?",
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Trop de tentatives : réessayez dans une minute"},
    )


@app.exception_handler(IntegrityError)
async def erreur_integrite(request: Request, exc: IntegrityError):
    # Contrainte de la base violée (doublon, référence vers une donnée inexistante...)
    logger.warning("Erreur d'intégrité sur %s %s : %s", request.method, request.url.path, exc.orig)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Opération impossible : elle violerait l'intégrité des données"},
    )


@app.exception_handler(Exception)
async def erreur_inattendue(request: Request, exc: Exception):
    # Le détail complet (trace) va dans les logs, jamais dans la réponse :
    # il pourrait révéler la structure interne de l'application
    logger.exception("Erreur inattendue sur %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erreur interne du serveur"},
    )


@app.get("/", summary="Vérifier que l'API répond", tags=["Santé"])
def accueil():
    return {"message": "API Wacdo fonctionnelle !"}
