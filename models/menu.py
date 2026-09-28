from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from models.database import Base


class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    description = Column(String(500))
    prix = Column(Numeric(8, 2), nullable=False)
    image_url = Column(String(255))
    disponible = Column(Boolean, nullable=False, default=True)
    # Le plat fixe du menu (ex. le Big Mac)
    produit_principal_id = Column(Integer, ForeignKey("produits.id"), nullable=False)

    produit_principal = relationship("Produit")
    groupes = relationship(
        "MenuGroupe", back_populates="menu", cascade="all, delete-orphan"
    )


class MenuGroupe(Base):
    """Un groupe de choix dans un menu : Accompagnement, Boisson, Sauce..."""
    __tablename__ = "menu_groupes"

    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id"), nullable=False)
    nom = Column(String(50), nullable=False)
    obligatoire = Column(Boolean, nullable=False, default=True)
    max_choix = Column(Integer, nullable=False, default=1)

    menu = relationship("Menu", back_populates="groupes")
    options = relationship(
        "MenuGroupeProduit", back_populates="groupe", cascade="all, delete-orphan"
    )


class MenuGroupeProduit(Base):
    """Un produit proposé dans un groupe, avec un éventuel supplément de prix."""
    __tablename__ = "menu_groupe_produits"
    __table_args__ = (UniqueConstraint("groupe_id", "produit_id"),)

    id = Column(Integer, primary_key=True)
    groupe_id = Column(Integer, ForeignKey("menu_groupes.id"), nullable=False)
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=False)
    supplement = Column(Numeric(8, 2), nullable=False, default=0)

    groupe = relationship("MenuGroupe", back_populates="options")
    produit = relationship("Produit")