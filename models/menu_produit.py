from sqlalchemy import Column, ForeignKey, Table

from models.database import Base


association_table = Table(
    "menu_produit",
    Base.metadata,
    Column("menu_id", ForeignKey("menus.id"), primary_key=True),
    Column("produit_id", ForeignKey("produits.id"), primary_key=True),
)