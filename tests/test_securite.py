import logging
from datetime import timedelta

import jwt

from schemas.user import Role
from utils.jwt import create_access_token
from utils.limiter import limiter
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


# ---------- Contenu du token JWT ----------

def _payload(entetes):
    token = entetes["Authorization"].split(" ")[1]
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


def test_token_contient_id_role_et_expiration(client, creer_compte):
    payload = _payload(creer_compte(Role.preparateur))
    assert payload["sub"].isdigit()
    assert payload["role"] == "preparateur"
    assert "exp" in payload
    assert "email" not in payload   # pas de donnée personnelle inutile dans le token


def test_token_reste_valide_apres_changement_de_nom(client, creer_compte):
    entetes = creer_compte(Role.accueil)
    client.patch("/users/me", json={"username": "nouveau_nom"}, headers=entetes)
    reponse = client.get("/users/me", headers=entetes)
    assert reponse.status_code == 200
    assert reponse.json()["username"] == "nouveau_nom"


def test_token_expire_refuse(client, creer_compte):
    creer_compte(Role.accueil)
    token = create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1))
    reponse = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert reponse.status_code == 401


def test_token_signe_avec_une_autre_cle_refuse(client, creer_compte):
    creer_compte(Role.accueil)
    faux = jwt.encode({"sub": "1", "role": "administrateur"}, "cle-pirate-qui-n-est-pas-celle-du-serveur-0123456789", algorithm="HS256")
    reponse = client.get("/users/all", headers={"Authorization": f"Bearer {faux}"})
    assert reponse.status_code == 401


# ---------- Limitation de débit ----------

def test_login_bloque_apres_trop_de_tentatives(client, creer_compte):
    creer_compte(Role.accueil)
    limiter.enabled = True
    limiter.reset()
    maximum = int(settings.LOGIN_RATE_LIMIT.split("/")[0])

    for _ in range(maximum):
        reponse = client.post("/users/login", data={"username": "accueil", "password": "faux"})
        assert reponse.status_code == 401

    reponse = client.post("/users/login", data={"username": "accueil", "password": "faux"})
    assert reponse.status_code == 429
    assert reponse.json()["detail"] == "Trop de tentatives : réessayez dans une minute"


# ---------- Logs et traçabilité ----------

def test_connexion_echouee_journalisee_sans_mot_de_passe(client, creer_compte, caplog):
    creer_compte(Role.accueil)
    with caplog.at_level(logging.INFO, logger="wacdo"):
        client.post("/users/login", data={"username": "accueil", "password": "MotSecret99"})

    assert "Connexion échouée : identifiant=accueil" in caplog.text
    assert "MotSecret99" not in caplog.text   # un mot de passe ne doit jamais être journalisé


def test_changement_de_statut_journalise_avec_son_auteur(client, creer_compte, caplog):
    admin = creer_compte(Role.administrateur)
    accueil = creer_compte(Role.accueil)
    preparateur = creer_compte(Role.preparateur)
    produit = client.post("/produits/", json={"nom": "Frites", "prix": "2.50"}, headers=admin).json()
    commande = client.post(
        "/commandes/",
        json={"numero": "T42", "mode": "comptoir", "lignes": [{"produit_id": produit["id"]}]},
        headers=accueil,
    ).json()

    with caplog.at_level(logging.INFO, logger="wacdo"):
        client.post(f"/commandes/{commande['id']}/preparer", headers=preparateur)

    assert "numéro=T42 saisie -> preparee par=preparateur" in caplog.text


def test_chaque_requete_est_journalisee(client, creer_compte, caplog):
    entetes = creer_compte(Role.accueil)
    with caplog.at_level(logging.INFO, logger="wacdo"):
        client.get("/produits/", headers=entetes)
    assert "GET /produits/ -> 200" in caplog.text
    assert "utilisateur=accueil" in caplog.text
