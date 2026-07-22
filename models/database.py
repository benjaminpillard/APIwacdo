from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from utils.setting import settings



database_url = settings.DATABASE_URL
# Adapter les vieux formats Postgres vers psycopg
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
elif database_url.startswith("postgresql+psycopg2://"):
    database_url = database_url.replace("postgresql+psycopg2://", "postgresql+psycopg://", 1)

connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}

engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    # Ouvrir puis fermer proprement la session SQLAlchemy
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()