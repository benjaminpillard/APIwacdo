from sqlalchemy import select
from sqlalchemy.orm import Session

from controllers.base import CRUDBase
from models.categorie import Categorie
from models.menu import MenuGroupe
from models.produit import Produit


class CategorieController(CRUDBase[Categorie]):
    message_introuvable = "Catégorie introuvable"
    message_doublon = "Cette catégorie existe déjà"   # le nom est unique en base

    def lister_toutes(self, db: Session):
        # Tri par nom pour un affichage stable
        return self.lister(db, limit=1000, tri=[Categorie.nom])

    def delete(self, db: Session, categorie: Categorie) -> None:
        # Surcharge : on refuse de supprimer une catégorie encore utilisée
        self.verifier_non_utilise(db, [
            (select(Produit.id).where(Produit.categorie_id == categorie.id),
             "des produits utilisent cette catégorie"),
            (select(MenuGroupe.id).where(MenuGroupe.categorie_id == categorie.id),
             "un groupe de menu utilise cette catégorie"),
        ])
        super().delete(db, categorie)


categorie_controller = CategorieController(Categorie)
