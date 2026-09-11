"""Module de fuzzy matching pour tolérance aux fautes de frappe.
Utilise rapidfuzz pour détecter les variantes de termes critiques avec distance de Levenshtein.
"""

from typing import List, Tuple, Set

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


# Termes critiques nécessitant fuzzy matching (section 2.1 et 2.2 du document)
CRITICAL_TERMS = [
    # Codes secrets / OTP
    "code secret",
    "code otp",
    "code pin",
    "mot de passe",
    "code de retrait",
    "code de validation",
    "pin momo",
    "pin moov",
    "pin mtn",
    
    # Demandes d'argent
    "frais de dossier",
    "frais d'inscription",
    "caution",
    "caution remboursable",
    "frais de deblocage",
    "depot prealable",
    "commission avant",
    "frais de traitement",
    "frais de douane",
    "frais de dedouanement",
    
    # Urgence
    "urgent",
    "tres urgent",
    "immediat",
    "immediatement",
    "dernier delai",
    "derniere chance",
    
    # Promesses de gain
    "vous avez gagne",
    "tirage au sort",
    "felicitations",
    "subvention",
    "cadeau surprise",
    "jackpot",
    
    # Usurpation
    "service client mtn",
    "assistance moov",
    "agent agree",
    "service client",
]


def _sliding_windows(text: str, max_words: int = 3) -> List[str]:
    """Génère des fenêtres glissantes de 1 à max_words mots.
    
    Args:
        text: Texte à découper
        max_words: Nombre maximum de mots par fenêtre
        
    Returns:
        Liste de chaînes (fenêtres de texte)
    """
    words = text.split()
    windows = []
    
    for window_size in range(1, min(max_words + 1, len(words) + 1)):
        for i in range(len(words) - window_size + 1):
            window = " ".join(words[i:i+window_size])
            windows.append(window)
    
    return windows


def fuzzy_contains(text: str, terms: List[str] = None, threshold: int = 85) -> List[Tuple[str, str, int]]:
    """Recherche des termes critiques avec tolérance aux fautes de frappe.
    
    Utilise la distance de Levenshtein (via rapidfuzz) pour matcher des variantes
    avec fautes de frappe, espaces manquants, ou petites erreurs.
    
    Args:
        text: Texte à analyser (déjà normalisé)
        terms: Liste optionnelle de termes à chercher (défaut: CRITICAL_TERMS)
        threshold: Score de similarité minimum (0-100), défaut 85%
        
    Returns:
        Liste de tuples (terme_trouvé, terme_référence, score_similarité)
        
    Exemples:
        "fré de dossié" match "frais de dossier" (score ~87)
        "kode sekret" match "code secret" (score ~82)
        "urjant" match "urgent" (score ~86)
    """
    if not HAS_RAPIDFUZZ:
        # Repli sans rapidfuzz : retour vide (fuzzy matching désactivé)
        return []
    
    if terms is None:
        terms = CRITICAL_TERMS
    
    matched = []
    seen_terms = set()  # Éviter les doublons
    
    # Générer des fenêtres glissantes de 1 à 3 mots
    windows = _sliding_windows(text, max_words=3)
    
    for window in windows:
        # Nettoyer la fenêtre
        window_clean = window.strip().lower()
        
        if len(window_clean) < 3:
            # Trop court pour fuzzy matching fiable
            continue
        
        for term in terms:
            # Calculer similarité
            score = fuzz.ratio(window_clean, term.lower())
            
            if score >= threshold:
                # Match trouvé
                if term not in seen_terms:
                    matched.append((window, term, score))
                    seen_terms.add(term)
    
    return matched


def enhance_rules_with_fuzzy(text: str, threshold: int = 85) -> Set[str]:
    """Détecte des variantes floues de termes critiques pour enrichir la détection.
    
    Retourne un ensemble de codes de catégories détectées par fuzzy matching
    pour être combinées avec les règles regex standard.
    
    Args:
        text: Texte normalisé
        threshold: Score minimum de similarité
        
    Returns:
        Ensemble de catégories ("OTP", "MONEY_REQ", "URGENCY", "GAIN", "USURPATION")
    """
    matches = fuzzy_contains(text, threshold=threshold)
    
    categories = set()
    
    for window, term, score in matches:
        # Mapper les termes aux catégories de règles
        if any(x in term for x in ["code", "pin", "mot de passe", "otp"]):
            categories.add("OTP")
        elif any(x in term for x in ["frais", "caution", "depot", "commission"]):
            categories.add("MONEY_REQ")
        elif any(x in term for x in ["urgent", "immediat", "dernier", "derniere"]):
            categories.add("URGENCY")
        elif any(x in term for x in ["gagne", "tirage", "felicitation", "subvention", "cadeau", "jackpot"]):
            categories.add("GAIN")
        elif any(x in term for x in ["service client", "assistance", "agent agree"]):
            categories.add("USURPATION")
    
    return categories


def get_fuzzy_matches_report(text: str, threshold: int = 85) -> str:
    """Génère un rapport détaillé des matches fuzzy pour debugging.
    
    Args:
        text: Texte à analyser
        threshold: Score minimum
        
    Returns:
        Chaîne formatée avec les matches trouvés
    """
    matches = fuzzy_contains(text, threshold=threshold)
    
    if not matches:
        return "Aucun match fuzzy détecté."
    
    report_lines = [f"Matches fuzzy trouvés ({len(matches)}):"]
    for window, term, score in matches:
        report_lines.append(f"  • '{window}' → '{term}' (similarité: {score}%)")
    
    return "\n".join(report_lines)
