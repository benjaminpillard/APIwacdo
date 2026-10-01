# APIwacdo

API REST (back-office) pour la borne de commande Wacdo : gestion des utilisateurs, catégories, produits, menus (avec groupes de choix) et commandes, avec authentification par rôle.

## Stack

- Python / FastAPI
- SQLAlchemy (ORM) + Alembic (migrations)
- PostgreSQL en production, SQLite en développement
- JWT (authentification), mots de passe hachés (argon2 via `pwdlib`)
- pytest (tests automatisés)

## Structure du projet

```text
.
├── main.py
├── create_admin.py        # crée le premier compte administrateur
├── controllers/            # logique métier
├── models/                 # modèles SQLAlchemy
├── routes/                 # routes FastAPI
├── schemas/                 # schémas Pydantic (validation des entrées/sorties)
├── utils/                  # auth, hash, jwt, configuration
├── alembic/                # migrations de la base de données
├── tests/                  # tests automatisés (pytest)
├── docs/                   # MCD/MLD et schémas fonctionnels du projet
└── requirements.txt
```

## Modèle de données

Le modèle complet (schéma conceptuel et schéma physique) est documenté dans [`docs/MCD_MLD_APIwacdo.md`](docs/MCD_MLD_APIwacdo.md).
Les parcours utilisateurs par rôle sont documentés dans [`docs/Schemas_fonctionnels_APIwacdo.md`](docs/Schemas_fonctionnels_APIwacdo.md).

Résumé des entités principales : `Utilisateur`, `Categorie`, `Produit`, `Menu` (avec `MenuGroupe` et `MenuGroupeProduit` pour les choix type « menu avec frites/boisson/sauce au choix »), `Commande` (avec `LigneCommande` et `LigneCommandeChoix`).

## Rôles et permissions

| Rôle | Peut faire |
|---|---|
| `administrateur` | Tout : gérer le catalogue (catégories, produits, menus), créer des comptes, voir/modifier/supprimer toute commande |
| `preparateur` | Voir les commandes à préparer (triées par heure de livraison), les déclarer « préparées » |
| `accueil` | Saisir une commande, la remettre au client (la déclarer « livrée ») |

Chaque utilisateur peut aussi consulter, modifier et supprimer son propre profil (`/users/me`), quel que soit son rôle.

## Prérequis

- Python 3.10+
- pip

## Installation

1. Cloner le dépôt :

```bash
git clone https://github.com/benjaminpillard/APIwacdo.git
cd APIwacdo
```

2. Créer et activer un environnement virtuel :

```bash
python -m venv .venv
source .venv/Scripts/activate   # Windows (PowerShell) : .venv\Scripts\activate
```

3. Installer les dépendances :

```bash
pip install -r requirements.txt
```

## Configuration

Créer un fichier `.env` à la racine (jamais commité, voir `.gitignore`) :

```env
SECRET_KEY=une_cle_generee_aleatoirement
ALGORITHM=HS256
DATABASE_URL=sqlite:///./app.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Notes :

- `DATABASE_URL` accepte SQLite (développement) et PostgreSQL (production).
- Pour générer une `SECRET_KEY` sûre : `python -c "import secrets; print(secrets.token_hex(32))"`.
- Les rôles utilisés par l'API sont : `administrateur`, `preparateur`, `accueil`.

## Base de données et migrations

Les tables sont créées et mises à jour via **Alembic**, jamais automatiquement par l'application.

Première mise en place :

```bash
alembic upgrade head
python create_admin.py
```

`create_admin.py` demande un nom d'utilisateur, un email et un mot de passe, et crée le premier compte `administrateur` (nécessaire, car la création de comptes via l'API est elle-même réservée à un administrateur).

Après toute modification d'un modèle (`models/`) :

```bash
alembic revision --autogenerate -m "Description du changement"
alembic upgrade head
```

## Lancer l'API

```bash
fastapi dev main.py
```

Alternative :

```bash
uvicorn main:app --reload
```

Ensuite ouvrir :

- Swagger UI : http://127.0.0.1:8000/docs
- ReDoc : http://127.0.0.1:8000/redoc

## Authentification

- Endpoint de connexion : `POST /users/login`
- Format : `application/x-www-form-urlencoded`
- Champs : `username`, `password`
- Réponse : un token JWT (`access_token`)

Utiliser ensuite ce token sur les routes protégées :

```http
Authorization: Bearer <token>
```

Dans Swagger, cliquer sur le bouton **Authorize** et renseigner les identifiants.

## Tests

```bash
pytest -v
```

Les tests couvrent la sécurité de la création de comptes (`tests/test_users.py`) et toute la logique des commandes : choix de menu valides/invalides, prix figés au moment de la commande, circuit des statuts par rôle (`tests/test_commande.py`). Ils tournent sur une base SQLite en mémoire, indépendante de la base de développement.

## Endpoints principaux

| Ressource | Routes |
|---|---|
| Utilisateurs | `POST /users/register` (admin), `POST /users/login`, `GET/PATCH/DELETE /users/me`, `GET /users/all` (admin), `DELETE /users/{id}` (admin) |
| Catégories | `GET/POST /categories/`, `GET/PUT/DELETE /categories/{id}` |
| Produits | `GET/POST /produits/`, `GET/PUT/PATCH/DELETE /produits/{id}` (filtres : `categorie_id`, `disponible`) |
| Menus | `GET/POST /menus/`, `GET/PUT/DELETE /menus/{id}`, `POST/DELETE /menus/{id}/groupes`, `POST/DELETE /menus/groupes/{id}/produits` |
| Commandes | `GET/POST /commandes/`, `GET/DELETE /commandes/{id}`, `POST /commandes/{id}/preparer`, `POST /commandes/{id}/livrer` (filtres : `statut`, `mode`) |

## Déploiement

Le projet est pensé pour être déployé sur [Render](https://render.com), avec une base PostgreSQL séparée :

1. Créer un service **PostgreSQL** sur Render, copier son *Internal Database URL*.
2. Créer un **Web Service**, relié au dépôt GitHub :
   - Build Command : `pip install -r requirements.txt`
   - Start Command : `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Renseigner les variables d'environnement (`DATABASE_URL`, `SECRET_KEY`, `ALGORITHM`).
4. Dans le shell du service, lancer :

```bash
alembic upgrade head
python create_admin.py
```
