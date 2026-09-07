"""Module de normalisation et nettoyage de texte pour SûrCheck AI.
Conçu pour contrer l'obfuscation et le leetspeak sans altérer le sens.
"""

import re
import unicodedata

# Substitutions fréquentes de contournement
LEET_SUBS = {
    "@": "a",
    "4": "a",
    "0": "o",
    "1": "i",
    "!": "i",
    "|": "i",
    "$": "s",
    "5": "s",
    "3": "e",
    "€": "e",
    "7": "t",
    "+": "t",
    "8": "b",
}


def strip_accents(text: str) -> str:
    """Supprime les accents pour uniformiser l'analyse des règles."""
    nfkd_form = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)])


def normalize_text(text: str, apply_leet: bool = False) -> str:
    """Normalise une chaîne de caractères :
    - Mise en minuscules
    - Nettoyage des espaces multiples
    - Suppression des accents
    - Substitution leetspeak optionnelle pour la détection de mots-clés masqués
    """
    if not text:
        return ""

    # Nettoyage initial
    cleaned = text.strip().lower()

    # Normalisation des retours à la ligne et tabulations
    cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)

    if apply_leet:
        chars = []
        for char in cleaned:
            chars.append(LEET_SUBS.get(char, char))
        cleaned = "".join(chars)

    # Réduction des espaces
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned


def normalize_url(url: str) -> str:
    """Normalise une URL pour comparaison et réputation."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.lower().rstrip("/")
