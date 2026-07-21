from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from models.database import Base
from sqlalchemy.orm import relationship
from models.menu_produit import association_table as menu_association_table
from models.commande_produit import association_table as commande_association_table



class Produit(Base):
    __tablename__ = "produits"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    price = Column(Float)
    currency = Column(String, default="EUR")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    menus = relationship("Menu",
            secondary=menu_association_table,
            back_populates="produits"
        )
    
    commandes = relationship("Commande",
            secondary=commande_association_table,
            back_populates="produits"
        )