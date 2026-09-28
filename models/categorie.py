from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from models.database import Base


class Categorie(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(50), unique=True, nullable=False)

    produits = relationship("Produit", back_populates="categorie")