from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from models.database import Base
from sqlalchemy.orm import relationship



class Produit(Base):
    __tablename__ = "produits"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    price = Column(Float)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    menus = relationship("Menu",
            secondary="menu_produit", 
            back_populates="produits"
        )
    
    commandes = relationship("Commande",
            secondary="commande_produit",
            back_populates="produits"
        )