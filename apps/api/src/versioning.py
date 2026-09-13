"""Versioning structuré du moteur d'analyse SûrCheck AI.

Ce module encode de manière traçable :
- Version du moteur de règles (rules)
- Version du corpus ML (ml)
- Version de la base de réputation (reputation)

Format : "rules:YYYY.MM.V|ml:X.Y|reputation:YYYY.MM"

Conforme à FIABILISATION_PAIEMENT_SASPAY_SURCHECK_AI.md Section 4.3
"""

from datetime import datetime
from typing import NamedTuple


class EngineVersion(NamedTuple):
    """Version structurée du moteur d'analyse."""
    rules_version: str  # Ex: "2026.09.1"
    ml_version: str     # Ex: "0.4"
    reputation_version: str  # Ex: "2026.09"


# ─── VERSIONS ACTUELLES ──────────────────────────────────────────────────────

# Version du moteur de règles (règles heuristiques)
# Format : YYYY.MM.PATCH
# Incrémenter PATCH à chaque modification de rules.py, scorer.py, classifier.py
RULES_VERSION = "2026.09.2"

# Version du corpus ML (modèle de classification)
# Format : MAJOR.MINOR
# Actuellement désactivé (pas de ML en production)
ML_VERSION = "0.0"

# Version de la base de réputation communautaire
# Format : YYYY.MM (mois de dernière synchronisation)
# Basé sur la date de dernière mise à jour significative de la DB
REPUTATION_VERSION = "2026.09"


# ─── VERSION COMPLÈTE ────────────────────────────────────────────────────────

CURRENT_ENGINE_VERSION = EngineVersion(
    rules_version=RULES_VERSION,
    ml_version=ML_VERSION,
    reputation_version=REPUTATION_VERSION,
)


def get_engine_version_string() -> str:
    """Retourne la version complète du moteur au format standardisé.
    
    Format : "rules:YYYY.MM.V|ml:X.Y|reputation:YYYY.MM"
    
    Returns:
        Chaîne de version encodée
    
    Example:
        >>> get_engine_version_string()
        'rules:2026.09.2|ml:0.0|reputation:2026.09'
    """
    return (
        f"rules:{CURRENT_ENGINE_VERSION.rules_version}"
        f"|ml:{CURRENT_ENGINE_VERSION.ml_version}"
        f"|reputation:{CURRENT_ENGINE_VERSION.reputation_version}"
    )


def parse_engine_version(version_string: str) -> EngineVersion | None:
    """Parse une chaîne de version encodée.
    
    Args:
        version_string: Chaîne au format "rules:X|ml:Y|reputation:Z"
    
    Returns:
        EngineVersion ou None si format invalide
    
    Example:
        >>> v = parse_engine_version("rules:2026.09.1|ml:0.4|reputation:2026.09")
        >>> v.rules_version
        '2026.09.1'
    """
    try:
        parts = version_string.split("|")
        if len(parts) != 3:
            return None
        
        rules = parts[0].split(":", 1)[1]
        ml = parts[1].split(":", 1)[1]
        reputation = parts[2].split(":", 1)[1]
        
        return EngineVersion(
            rules_version=rules,
            ml_version=ml,
            reputation_version=reputation,
        )
    except (IndexError, ValueError):
        return None


def get_version_changelog() -> dict[str, list[str]]:
    """Retourne le changelog des versions du moteur.
    
    Returns:
        Dictionnaire {version: [changements]}
    """
    return {
        "2026.09.2": [
            "Correction bug RiskLevel enum (analyze.py ligne 63)",
            "Ajout validation startup secrets production",
            "Nettoyage valeurs par défaut sensibles config.py",
        ],
        "2026.09.1": [
            "Migration complète SasPay (suppression Chariow)",
            "Simplification provider paiement unique",
            "Amélioration détection réseau Mobile Money Bénin",
        ],
        "2026.09.0": [
            "Version initiale moteur hybride règles + réputation",
            "Classification 7 catégories fraudes",
            "Scoring 0-100 avec 3 niveaux risque",
        ],
    }


def get_version_info() -> dict:
    """Retourne informations complètes sur la version actuelle.
    
    Returns:
        Dictionnaire avec version, composants, date
    """
    return {
        "version": get_engine_version_string(),
        "components": {
            "rules": {
                "version": RULES_VERSION,
                "description": "Moteur de règles heuristiques",
                "status": "active",
            },
            "ml": {
                "version": ML_VERSION,
                "description": "Modèle de classification ML",
                "status": "inactive" if ML_VERSION == "0.0" else "active",
            },
            "reputation": {
                "version": REPUTATION_VERSION,
                "description": "Base de réputation communautaire",
                "status": "active",
            },
        },
        "build_date": datetime.now().isoformat(),
    }


def compare_versions(v1: str, v2: str) -> int:
    """Compare deux versions de règles.
    
    Args:
        v1: Première version (ex: "2026.09.1")
        v2: Deuxième version (ex: "2026.09.2")
    
    Returns:
        -1 si v1 < v2, 0 si égales, 1 si v1 > v2
    """
    try:
        parts1 = [int(p) for p in v1.split(".")]
        parts2 = [int(p) for p in v2.split(".")]
        
        for p1, p2 in zip(parts1, parts2):
            if p1 < p2:
                return -1
            elif p1 > p2:
                return 1
        
        # Si longueurs différentes
        if len(parts1) < len(parts2):
            return -1
        elif len(parts1) > len(parts2):
            return 1
        
        return 0
    except (ValueError, AttributeError):
        return 0


# ─── COMPATIBILITÉ ───────────────────────────────────────────────────────────

def get_legacy_version() -> str:
    """Retourne la version au format legacy (pour rétrocompatibilité).
    
    Returns:
        Version courte (ex: "v1.0.0")
    """
    # Extraire juste la version rules pour compatibilité
    return f"v{RULES_VERSION}"


# Alias pour rétrocompatibilité
ENGINE_VERSION = get_engine_version_string()
