"""Journalisation de l'application (logs et traçabilité).

Deux journaux :
- « wacdo »       : le fonctionnement technique (requêtes, erreurs)
- « wacdo.audit » : les actions sensibles (connexions, comptes, commandes)

Les logs sont écrits sur la sortie standard : Render les collecte et les affiche
dans l'onglet « Logs » du service. On n'y écrit jamais de mot de passe ni de token.
"""
import logging
import sys

logger = logging.getLogger("wacdo")
audit = logging.getLogger("wacdo.audit")


def configurer_logs(niveau: int = logging.INFO) -> None:
    gestionnaire = logging.StreamHandler(sys.stdout)
    gestionnaire.setFormatter(
        logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    )
    logger.handlers = [gestionnaire]
    logger.setLevel(niveau)
