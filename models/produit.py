from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.database import Base


class Produit(Base):
    __tablename__ = "produits"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False, index=True)
    description = Column(String(500))
    prix = Column(Numeric(8, 2), nullable=False)
    image_url = Column(String(255))
    disponible = Column(Boolean, nullable=False, default=True)
    categorie_id = Column(Integer, ForeignKey("categories.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    categorie = relationship("Categorie", back_populates="produits")