from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

from models.database import Base, engine

from routes.produit_routes import produit_router
from routes.menus_routes import menu_router
from routes.user_route import utilisateur_route
from routes.commande_route import commande_router
from routes.categorie_routes import categorie_router

from utils.setting import settings


app = FastAPI()
# Creer les tables au demarrage

# Base.metadata.create_all(bind=engine)  # remplacé par Alembic
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Brancher les routes de l'API

app.include_router(produit_router)
app.include_router(menu_router)
app.include_router(utilisateur_route)
app.include_router(commande_router)
app.include_router(categorie_router)

# Autoriser les origines front configurees
app.add_middleware(
    CORSMiddleware,
    allow_origins= settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/")
def accueil():
    return {"message": "API Wacdo fonctionnelle !"}