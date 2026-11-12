from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from routes.produit_routes import produit_router
from routes.menus_routes import menu_router
from routes.user_route import utilisateur_route
from routes.commande_route import commande_router
from routes.categorie_routes import categorie_router

from utils.setting import settings


# Les tables sont créées et mises à jour par Alembic (alembic upgrade head)
app = FastAPI()

# Brancher les routes de l'API
app.include_router(produit_router)
app.include_router(menu_router)
app.include_router(utilisateur_route)
app.include_router(commande_router)
app.include_router(categorie_router)

# Autoriser les origines front configurees
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# ---------- Gestion globale des erreurs ----------
# Filet de sécurité : les cas prévus sont traités dans les controllers (404, 409...).
# Ces gestionnaires évitent qu'un cas oublié remonte en erreur 500 brute.

@app.exception_handler(IntegrityError)
async def erreur_integrite(request: Request, exc: IntegrityError):
    # Contrainte de la base violée (doublon, référence vers une donnée inexistante...)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Opération impossible : elle violerait l'intégrité des données"},
    )


@app.exception_handler(Exception)
async def erreur_inattendue(request: Request, exc: Exception):
    # Ne jamais renvoyer le détail technique au client (il pourrait révéler la structure interne)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erreur interne du serveur"},
    )


@app.get("/")
def accueil():
    return {"message": "API Wacdo fonctionnelle !"}
