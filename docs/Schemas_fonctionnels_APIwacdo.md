# Schémas fonctionnels — APIwacdo

Ces schémas décrivent l'enchaînement des actions possibles pour chaque rôle, en fonction des droits définis dans l'application (`require_role`).

## 1. Authentification (commune aux 3 rôles)

```mermaid
flowchart TD
    A[Utilisateur ouvre l'application] --> P["Politique de confidentialité\nGET /confidentialite (publique)"]
    P --> B["POST /users/login\navec identifiant + mot de passe"]
    B --> R{Plus de 5 essais\nen 1 minute ?}
    R -- Oui --> S[429 Trop de tentatives\n+ trace dans les logs]
    S --> B
    R -- Non --> C{Identifiants valides\net compte actif ?}
    C -- Non --> D[401 Unauthorized\n+ trace dans les logs]
    D --> B
    C -- Oui --> E["Un jeton JWT est délivré\n(id, rôle, expiration)"]
    E --> F["Le jeton est joint à chaque requête suivante\n(en-tête Authorization)"]
    F --> T{Jeton valide, non expiré\net compte toujours actif ?}
    T -- Non --> D
    T -- Oui --> G{Rôle vérifié par la route\ndemandée ?}
    G -- Rôle insuffisant --> H[403 Forbidden]
    G -- Rôle autorisé --> I[Accès à la fonctionnalité]
```

## 2. Parcours du compte Accueil

L'accueil saisit les commandes (au comptoir ou par téléphone) et les remet aux clients.

```mermaid
flowchart TD
    A[Connexion] --> B["Consulter le catalogue\nGET /produits, /menus"]
    B --> C["Saisir une commande\nPOST /commandes"]
    C --> D{La commande est-elle\nvalide ?}
    D -- "Non\n(choix de menu incomplet,\nnuméro déjà utilisé...)" --> E[400 / 409 : message d'erreur]
    E --> C
    D -- Oui --> F["Commande créée\nstatut = saisie"]
    F --> G["Attente : le préparateur\ndéclare la commande 'préparée'"]
    G --> H["Remettre la commande au client\nPOST /commandes/id/livrer"]
    H --> I["Commande livrée\nstatut = livree"]
```

## 3. Parcours du compte Préparation de commandes

Le préparateur voit les commandes à préparer, triées par heure de livraison, et les déclare prêtes.

```mermaid
flowchart TD
    A[Connexion] --> B["Lister les commandes à préparer\nGET /commandes?statut=saisie\n(triées par heure de livraison croissante)"]
    B --> C[Choisir la commande la plus urgente]
    C --> D["Consulter le détail\nGET /commandes/id\n(produits, menus, choix du client)"]
    D --> E[Préparer physiquement la commande]
    E --> F["Déclarer la commande prête\nPOST /commandes/id/preparer"]
    F --> G["Commande prête\nstatut = preparee"]
    G --> B
```

## 4. Parcours du compte Administration

L'administrateur gère le catalogue et les comptes utilisateurs.

```mermaid
flowchart TD
    A[Connexion] --> B{Que veut gérer\nl'administrateur ?}

    B -- Catalogue --> C["Créer / modifier une catégorie\nPOST, PUT /categories"]
    C --> D["Créer / modifier un produit\nPOST, PATCH /produits\n(nom, prix, disponibilité, image)"]
    D --> E["Créer un menu\nPOST /menus\n(plat principal fixe)"]
    E --> F["Ajouter des groupes de choix au menu\nPOST /menus/id/groupes\n(ex. Boisson, obligatoire, 1 choix)"]
    F --> G["Lier le groupe à une catégorie\nou y ajouter des produits un par un\nPOST /menus/groupes/id/produits"]

    D --> X["Supprimer un produit\nDELETE /produits/id"]
    X --> Y{Déjà commandé ou\nutilisé dans un menu ?}
    Y -- Oui --> Z["409 : le rendre indisponible\nPATCH /produits/id"]
    Y -- Non --> W[Produit supprimé]

    B -- Utilisateurs --> H["Créer un compte\nPOST /users/register\n(rôle : accueil / préparateur / administrateur)"]
    H --> I["Consulter / supprimer un compte\nGET /users/all, DELETE /users/id\n(même règle que la suppression RGPD, voir § 7)"]
```

## 5. Cycle de vie d'une commande (vue d'ensemble)

C'est le schéma central de l'application : il résume les statuts possibles d'une commande et qui a le droit de faire passer la commande d'un statut à l'autre.

```mermaid
stateDiagram-v2
    [*] --> saisie : Accueil crée la commande\n(POST /commandes)
    saisie --> preparee : Préparateur\n(POST /commandes/id/preparer)
    preparee --> livree : Accueil\n(POST /commandes/id/livrer)
    livree --> [*]

    note right of saisie
        Aucun retour en arrière possible :
        les transitions suivent un sens unique,
        contrôlé par le contrôleur (TRANSITIONS)
    end note
```

## 6. Vérification des choix d'un menu (logique interne)

Ce schéma détaille ce qui se passe à l'intérieur de `POST /commandes` quand une ligne concerne un menu, puisque c'est la partie la plus complexe du projet.

```mermaid
flowchart TD
    A[Ligne de commande = un menu] --> B{Pour chaque groupe\ndu menu}
    B --> C{Le client a-t-il fait\nun choix dans ce groupe ?}
    C -- "Non, et le groupe\nest obligatoire" --> D[400 : choix obligatoire manquant]
    C -- Oui --> E{Le produit choisi\nfait-il partie des\nproduits proposés\npar ce groupe ?}
    E -- Non --> F[400 : produit non proposé\nou non disponible]
    E -- Oui --> G{Le nombre de choix\ndépasse-t-il max_choix ?}
    G -- Oui --> H[400 : trop de choix]
    G -- Non --> I[Choix accepté]
    I --> J{Le groupe est-il\nrempli à la main\n(pas lié à une catégorie) ?}
    J -- Oui --> K[Ajouter le supplément\ndu produit choisi au prix]
    J -- Non --> L[Pas de supplément\n-- produit pris dans la catégorie]
    K --> M[Ligne suivante / fin]
    L --> M
```

## 7. Données personnelles (RGPD, commun aux 3 rôles)

Chaque employé peut consulter, modifier et supprimer ses propres données. La suppression s'adapte pour ne pas casser l'historique des commandes.

```mermaid
flowchart TD
    A[Utilisateur connecté] --> B{Que veut-il faire ?}
    B -- S'informer --> I["GET /confidentialite\n(données stockées, usage,\ndurée de conservation, droits)"]
    B -- Consulter --> C["GET /users/me\n(jamais de mot de passe renvoyé)"]
    B -- Modifier --> D["PATCH /users/me\n(nom, email, mot de passe)\nle rôle ne peut pas être modifié"]
    B -- Supprimer --> E["DELETE /users/me"]
    E --> F{Dernier administrateur\nactif ?}
    F -- Oui --> G[409 : suppression refusée]
    F -- Non --> H{A-t-il saisi\ndes commandes ?}
    H -- Non --> J[Compte supprimé]
    H -- Oui --> K["Compte anonymisé :\nnom et email remplacés,\nmot de passe aléatoire,\nactif = false"]
    K --> L["Les commandes restent intactes,\nsans donnée personnelle"]
    J --> M[Ses anciens jetons sont refusés]
    L --> M
```

## 8. Traçabilité

Chaque requête et chaque action sensible laissent une trace dans les journaux (onglet *Logs* de Render) :

| Événement | Exemple de ligne |
|---|---|
| Toute requête | `POST /commandes/ -> 201 (36 ms) utilisateur=accueil ip=…` |
| Connexion réussie / échouée | `Connexion échouée : identifiant=accueil ip=…` |
| Accès refusé | `Accès refusé : utilisateur=accueil rôle=accueil rôles requis=administrateur` |
| Commande | `Statut de commande : numéro=T42 saisie -> preparee par=preparateur` |
| Compte | `Compte anonymisé (il a des commandes) : ancien utilisateur=julie` |

Aucun mot de passe ni jeton n'est jamais écrit dans les journaux.
