from schemas.user import Role

ROUTES_PUBLIQUES = {("post", "/users/login"), ("get", "/confidentialite/"), ("get", "/")}


def _operations(client):
    schema = client.get("/openapi.json").json()
    for chemin, methodes in schema["paths"].items():
        for methode, operation in methodes.items():
            yield methode, chemin, operation


def test_swagger_accessible(client):
    assert client.get("/docs").status_code == 200
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "API Wacdo — Back-office"
    assert schema["info"]["version"] == "1.0.0"


def test_chaque_route_a_un_resume_et_un_tag(client):
    for methode, chemin, operation in _operations(client):
        assert operation.get("summary"), f"{methode.upper()} {chemin} : summary manquant"
        assert operation.get("tags"), f"{methode.upper()} {chemin} : tag manquant"


def test_routes_protegees_documentent_l_erreur_401(client):
    for methode, chemin, operation in _operations(client):
        if (methode, chemin) in ROUTES_PUBLIQUES:
            continue
        assert "401" in operation["responses"], f"{methode.upper()} {chemin} : 401 non documentée"


def test_reponse_documentee_conforme_a_la_reponse_reelle(client, creer_compte):
    # La doc annonce une 404 au format {"detail": ...} : on vérifie que c'est bien le cas
    admin = creer_compte(Role.administrateur)
    reponse = client.get("/produits/999", headers=admin)
    assert reponse.status_code == 404
    assert set(reponse.json()) == {"detail"}


def test_pagination_limitee_a_100(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    assert client.get("/produits/?limit=1000", headers=admin).status_code == 422
    assert client.get("/produits/?limit=100", headers=admin).status_code == 200
