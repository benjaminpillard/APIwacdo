from schemas.user import Role


def _creer_produit(client, entetes, **donnees):
    corps = {"nom": "Frites", "prix": "2.50", **donnees}
    reponse = client.post("/produits/", json=corps, headers=entetes)
    assert reponse.status_code == 201
    return reponse.json()


def test_creer_produit_categorie_inexistante_refuse(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    reponse = client.post(
        "/produits/", json={"nom": "X", "prix": "1.00", "categorie_id": 999}, headers=admin
    )
    assert reponse.status_code == 404
    assert reponse.json()["detail"] == "Catégorie introuvable"


def test_modifier_produit_categorie_inexistante_refuse(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    produit = _creer_produit(client, admin)
    reponse = client.patch(
        f"/produits/{produit['id']}", json={"categorie_id": 999}, headers=admin
    )
    assert reponse.status_code == 404


def test_supprimer_produit_jamais_utilise(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    produit = _creer_produit(client, admin)

    assert client.delete(f"/produits/{produit['id']}", headers=admin).status_code == 204
    assert client.get(f"/produits/{produit['id']}", headers=admin).status_code == 404


def test_supprimer_produit_deja_commande_refuse(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    accueil = creer_compte(Role.accueil)
    produit = _creer_produit(client, admin)
    client.post(
        "/commandes/",
        json={"numero": "A1", "mode": "comptoir", "lignes": [{"produit_id": produit["id"]}]},
        headers=accueil,
    )

    reponse = client.delete(f"/produits/{produit['id']}", headers=admin)

    assert reponse.status_code == 409
    assert "déjà été commandé" in reponse.json()["detail"]
    # La commande garde bien son produit
    commande = client.get("/commandes/1", headers=admin).json()
    assert commande["lignes"][0]["produit"]["id"] == produit["id"]


def test_supprimer_produit_principal_d_un_menu_refuse(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    burger = _creer_produit(client, admin, nom="Burger", prix="5.00")
    client.post(
        "/menus/",
        json={"nom": "Menu Burger", "prix": "8.00", "produit_principal_id": burger["id"]},
        headers=admin,
    )

    reponse = client.delete(f"/produits/{burger['id']}", headers=admin)

    assert reponse.status_code == 409
    # Le menu reste lisible (avant la correction, GET /menus plantait)
    assert client.get("/menus/", headers=admin).status_code == 200


def test_supprimer_produit_reserve_a_l_admin(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    accueil = creer_compte(Role.accueil)
    produit = _creer_produit(client, admin)

    assert client.delete(f"/produits/{produit['id']}", headers=accueil).status_code == 403
