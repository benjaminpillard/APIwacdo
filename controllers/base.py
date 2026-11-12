"""Controller générique : les opérations communes à toutes les ressources.

CRUDBase[Modele] sait lire, lister, créer, modifier et supprimer n'importe quel
modèle SQLAlchemy. Chaque controller (produits, menus, commandes...) en HÉRITE
et ne réécrit (surcharge) que ce qui lui est propre :

    class ProduitController(CRUDBase[Produit]):
        message_introuvable = "Produit introuvable"

        def delete(self, db, produit):      # surcharge : vérifications en plus
            ...
            super().delete(db, produit)     # puis comportement commun

Avantages : pas de code dupliqué, des messages et des statuts HTTP cohérents
partout, et un seul endroit à corriger en cas de bug.
"""
from typing import Any, Generic, Sequence, TypeVar

from fastapi import HTTPException, status
from pydantic import BaseModel
from sqlalchemy import Select, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.database import Base

# « Modele » représente n'importe quelle classe de modèle (Produit, Menu...) :
# c'est ce qui rend la classe générique.
Modele = TypeVar("Modele", bound=Base)


class CRUDBase(Generic[Modele]):
    # Messages d'erreur, redéfinis par chaque classe fille
    message_introuvable = "Ressource introuvable"
    message_doublon = "Cette ressource existe déjà"

    def __init__(self, modele: type[Modele]):
        self.modele = modele

    # ---------- Lecture ----------

    def requete(self) -> Select:
        """Requête de base. Surchargée quand il faut charger des relations
        en une seule fois (ex. un menu avec ses groupes et leurs produits)."""
        return select(self.modele)

    def get(self, db: Session, id: int) -> Modele:
        """Renvoie l'élément, ou lève une 404."""
        element = db.execute(self.requete().where(self.modele.id == id)).scalars().first()
        if element is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=self.message_introuvable)
        return element

    def lister(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filtres: Sequence[Any] = (),
        tri: Sequence[Any] = (),
    ) -> Sequence[Modele]:
        """Liste paginée. `filtres` et `tri` sont des expressions SQLAlchemy,
        ex. filtres=[Produit.disponible == True], tri=[Produit.nom]."""
        stmt = self.requete()
        for filtre in filtres:
            stmt = stmt.where(filtre)
        stmt = stmt.order_by(*tri).offset(skip).limit(limit)
        return db.execute(stmt).scalars().all()

    # ---------- Écriture ----------

    def create(self, db: Session, donnees: BaseModel | dict) -> Modele:
        valeurs = donnees.model_dump() if isinstance(donnees, BaseModel) else donnees
        element = self.modele(**valeurs)
        db.add(element)
        self._commit(db)
        return self.get(db, element.id)

    def update(self, db: Session, element: Modele, donnees: BaseModel | dict, *, partiel: bool = True) -> Modele:
        """partiel=True (PATCH) : seuls les champs envoyés changent.
        partiel=False (PUT) : l'élément est entièrement remplacé."""
        if isinstance(donnees, BaseModel):
            valeurs = donnees.model_dump(exclude_unset=partiel)
        else:
            valeurs = donnees
        for champ, valeur in valeurs.items():
            setattr(element, champ, valeur)
        self._commit(db)
        return self.get(db, element.id)

    def delete(self, db: Session, element: Modele) -> None:
        db.delete(element)
        db.commit()

    # ---------- Outils pour les classes filles ----------

    def verifier_non_utilise(self, db: Session, utilisations: list[tuple[Select, str]]) -> None:
        """Lève une 409 si l'une des requêtes trouve une ligne qui utilise l'élément.
        Chaque utilisation est un couple (requête, raison affichée)."""
        for requete, raison in utilisations:
            if db.execute(requete.limit(1)).first() is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Impossible de supprimer : {raison}",
                )

    def verifier_existe(self, db: Session, modele: type[Base], id: int | None, message: str) -> None:
        """404 si une référence (ex. categorie_id) pointe vers un élément inexistant."""
        if id is not None and db.get(modele, id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    def _commit(self, db: Session) -> None:
        # Une contrainte d'unicité violée devient une 409 avec un message clair
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=self.message_doublon)
