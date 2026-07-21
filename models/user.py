from sqlalchemy import Column, Integer, String
from models.database import Base
from sqlalchemy.orm import relationship



class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    role = Column(String, default="Accueil")  # Default role is 'user'

    commandes = relationship("Commande", back_populates="utilisateur")

    
