"""Module de réputation et de hachage sécurisé pour SûrCheck AI.
Protège les numéros de téléphone et respecte la minimisation des données personnelles.
"""

import hashlib
import re
from typing import Optional, Dict, Any
from ..config import settings


def normalize_phone_number(raw_phone: str, default_country: str = "+229") -> str:
    """Normalise un numéro de téléphone ouest-africain au format international E.164.
    Prend en charge les formats béninois (8 ou 10 chiffres).
    """
    digits = re.sub(r"[^\d+]", "", raw_phone)

    if digits.startswith("+"):
        return digits

    if digits.startswith("00229"):
        return "+229" + digits[5:]

    if digits.startswith("229"):
        return "+229" + digits[3:]

    if digits.startswith("01") and len(digits) == 10:
        # Format béninois avec préfixe 01 (ex: 0197000000)
        return "+229" + digits[2:]

    if len(digits) == 8:
        # Format béninois standard à 8 chiffres (ex: 97000000)
        return "+229" + digits

    return default_country + digits if not digits.startswith("+") else digits


def hash_phone_number(normalized_phone: str) -> str:
    """Hache le numéro de téléphone avec un sel cryptographique pour indexation sécurisée.
    Le numéro en clair ne doit jamais être exposé.
    """
    salt = settings.PHONE_HASH_SALT
    data = f"{salt}:{normalized_phone}".encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def mask_phone_number(normalized_phone: str) -> str:
    """Masque un numéro de téléphone pour un affichage public sécurisé.
    Exemple: +229 97 •• •• 89
    """
    if len(normalized_phone) < 6:
        return "•••"
    prefix = normalized_phone[:6]
    suffix = normalized_phone[-2:]
    return f"{prefix} •• •• {suffix}"


def mask_url(url: str) -> str:
    """Masque une URL pour un affichage sécurisé."""
    if len(url) <= 15:
        return url
    return url[:12] + "•••"
