from schemas.user import Role
from tests.conftest import MOT_DE_PASSE


def _passer_une_commande(client, admin, accueil):
    produit = client.post(
        "/produits/", json={"nom": "Frites", "prix": "2.50"}, headers=admin
    ).json()
    reponse = client.post(
        "/commandes/",
        json={"numero": "A1", "mode": "comptoir", "lignes": [{"produit_id": produit["id"]}]},
        headers=accueil,
    )
    assert reponse.status_code == 201
    return reponse.json()


def test_consulter_ses_donnees(client, creer_compte):
    accueil = creer_compte(Role.accueil)
    reponse = client.get("/users/me", headers=accueil)
    assert reponse.status_code == 200
    assert reponse.json()["username"] == "accueil"
    assert "password" not in reponse.json()   # le hash n'est jamais renvoyé


def test_modifier_ses_donnees(client, creer_compte):
    accueil = creer_compte(Role.accueil)
    reponse = client.patch("/users/me", json={"email": "nouvel@test.fr"}, headers=accueil)
    assert reponse.status_code == 200
    assert reponse.json()["email"] == "nouvel@test.fr"


def test_ne_peut_pas_se_donner_un_role(client, creer_compte):
    accueil = creer_compte(Role.accueil)
    client.patch("/users/me", json={"role": "administrateur"}, headers=accueil)
    assert client.get("/users/me", headers=accueil).json()["role"] == "accueil"


def test_supprimer_compte_sans_commande(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    accueil = creer_compte(Role.accueil)

    assert client.delete("/users/me", headers=accueil).status_code == 204

    noms = [u["username"] for u in client.get("/users/all", headers=admin).json()]
    assert "accueil" not in noms


def test_supprimer_compte_avec_commandes_anonymise(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    accueil = creer_compte(Role.accueil)
    commande = _passer_une_commande(client, admin, accueil)

    assert client.delete("/users/me", headers=accueil).status_code == 204

    # Plus aucune donnée personnelle
    utilisateurs = client.get("/users/all", headers=admin).json()
    anonyme = next(u for u in utilisateurs if u["id"] == commande["utilisateur_id"])
    assert anonyme["username"].startswith("supprime_")
    assert "accueil@test.fr" not in [u["email"] for u in utilisateurs]

    # Plus de connexion possible, ni avec l'ancien token ni avec l'ancien mot de passe
    assert client.get("/users/me", headers=accueil).status_code == 401
    login = client.post("/users/login", data={"username": "accueil", "password": MOT_DE_PASSE})
    assert login.status_code == 401

    # La commande est intacte
    assert client.get(f"/commandes/{commande['id']}", headers=admin).status_code == 200


def test_admin_supprime_un_compte_avec_commandes(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    accueil = creer_compte(Role.accueil)
    commande = _passer_une_commande(client, admin, accueil)

    reponse = client.delete(f"/users/{commande['utilisateur_id']}", headers=admin)
    assert reponse.status_code == 204


def test_dernier_admin_ne_peut_pas_etre_supprime(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    reponse = client.delete("/users/me", headers=admin)
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == "Impossible de supprimer le dernier administrateur"


def test_admin_supprimable_s_il_en_reste_un_autre(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    client.post(
        "/users/register",
        json={"username": "admin2", "email": "admin2@test.fr",
              "password": MOT_DE_PASSE, "role": "administrateur"},
        headers=admin,
    )
    assert client.delete("/users/me", headers=admin).status_code == 204
