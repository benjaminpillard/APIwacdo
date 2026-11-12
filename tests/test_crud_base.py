"""Tests unitaires du controller générique CRUDBase.

Ils appellent directement les classes Python (sans passer par l'API HTTP)
pour vérifier le comportement commun hérité par tous les controllers.
"""
import pytest
from fastapi import HTTPException
from sqlalchemy import select

from controllers.base import CRUDBase
from controllers.categorie import CategorieController, categorie_controller
from controllers.commande import CommandeController
from controllers.menu import MenuController, GroupeController
from controllers.produit import ProduitController, produit_controller
from controllers.user import UtilisateurController
from models.categorie import Categorie
from models.produit import Produit
from schemas.produit import ProduitCreate, ProduitUpdate
from schemas.user import Role


@pytest.fixture()
def db(session_factory):
    session = session_factory()
    yield session
    session.close()


# ---------- Héritage ----------

@pytest.mark.parametrize("classe", [
    ProduitController, CategorieController, MenuController,
    GroupeController, CommandeController, UtilisateurController,
])
def test_tous_les_controllers_heritent_de_crudbase(classe):
    assert issubclass(classe, CRUDBase)


def test_chaque_controller_a_son_propre_message(db):
    # L'attribut de classe est redéfini (surchargé) dans chaque classe fille
    with pytest.raises(HTTPException) as erreur:
        produit_controller.get(db, 999)
    assert erreur.value.status_code == 404
    assert erreur.value.detail == "Produit introuvable"

    with pytest.raises(HTTPException) as erreur:
        categorie_controller.get(db, 999)
    assert erreur.value.detail == "Catégorie introuvable"


# ---------- Comportement commun ----------

def test_create_puis_get(db):
    cree = produit_controller.create(db, ProduitCreate(nom="Frites", prix="2.50"))
    assert produit_controller.get(db, cree.id).nom == "Frites"


def test_create_accepte_un_dict(db):
    categorie = categorie_controller.create(db, {"nom": "Desserts"})
    assert categorie.id is not None


def test_doublon_donne_une_409_avec_le_message_de_la_classe(db):
    categorie_controller.create(db, {"nom": "Boissons"})
    with pytest.raises(HTTPException) as erreur:
        categorie_controller.create(db, {"nom": "Boissons"})
    assert erreur.value.status_code == 409
    assert erreur.value.detail == "Cette catégorie existe déjà"


def test_lister_avec_filtres_tri_et_pagination(db):
    for nom, dispo in [("Coca", True), ("Burger", True), ("Ancien", False)]:
        produit_controller.create(db, {"nom": nom, "prix": 1, "disponible": dispo})

    disponibles = produit_controller.lister(
        db, filtres=[Produit.disponible.is_(True)], tri=[Produit.nom]
    )
    assert [p.nom for p in disponibles] == ["Burger", "Coca"]

    premier = produit_controller.lister(db, limit=1, tri=[Produit.nom])
    assert [p.nom for p in premier] == ["Ancien"]


def test_update_partiel_ne_modifie_que_les_champs_envoyes(db):
    produit = produit_controller.create(
        db, ProduitCreate(nom="Frites", prix="2.50", description="Croustillantes")
    )
    modifie = produit_controller.update(db, produit, ProduitUpdate(prix="3.00"), partiel=True)
    assert str(modifie.prix) == "3.00"
    assert modifie.description == "Croustillantes"


def test_update_complet_remplace_tout(db):
    produit = produit_controller.create(
        db, ProduitCreate(nom="Frites", prix="2.50", description="Croustillantes")
    )
    modifie = produit_controller.update(db, produit, ProduitCreate(nom="Frites", prix="3.00"), partiel=False)
    assert modifie.description is None


def test_delete(db):
    categorie = categorie_controller.create(db, {"nom": "Temporaire"})
    categorie_controller.delete(db, categorie)
    assert db.execute(select(Categorie).where(Categorie.nom == "Temporaire")).first() is None


# ---------- Surcharges (polymorphisme) ----------

def test_surcharge_delete_categorie_utilisee(db):
    categorie = categorie_controller.create(db, {"nom": "Boissons"})
    produit_controller.create(db, {"nom": "Coca", "prix": 2, "categorie_id": categorie.id})

    with pytest.raises(HTTPException) as erreur:
        categorie_controller.delete(db, categorie)
    assert erreur.value.status_code == 409


def test_surcharge_create_produit_verifie_la_categorie(db):
    with pytest.raises(HTTPException) as erreur:
        produit_controller.create(db, {"nom": "X", "prix": 1, "categorie_id": 999})
    assert erreur.value.status_code == 404
    assert erreur.value.detail == "Catégorie introuvable"


# ---------- Via l'API : comportements touchés par la refonte ----------

def test_put_remplace_entierement_le_produit(client, creer_compte):
    admin = creer_compte(Role.administrateur)
    produit = client.post(
        "/produits/", json={"nom": "Frites", "prix": "2.50", "description": "Croustillantes"}, headers=admin
    ).json()

    reponse = client.put(f"/produits/{produit['id']}", json={"nom": "Frites", "prix": "3.00"}, headers=admin)

    assert reponse.status_code == 200
    assert reponse.json()["description"] is None   # PUT : remplacement complet


def test_admin_anonymise_ne_compte_pas_comme_admin(client, creer_compte, session_factory):
    from tests.conftest import MOT_DE_PASSE
    admin = creer_compte(Role.administrateur)

    # Un second admin passe une commande, puis supprime son compte : il est anonymisé
    client.post("/users/register", json={
        "username": "admin2", "email": "admin2@test.fr", "password": MOT_DE_PASSE, "role": "administrateur",
    }, headers=admin)
    token2 = client.post("/users/login", data={"username": "admin2", "password": MOT_DE_PASSE}).json()["access_token"]
    admin2 = {"Authorization": f"Bearer {token2}"}
    produit = client.post("/produits/", json={"nom": "Frites", "prix": "2.50"}, headers=admin).json()
    client.post("/commandes/", json={
        "numero": "A1", "mode": "comptoir", "lignes": [{"produit_id": produit["id"]}],
    }, headers=admin2)
    assert client.delete("/users/me", headers=admin2).status_code == 204

    # Il ne reste qu'un admin ACTIF : il ne peut pas se supprimer
    reponse = client.delete("/users/me", headers=admin)
    assert reponse.status_code == 409
