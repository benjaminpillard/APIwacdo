import pytest

from schemas.user import Role


@pytest.fixture()
def carte(client, creer_compte):
    """Burger, Frites, Potatoes, Coca, Sprite (indisponible), catégorie Boissons
    et un menu vide autour du Burger."""
    admin = creer_compte(Role.administrateur)

    def produit(**donnees):
        return client.post("/produits/", json=donnees, headers=admin).json()

    boissons = client.post("/categories/", json={"nom": "Boissons"}, headers=admin).json()
    ids = {
        "burger": produit(nom="Burger", prix="5.00")["id"],
        "frites": produit(nom="Frites", prix="2.50")["id"],
        "potatoes": produit(nom="Potatoes", prix="2.90")["id"],
        "coca": produit(nom="Coca", prix="2.00", categorie_id=boissons["id"])["id"],
        "sprite": produit(nom="Sprite", prix="2.00", categorie_id=boissons["id"], disponible=False)["id"],
        "boissons": boissons["id"],
    }
    menu = client.post(
        "/menus/", json={"nom": "Menu Burger", "prix": "8.00", "produit_principal_id": ids["burger"]},
        headers=admin,
    ).json()
    ids["menu"] = menu["id"]
    return admin, ids


def _groupe(client, admin, menu_id, **donnees):
    menu = client.post(f"/menus/{menu_id}/groupes", json=donnees, headers=admin).json()
    return menu["groupes"][-1]


# ---------- Menus ----------

def test_creer_menu_renvoie_sa_composition(client, carte):
    admin, ids = carte
    menu = client.get(f"/menus/{ids['menu']}", headers=admin).json()
    assert menu["produit_principal"]["nom"] == "Burger"
    assert menu["groupes"] == []


def test_creer_menu_produit_principal_inexistant(client, carte):
    admin, _ = carte
    reponse = client.post(
        "/menus/", json={"nom": "X", "prix": "5.00", "produit_principal_id": 999}, headers=admin
    )
    assert reponse.status_code == 404


def test_lister_menus_filtre_disponibilite(client, carte):
    admin, ids = carte
    client.post(
        "/menus/", json={"nom": "Ancien menu", "prix": "7.00", "produit_principal_id": ids["burger"],
                         "disponible": False},
        headers=admin,
    )
    noms = [m["nom"] for m in client.get("/menus/?disponible=true", headers=admin).json()]
    assert noms == ["Menu Burger"]


def test_rechercher_menu(client, carte):
    admin, _ = carte
    assert len(client.get("/menus/search?nom=burger", headers=admin).json()) == 1
    assert client.get("/menus/search?nom=pizza", headers=admin).status_code == 404


# ---------- Groupes de choix ----------

def test_groupe_lie_a_une_categorie_ne_propose_que_les_produits_disponibles(client, carte):
    admin, ids = carte
    groupe = _groupe(client, admin, ids["menu"], nom="Boisson", categorie_id=ids["boissons"])
    proposes = [p["nom"] for p in groupe["produits_proposes"]]
    assert proposes == ["Coca"]   # Sprite est indisponible


def test_groupe_categorie_inexistante(client, carte):
    admin, ids = carte
    reponse = client.post(f"/menus/{ids['menu']}/groupes", json={"nom": "X", "categorie_id": 999}, headers=admin)
    assert reponse.status_code == 404


def test_ajouter_et_retirer_un_produit_dans_un_groupe(client, carte):
    admin, ids = carte
    groupe = _groupe(client, admin, ids["menu"], nom="Accompagnement")

    menu = client.post(
        f"/menus/groupes/{groupe['id']}/produits",
        json={"produit_id": ids["potatoes"], "supplement": "0.50"}, headers=admin,
    ).json()
    option = menu["groupes"][0]["options"][0]
    assert option["produit"]["nom"] == "Potatoes"
    assert option["supplement"] == "0.50"

    menu = client.delete(f"/menus/groupes/{groupe['id']}/produits/{ids['potatoes']}", headers=admin).json()
    assert menu["groupes"][0]["options"] == []


def test_produit_en_double_dans_un_groupe_refuse(client, carte):
    admin, ids = carte
    groupe = _groupe(client, admin, ids["menu"], nom="Accompagnement")
    url = f"/menus/groupes/{groupe['id']}/produits"
    client.post(url, json={"produit_id": ids["frites"]}, headers=admin)
    assert client.post(url, json={"produit_id": ids["frites"]}, headers=admin).status_code == 409


def test_ajout_manuel_refuse_dans_un_groupe_lie_a_une_categorie(client, carte):
    admin, ids = carte
    groupe = _groupe(client, admin, ids["menu"], nom="Boisson", categorie_id=ids["boissons"])
    reponse = client.post(f"/menus/groupes/{groupe['id']}/produits", json={"produit_id": ids["frites"]}, headers=admin)
    assert reponse.status_code == 409


# ---------- Commande d'un menu : suppléments et règles de choix ----------

def _commander_menu(client, creer_compte, menu_id, choix, numero="M1"):
    accueil = creer_compte(Role.accueil)
    return client.post(
        "/commandes/",
        json={"numero": numero, "mode": "comptoir", "lignes": [{"menu_id": menu_id, "choix": choix}]},
        headers=accueil,
    )


def test_supplement_ajoute_au_prix_du_menu(client, creer_compte, carte):
    admin, ids = carte
    groupe = _groupe(client, admin, ids["menu"], nom="Accompagnement")
    url = f"/menus/groupes/{groupe['id']}/produits"
    client.post(url, json={"produit_id": ids["frites"]}, headers=admin)
    client.post(url, json={"produit_id": ids["potatoes"], "supplement": "0.50"}, headers=admin)

    reponse = _commander_menu(client, creer_compte, ids["menu"],
                              [{"groupe_id": groupe["id"], "produit_id": ids["potatoes"]}])

    assert reponse.status_code == 201
    assert reponse.json()["total"] == "8.50"   # 8.00 + 0.50 de supplément


def test_trop_de_choix_dans_un_groupe_refuse(client, creer_compte, carte):
    admin, ids = carte
    groupe = _groupe(client, admin, ids["menu"], nom="Accompagnement", max_choix=1)
    url = f"/menus/groupes/{groupe['id']}/produits"
    client.post(url, json={"produit_id": ids["frites"]}, headers=admin)
    client.post(url, json={"produit_id": ids["potatoes"]}, headers=admin)

    reponse = _commander_menu(client, creer_compte, ids["menu"], [
        {"groupe_id": groupe["id"], "produit_id": ids["frites"]},
        {"groupe_id": groupe["id"], "produit_id": ids["potatoes"]},
    ])
    assert reponse.status_code == 400
    assert "1 choix maximum" in reponse.json()["detail"]


def test_menu_indisponible_ne_peut_pas_etre_commande(client, creer_compte, carte):
    admin, ids = carte
    client.put(
        f"/menus/{ids['menu']}",
        json={"nom": "Menu Burger", "prix": "8.00", "produit_principal_id": ids["burger"], "disponible": False},
        headers=admin,
    )
    reponse = _commander_menu(client, creer_compte, ids["menu"], [])
    assert reponse.status_code == 400


def test_menu_dont_le_produit_principal_est_indisponible(client, creer_compte, carte):
    admin, ids = carte
    client.patch(f"/produits/{ids['burger']}", json={"disponible": False}, headers=admin)
    reponse = _commander_menu(client, creer_compte, ids["menu"], [])
    assert reponse.status_code == 400


# ---------- Suppressions protégées ----------

def test_supprimer_menu_jamais_commande(client, carte):
    admin, ids = carte
    assert client.delete(f"/menus/{ids['menu']}", headers=admin).status_code == 204
    assert client.get(f"/menus/{ids['menu']}", headers=admin).status_code == 404


def test_supprimer_menu_deja_commande_refuse(client, creer_compte, carte):
    admin, ids = carte
    _commander_menu(client, creer_compte, ids["menu"], [])
    reponse = client.delete(f"/menus/{ids['menu']}", headers=admin)
    assert reponse.status_code == 409


def test_supprimer_groupe_deja_utilise_refuse(client, creer_compte, carte):
    admin, ids = carte
    groupe = _groupe(client, admin, ids["menu"], nom="Boisson", categorie_id=ids["boissons"])
    _commander_menu(client, creer_compte, ids["menu"], [{"groupe_id": groupe["id"], "produit_id": ids["coca"]}])

    assert client.delete(f"/menus/groupes/{groupe['id']}", headers=admin).status_code == 409
