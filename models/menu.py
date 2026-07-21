from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import relationship
from models.database import Base

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    price = Column(Float)

    produits = relationship("Produit",
            secondary="menu_produit", 
            back_populates="menus"
        )
    
