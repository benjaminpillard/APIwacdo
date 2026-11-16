# APIwacdo

API REST du **back-office Wacdo** : gestion du catalogue (produits, catégories, menus et leur composition), des commandes et des comptes employés, avec des droits différents selon le rôle.

- **Documentation interactive** : `/docs` (Swagger) et `/redoc`
- **Collection Postman** : [`docs/postman/`](docs/postman/)
- **Modèle de données** : [`docs/MCD_MLD_APIwacdo.md`](docs/MCD_MLD_APIwacdo.md)
- **Script SQL de la base** : [`docs/base_de_donnees/schema_postgresql.sql`](docs/base_de_donnees/schema_postgresql.sql)
- **Schémas fonctionnels** : [`docs/Schemas_fonctionnels_APIwacdo.md`](docs/Schemas_fonctionnels_APIwacdo.md)

## Sommaire

1. [Stack technique](#stack-technique)
2. [Fonctionnalités et rôles](#fonctionnalités-et-rôles)
3. [Architecture](#architecture)
4. [Sécurité](#sécurité)
5. [Données personnelles (RGPD)](#données-personnelles-rgpd)
6. [Installation](#installation)
7. [Configuration](#configuration)
8. [Base de données et migrations](#base-de-données-et-migrations)
9. [Lancer l'API](#lancer-lapi)
10. [Tests](#tests)
11. [Tester avec Postman](#tester-avec-postman)
12. [Déploiement](#déploiement)
13. [Endpoints](#endpoints)
14. [Limites connues](#limites-connues)

## Stack technique

| Besoin | Outil |
|---|---|
| Langage et framework | Python 3.12, FastAPI |
| Base de données | PostgreSQL en production (Neon), SQLite en développement |
| ORM et migrations | SQLAlchemy 2, Alembic |
| Validation | Pydantic 2 |
| Authentification | OAuth2 Password Flow, JWT (PyJWT), hachage Argon2 (pwdlib) |
| Limitation de débit | slowapi |
| Tests | pytest, pytest-cov |
| Hébergement | Render (API), Neon (base PostgreSQL) |

## Fonctionnalités et rôles

| Rôle | Peut faire |
|---|---|
| `administrateur` | Tout : catalogue (catégories, produits, menus et leur composition), comptes employés, commandes |
| `preparateur` | Voir les commandes à préparer (triées par heure de livraison croissante) et les déclarer « préparées » |
| `accueil` | Saisir une commande (comptoir ou téléphone) et la remettre au client (la déclarer « livrée ») |

Tous les rôles peuvent consulter le catalogue et les commandes, et gérer leurs propres données (`/users/me`).

> **Choix assumé** : l'administrateur hérite de toutes les permissions, pour pouvoir dépanner en l'absence d'un équipier.

**Cycle d'une commande** : `saisie` → `preparee` (préparateur) → `livree` (accueil). Aucune étape ne peut être sautée ni annulée. Il n'y a pas de paiement : une commande est identifiée par son numéro de ticket.

**Règles métier principales**
- Le **prix est figé** au moment de la commande, et le **total est calculé par l'API**, jamais envoyé par le client.
- Un menu a un produit principal fixe et des **groupes de choix** (boisson, accompagnement…). Un groupe est soit lié à une catégorie (tous ses produits disponibles sont proposés), soit rempli produit par produit, avec un éventuel supplément de prix.
- À la saisie d'un menu, l'API vérifie les choix : groupes obligatoires remplis, nombre maximum respecté, produits proposés et disponibles.
- Un produit, un menu, une catégorie ou un groupe **déjà utilisé ne peut pas être supprimé** (409) : on le rend indisponible, pour préserver l'historique.

## Architecture

Le projet suit une organisation **MVC** adaptée à une API :

```text
.
├── main.py                  # application : routes montées, CORS, logs, gestion globale des erreurs
├── models/                  # Modèle : tables SQLAlchemy
├── schemas/                 # Vue : format des données reçues et renvoyées (Pydantic)
├── controllers/             # Contrôleur : logique métier
│   └── base.py              #   classe générique CRUDBase dont héritent tous les controllers
├── routes/                  # endpoints FastAPI : rôles autorisés, appel du controller
├── utils/                   # authentification, JWT, hachage, logs, limitation de débit, configuration
├── alembic/                 # migrations de la base de données
├── tests/                   # tests automatisés (pytest)
├── docs/                    # MCD/MLD, script SQL, schémas fonctionnels, collection Postman
├── create_admin.py          # crée un compte administrateur
├── seed.py                  # charge des données de démonstration
├── requirements.txt         # dépendances de production
└── requirements-dev.txt     # dépendances de développement (couverture de tests)
```

**Parcours d'une requête** : `routes/` vérifie le token et le rôle → `controllers/` applique les règles métier → `models/` lit et écrit en base → `schemas/` met en forme la réponse.

### Classe générique et héritage

`controllers/base.py` définit `CRUDBase[Modele]`, une classe **générique** qui regroupe les opérations communes à toutes les ressources : lecture (404 automatique), liste filtrée, triée et paginée, création, modification (PATCH partiel ou PUT complet), suppression, et des outils (refus de suppression d'un élément utilisé, doublon → 409).

Chaque controller en **hérite** et ne **surcharge** que sa logique propre :

```python
class ProduitController(CRUDBase[Produit]):
    message_introuvable = "Produit introuvable"

    def delete(self, db, produit):
        self.verifier_non_utilise(db, [...])   # vérifications propres aux produits
        super().delete(db, produit)            # puis le comportement commun
```

Six classes en héritent : catégories, produits, menus, groupes de choix, commandes et utilisateurs.

## Sécurité

| Mesure | Mise en œuvre |
|---|---|
| Authentification | OAuth2 Password Flow : `POST /users/login` renvoie un **JWT** signé (HS256) contenant l'id (`sub`), le rôle et l'expiration. Pas d'email dans le token, qui n'est pas chiffré. |
| Mots de passe | Hachés avec **Argon2**, jamais stockés ni renvoyés en clair |
| Rôles | Dépendance `require_role(...)` sur chaque route. Le rôle est **revérifié en base** à chaque requête : un retrait de droits s'applique immédiatement. |
| Validation | Toutes les entrées passent par des schémas **Pydantic** (types, longueurs, prix > 0…) → 422 si invalides |
| Injections SQL | Requêtes paramétrées par l'ORM SQLAlchemy, aucune requête SQL construite à la main |
| Brute-force | **5 tentatives de connexion par minute** et par IP (429 au-delà) |
| CORS | Seules les origines listées dans `CORS_ORIGINS` sont autorisées, avec les seules méthodes utiles |
| Erreurs | Format uniforme `{"detail": "..."}` en français. Une erreur imprévue renvoie un message générique, jamais de détail technique. |
| Logs et traçabilité | Une ligne par requête (statut, durée, utilisateur, IP), plus un journal d'audit : connexions, accès refusés, comptes, commandes. Aucun mot de passe ni token journalisé. |
| Secrets | Dans des variables d'environnement (`.env` jamais commité) |

## Données personnelles (RGPD)

- **Information** : `GET /confidentialite/` (route publique) décrit les données stockées, leur usage, la base légale, la durée de conservation, les destinataires et les droits.
- **Droit d'accès** : `GET /users/me`
- **Droit de rectification** : `PATCH /users/me` (le rôle ne peut pas être modifié par l'utilisateur lui-même)
- **Droit à l'effacement** : `DELETE /users/me`
  - un compte sans commande est supprimé ;
  - un compte qui a saisi des commandes est **anonymisé** (nom, email et mot de passe remplacés, compte désactivé), ce qui préserve l'historique des commandes sans donnée personnelle ;
  - le dernier administrateur actif ne peut pas être supprimé.
- **Minimisation** : aucune donnée client n'est collectée, une commande n'est identifiée que par son numéro de ticket.

## Installation

Prérequis : Python 3.10 ou plus.

```bash
git clone https://github.com/benjaminpillard/APIwacdo.git
cd APIwacdo
python -m venv .venv
source .venv/Scripts/activate      # Windows PowerShell : .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Configuration

Copier `.env.example` en `.env` et le compléter. Le fichier `.env` n'est jamais commité.

| Variable | Obligatoire | Description |
|---|---|---|
| `SECRET_KEY` | oui | Clé de signature des JWT, longue et aléatoire : `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `ALGORITHM` | oui | `HS256` |
| `DATABASE_URL` | oui | `sqlite:///./app.db` en local, chaîne de connexion PostgreSQL en production (Neon) |
| `CORS_ORIGINS` | non | Origines du front autorisées, séparées par des virgules |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | non | Durée de validité d'un token (défaut : 60) |
| `LOGIN_RATE_LIMIT` | non | Limite de tentatives de connexion par IP (défaut : `5/minute`) |

## Base de données et migrations

La structure de la base est gérée **uniquement par Alembic**, jamais créée automatiquement par l'application. Alembic lit `DATABASE_URL` : les migrations visent donc toujours la même base que l'API.

```bash
alembic upgrade head        # crée ou met à jour les tables
python create_admin.py      # crée le premier administrateur (identifiant, email, mot de passe)
python seed.py              # facultatif : données de démonstration
```

`seed.py` charge un jeu de démonstration : 5 catégories, 16 produits (dont un indisponible), 3 menus avec leurs groupes de choix (accompagnement avec supplément, boisson, sauces facultatives), les comptes `preparateur_demo` et `accueil_demo` (mots de passe demandés au clavier) et 4 commandes à différents stades. Il peut être relancé sans créer de doublons.

Le script SQL complet de création de la base PostgreSQL est fourni dans [`docs/base_de_donnees/schema_postgresql.sql`](docs/base_de_donnees/schema_postgresql.sql). Il est généré par `alembic upgrade head --sql`.

Après une modification d'un modèle (`models/`) :

```bash
alembic revision --autogenerate -m "description du changement"
# relire le fichier généré dans alembic/versions/ (compatibilité PostgreSQL), puis :
alembic upgrade head
```

## Lancer l'API

```bash
uvicorn main:app --reload
```

- Swagger : http://127.0.0.1:8000/docs. Le bouton **Authorize** permet de se connecter.
- ReDoc : http://127.0.0.1:8000/redoc

## Tests

```bash
pytest                       # 155 tests
pytest --cov=.               # avec la couverture de code (96 %)
```

Les tests tournent sur une base SQLite en mémoire, recréée pour chaque test : la base de développement n'est jamais touchée.

| Fichier | Ce qui est testé |
|---|---|
| `test_crud_base.py` | **Tests unitaires** de la classe générique (héritage, comportement commun, surcharges) |
| `test_roles.py` | **Matrice des permissions** : chaque route × chaque rôle (autorisé ou 403), et sans token (401) |
| `test_securite.py` | Contenu du JWT, token expiré ou falsifié, limitation de débit, CORS, logs |
| `test_rgpd.py` | Consultation, modification, suppression et anonymisation, politique de confidentialité |
| `test_produits.py`, `test_categories.py`, `test_menus.py` | Catalogue, composition des menus, suppléments, suppressions protégées |
| `test_commande.py` | Saisie, prix figés, choix de menu, circuit des statuts, tri par heure de livraison |
| `test_users.py` | Création de comptes |
| `test_documentation.py` | Chaque route est documentée dans Swagger, et la doc correspond aux réponses réelles |
| `test_seed.py` | Le jeu de démonstration est cohérent et peut être rechargé sans doublon |

## Tester avec Postman

1. Importer dans Postman les fichiers de [`docs/postman/`](docs/postman/) : la collection et l'environnement **Local** ou **Production**.
2. Dans l'environnement, renseigner `admin_password` (et `baseUrl` pour la production).
3. Lancer la collection dans l'ordre avec le **Runner**.

La collection (40 requêtes, avec des tests automatiques) déroule tout le parcours : connexion des 3 rôles, création du catalogue et d'un menu, circuit complet d'une commande, contrôle d'accès et RGPD. Les ids et les tokens sont enregistrés automatiquement.

> La collection fait 4 tentatives de connexion : la relancer deux fois dans la même minute déclenche la limitation de débit (429). C'est le comportement attendu.

## Déploiement

L'application est en production sur deux services :

| Rôle | Service | Détail |
|---|---|---|
| API (FastAPI) | **Render** (Web Service) | redéployée automatiquement à chaque fusion sur `main` |
| Base de données | **Neon** (PostgreSQL) | région Europe (Francfort) : les données restent dans l'UE |

La base est séparée de l'API : un redéploiement de Render ne touche jamais aux données.

### 1. Base de données (Neon)

1. Créer un projet sur [neon.tech](https://neon.tech), dans une région européenne. La base `neondb` est créée avec le projet.
2. Bouton **Connect** : copier la chaîne de connexion `postgresql://…?sslmode=require`.

### 2. API (Render)

1. Créer un **Web Service** relié au dépôt GitHub :
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** :
     ```
     alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT --proxy-headers --forwarded-allow-ips="*"
     ```
     `alembic upgrade head` applique les migrations à chaque déploiement (les tables sont créées au premier). `--proxy-headers` permet à l'API de voir la vraie IP des clients derrière le proxy de Render : sans cette option, la limitation de débit bloquerait tout le monde en même temps.
2. Variables d'environnement (**Environment**) : `DATABASE_URL` (chaîne de connexion Neon), `SECRET_KEY`, `ALGORITHM`, `CORS_ORIGINS`.

### 3. Premier administrateur et données de démonstration

Depuis sa machine, en visant la base de production (PowerShell) :

```powershell
$env:DATABASE_URL = "<chaîne de connexion Neon>"
python create_admin.py
python seed.py                   # facultatif : catalogue, comptes et commandes de démo
Remove-Item Env:DATABASE_URL     # revenir à la base locale
```

### 4. Vérification

- `https://<service>.onrender.com/docs` : se connecter avec **Authorize**, puis `GET /users/me`.
- Collection Postman avec l'environnement **Production**.
- Journaux : onglet **Logs** du service Render.

> Sur les offres gratuites, Render et Neon mettent leurs serveurs en veille quand ils ne sont pas utilisés : la première requête peut prendre jusqu'à une minute.

## Endpoints

| Ressource | Routes |
|---|---|
| Public | `GET /`, `GET /confidentialite/`, `POST /users/login` |
| Utilisateurs | `GET/PATCH/DELETE /users/me`, `POST /users/register`, `GET /users/all`, `DELETE /users/{id}` |
| Catégories | `GET/POST /categories/`, `GET/PUT/DELETE /categories/{id}` |
| Produits | `GET/POST /produits/` (filtres `categorie_id`, `disponible`), `GET /produits/search`, `GET/PUT/PATCH/DELETE /produits/{id}` |
| Menus | `GET/POST /menus/` (filtre `disponible`), `GET /menus/search`, `GET/PUT/DELETE /menus/{id}`, `POST /menus/{id}/groupes`, `DELETE /menus/groupes/{id}`, `POST /menus/groupes/{id}/produits`, `DELETE /menus/groupes/{id}/produits/{produit_id}` |
| Commandes | `GET/POST /commandes/` (filtres `statut`, `mode`), `GET/DELETE /commandes/{id}`, `POST /commandes/{id}/preparer`, `POST /commandes/{id}/livrer` |

Le détail de chaque route (paramètres, rôles, réponses et erreurs possibles) est dans Swagger.

## Limites connues

Ce sont les limites identifiées du projet, et les pistes d'évolution qui y répondraient :

| Limite | Conséquence | Évolution possible |
|---|---|---|
| Pas de déconnexion ni de révocation de token | Un token reste valide jusqu'à son expiration (60 min). Seule la désactivation d'un compte l'invalide plus tôt. | Liste de tokens révoqués, ou tokens courts + *refresh token* |
| Limitation de débit stockée en mémoire | Compteurs remis à zéro au redémarrage et non partagés si plusieurs instances tournent | Stockage partagé (Redis) |
| Énumérations `statut` et `mode` stockées en texte sans contrainte en base | Les valeurs sont contrôlées par l'application, mais pas par la base elle-même | Contrainte `CHECK` ajoutée par une migration |
| Numéro de ticket saisi par l'accueil | Doit être unique : un doublon est refusé (409) mais pas généré automatiquement | Numérotation automatique par jour |
| Images gérées par URL | Pas d'envoi de fichier image | Upload vers un stockage d'objets |
| API réservée au back-office | La borne client publique (commande par le client lui-même) n'est pas couverte | Routes publiques en lecture et mode de commande « borne » |
| Pas de verrouillage lors des changements de statut | Deux actions simultanées sur la même commande ne sont pas sérialisées (risque faible en pratique) | Verrou de ligne (`SELECT ... FOR UPDATE`) |
| Tests sur SQLite, production sur PostgreSQL | Écart possible entre les deux moteurs (réduit en activant les clés étrangères sous SQLite) | Lancer aussi les tests sur PostgreSQL (conteneur) |
| Recherche par nom simple (`ILIKE`) | Pas de tolérance aux fautes ni de recherche plein texte | Index plein texte PostgreSQL |
| Journaux uniquement sur la sortie standard | Durée de conservation limitée à celle de Render | Envoi vers un service de journalisation |
| Hébergement sur des offres gratuites | Mise en veille : première requête lente après une période d'inactivité | Offres payantes sans mise en veille |
