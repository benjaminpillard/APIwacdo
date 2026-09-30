import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import models  # charge tous les modèles
from models.database import Base, get_db
from main import app
from schemas.user import UserCreate
from controllers.user import create_user

MOT_DE_PASSE = "Test1234!"


@pytest.fixture()
def session_factory():
    # Base SQLite en mémoire, neuve pour chaque test
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client(session_factory):
    # Remplace la vraie base par la base de test
    def override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def creer_compte(client, session_factory):
    # Crée un compte avec le rôle voulu et renvoie l'en-tête d'authentification
    def _creer(role):
        db = session_factory()
        try:
            create_user(
                UserCreate(
                    username=role.value,
                    email=f"{role.value}@test.fr",
                    password=MOT_DE_PASSE,
                    role=role,
                ),
                db,
            )
        finally:
            db.close()

        reponse = client.post(
            "/users/login",
            data={"username": role.value, "password": MOT_DE_PASSE},
        )
        assert reponse.status_code == 200
        return {"Authorization": f"Bearer {reponse.json()['access_token']}"}

    return _creer