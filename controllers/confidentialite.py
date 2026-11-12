"""Information des utilisateurs sur leurs données personnelles (RGPD, articles 13 et 14).

Le contenu est centralisé ici pour être servi par l'API (route /confidentialite)
et affiché par le front-end, par exemple sur l'écran de connexion.
"""
from schemas.confidentialite import PolitiqueConfidentialite

POLITIQUE = PolitiqueConfidentialite(
    responsable="Wacdo, exploitant du restaurant",
    personnes_concernees=(
        "Les employés disposant d'un compte sur le back-office "
        "(administration, préparation, accueil). Aucune donnée client n'est collectée : "
        "une commande est identifiée par un simple numéro de ticket."
    ),
    donnees_collectees=[
        {"donnee": "Nom d'utilisateur", "finalite": "Se connecter et identifier l'auteur des actions"},
        {"donnee": "Adresse email", "finalite": "Identifier le compte de manière unique"},
        {"donnee": "Mot de passe", "finalite": "Authentification (stocké uniquement sous forme hachée, jamais en clair)"},
        {"donnee": "Rôle", "finalite": "Limiter les actions autorisées selon le poste"},
        {"donnee": "Commandes saisies", "finalite": "Suivi et traçabilité des commandes"},
        {"donnee": "Adresse IP et date des connexions (journaux)", "finalite": "Sécurité : détection des accès frauduleux"},
    ],
    base_legale="Intérêt légitime de l'employeur : organisation du travail et sécurité du système.",
    duree_conservation=(
        "Les données du compte sont conservées tant que le compte existe. "
        "À la suppression, le compte est effacé ; s'il a saisi des commandes, il est anonymisé "
        "(nom, email et mot de passe remplacés) afin de conserver l'historique des commandes "
        "sans donnée personnelle. Les journaux techniques sont conservés selon la durée "
        "de rétention de l'hébergeur."
    ),
    destinataires=(
        "Aucune donnée n'est vendue ni partagée avec des tiers. Seuls les administrateurs "
        "de Wacdo y ont accès. L'application est hébergée par Render (prestataire technique)."
    ),
    securite=[
        "Mots de passe hachés avec Argon2",
        "Authentification par token JWT à durée limitée",
        "Accès aux données limité selon le rôle",
        "Nombre de tentatives de connexion limité",
        "Communications chiffrées (HTTPS) en production",
    ],
    droits=[
        {"droit": "Consulter ses données", "comment": "GET /users/me"},
        {"droit": "Modifier ses données", "comment": "PATCH /users/me"},
        {"droit": "Supprimer son compte", "comment": "DELETE /users/me"},
    ],
    contact="Pour toute question : l'administrateur de l'application Wacdo.",
)


def get_politique() -> PolitiqueConfidentialite:
    return POLITIQUE
