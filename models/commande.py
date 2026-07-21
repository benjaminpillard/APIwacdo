from sqlalchemy import Column, DateTime, Integer, String, Float, ForeignKey, func
from sqlalchemy.orm import relationship
from models.commande_produit import association_table

from models.database import Base

class Commande(Base):
    __tablename__ = "commandes"

    id = Column(Integer, primary_key=True, index=True)
    number = Column(String, unique=True)
    status = Column(String)
    total = Column(Float)
    user_id = Column(Integer, ForeignKey("utilisateurs.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    produits = relationship("Produit",
            secondary=association_table,
            back_populates="commandes"
        )
    
    utilisateur = relationship("Utilisateur", back_populates="commandes")