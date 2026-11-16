"""Le script de démonstration doit charger des données cohérentes et pouvoir être relancé."""
from models import Categorie, Commande, Menu, Produit, Utilisateur
from seed import charger_donnees_demo

MDP = "Demo12345!"


def _compter(db):
    return {m.__name__: db.query(m).count() for m in (Categorie, Produit, Menu, Utilisateur, Commande)}


def test_seed_charge_le_catalogue_et_les_commandes(session_factory):
    db = session_factory()
    charger_donnees_demo(db, MDP, MDP)

    assert _compter(db) == {"Categorie": 5, "Produit": 16, "Menu": 3, "Utilisateur": 2, "Commande": 4}
    statuts = sorted(c.statut.value for c in db.query(Commande))
    assert statuts == ["livree", "preparee", "saisie", "saisie"]
    db.close()


def test_seed_peut_etre_relance_sans_doublon(session_factory):
    db = session_factory()
    charger_donnees_demo(db, MDP, MDP)
    avant = _compter(db)
    charger_donnees_demo(db, MDP, MDP)
    assert _compter(db) == avant
    db.close()


def test_menu_de_demo_avec_supplement(client, session_factory, creer_compte):
    from schemas.user import Role
    db = session_factory()
    charger_donnees_demo(db, MDP, MDP)
    db.close()

    entetes = creer_compte(Role.administrateur)
    commande = next(c for c in client.get("/commandes/", headers=entetes).json() if c["numero"] == "DEMO-001")
    # Menu Classic 8,90 + Potatoes 0,50, le tout × 2
    assert commande["total"] == "18.80"
