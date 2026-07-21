from sqlalchemy import Column, ForeignKey, Table
from models.database import Base

association_table = Table(
    "association_table",
    Base.metadata,
    Column("commande_id", ForeignKey("commandes.id"), primary_key=True),
    Column("produit_id", ForeignKey("produits.id"), primary_key=True)
)