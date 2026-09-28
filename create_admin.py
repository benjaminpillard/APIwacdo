import getpass
from models.database import SessionLocal
from models.user import Utilisateur
from models.commande import Commande
from models.produit import Produit
from models.menu import Menu
from schemas.user import UserCreate, Role
from controllers.user import create_user

username = input("Username : ")
email = input("Email : ")
password = getpass.getpass("Mot de passe : ")

db = SessionLocal()
try:
    admin = create_user(
        UserCreate(username=username, email=email, password=password, role=Role.administrateur),
        db,
    )
    print(f"Admin créé : {admin.username}")
finally:
    db.close()