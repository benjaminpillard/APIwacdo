"""Matrice des permissions : chaque route est appelée avec chacun des 3 rôles.

- rôle autorisé : la requête passe le contrôle d'accès (ni 401 ni 403)
- rôle non autorisé : 403 avec un message clair
"""
import pytest

from schemas.user import Role

ADMIN, PREPA, ACCUEIL = Role.administrateur, Role.preparateur, Role.accueil
TOUS = {ADMIN, PREPA, ACCUEIL}

# (méthode, chemin, corps JSON, rôles autorisés)
# Les identifiants 1 désignent le produit, le menu, le groupe et la commande
# créés par la fixture `donnees`.
MATRICE = [
    # Produits : lecture pour tous, gestion réservée à l'administration
    ("get", "/produits/", None, TOUS),
    ("get", "/produits/1", None, TOUS),
    ("get", "/produits/search?title=fri", None, TOUS),
    ("post", "/produits/", {"nom": "Coca", "prix": "2.00"}, {ADMIN}),
    ("put", "/produits/1", {"nom": "Frites", "prix": "2.80"}, {ADMIN}),
    ("patch", "/produits/1", {"disponible": True}, {ADMIN}),
    ("delete", "/produits/999", None, {ADMIN}),
    # Catégories
    ("get", "/categories/", None, TOUS),
    ("post", "/categories/", {"nom": "Desserts"}, {ADMIN}),
    ("put", "/categories/1", {"nom": "Accompagnements"}, {ADMIN}),
    ("delete", "/categories/999", None, {ADMIN}),
    # Menus et leur composition
    ("get", "/menus/", None, TOUS),
    ("get", "/menus/1", None, TOUS),
    ("post", "/menus/", {"nom": "Menu Maxi", "prix": "9.00", "produit_principal_id": 2}, {ADMIN}),
    ("put", "/menus/1", {"nom": "Menu Burger", "prix": "8.50", "produit_principal_id": 2}, {ADMIN}),
    ("post", "/menus/1/groupes", {"nom": "Sauce", "obligatoire": False}, {ADMIN}),
    ("post", "/menus/groupes/1/produits", {"produit_id": 1}, {ADMIN}),
    ("delete", "/menus/999", None, {ADMIN}),
    # Commandes : chaque rôle a sa part du circuit
    ("get", "/commandes/", None, TOUS),
    ("get", "/commandes/1", None, TOUS),
    ("post", "/commandes/",
     {"numero": "B1", "mode": "telephone", "lignes": [{"produit_id": 1}]}, {ADMIN, ACCUEIL}),
    ("post", "/commandes/1/preparer", None, {ADMIN, PREPA}),
    ("post", "/commandes/1/livrer", None, {ADMIN, ACCUEIL}),
    ("delete", "/commandes/999", None, {ADMIN}),
    # Gestion des utilisateurs : administration uniquement
    ("get", "/users/all", None, {ADMIN}),
    ("post", "/users/register",
     {"username": "nouveau", "email": "nouveau@test.fr", "password": "Nouveau123!"}, {ADMIN}),
    ("delete", "/users/999", None, {ADMIN}),
    # Ses propres données : tout le monde
    ("get", "/users/me", None, TOUS),
]


@pytest.fixture()
def donnees(client, creer_compte):
    """Un compte par rôle + un petit catalogue + une commande."""
    entetes = {role: creer_compte(role) for role in (ADMIN, PREPA, ACCUEIL)}
    admin = entetes[ADMIN]

    client.post("/categories/", json={"nom": "Accompagnements"}, headers=admin)
    client.post("/produits/", json={"nom": "Frites", "prix": "2.50"}, headers=admin)       # id 1
    client.post("/produits/", json={"nom": "Burger", "prix": "5.00"}, headers=admin)       # id 2
    client.post("/menus/", json={"nom": "Menu Burger", "prix": "8.00", "produit_principal_id": 2}, headers=admin)
    client.post("/menus/1/groupes", json={"nom": "Accompagnement", "obligatoire": False}, headers=admin)
    client.post(
        "/commandes/",
        json={"numero": "A1", "mode": "comptoir", "lignes": [{"produit_id": 1}]},
        headers=entetes[ACCUEIL],
    )
    return entetes


def _appeler(client, methode, chemin, corps, entetes):
    if corps is None:
        return client.request(methode, chemin, headers=entetes)
    return client.request(methode, chemin, json=corps, headers=entetes)


@pytest.mark.parametrize(
    "methode, chemin, corps, autorises",
    MATRICE,
    ids=[f"{m.upper()} {c}" for m, c, _, _ in MATRICE],
)
def test_matrice_des_roles(client, donnees, methode, chemin, corps, autorises):
    # Les rôles refusés d'abord : leurs appels ne modifient rien
    for role in sorted(TOUS - autorises, key=lambda r: r.value):
        reponse = _appeler(client, methode, chemin, corps, donnees[role])
        assert reponse.status_code == 403, f"{role.value} devrait être refusé"
        assert reponse.json()["detail"] == "Accès interdit : permission insuffisante pour votre rôle"

    for role in sorted(autorises, key=lambda r: r.value):
        reponse = _appeler(client, methode, chemin, corps, donnees[role])
        assert reponse.status_code not in (401, 403), (
            f"{role.value} devrait être autorisé, reçu {reponse.status_code} : {reponse.text}"
        )


@pytest.mark.parametrize("methode, chemin, corps, _", MATRICE, ids=[f"{m.upper()} {c}" for m, c, _, _ in MATRICE])
def test_sans_token_toujours_401(client, methode, chemin, corps, _):
    reponse = _appeler(client, methode, chemin, corps, {})
    assert reponse.status_code == 401
