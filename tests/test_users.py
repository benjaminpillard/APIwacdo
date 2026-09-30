from schemas.user import Role

NOUVEAU_COMPTE = {
    "username": "nouveau",
    "email": "nouveau@test.fr",
    "password": "Nouveau123!",
    "role": "accueil",
}


def test_register_sans_token_refuse(client):
    reponse = client.post("/users/register", json=NOUVEAU_COMPTE)
    assert reponse.status_code == 401


def test_register_par_accueil_refuse(client, creer_compte):
    entetes = creer_compte(Role.accueil)
    reponse = client.post("/users/register", json=NOUVEAU_COMPTE, headers=entetes)
    assert reponse.status_code == 403


def test_register_par_admin_accepte(client, creer_compte):
    entetes = creer_compte(Role.administrateur)
    reponse = client.post("/users/register", json=NOUVEAU_COMPTE, headers=entetes)
    assert reponse.status_code == 201
    assert reponse.json()["role"] == "accueil"


def test_register_role_invalide_refuse(client, creer_compte):
    entetes = creer_compte(Role.administrateur)
    compte = {**NOUVEAU_COMPTE, "role": "root"}
    reponse = client.post("/users/register", json=compte, headers=entetes)
    assert reponse.status_code == 422


def test_register_mot_de_passe_trop_court_refuse(client, creer_compte):
    entetes = creer_compte(Role.administrateur)
    compte = {**NOUVEAU_COMPTE, "password": "abc"}
    reponse = client.post("/users/register", json=compte, headers=entetes)
    assert reponse.status_code == 422


def test_register_doublon_refuse(client, creer_compte):
    entetes = creer_compte(Role.administrateur)
    client.post("/users/register", json=NOUVEAU_COMPTE, headers=entetes)
    reponse = client.post("/users/register", json=NOUVEAU_COMPTE, headers=entetes)
    assert reponse.status_code == 409