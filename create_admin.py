import getpass

from models import Base
from models.database import SessionLocal, engine
from schemas.user import UserCreate, Role
from controllers.user import create_user

# Crée les tables si elles n'existent pas encore
Base.metadata.create_all(bind=engine)

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