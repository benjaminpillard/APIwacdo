from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, declarative_base

from utils.setting import settings


def normaliser_url(url: str) -> str:
    # Adapter les vieux formats Postgres (ex. celui fourni par Render) vers le driver psycopg 3
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    if url.startswith("postgresql+psycopg2://"):
        return url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)
    return url


database_url = normaliser_url(settings.DATABASE_URL)

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


@event.listens_for(Engine, "connect")
def activer_cles_etrangeres_sqlite(dbapi_connection, connection_record):
    # SQLite ne vérifie pas les clés étrangères par défaut (contrairement à PostgreSQL).
    # On les active à chaque connexion pour que le développement et les tests
    # se comportent comme la production.
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def get_db():
    # Ouvrir puis fermer proprement la session SQLAlchemy
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
