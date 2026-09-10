"""Module d'extraction d'entités pour SûrCheck AI.
Extrait les numéros de téléphone (spécificités Bénin/Afrique de l'Ouest),
les liens/domaines, les montants en FCFA et les mentions de codes.
"""

import re
from typing import List, Dict, Any
from urllib.parse import urlparse


# Regex pour numéros Bénin (+229) et Afrique de l'Ouest
PHONE_REGEX = re.compile(
    r"(?:\+?229\s*)?(?:01\s*)?(?:4[0-9]|5[0-9]|6[0-9]|9[0-9])[\s.-]?(?:[0-9]{2}[\s.-]?){3}",
    re.IGNORECASE,
)

# Regex pour URLs (accepte avec ou sans protocole)
URL_REGEX = re.compile(
    r"(?:https?://)?(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?",
    re.IGNORECASE,
)

# Regex pour montants en FCFA
CURRENCY_REGEX = re.compile(
    r"(?:[0-9]{1,3}(?:[\s.,][0-9]{3})*|[0-9]+)\s*(?:f\s*cfa|fcfa|f\b|francs?\b|cfa\b)",
    re.IGNORECASE,
)

# Domaines de raccourcisseurs d'URL connus (liste étendue)
SHORTENER_DOMAINS = {
    "bit.ly", "tinyurl.com", "cutt.ly", "is.gd", "t.co",
    "rb.gy", "goo.su", "ow.ly", "buff.ly", "wa.link", "wa.me",
    "short.io", "rebrand.ly", "lnkd.in", "s.id", "tiny.cc",
    "clickme.net", "clck.ru", "shorturl.at", "v.gd", "tr.im",
    "x.co", "go.dev", "go2.link", "tinycc.com", "url.bz",
}


def extract_phone_numbers(text: str) -> List[str]:
    """Extrait et normalise les numéros de téléphone potentiels."""
    matches = PHONE_REGEX.findall(text)
    cleaned_numbers = []
    for match in matches:
        digits_only = re.sub(r"[^\d+]", "", match)
        if len(digits_only) >= 8:
            cleaned_numbers.append(digits_only)
    return list(set(cleaned_numbers))


def extract_urls(text: str) -> List[Dict[str, Any]]:
    """Extrait les URLs du texte et analyse leurs domaines."""
    urls = URL_REGEX.findall(text)
    extracted = []
    for url in set(urls):
        try:
            # Normaliser l'URL : ajouter https:// si absent
            normalized_url = url if url.startswith(("http://", "https://")) else f"https://{url}"
            parsed = urlparse(normalized_url)
            domain = parsed.netloc.lower()
            
            is_shortener = domain in SHORTENER_DOMAINS or any(
                domain.endswith("." + s) for s in SHORTENER_DOMAINS
            )
            extracted.append({
                "url": normalized_url,
                "domain": domain,
                "is_shortener": is_shortener,
                "scheme": parsed.scheme,
            })
        except Exception:
            extracted.append({
                "url": url,
                "domain": "",
                "is_shortener": False,
                "scheme": "unknown",
            })
    return extracted


def extract_amounts(text: str) -> List[str]:
    """Extrait les montants financiers formulés en FCFA."""
    return list(set(CURRENCY_REGEX.findall(text)))
