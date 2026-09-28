from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Enum, ForeignKey, CheckConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from models.database import Base
from models.enums import StatutCommande, ModeCommande


class Commande(Base):
    __tablename__ = "commandes"

    id = Column(Integer, primary_key=True, index=True)
    numero = Column(String(20), unique=True, nullable=False)
    statut = Column(
        Enum(StatutCommande, native_enum=False),
        nullable=False, default=StatutCommande.saisie, index=True,
    )
    mode = Column(Enum(ModeCommande, native_enum=False), nullable=False)
    heure_livraison = Column(DateTime(timezone=True), index=True)
    total = Column(Numeric(8, 2), nullable=False, default=0)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    utilisateur = relationship("Utilisateur", back_populates="commandes")
    lignes = relationship(
        "LigneCommande", back_populates="commande", cascade="all, delete-orphan"
    )


class LigneCommande(Base):
    __tablename__ = "lignes_commande"
    __table_args__ = (
        # Une ligne concerne soit un produit, soit un menu, jamais les deux
        CheckConstraint("(produit_id IS NULL) <> (menu_id IS NULL)"),
    )

    id = Column(Integer, primary_key=True)
    commande_id = Column(Integer, ForeignKey("commandes.id"), nullable=False)
    produit_id = Column(Integer, ForeignKey("produits.id"))
    menu_id = Column(Integer, ForeignKey("menus.id"))
    quantite = Column(Integer, nullable=False, default=1)
    # Prix figé au moment de la commande
    prix_unitaire = Column(Numeric(8, 2), nullable=False)

    commande = relationship("Commande", back_populates="lignes")
    produit = relationship("Produit")
    menu = relationship("Menu")
    choix = relationship(
        "LigneCommandeChoix", back_populates="ligne", cascade="all, delete-orphan"
    )


class LigneCommandeChoix(Base):
    """Ce que le client a choisi dans un groupe du menu (frites, boisson, sauce...)."""
    __tablename__ = "lignes_commande_choix"

    id = Column(Integer, primary_key=True)
    ligne_commande_id = Column(Integer, ForeignKey("lignes_commande.id"), nullable=False)
    groupe_id = Column(Integer, ForeignKey("menu_groupes.id"), nullable=False)
    produit_id = Column(Integer, ForeignKey("produits.id"), nullable=False)

    ligne = relationship("LigneCommande", back_populates="choix")
    groupe = relationship("MenuGroupe")
    produit = relationship("Produit")