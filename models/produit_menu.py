from sqlalchemy import Column, ForeignKey, Table
from models.database import Base

produit_menu_association_table = Table(
    "produit_menu_association",
    Base.metadata,
    Column("menu_id", ForeignKey("menus.id"), primary_key=True),
    Column("produit_id", ForeignKey("produits.id"), primary_key=True)
)