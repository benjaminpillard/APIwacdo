import pytest
from schemas.user import Role


@pytest.fixture()
def catalogue(client, creer_compte):
    """Crée une catégorie Boissons, un Big Mac, un Coca, un Sprite,
    et un menu 'Menu Big Mac' avec un groupe Boisson obligatoire
    lié à cette catégorie. Renvoie les en-têtes admin et les ids utiles."""
    entetes_admin = creer_compte(Role.administrateur)

    categorie = client.post(
        "/categories/", json={"nom": "Boissons"}, headers=entetes_admin
    ).json()

    big_mac = client.post(
        "/produits/",
        json={"nom": "Big Mac", "prix": 5.90, "disponible": True},
        headers=entetes_admin,
    ).json()
    coca = client.post(
        "/produits/",
        json={"nom": "Coca", "prix": 2.00, "disponible": True, "categorie_id": categorie["id"]},
        headers=entetes_admin,
    ).json()
    sprite = client.post(
        "/produits/",
        json={"nom": "Sprite", "prix": 2.00, "disponible": True, "categorie_id": categorie["id"]},
        headers=entetes_admin,
    ).json()

    menu = client.post(
        "/menus/",
        json={"nom": "Menu Big Mac", "prix": 8.90, "produit_principal_id": big_mac["id"]},
        headers=entetes_admin,
    ).json()
    menu = client.post(
        f"/menus/{menu['id']}/groupes",
        json={"nom": "Boisson", "obligatoire": True, "max_choix": 1, "categorie_id": categorie["id"]},
        headers=entetes_admin,
    ).json()
    groupe_boisson_id = menu["groupes"][0]["id"]

    return {
        "entetes_admin": entetes_admin,
        "big_mac_id": big_mac["id"],
        "coca_id": coca["id"],
        "sprite_id": sprite["id"],
        "menu_id": menu["id"],
        "groupe_boisson_id": groupe_boisson_id,
    }


def test_commande_produit_seul(client, creer_compte, catalogue):
    entetes = creer_compte(Role.accueil)
    reponse = client.post(
        "/commandes/",
        json={
            "numero": "1",
            "mode": "comptoir",
            "lignes": [{"produit_id": catalogue["big_mac_id"], "quantite": 2}],
        },
        headers=entetes,
    )
    assert reponse.status_code == 201
    corps = reponse.json()
    assert corps["total"] == "11.80"
    assert corps["statut"] == "saisie"


def test_commande_menu_avec_choix_valide(client, creer_compte, catalogue):
    entetes = creer_compte(Role.accueil)
    reponse = client.post(
        "/commandes/",
        json={
            "numero": "2",
            "mode": "comptoir",
            "lignes": [{
                "menu_id": catalogue["menu_id"],
                "quantite": 1,
                "choix": [{"groupe_id": catalogue["groupe_boisson_id"], "produit_id": catalogue["coca_id"]}],
            }],
        },
        headers=entetes,
    )
    assert reponse.status_code == 201
    assert reponse.json()["total"] == "8.90"


def test_commande_choix_obligatoire_manquant_refuse(client, creer_compte, catalogue):
    entetes = creer_compte(Role.accueil)
    reponse = client.post(
        "/commandes/",
        json={
            "numero": "3",
            "mode": "comptoir",
            "lignes": [{"menu_id": catalogue["menu_id"], "quantite": 1, "choix": []}],
        },
        headers=entetes,
    )
    assert reponse.status_code == 400


def test_commande_choix_hors_groupe_refuse(client, creer_compte, catalogue):
    entetes = creer_compte(Role.accueil)
    reponse = client.post(
        "/commandes/",
        json={
            "numero": "4",
            "mode": "comptoir",
            "lignes": [{
                "menu_id": catalogue["menu_id"],
                "quantite": 1,
                "choix": [{"groupe_id": catalogue["groupe_boisson_id"], "produit_id": catalogue["big_mac_id"]}],
            }],
        },
        headers=entetes,
    )
    assert reponse.status_code == 400


def test_commande_numero_doublon_refuse(client, creer_compte, catalogue):
    entetes = creer_compte(Role.accueil)
    corps = {
        "numero": "5",
        "mode": "comptoir",
        "lignes": [{"produit_id": catalogue["big_mac_id"], "quantite": 1}],
    }
    client.post("/commandes/", json=corps, headers=entetes)
    reponse = client.post("/commandes/", json=corps, headers=entetes)
    assert reponse.status_code == 409


def test_prix_fige_apres_changement_de_prix(client, creer_compte, catalogue):
    entetes = creer_compte(Role.accueil)
    commande = client.post(
        "/commandes/",
        json={
            "numero": "6",
            "mode": "comptoir",
            "lignes": [{"produit_id": catalogue["big_mac_id"], "quantite": 1}],
        },
        headers=entetes,
    ).json()

    client.patch(
        f"/produits/{catalogue['big_mac_id']}",
        json={"prix": 99.00},
        headers=catalogue["entetes_admin"],
    )

    relue = client.get(f"/commandes/{commande['id']}", headers=entetes).json()
    assert relue["total"] == "5.90"


def test_circuit_de_statuts_par_role(client, creer_compte, catalogue):
    entetes_accueil = creer_compte(Role.accueil)
    entetes_prepa = creer_compte(Role.preparateur)

    commande = client.post(
        "/commandes/",
        json={
            "numero": "7",
            "mode": "comptoir",
            "lignes": [{"produit_id": catalogue["big_mac_id"], "quantite": 1}],
        },
        headers=entetes_accueil,
    ).json()
    commande_id = commande["id"]

    # L'accueil ne peut pas préparer
    assert client.post(f"/commandes/{commande_id}/preparer", headers=entetes_accueil).status_code == 403
    # Le préparateur ne peut pas livrer directement
    assert client.post(f"/commandes/{commande_id}/livrer", headers=entetes_prepa).status_code == 403
    # Le préparateur prépare
    reponse = client.post(f"/commandes/{commande_id}/preparer", headers=entetes_prepa)
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "preparee"
    # L'accueil livre
    reponse = client.post(f"/commandes/{commande_id}/livrer", headers=entetes_accueil)
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "livree"
    # On ne peut pas livrer deux fois
    assert client.post(f"/commandes/{commande_id}/livrer", headers=entetes_accueil).status_code == 409


def test_saut_direct_a_livree_refuse(client, creer_compte, catalogue):
    entetes = creer_compte(Role.accueil)
    commande = client.post(
        "/commandes/",
        json={
            "numero": "8",
            "mode": "comptoir",
            "lignes": [{"produit_id": catalogue["big_mac_id"], "quantite": 1}],
        },
        headers=entetes,
    ).json()
    reponse = client.post(f"/commandes/{commande['id']}/livrer", headers=entetes)
    assert reponse.status_code == 409

def test_commandes_a_preparer_triees_par_heure_de_livraison(client, creer_compte, catalogue):
    accueil = creer_compte(Role.accueil)
    preparateur = creer_compte(Role.preparateur)
    ligne = [{"produit_id": catalogue["big_mac_id"]}]

    # Saisies dans le désordre ; T3 n'a pas d'heure de livraison
    for numero, heure in [("T1", "2026-11-12T12:30:00"), ("T2", "2026-11-12T12:00:00"), ("T3", None)]:
        corps = {"numero": numero, "mode": "telephone", "lignes": ligne}
        if heure:
            corps["heure_livraison"] = heure
        client.post("/commandes/", json=corps, headers=accueil)

    # Une commande déjà préparée ne doit pas apparaître dans la liste « à préparer »
    t4 = client.post(
        "/commandes/",
        json={"numero": "T4", "mode": "comptoir", "heure_livraison": "2026-11-12T11:00:00", "lignes": ligne},
        headers=accueil,
    ).json()
    client.post(f"/commandes/{t4['id']}/preparer", headers=preparateur)

    a_preparer = client.get("/commandes/?statut=saisie", headers=preparateur).json()
    assert [c["numero"] for c in a_preparer] == ["T2", "T1", "T3"]


def test_filtrer_les_commandes_par_mode(client, creer_compte, catalogue):
    accueil = creer_compte(Role.accueil)
    ligne = [{"produit_id": catalogue["big_mac_id"]}]
    client.post("/commandes/", json={"numero": "C1", "mode": "comptoir", "lignes": ligne}, headers=accueil)
    client.post("/commandes/", json={"numero": "P1", "mode": "telephone", "lignes": ligne}, headers=accueil)

    par_telephone = client.get("/commandes/?mode=telephone", headers=accueil).json()
    assert [c["numero"] for c in par_telephone] == ["P1"]


def test_ligne_avec_produit_et_menu_refusee(client, creer_compte, catalogue):
    accueil = creer_compte(Role.accueil)
    reponse = client.post(
        "/commandes/",
        json={"numero": "X", "mode": "comptoir",
              "lignes": [{"produit_id": catalogue["big_mac_id"], "menu_id": catalogue["menu_id"]}]},
        headers=accueil,
    )
    assert reponse.status_code == 422


def test_commande_sans_ligne_refusee(client, creer_compte):
    accueil = creer_compte(Role.accueil)
    reponse = client.post("/commandes/", json={"numero": "X", "mode": "comptoir", "lignes": []}, headers=accueil)
    assert reponse.status_code == 422


def test_produit_indisponible_refuse(client, creer_compte, catalogue):
    accueil = creer_compte(Role.accueil)
    client.patch(f"/produits/{catalogue['coca_id']}", json={"disponible": False},
                 headers=catalogue["entetes_admin"])
    reponse = client.post(
        "/commandes/",
        json={"numero": "X", "mode": "comptoir", "lignes": [{"produit_id": catalogue["coca_id"]}]},
        headers=accueil,
    )
    assert reponse.status_code == 400
    assert "n'est plus disponible" in reponse.json()["detail"]
