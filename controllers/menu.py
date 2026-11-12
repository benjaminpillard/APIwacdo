from pydantic import BaseModel
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException

from controllers.base import CRUDBase
from models.categorie import Categorie
from models.commande import LigneCommande, LigneCommandeChoix
from models.menu import Menu, MenuGroupe, MenuGroupeProduit
from models.produit import Produit
from schemas.menu import GroupeCreate, OptionCreate


class MenuController(CRUDBase[Menu]):
    message_introuvable = "Menu introuvable"

    def requete(self) -> Select:
        # Surcharge : on charge d'un coup le plat principal, les groupes, leurs options,
        # leur catégorie et les produits de cette catégorie (évite des dizaines de requêtes)
        return select(Menu).options(
            selectinload(Menu.produit_principal),
            selectinload(Menu.groupes)
            .selectinload(MenuGroupe.options)
            .selectinload(MenuGroupeProduit.produit),
            selectinload(Menu.groupes)
            .selectinload(MenuGroupe.categorie)
            .selectinload(Categorie.produits),
        )

    def lister_filtre(self, db: Session, skip: int, limit: int, disponible: bool | None = None):
        filtres = [Menu.disponible == disponible] if disponible is not None else []
        return self.lister(db, skip=skip, limit=limit, filtres=filtres, tri=[Menu.nom])

    def rechercher(self, db: Session, texte: str):
        menus = self.lister(db, filtres=[Menu.nom.ilike(f"%{texte}%")], tri=[Menu.nom])
        if not menus:
            raise HTTPException(status_code=404, detail="Aucun menu trouvé")
        return menus

    def create(self, db: Session, donnees: BaseModel | dict) -> Menu:
        # Surcharge : le produit principal doit exister
        self._verifier_produit_principal(db, donnees)
        return super().create(db, donnees)

    def update(self, db: Session, menu: Menu, donnees: BaseModel | dict, *, partiel: bool = True) -> Menu:
        self._verifier_produit_principal(db, donnees)
        return super().update(db, menu, donnees, partiel=partiel)

    def delete(self, db: Session, menu: Menu) -> None:
        # On garde l'historique : impossible de supprimer un menu déjà commandé
        self.verifier_non_utilise(db, [
            (select(LigneCommande.id).where(LigneCommande.menu_id == menu.id),
             "ce menu a déjà été commandé (désactivez-le plutôt)"),
        ])
        super().delete(db, menu)   # les groupes et options partent avec (cascade)

    def _verifier_produit_principal(self, db: Session, donnees: BaseModel | dict) -> None:
        valeurs = donnees.model_dump(exclude_unset=True) if isinstance(donnees, BaseModel) else donnees
        self.verifier_existe(db, Produit, valeurs.get("produit_principal_id"), "Produit introuvable")


class GroupeController(CRUDBase[MenuGroupe]):
    """Les groupes de choix d'un menu (Boisson, Accompagnement, Sauce...)
    et les produits proposés dans chacun (Frites, Coca, Ketchup...).
    Chaque méthode renvoie le menu complet mis à jour, pratique pour le front."""
    message_introuvable = "Groupe introuvable"

    def ajouter(self, db: Session, menu_id: int, donnees: GroupeCreate) -> Menu:
        menu = menu_controller.get(db, menu_id)
        self.verifier_existe(db, Categorie, donnees.categorie_id, "Catégorie introuvable")
        super().create(db, {"menu_id": menu.id, **donnees.model_dump()})
        return menu_controller.get(db, menu_id)

    def supprimer(self, db: Session, groupe_id: int) -> Menu:
        groupe = self.get(db, groupe_id)
        menu_id = groupe.menu_id
        self.verifier_non_utilise(db, [
            (select(LigneCommandeChoix.id).where(LigneCommandeChoix.groupe_id == groupe_id),
             "ce groupe a déjà été utilisé dans une commande"),
        ])
        super().delete(db, groupe)
        return menu_controller.get(db, menu_id)

    def ajouter_option(self, db: Session, groupe_id: int, donnees: OptionCreate) -> Menu:
        groupe = self.get(db, groupe_id)
        if groupe.categorie_id is not None:
            raise HTTPException(
                status_code=409,
                detail="Ce groupe est lié à une catégorie : ses produits viennent de la catégorie",
            )
        self.verifier_existe(db, Produit, donnees.produit_id, "Produit introuvable")

        deja_present = db.execute(
            select(MenuGroupeProduit.id).where(
                MenuGroupeProduit.groupe_id == groupe_id,
                MenuGroupeProduit.produit_id == donnees.produit_id,
            )
        ).first()
        if deja_present is not None:
            raise HTTPException(status_code=409, detail="Ce produit est déjà dans ce groupe")

        db.add(MenuGroupeProduit(groupe_id=groupe_id, **donnees.model_dump()))
        db.commit()
        return menu_controller.get(db, groupe.menu_id)

    def retirer_option(self, db: Session, groupe_id: int, produit_id: int) -> Menu:
        groupe = self.get(db, groupe_id)
        option = db.execute(
            select(MenuGroupeProduit).where(
                MenuGroupeProduit.groupe_id == groupe_id,
                MenuGroupeProduit.produit_id == produit_id,
            )
        ).scalars().first()
        if option is None:
            raise HTTPException(status_code=404, detail="Ce produit n'est pas dans ce groupe")

        db.delete(option)
        db.commit()
        return menu_controller.get(db, groupe.menu_id)


menu_controller = MenuController(Menu)
groupe_controller = GroupeController(MenuGroupe)
