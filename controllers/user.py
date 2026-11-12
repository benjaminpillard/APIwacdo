import secrets

from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from controllers.base import CRUDBase
from models.commande import Commande
from models.user import Utilisateur
from schemas.user import UserCreate, Role
from utils.hash import hash_password, verify_password
from utils.logger import audit


class UtilisateurController(CRUDBase[Utilisateur]):
    message_introuvable = "Utilisateur introuvable"
    message_doublon = "Nom d'utilisateur ou email déjà utilisé"

    def lister_tous(self, db: Session):
        return self.lister(db, limit=1000, tri=[Utilisateur.username])

    def create(self, db: Session, donnees: UserCreate) -> Utilisateur:
        # Surcharge : le mot de passe est haché avant d'être enregistré, jamais stocké en clair
        utilisateur = super().create(db, {
            "username": donnees.username,
            "email": donnees.email,
            "password": hash_password(donnees.password),
            "role": donnees.role.value,   # .value : on stocke la chaîne, pas l'enum
        })
        audit.info("Compte créé : utilisateur=%s rôle=%s", utilisateur.username, utilisateur.role)
        return utilisateur

    def update(self, db: Session, utilisateur: Utilisateur, donnees: BaseModel | dict, *, partiel: bool = True) -> Utilisateur:
        # Surcharge : un nouveau mot de passe est haché lui aussi
        valeurs = donnees.model_dump(exclude_unset=True) if isinstance(donnees, BaseModel) else dict(donnees)
        if "password" in valeurs:
            valeurs["password"] = hash_password(valeurs["password"])
        return super().update(db, utilisateur, valeurs)

    def authentifier(self, db: Session, username: str, password: str) -> Utilisateur | None:
        utilisateur = db.execute(
            select(Utilisateur).where(Utilisateur.username == username)
        ).scalars().first()

        # Un compte anonymisé (RGPD) ne peut plus se connecter
        if utilisateur is None or not utilisateur.actif:
            return None
        if not verify_password(str(utilisateur.password), password):
            return None
        return utilisateur

    def delete(self, db: Session, utilisateur: Utilisateur) -> None:
        """Droit à l'effacement (RGPD).

        - Sans commande : le compte est réellement supprimé.
        - Avec des commandes : on ne peut pas le supprimer sans casser l'historique
          (chaque commande garde son auteur). On l'anonymise donc : toutes les données
          personnelles sont remplacées et le compte est désactivé,
          mais les commandes restent cohérentes.
        """
        # On ne supprime jamais le dernier administrateur actif :
        # plus personne ne pourrait gérer l'application
        if utilisateur.role == Role.administrateur.value:
            nb_admins_actifs = db.execute(
                select(func.count()).select_from(Utilisateur).where(
                    Utilisateur.role == Role.administrateur.value,
                    Utilisateur.actif.is_(True),
                )
            ).scalar_one()
            if nb_admins_actifs <= 1:
                raise HTTPException(status_code=409, detail="Impossible de supprimer le dernier administrateur")

        a_des_commandes = db.execute(
            select(Commande.id).where(Commande.utilisateur_id == utilisateur.id).limit(1)
        ).first() is not None

        ancien_nom = utilisateur.username
        if a_des_commandes:
            utilisateur.actif = False
            utilisateur.username = f"supprime_{utilisateur.id}"
            utilisateur.email = f"supprime_{utilisateur.id}@example.com"   # domaine réservé, n'appartient à personne
            # Mot de passe aléatoire jamais communiqué : plus aucune connexion possible
            utilisateur.password = hash_password(secrets.token_urlsafe(32))
            db.commit()
        else:
            super().delete(db, utilisateur)

        audit.info(
            "Compte %s : ancien utilisateur=%s",
            "anonymisé (il a des commandes)" if a_des_commandes else "supprimé",
            ancien_nom,
        )


utilisateur_controller = UtilisateurController(Utilisateur)
