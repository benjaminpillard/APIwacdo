# Modèle de données — APIwacdo

Ce document reprend le modèle conceptuel (MCD) et le modèle logique (MLD) de la base de données du projet, tels qu'ils sont implémentés dans `models/`.

## 1. Modèle Conceptuel de Données (MCD)

### 1.1 Liste des entités et de leurs propriétés

**UTILISATEUR**
- id (identifiant)
- username
- email
- password (haché)
- role (administrateur / preparateur / accueil)
- actif *(faux quand le compte a été supprimé puis anonymisé, voir RGPD)*

**CATEGORIE**
- id
- nom

**PRODUIT**
- id
- nom
- description
- prix
- image_url
- disponible
- created_at
- updated_at

**MENU**
- id
- nom
- description
- prix
- image_url
- disponible

**MENU_GROUPE** *(un groupe de choix dans un menu : "Boisson", "Accompagnement"...)*
- id
- nom
- obligatoire
- max_choix

**COMMANDE**
- id
- numero
- statut (saisie / preparee / livree)
- mode (comptoir / telephone)
- heure_livraison
- total
- created_at

**LIGNE_COMMANDE** *(une ligne du ticket : un produit seul, ou un menu)*
- id
- quantite
- prix_unitaire *(prix figé au moment de la commande)*

### 1.2 Associations et cardinalités

| Association | Entité 1 | Cardinalité | Entité 2 | Cardinalité | Sens |
|---|---|---|---|---|---|
| CLASSER | CATEGORIE | 0,n | PRODUIT | 0,1 | une catégorie classe des produits ; un produit appartient à 0 ou 1 catégorie |
| COMPOSER | MENU | 1,1 | PRODUIT | 0,n | un menu a exactement un produit principal (ex. le Big Mac) ; un produit peut être le principal de plusieurs menus |
| POSSEDER | MENU | 1,n | MENU_GROUPE | 1,1 | un menu possède un ou plusieurs groupes de choix ; un groupe appartient à un seul menu |
| CIBLER | MENU_GROUPE | 0,n | CATEGORIE | 0,1 | un groupe peut être lié à une catégorie (le groupe propose alors tous les produits disponibles de cette catégorie) |
| PROPOSER | MENU_GROUPE | 0,n | PRODUIT | 0,n | un groupe peut aussi proposer des produits choisis un par un *(association porteuse de l'attribut `supplement`)* |
| SAISIR | UTILISATEUR | 0,n | COMMANDE | 1,1 | un utilisateur saisit plusieurs commandes ; une commande est saisie par un seul utilisateur |
| CONTENIR | COMMANDE | 1,n | LIGNE_COMMANDE | 1,1 | une commande contient une ou plusieurs lignes ; une ligne appartient à une seule commande |
| CONCERNER_PRODUIT | LIGNE_COMMANDE | 0,1 | PRODUIT | 0,n | une ligne concerne éventuellement un produit seul |
| CONCERNER_MENU | LIGNE_COMMANDE | 0,1 | MENU | 0,n | une ligne concerne éventuellement un menu *(exclusif avec CONCERNER_PRODUIT : une ligne a l'un ou l'autre, jamais les deux)* |
| CHOISIR | LIGNE_COMMANDE | 0,n | MENU_GROUPE | 0,n | pour une ligne de type menu, on enregistre le choix fait dans chaque groupe *(association porteuse, résolue par PRODUIT choisi)* |

### 1.3 Schéma (notation Merise, via Mermaid)

```mermaid
erDiagram
    CATEGORIE ||--o{ PRODUIT : classe
    PRODUIT ||--o{ MENU : "est le plat principal de"
    MENU ||--o{ MENU_GROUPE : possede
    CATEGORIE |o--o{ MENU_GROUPE : cible
    MENU_GROUPE }o--o{ PRODUIT : propose
    UTILISATEUR ||--o{ COMMANDE : saisit
    COMMANDE ||--o{ LIGNE_COMMANDE : contient
    PRODUIT |o--o{ LIGNE_COMMANDE : concerne
    MENU |o--o{ LIGNE_COMMANDE : concerne
    LIGNE_COMMANDE }o--o{ MENU_GROUPE : choisit
    PRODUIT ||--o{ LIGNE_COMMANDE_CHOIX : "est le choix de"
```

---

## 2. Modèle Logique de Données (MLD)

Notation : `TABLE(clé_primaire, attribut, ..., #clé_étrangère)`. Le `#` marque une clé étrangère.

```
UTILISATEUR(id, username, email, password, role, actif)
    contraintes d'unicité : username, email

CATEGORIE(id, nom)

PRODUIT(id, nom, description, prix, image_url, disponible, created_at, updated_at,
        #categorie_id)
    #categorie_id référence CATEGORIE.id (nullable)

MENU(id, nom, description, prix, image_url, disponible,
     #produit_principal_id)
    #produit_principal_id référence PRODUIT.id (non nul)

MENU_GROUPE(id, nom, obligatoire, max_choix,
            #menu_id, #categorie_id)
    #menu_id référence MENU.id (non nul)
    #categorie_id référence CATEGORIE.id (nullable)

MENU_GROUPE_PRODUIT(id, supplement,
                     #groupe_id, #produit_id)
    #groupe_id référence MENU_GROUPE.id (non nul)
    #produit_id référence PRODUIT.id (non nul)
    contrainte d'unicité : (groupe_id, produit_id)

COMMANDE(id, numero, statut, mode, heure_livraison, total, created_at, updated_at,
         #utilisateur_id)
    #utilisateur_id référence UTILISATEUR.id (non nul)
    contrainte d'unicité : numero

LIGNE_COMMANDE(id, quantite, prix_unitaire,
               #commande_id, #produit_id, #menu_id)
    #commande_id référence COMMANDE.id (non nul)
    #produit_id référence PRODUIT.id (nullable)
    #menu_id référence MENU.id (nullable)
    contrainte : (produit_id IS NULL) <> (menu_id IS NULL)  -- l'un ou l'autre, jamais les deux

LIGNE_COMMANDE_CHOIX(id,
                      #ligne_commande_id, #groupe_id, #produit_id)
    #ligne_commande_id référence LIGNE_COMMANDE.id (non nul)
    #groupe_id référence MENU_GROUPE.id (non nul)
    #produit_id référence PRODUIT.id (non nul)
```

### 2.1 Remarques de passage du MCD au MLD

- Les associations **1,1 / 0,n ou 1,n** (CLASSER, COMPOSER, POSSEDER, CIBLER, SAISIR, CONTENIR, CONCERNER_PRODUIT, CONCERNER_MENU) deviennent une simple clé étrangère dans la table du côté « plusieurs ».
- L'association **0,n / 0,n** PROPOSER, qui porte l'attribut `supplement`, devient une **table à part entière** : `MENU_GROUPE_PRODUIT`. C'est elle qui permet de proposer un même produit dans plusieurs groupes, avec un supplément de prix différent selon le groupe.
- L'association **0,n / 0,n** CHOISIR devient elle aussi une table à part, `LIGNE_COMMANDE_CHOIX`, qui relie une ligne de commande, un groupe et le produit réellement choisi par le client dans ce groupe.
- Les colonnes `statut` et `mode` sont des **énumérations** (`saisie`, `preparee`, `livree` ; `comptoir`, `telephone`), stockées en texte. Les valeurs sont contrôlées par l'application (Pydantic à l'entrée de l'API, type `Enum` de SQLAlchemy à l'écriture).
- `prix_unitaire` (dans `LIGNE_COMMANDE`) et `supplement` (dans `MENU_GROUPE_PRODUIT`) sont stockés en `NUMERIC(8,2)`, jamais en nombre à virgule flottante, pour éviter les erreurs d'arrondi sur des montants d'argent.

---

## 3. Schéma physique (tel qu'implémenté)

Les tables sont créées par les migrations Alembic :

| Migration | Contenu |
|---|---|
| `c1bd65457d10_creation_initiale_des_tables.py` | les 9 tables |
| `8f77dab79eda_ajout_colonne_actif_sur_utilisateurs.py` | colonne `utilisateurs.actif` (anonymisation RGPD) |

```mermaid
erDiagram
    utilisateurs {
        INTEGER id PK
        VARCHAR username UK "identifiant de connexion"
        VARCHAR email UK
        VARCHAR password "hash Argon2, jamais en clair"
        VARCHAR role "administrateur, preparateur, accueil"
        BOOLEAN actif "false si anonymisé"
    }
    categories {
        INTEGER id PK
        VARCHAR_50 nom UK
    }
    produits {
        INTEGER id PK
        VARCHAR_100 nom
        VARCHAR_500 description
        NUMERIC_8_2 prix
        VARCHAR_255 image_url
        BOOLEAN disponible
        INTEGER categorie_id FK
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }
    menus {
        INTEGER id PK
        VARCHAR_100 nom
        VARCHAR_500 description
        NUMERIC_8_2 prix
        VARCHAR_255 image_url
        BOOLEAN disponible
        INTEGER produit_principal_id FK
    }
    menu_groupes {
        INTEGER id PK
        INTEGER menu_id FK
        VARCHAR_50 nom
        BOOLEAN obligatoire
        INTEGER max_choix
        INTEGER categorie_id FK "facultatif"
    }
    menu_groupe_produits {
        INTEGER id PK
        INTEGER groupe_id FK
        INTEGER produit_id FK
        NUMERIC_8_2 supplement
    }
    commandes {
        INTEGER id PK
        VARCHAR_20 numero UK "numéro du ticket"
        VARCHAR_9 statut "saisie, preparee, livree"
        VARCHAR_9 mode "comptoir, telephone"
        TIMESTAMPTZ heure_livraison "indexé : tri des commandes à préparer"
        NUMERIC_8_2 total
        INTEGER utilisateur_id FK
        TIMESTAMPTZ created_at
        TIMESTAMPTZ updated_at
    }
    lignes_commande {
        INTEGER id PK
        INTEGER commande_id FK
        INTEGER produit_id FK "OU menu_id"
        INTEGER menu_id FK "OU produit_id"
        INTEGER quantite
        NUMERIC_8_2 prix_unitaire "figé à la commande"
    }
    lignes_commande_choix {
        INTEGER id PK
        INTEGER ligne_commande_id FK
        INTEGER groupe_id FK
        INTEGER produit_id FK
    }

    categories ||--o{ produits : categorie_id
    produits ||--o{ menus : produit_principal_id
    menus ||--o{ menu_groupes : menu_id
    categories |o--o{ menu_groupes : categorie_id
    menu_groupes ||--o{ menu_groupe_produits : groupe_id
    produits ||--o{ menu_groupe_produits : produit_id
    utilisateurs ||--o{ commandes : utilisateur_id
    commandes ||--o{ lignes_commande : commande_id
    produits |o--o{ lignes_commande : produit_id
    menus |o--o{ lignes_commande : menu_id
    lignes_commande ||--o{ lignes_commande_choix : ligne_commande_id
    menu_groupes ||--o{ lignes_commande_choix : groupe_id
    produits ||--o{ lignes_commande_choix : produit_id
```

### 3.1 Choix des types

| Donnée | Type | Pourquoi |
|---|---|---|
| Prix, suppléments, totaux | `NUMERIC(8,2)` | valeur exacte au centime, pas d'erreur d'arrondi comme avec un `FLOAT` |
| Dates | `TIMESTAMP WITH TIME ZONE` | pas d'ambiguïté d'heure (heure d'été, serveur dans un autre fuseau) |
| Disponibilité, obligatoire, actif | `BOOLEAN` | deux états seulement |
| Statut, mode | énumération stockée en `VARCHAR` | liste fermée de valeurs, contrôlée par l'application (Python `Enum`) |
| Textes | `VARCHAR(n)` | longueur maximale identique à la validation Pydantic de l'API |
| Mot de passe | `VARCHAR` | contient un hash Argon2 (le mot de passe en clair n'est jamais stocké) |

### 3.2 Intégrité et performances

- **Clés étrangères** sur toutes les relations : impossible de référencer un produit, un menu ou une catégorie inexistant (vérifiées aussi en développement sous SQLite grâce à `PRAGMA foreign_keys=ON`).
- **Contrainte de vérification** sur `lignes_commande` : une ligne concerne un produit **ou** un menu, jamais les deux ni aucun.
- **Contraintes d'unicité** : nom de catégorie, username, email, numéro de commande, couple (groupe, produit).
- **Index** sur les colonnes filtrées ou triées : `produits.nom`, `commandes.statut`, `commandes.heure_livraison`, `utilisateurs.username`, `utilisateurs.email`.
- **Suppressions protégées** par l'API : un produit, un menu, une catégorie ou un groupe déjà utilisé ne peut pas être supprimé (409), pour préserver l'historique des commandes. Il faut le rendre indisponible.
