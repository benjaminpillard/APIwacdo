"""Charge des données de démonstration : catalogue, menus, comptes de démo et commandes.

Prérequis : la base est à jour (alembic upgrade head) et un administrateur existe.
Usage     : python seed.py

Le script peut être relancé sans risque : ce qui existe déjà est conservé, rien n'est dupliqué.
Les mots de passe des comptes de démo sont demandés au clavier, jamais écrits dans le code.
"""
import getpass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

import models  # charge tous les modèles (relations entre tables)
from controllers.categorie import categorie_controller
from controllers.commande import commande_controller
from controllers.menu import menu_controller, groupe_controller
from controllers.produit import produit_controller
from controllers.user import utilisateur_controller
from models.categorie import Categorie
from models.commande import Commande
from models.menu import Menu
from models.produit import Produit
from models.user import Utilisateur
from schemas.commande import CommandeCreate
from schemas.menu import GroupeCreate, OptionCreate
from schemas.user import UserCreate, Role


def _image(texte: str) -> str:
    # Image d'illustration générique (le vrai visuel serait fourni par le restaurant)
    return f"https://placehold.co/400x300?text={texte.replace(' ', '+')}"


CATEGORIES = ["Burgers", "Accompagnements", "Boissons", "Desserts", "Sauces"]

# (nom, description, prix, catégorie, disponible)
PRODUITS = [
    ("Classic Burger", "Steak haché, cheddar, salade, tomate, sauce maison", "5.90", "Burgers", True),
    ("Double Cheese", "Deux steaks, double cheddar, oignons, cornichons", "6.90", "Burgers", True),
    ("Chicken Burger", "Filet de poulet pané, salade, sauce blanche", "6.20", "Burgers", True),
    ("Veggie Burger", "Galette de légumes, avocat, tomate, roquette", "6.50", "Burgers", True),
    ("Frites", "Frites croustillantes, portion moyenne", "2.50", "Accompagnements", True),
    ("Potatoes", "Quartiers de pommes de terre épicés", "2.90", "Accompagnements", True),
    ("Salade", "Petite salade verte et tomates cerises", "2.80", "Accompagnements", True),
    ("Cola", "Soda 50 cl", "2.20", "Boissons", True),
    ("Thé glacé", "Thé glacé pêche 50 cl", "2.20", "Boissons", True),
    ("Eau minérale", "Bouteille 50 cl", "1.80", "Boissons", True),
    ("Jus d'orange", "Pur jus 33 cl (en rupture)", "2.50", "Boissons", False),
    ("Sundae caramel", "Glace vanille, nappage caramel", "2.90", "Desserts", True),
    ("Cookie", "Cookie aux pépites de chocolat", "1.90", "Desserts", True),
    ("Ketchup", "Sauce tomate", "0.30", "Sauces", True),
    ("Mayonnaise", "Sauce mayonnaise", "0.30", "Sauces", True),
    ("Barbecue", "Sauce barbecue fumée", "0.30", "Sauces", True),
]

# Menus : (nom, description, prix, produit principal)
MENUS = [
    ("Menu Classic", "Classic Burger + accompagnement + boisson", "8.90", "Classic Burger"),
    ("Menu Double Cheese", "Double Cheese + accompagnement + boisson", "9.90", "Double Cheese"),
    ("Menu Chicken", "Chicken Burger + accompagnement + boisson + sauce", "9.40", "Chicken Burger"),
]


def _cree_ou_existant(db: Session, modele, nom: str):
    return db.execute(select(modele).where(modele.nom == nom)).scalars().first()


def charger_catalogue(db: Session) -> dict[str, int]:
    """Catégories, produits et menus avec leurs groupes de choix. Renvoie les ids par nom."""
    ids: dict[str, int] = {}

    for nom in CATEGORIES:
        categorie = _cree_ou_existant(db, Categorie, nom) or categorie_controller.create(db, {"nom": nom})
        ids[nom] = categorie.id

    for nom, description, prix, categorie, disponible in PRODUITS:
        produit = _cree_ou_existant(db, Produit, nom) or produit_controller.create(db, {
            "nom": nom, "description": description, "prix": prix, "image_url": _image(nom),
            "disponible": disponible, "categorie_id": ids[categorie],
        })
        ids[nom] = produit.id

    for nom, description, prix, principal in MENUS:
        if _cree_ou_existant(db, Menu, nom) is not None:
            ids[nom] = _cree_ou_existant(db, Menu, nom).id
            continue
        menu = menu_controller.create(db, {
            "nom": nom, "description": description, "prix": prix,
            "image_url": _image(nom), "produit_principal_id": ids[principal],
        })
        ids[nom] = menu.id

        # Accompagnement : produits ajoutés un par un, avec un supplément pour les Potatoes
        menu = groupe_controller.ajouter(db, menu.id, GroupeCreate(nom="Accompagnement", obligatoire=True, max_choix=1))
        groupe = menu.groupes[-1]
        groupe_controller.ajouter_option(db, groupe.id, OptionCreate(produit_id=ids["Frites"]))
        groupe_controller.ajouter_option(db, groupe.id, OptionCreate(produit_id=ids["Salade"]))
        groupe_controller.ajouter_option(db, groupe.id, OptionCreate(produit_id=ids["Potatoes"], supplement="0.50"))

        # Boisson : toutes les boissons disponibles de la catégorie
        groupe_controller.ajouter(db, menu.id, GroupeCreate(
            nom="Boisson", obligatoire=True, max_choix=1, categorie_id=ids["Boissons"],
        ))

        # Sauces facultatives (jusqu'à 2) pour le menu Chicken
        if nom == "Menu Chicken":
            groupe_controller.ajouter(db, menu.id, GroupeCreate(
                nom="Sauce", obligatoire=False, max_choix=2, categorie_id=ids["Sauces"],
            ))

    return ids


def charger_comptes(db: Session, mot_de_passe_preparateur: str, mot_de_passe_accueil: str) -> dict[str, int]:
    """Un compte préparateur et un compte accueil de démonstration."""
    comptes = {}
    for username, role, mot_de_passe in [
        ("preparateur_demo", Role.preparateur, mot_de_passe_preparateur),
        ("accueil_demo", Role.accueil, mot_de_passe_accueil),
    ]:
        existant = db.execute(select(Utilisateur).where(Utilisateur.username == username)).scalars().first()
        utilisateur = existant or utilisateur_controller.create(db, UserCreate(
            username=username, email=f"{username}@wacdo.fr", password=mot_de_passe, role=role,
        ))
        comptes[username] = utilisateur.id
    return comptes


def charger_commandes(db: Session, ids: dict[str, int], accueil_id: int) -> None:
    """Quelques commandes à différents stades, pour montrer le circuit et le tri par heure."""
    menu_classic = menu_controller.get(db, ids["Menu Classic"])
    groupes = {g.nom: g.id for g in menu_classic.groupes}
    maintenant = datetime.now(timezone.utc).replace(second=0, microsecond=0)

    commandes = [
        # (numéro, mode, minutes avant livraison, lignes, statut final)
        ("DEMO-001", "telephone", 45, [
            {"menu_id": ids["Menu Classic"], "quantite": 2, "choix": [
                {"groupe_id": groupes["Accompagnement"], "produit_id": ids["Potatoes"]},
                {"groupe_id": groupes["Boisson"], "produit_id": ids["Cola"]},
            ]},
        ], "saisie"),
        ("DEMO-002", "comptoir", 15, [
            {"produit_id": ids["Veggie Burger"]},
            {"produit_id": ids["Eau minérale"]},
        ], "saisie"),
        ("DEMO-003", "comptoir", 5, [
            {"produit_id": ids["Double Cheese"]},
            {"produit_id": ids["Frites"]},
        ], "preparee"),
        ("DEMO-004", "telephone", -30, [
            {"produit_id": ids["Sundae caramel"], "quantite": 3},
        ], "livree"),
    ]

    for numero, mode, minutes, lignes, statut in commandes:
        if db.execute(select(Commande.id).where(Commande.numero == numero)).first():
            continue
        commande = commande_controller.saisir(db, CommandeCreate(
            numero=numero, mode=mode, heure_livraison=maintenant + timedelta(minutes=minutes), lignes=lignes,
        ), accueil_id)
        if statut in ("preparee", "livree"):
            commande_controller.changer_statut(db, commande.id, models.StatutCommande.preparee, "seed")
        if statut == "livree":
            commande_controller.changer_statut(db, commande.id, models.StatutCommande.livree, "seed")


def charger_donnees_demo(db: Session, mot_de_passe_preparateur: str, mot_de_passe_accueil: str) -> None:
    ids = charger_catalogue(db)
    comptes = charger_comptes(db, mot_de_passe_preparateur, mot_de_passe_accueil)
    charger_commandes(db, ids, comptes["accueil_demo"])


if __name__ == "__main__":
    from fastapi import HTTPException
    from pydantic import ValidationError
    from models.database import SessionLocal

    def demander_mot_de_passe(compte: str) -> str:
        # Rien ne s'affiche pendant la saisie : c'est normal (le mot de passe reste invisible)
        while True:
            mot_de_passe = getpass.getpass(f"Mot de passe de {compte} (invisible pendant la saisie) : ")
            if len(mot_de_passe) >= 8:
                return mot_de_passe
            print("  8 caractères minimum, recommencez.")

    print("Données de démonstration Wacdo")
    print("Comptes créés : preparateur_demo et accueil_demo (8 caractères minimum)")
    mdp_prepa = demander_mot_de_passe("preparateur_demo")
    mdp_accueil = demander_mot_de_passe("accueil_demo")

    session = SessionLocal()
    try:
        charger_donnees_demo(session, mdp_prepa, mdp_accueil)
        print("Données chargées :")
        for modele, libelle in [(Categorie, "catégories"), (Produit, "produits"), (Menu, "menus"),
                                (Utilisateur, "comptes"), (Commande, "commandes")]:
            print(f"  {session.query(modele).count():>3} {libelle}")
    except ValidationError as e:
        # On n'affiche que le champ et la règle, jamais la valeur saisie (ce peut être un mot de passe)
        for erreur in e.errors():
            print(f"Données invalides : {'.'.join(map(str, erreur['loc']))} : {erreur['msg']}")
    except HTTPException as e:
        print(f"Erreur : {e.detail}")
    finally:
        session.close()
