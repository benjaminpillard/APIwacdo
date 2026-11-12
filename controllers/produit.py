from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from controllers.base import CRUDBase
from models.categorie import Categorie
from models.commande import LigneCommande, LigneCommandeChoix
from models.menu import Menu, MenuGroupeProduit
from models.produit import Produit


class ProduitController(CRUDBase[Produit]):
    message_introuvable = "Produit introuvable"

    def lister_filtre(
        self,
        db: Session,
        skip: int,
        limit: int,
        categorie_id: int | None = None,
        disponible: bool | None = None,
    ):
        # Filtres facultatifs : on ne les applique que s'ils sont fournis
        filtres = []
        if categorie_id is not None:
            filtres.append(Produit.categorie_id == categorie_id)
        if disponible is not None:
            filtres.append(Produit.disponible == disponible)
        return self.lister(db, skip=skip, limit=limit, filtres=filtres, tri=[Produit.nom])

    def rechercher(self, db: Session, texte: str):
        # Requête paramétrée par SQLAlchemy : pas d'injection SQL possible
        produits = self.lister(db, filtres=[Produit.nom.ilike(f"%{texte}%")], tri=[Produit.nom])
        if not produits:
            raise HTTPException(status_code=404, detail="Aucun produit trouvé")
        return produits

    def create(self, db: Session, donnees: BaseModel | dict) -> Produit:
        # Surcharge : la catégorie indiquée doit exister
        self._verifier_categorie(db, donnees)
        return super().create(db, donnees)

    def update(self, db: Session, produit: Produit, donnees: BaseModel | dict, *, partiel: bool = True) -> Produit:
        self._verifier_categorie(db, donnees)
        return super().update(db, produit, donnees, partiel=partiel)

    def delete(self, db: Session, produit: Produit) -> None:
        # Surcharge : on garde l'historique et la cohérence des menus.
        # Un produit déjà utilisé ne se supprime pas, on le rend indisponible.
        self.verifier_non_utilise(db, [
            (select(LigneCommande.id).where(LigneCommande.produit_id == produit.id),
             "il a déjà été commandé (rendez-le indisponible plutôt)"),
            (select(LigneCommandeChoix.id).where(LigneCommandeChoix.produit_id == produit.id),
             "il a déjà été choisi dans un menu commandé (rendez-le indisponible plutôt)"),
            (select(Menu.id).where(Menu.produit_principal_id == produit.id),
             "il est le produit principal d'un menu (rendez-le indisponible plutôt)"),
            (select(MenuGroupeProduit.id).where(MenuGroupeProduit.produit_id == produit.id),
             "il est proposé dans un menu (rendez-le indisponible plutôt)"),
        ])
        super().delete(db, produit)

    def _verifier_categorie(self, db: Session, donnees: BaseModel | dict) -> None:
        valeurs = donnees.model_dump(exclude_unset=True) if isinstance(donnees, BaseModel) else donnees
        self.verifier_existe(db, Categorie, valeurs.get("categorie_id"), "Catégorie introuvable")


produit_controller = ProduitController(Produit)
