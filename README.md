# APIwacdo

API REST FastAPI pour la gestion des utilisateurs, produits, menus et commandes.

## Stack

- Python
- FastAPI
- SQLAlchemy
- Alembic
- JWT (authentification)

## Structure du projet

```text
.
|- main.py
|- controllers/
|- models/
|- routes/
|- schemas/
|- utils/
|- alembic/
|- alembic.ini
```

## Prerequis

- Python 3.10+
- pip

## Installation

1. Cloner le repo:

```bash
git clone https://github.com/benjaminpillard/APIwacdo.git
cd APIwacdo
```

2. Creer et activer un environnement virtuel:

```bash
python -m venv .venv
source .venv/Scripts/activate
```

3. Installer les dependances principales:

```bash
pip install fastapi "uvicorn[standard]" sqlalchemy alembic pydantic-settings pydantic[email] pyjwt pwdlib psycopg[binary]
```

## Configuration

Creer un fichier `.env` a la racine:

```env
SECRET_KEY=change_me
ALGORITHM=HS256
DATABASE_URL=sqlite:///./app.db
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

Notes:

- `DATABASE_URL` accepte SQLite et PostgreSQL.
- Les roles utilises par l'API sont: `administrateur`, `preparateur`, `accueil`.

## Lancer l'API

Commande utilisee dans ce projet:

```bash
fastapi dev main.py
```

Alternative:

```bash
uvicorn main:app --reload
```

Ensuite ouvrir:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## Authentification

- Endpoint login: `POST /users/login`
- Format: `application/x-www-form-urlencoded`
- Champs: `username`, `password`
- Reponse: token JWT (`access_token`)

Utiliser ensuite le header:

```http
Authorization: Bearer <token>
```

## Endpoints principaux

### Users (`/users`)

- `POST /users/register`
- `POST /users/login`
- `GET /users/me`
- `GET /users/all` (administrateur)
- `DELETE /users/{user_id}` (administrateur)

### Produits (`/produits`)

- `GET /produits/`
- `GET /produits/search?title=...`
- `GET /produits/{produit_id}`
- `POST /produits/` (administrateur)
- `PUT /produits/{produit_id}` (administrateur)
- `DELETE /produits/{produit_id}` (administrateur)

### Menus (`/menus`)

- `GET /menus/`
- `GET /menus/search?nom=...`
- `GET /menus/{menu_id}`
- `POST /menus/` (administrateur)
- `PUT /menus/{menu_id}` (administrateur)
- `DELETE /menus/{menu_id}` (administrateur)
- `POST /menus/{menu_id}/produits/{produit_id}` (administrateur)
- `DELETE /menus/{menu_id}/produits/{produit_id}` (administrateur)

### Commandes (`/commandes`)

- `GET /commandes/`
- `GET /commandes/{commande_id}`
- `POST /commandes/` (administrateur, accueil)
- `PUT /commandes/{commande_id}` (administrateur, preparateur)
- `DELETE /commandes/{commande_id}` (administrateur)
- `POST /commandes/{commande_id}/produits/{produit_id}` (administrateur, preparateur)
- `DELETE /commandes/{commande_id}/produits/{produit_id}` (administrateur, preparateur)

## Migrations Alembic

Le dossier Alembic est present, mais la configuration automatique des metadonnees semble incomplete.

Commandes utiles:

```bash
alembic revision -m "init"
alembic upgrade head
alembic downgrade -1
```

## Commandes Git utiles

```bash
git status
git add .
git commit -m "message"
git push
```

## Licence

A definir.