from schemas.user import Role
from utils.setting import settings


def test_login_mauvais_mot_de_passe(client, creer_compte):
    creer_compte(Role.accueil)
    reponse = client.post("/users/login", data={"username": "accueil", "password": "faux"})
    assert reponse.status_code == 401
    assert reponse.json()["detail"] == "Identifiant ou mot de passe incorrect"
    assert reponse.headers["www-authenticate"] == "Bearer"


def test_token_falsifie_refuse(client):
    reponse = client.get("/users/me", headers={"Authorization": "Bearer pas.un.token"})
    assert reponse.status_code == 401
    assert reponse.json()["detail"] == "Token invalide ou expiré"


def test_route_protegee_sans_token(client):
    assert client.get("/produits/").status_code == 401


def test_role_insuffisant_message_clair(client, creer_compte):
    preparateur = creer_compte(Role.preparateur)
    reponse = client.post("/produits/", json={"nom": "X", "prix": "1.00"}, headers=preparateur)
    assert reponse.status_code == 403
    assert "permission insuffisante" in reponse.json()["detail"]


def test_cors_preflight_origine_autorisee(client):
    if not settings.cors_origins_list:
        return  # aucune origine configurée dans l'environnement de test
    origine = settings.cors_origins_list[0]
    reponse = client.options(
        "/produits/1",
        headers={"Origin": origine, "Access-Control-Request-Method": "PATCH"},
    )
    assert reponse.status_code == 200
    assert reponse.headers["access-control-allow-origin"] == origine
    assert "PATCH" in reponse.headers["access-control-allow-methods"]


def test_cors_origine_inconnue_refusee(client):
    reponse = client.options(
        "/produits/",
        headers={"Origin": "https://site-pirate.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in reponse.headers
