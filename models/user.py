from sqlalchemy import Boolean, Column, Integer, String, true
from models.database import Base
from sqlalchemy.orm import relationship



class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    role = Column(String, default="accueil")  # rôle par défaut : le moins de droits

    # False quand le compte a été supprimé puis anonymisé (RGPD) : plus aucune connexion possible
    actif = Column(Boolean, nullable=False, default=True, server_default=true())

    commandes = relationship("Commande", back_populates="utilisateur")

    
