"""Source unique de vérité pour les tarifs SûrCheck AI.

Ce module centralise tous les prix des packs de crédits.
Aucun autre fichier (documentation, frontend, tests) ne doit définir
de prix différent sans référencer explicitement ce module.

Conforme à FIABILISATION_PAIEMENT_SASPAY_SURCHECK_AI.md Section 4.1
"""

from .config import settings


# ─── TARIFS OFFICIELS SÛRCHECK (Source unique de vérité) ────────────────────

OFFICIAL_PACKS = {
    "pack_1": {
        "id": "pack_1",
        "credits": 1,
        "amount_fcfa": settings.CREDIT_PACK_1_FCFA,  # 600 FCFA
        "label": "Analyse unique",
        "unit_price_fcfa": 600,
        "popular": False,
        "description": "1 analyse complète immédiate",
        "savings_percent": 0,
    },
    "pack_5": {
        "id": "pack_5",
        "credits": 5,
        "amount_fcfa": settings.CREDIT_PACK_5_FCFA,  # 1500 FCFA
        "label": "Petit pack",
        "unit_price_fcfa": 300,
        "popular": False,
        "description": "5 analyses complètes réutilisables",
        "savings_percent": 50,  # 50% vs prix unitaire
    },
    "pack_10": {
        "id": "pack_10",
        "credits": 10,
        "amount_fcfa": settings.CREDIT_PACK_10_FCFA,  # 2500 FCFA
        "label": "Pack recommandé",
        "unit_price_fcfa": 250,
        "popular": True,
        "description": "10 analyses complètes — Le plus populaire",
        "savings_percent": 58,  # 58% vs prix unitaire
    },
    "pack_25": {
        "id": "pack_25",
        "credits": 25,
        "amount_fcfa": settings.CREDIT_PACK_25_FCFA,  # 5000 FCFA
        "label": "Gros pack",
        "unit_price_fcfa": 200,
        "popular": False,
        "description": "25 analyses complètes",
        "savings_percent": 67,  # 67% vs prix unitaire
    },
}


def get_pack_by_id(pack_id: str) -> dict | None:
    """Retourne les détails d'un pack par son identifiant.
    
    Args:
        pack_id: Identifiant du pack (ex: "pack_10")
    
    Returns:
        Dictionnaire du pack ou None si introuvable
    """
    return OFFICIAL_PACKS.get(pack_id)


def get_all_packs() -> list[dict]:
    """Retourne la liste de tous les packs disponibles.
    
    Returns:
        Liste des packs triés par nombre de crédits croissant
    """
    return list(OFFICIAL_PACKS.values())


def get_pack_price(pack_id: str) -> int:
    """Retourne le prix en FCFA d'un pack.
    
    Args:
        pack_id: Identifiant du pack
    
    Returns:
        Prix en FCFA ou 0 si pack introuvable
    """
    pack = get_pack_by_id(pack_id)
    return pack["amount_fcfa"] if pack else 0


def get_pack_credits(pack_id: str) -> int:
    """Retourne le nombre de crédits d'un pack.
    
    Args:
        pack_id: Identifiant du pack
    
    Returns:
        Nombre de crédits ou 0 si pack introuvable
    """
    pack = get_pack_by_id(pack_id)
    return pack["credits"] if pack else 0


def format_price_fcfa(amount: int) -> str:
    """Formate un montant en FCFA lisible.
    
    Args:
        amount: Montant en FCFA (entier)
    
    Returns:
        Chaîne formatée (ex: "2 500 F CFA")
    """
    # Ajouter espaces milliers
    amount_str = f"{amount:,}".replace(",", " ")
    return f"{amount_str} F CFA"


# ─── VALIDATION COHÉRENCE ────────────────────────────────────────────────────

def validate_pricing_consistency() -> list[str]:
    """Vérifie la cohérence des tarifs définis.
    
    Règles :
    - Prix unitaire doit décroître avec volume
    - Économies doivent être croissantes
    - Montants doivent correspondre aux settings
    
    Returns:
        Liste des erreurs détectées (vide si tout OK)
    """
    errors = []
    
    packs_sorted = sorted(OFFICIAL_PACKS.values(), key=lambda p: p["credits"])
    
    for i in range(len(packs_sorted) - 1):
        current = packs_sorted[i]
        next_pack = packs_sorted[i + 1]
        
        # Prix unitaire doit décroître
        if current["unit_price_fcfa"] < next_pack["unit_price_fcfa"]:
            errors.append(
                f"{next_pack['id']} a un prix unitaire ({next_pack['unit_price_fcfa']} F) "
                f"supérieur à {current['id']} ({current['unit_price_fcfa']} F)"
            )
        
        # Économies doivent croître
        if current["savings_percent"] > next_pack["savings_percent"]:
            errors.append(
                f"{next_pack['id']} a moins d'économies ({next_pack['savings_percent']}%) "
                f"que {current['id']} ({current['savings_percent']}%)"
            )
    
    # Vérifier correspondance avec settings
    expected_values = {
        "pack_1": (1, settings.CREDIT_PACK_1_FCFA),
        "pack_5": (5, settings.CREDIT_PACK_5_FCFA),
        "pack_10": (10, settings.CREDIT_PACK_10_FCFA),
        "pack_25": (25, settings.CREDIT_PACK_25_FCFA),
    }
    
    for pack_id, (expected_credits, expected_amount) in expected_values.items():
        pack = OFFICIAL_PACKS.get(pack_id)
        if pack:
            if pack["credits"] != expected_credits:
                errors.append(
                    f"{pack_id} : credits={pack['credits']} attendu {expected_credits}"
                )
            if pack["amount_fcfa"] != expected_amount:
                errors.append(
                    f"{pack_id} : amount={pack['amount_fcfa']} attendu {expected_amount} (settings)"
                )
    
    return errors


# Validation au chargement du module
_validation_errors = validate_pricing_consistency()
if _validation_errors:
    import logging
    logger = logging.getLogger("surcheck.pricing")
    logger.error("⚠️ INCOHÉRENCES DÉTECTÉES DANS LES TARIFS:")
    for error in _validation_errors:
        logger.error(f"  - {error}")
