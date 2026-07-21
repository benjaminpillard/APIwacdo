from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from models.database import Base
from models.menu_produit import association_table

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    price = Column(Float)

    produits = relationship("Produit",
            secondary=association_table,
            back_populates="menus"
        )
    
