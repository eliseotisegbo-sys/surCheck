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


def normalize_text(text: str, apply_leet: bool = True) -> str:
    """Normalise une chaîne de caractères :
    - Mise en minuscules
    - Nettoyage des espaces multiples
    - Suppression des accents
    - Substitution leetspeak activée par défaut pour contrer l'obfuscation
    - Recollement des espacements suspects entre lettres
    - Réduction des répétitions de caractères
    - Mapping des émojis courants
    """
    if not text:
        return ""

    # Nettoyage initial
    cleaned = text.strip().lower()

    # Normalisation des retours à la ligne et tabulations
    cleaned = re.sub(r"[\r\n\t]+", " ", cleaned)
    
    # Mapping des émojis comme substituts visuels
    emoji_mapping = {
        "💰": " argent ",
        "💵": " argent ",
        "💴": " argent ",
        "💶": " argent ",
        "💷": " argent ",
        "💸": " argent ",
        "⚠️": " urgence ",
        "🚨": " urgence ",
        "⚡": " urgence ",
        "🎁": " cadeau ",
        "🎉": " cadeau ",
        "🔒": " code ",
        "🔐": " code ",
        "🔑": " code ",
        "📱": " telephone ",
        "☎️": " telephone ",
        "✅": " validation ",
        "❌": " refus ",
        "🏦": " banque ",
        "🏧": " banque ",
    }
    
    for emoji, replacement in emoji_mapping.items():
        cleaned = cleaned.replace(emoji, replacement)

    # Application du leetspeak
    if apply_leet:
        chars = []
        for char in cleaned:
            chars.append(LEET_SUBS.get(char, char))
        cleaned = "".join(chars)
    
    # Réduction des répétitions de caractères (>2 consécutifs → 2)
    # Exemple: "urrrgent" → "urgent", "viiiite" → "viite" → normalisé ensuite
    cleaned = re.sub(r"(.)\1{2,}", r"\1\1", cleaned)
    
    # Recollement des espacements suspects entre lettres isolées
    # Exemple: "c o d e  s e c r e t" → "code secret"
    # Pattern: lettres isolées séparées par espaces/points/tirets
    cleaned = _rejoin_spaced_letters(cleaned)

    # Réduction des espaces multiples (après tous les traitements)
    cleaned = re.sub(r"\s+", " ", cleaned)

    return cleaned


def _rejoin_spaced_letters(text: str) -> str:
    """Recolle les lettres isolées séparées par espaces/points/tirets.
    
    Exemples:
    - "c o d e" → "code"
    - "c.o.d.e s-e-c-r-e-t" → "code secret"
    - "f r a i s  d e  d o s s i e r" → "frais de dossier"
    """
    # Pattern: séquence de lettres isolées séparées par espaces, points, tirets
    # Minimum 3 lettres pour éviter faux positifs (ex: "a b c" légitime)
    pattern = r'\b([a-z])[\s\.\-]+([a-z])[\s\.\-]+([a-z])(?:[\s\.\-]+([a-z]))*(?:[\s\.\-]+([a-z]))*(?:[\s\.\-]+([a-z]))*(?:[\s\.\-]+([a-z]))*(?:[\s\.\-]+([a-z]))*(?:[\s\.\-]+([a-z]))*(?:[\s\.\-]+([a-z]))*'
    
    def rejoin_match(match):
        # Extraire toutes les lettres capturées
        letters = [g for g in match.groups() if g is not None]
        rejoined = ''.join(letters)
        return rejoined
    
    # Appliquer plusieurs fois pour capturer toutes les séquences
    previous = ""
    max_iterations = 3
    iteration = 0
    
    while previous != text and iteration < max_iterations:
        previous = text
        text = re.sub(pattern, rejoin_match, text)
        iteration += 1
    
    return text


def normalize_url(url: str) -> str:
    """Normalise une URL pour comparaison et réputation."""
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.lower().rstrip("/")


# Marqueurs de négation pour la détection de contexte préventif
NEGATION_MARKERS = [
    r"ne\s+(?:\w+\s+)?jamais",  # ne ... jamais
    r"ne\s+(?:\w+\s+)?pas",      # ne ... pas
    r"n['']envoyez\s+pas",
    r"ne\s+donnez\s+pas",
    r"ne\s+communiquez\s+pas",
    r"ne\s+partagez\s+(?:jamais|pas)",
    r"[eé]vitez\s+de",
    r"refusez\s+de",
    r"ne\s+cliquez\s+pas",
    r"ne\s+r[eé]pondez\s+pas",
    r"attention\s+[aà]",
    r"m[eé]fiez[-\s]vous\s+de",
    r"ne\s+tombez\s+pas\s+dans",
    r"ne\s+vous\s+laissez\s+pas\s+avoir",
    r"aucun\s+agent\s+ne\s+vous\s+demandera",
    r"personne\s+ne\s+doit\s+vous\s+demander",
    r"il\s+est\s+interdit\s+de\s+donner",
    r"surtout\s+ne\s+\w+\s+pas",
]

# Marqueurs de récit/narration (troisième personne, passé)
NARRATIVE_MARKERS = [
    r"quelqu['']un\s+m['']a\s+demand[eé]",
    r"on\s+m['']a\s+demand[eé]",
    r"j['']ai\s+re[cç]u\s+un\s+message\s+qui",
    r"un\s+individu\s+a\s+tent[eé]\s+de",
    r"une\s+personne\s+pr[eé]tendant\s+[eê]tre",
    r"ils\s+ont\s+essay[eé]\s+de",
    r"mon\s+ami\s+a\s+re[cç]u",
    r"ma\s+s[oœ]ur\s+a\s+[eé]t[eé]\s+contact[eé]e",
    r"quelqu['']un\s+a\s+re[cç]u",
    r"on\s+lui\s+a\s+demand[eé]",
    r"il\s+a\s+re[cç]u\s+un\s+sms",
]


def has_negation_before(text: str, match_start: int, window: int = 8) -> bool:
    """Détecte si une négation ou narration précède un match.
    
    Args:
        text: Le texte complet
        match_start: Position de début du match
        window: Nombre de mots à examiner avant le match
        
    Returns:
        True si une négation/narration est détectée, False sinon
    """
    # Extraire la fenêtre de texte avant le match
    window_start = max(0, match_start - 100)  # ~100 caractères = ~8-15 mots
    context = text[window_start:match_start].lower()
    
    # Vérifier les marqueurs de négation
    for pattern in NEGATION_MARKERS:
        if re.search(pattern, context, re.IGNORECASE):
            return True
    
    # Vérifier les marqueurs de narration
    for pattern in NARRATIVE_MARKERS:
        if re.search(pattern, context, re.IGNORECASE):
            return True
    
    return False


def has_narrative_context(text: str) -> bool:
    """Détecte si le texte entier est dans un contexte narratif/préventif.
    
    Returns:
        True si le message entier semble être un récit ou une mise en garde
    """
    text_lower = text.lower()
    
    # Vérifier les marqueurs de narration globaux
    for pattern in NARRATIVE_MARKERS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    # Vérifier les marqueurs de négation globaux forts
    strong_negation = [
        r"ne\s+(?:\w+\s+)?jamais",
        r"n['']envoyez\s+(?:jamais|pas)",
        r"ne\s+donnez\s+(?:jamais|pas)",
        r"aucun\s+agent\s+ne",
        r"personne\s+ne\s+doit",
    ]
    
    for pattern in strong_negation:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    
    return False
