-- Script SQL de création de la base Wacdo (PostgreSQL)
-- Généré par Alembic à partir des migrations : alembic upgrade head --sql
-- Ne pas modifier à la main : la source de vérité est le dossier alembic/versions/.

BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> c1bd65457d10

CREATE TABLE categories (
    id SERIAL NOT NULL, 
    nom VARCHAR(50) NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (nom)
);

CREATE INDEX ix_categories_id ON categories (id);

CREATE TABLE utilisateurs (
    id SERIAL NOT NULL, 
    username VARCHAR, 
    email VARCHAR, 
    password VARCHAR NOT NULL, 
    role VARCHAR, 
    PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_utilisateurs_email ON utilisateurs (email);

CREATE INDEX ix_utilisateurs_id ON utilisateurs (id);

CREATE UNIQUE INDEX ix_utilisateurs_username ON utilisateurs (username);

CREATE TABLE commandes (
    id SERIAL NOT NULL, 
    numero VARCHAR(20) NOT NULL, 
    statut VARCHAR(8) NOT NULL, 
    mode VARCHAR(9) NOT NULL, 
    heure_livraison TIMESTAMP WITH TIME ZONE, 
    total NUMERIC(8, 2) NOT NULL, 
    utilisateur_id INTEGER NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP), 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(utilisateur_id) REFERENCES utilisateurs (id), 
    UNIQUE (numero)
);

CREATE INDEX ix_commandes_heure_livraison ON commandes (heure_livraison);

CREATE INDEX ix_commandes_id ON commandes (id);

CREATE INDEX ix_commandes_statut ON commandes (statut);

CREATE TABLE produits (
    id SERIAL NOT NULL, 
    nom VARCHAR(100) NOT NULL, 
    description VARCHAR(500), 
    prix NUMERIC(8, 2) NOT NULL, 
    image_url VARCHAR(255), 
    disponible BOOLEAN NOT NULL, 
    categorie_id INTEGER, 
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (CURRENT_TIMESTAMP), 
    updated_at TIMESTAMP WITH TIME ZONE, 
    PRIMARY KEY (id), 
    FOREIGN KEY(categorie_id) REFERENCES categories (id)
);

CREATE INDEX ix_produits_id ON produits (id);

CREATE INDEX ix_produits_nom ON produits (nom);

CREATE TABLE menus (
    id SERIAL NOT NULL, 
    nom VARCHAR(100) NOT NULL, 
    description VARCHAR(500), 
    prix NUMERIC(8, 2) NOT NULL, 
    image_url VARCHAR(255), 
    disponible BOOLEAN NOT NULL, 
    produit_principal_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(produit_principal_id) REFERENCES produits (id)
);

CREATE INDEX ix_menus_id ON menus (id);

CREATE TABLE lignes_commande (
    id SERIAL NOT NULL, 
    commande_id INTEGER NOT NULL, 
    produit_id INTEGER, 
    menu_id INTEGER, 
    quantite INTEGER NOT NULL, 
    prix_unitaire NUMERIC(8, 2) NOT NULL, 
    PRIMARY KEY (id), 
    CHECK ((produit_id IS NULL) <> (menu_id IS NULL)), 
    FOREIGN KEY(commande_id) REFERENCES commandes (id), 
    FOREIGN KEY(menu_id) REFERENCES menus (id), 
    FOREIGN KEY(produit_id) REFERENCES produits (id)
);

CREATE TABLE menu_groupes (
    id SERIAL NOT NULL, 
    menu_id INTEGER NOT NULL, 
    nom VARCHAR(50) NOT NULL, 
    obligatoire BOOLEAN NOT NULL, 
    max_choix INTEGER NOT NULL, 
    categorie_id INTEGER, 
    PRIMARY KEY (id), 
    FOREIGN KEY(categorie_id) REFERENCES categories (id), 
    FOREIGN KEY(menu_id) REFERENCES menus (id)
);

CREATE INDEX ix_menu_groupes_id ON menu_groupes (id);

CREATE TABLE lignes_commande_choix (
    id SERIAL NOT NULL, 
    ligne_commande_id INTEGER NOT NULL, 
    groupe_id INTEGER NOT NULL, 
    produit_id INTEGER NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(groupe_id) REFERENCES menu_groupes (id), 
    FOREIGN KEY(ligne_commande_id) REFERENCES lignes_commande (id), 
    FOREIGN KEY(produit_id) REFERENCES produits (id)
);

CREATE TABLE menu_groupe_produits (
    id SERIAL NOT NULL, 
    groupe_id INTEGER NOT NULL, 
    produit_id INTEGER NOT NULL, 
    supplement NUMERIC(8, 2) NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(groupe_id) REFERENCES menu_groupes (id), 
    FOREIGN KEY(produit_id) REFERENCES produits (id), 
    UNIQUE (groupe_id, produit_id)
);

INSERT INTO alembic_version (version_num) VALUES ('c1bd65457d10') RETURNING alembic_version.version_num;

-- Running upgrade c1bd65457d10 -> 8f77dab79eda

ALTER TABLE utilisateurs ADD COLUMN actif BOOLEAN DEFAULT true NOT NULL;

UPDATE alembic_version SET version_num='8f77dab79eda' WHERE alembic_version.version_num = 'c1bd65457d10';

COMMIT;

