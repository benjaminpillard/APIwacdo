"""Limitation de débit (rate limiting) avec slowapi.

Chaque adresse IP a un nombre limité de requêtes sur les routes sensibles
(ex. 5 tentatives de connexion par minute) : cela bloque les attaques par force brute.

En production derrière le proxy de Render, uvicorn doit être lancé avec
--proxy-headers --forwarded-allow-ips="*" pour voir la vraie IP du client.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
