from schemas.user import Role


def test_creer_et_lister_triees_par_nom(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    for nom in ("Desserts", "Boissons", "Burgers"):
        assert client.post("/categories/", json={"nom": nom}, headers=admin).status_code == 201

    noms = [c["nom"] for c in client.get("/categories/", headers=admin).json()]
    assert noms == ["Boissons", "Burgers", "Desserts"]


def test_nom_en_double_refuse(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    client.post("/categories/", json={"nom": "Boissons"}, headers=admin)
    reponse = client.post("/categories/", json={"nom": "Boissons"}, headers=admin)
    assert reponse.status_code == 409
    assert reponse.json()["detail"] == "Cette catégorie existe déjà"


def test_nom_vide_refuse(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    assert client.post("/categories/", json={"nom": ""}, headers=admin).status_code == 422


def test_renommer(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    categorie = client.post("/categories/", json={"nom": "Boisson"}, headers=admin).json()
    reponse = client.put(f"/categories/{categorie['id']}", json={"nom": "Boissons"}, headers=admin)
    assert reponse.json()["nom"] == "Boissons"


def test_categorie_inexistante(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    assert client.get("/categories/999", headers=admin).status_code == 404


def test_filtrer_les_produits_par_categorie(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    boissons = client.post("/categories/", json={"nom": "Boissons"}, headers=admin).json()
    client.post("/produits/", json={"nom": "Coca", "prix": "2.00", "categorie_id": boissons["id"]}, headers=admin)
    client.post("/produits/", json={"nom": "Frites", "prix": "2.50"}, headers=admin)

    produits = client.get(f"/produits/?categorie_id={boissons['id']}", headers=admin).json()
    assert [p["nom"] for p in produits] == ["Coca"]


def test_supprimer_categorie_vide(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    categorie = client.post("/categories/", json={"nom": "Temporaire"}, headers=admin).json()
    assert client.delete(f"/categories/{categorie['id']}", headers=admin).status_code == 204


def test_supprimer_categorie_utilisee_par_un_produit_refuse(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    boissons = client.post("/categories/", json={"nom": "Boissons"}, headers=admin).json()
    client.post("/produits/", json={"nom": "Coca", "prix": "2.00", "categorie_id": boissons["id"]}, headers=admin)

    reponse = client.delete(f"/categories/{boissons['id']}", headers=admin)
    assert reponse.status_code == 409
    assert "des produits utilisent cette catégorie" in reponse.json()["detail"]
