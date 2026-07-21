from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware

from models.database import Base, engine

from routes.produit_routes import produit_router
from routes.menus_routes import menu_router
from routes.user_route import utilisateur_route
from routes.commande_route import commande_router

from utils.setting import settings


app = FastAPI()
Base.metadata.create_all(bind=engine)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

app.include_router(produit_router)
app.include_router(menu_router)
app.include_router(utilisateur_route)
app.include_router(commande_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins= settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)