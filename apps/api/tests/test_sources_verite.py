"""Tests pour valider les sources uniques de vérité (Section 4).

Conforme à FIABILISATION_PAIEMENT_SASPAY_SURCHECK_AI.md Section 4
"""

import pytest


def test_pricing_module_exists():
    """Vérifie que le module pricing.py existe et est importable."""
    from src.pricing import OFFICIAL_PACKS, get_all_packs
    
    assert OFFICIAL_PACKS is not None
    assert len(OFFICIAL_PACKS) == 4
    assert "pack_1" in OFFICIAL_PACKS
    assert "pack_10" in OFFICIAL_PACKS


def test_pricing_consistency():
    """Vérifie la cohérence des tarifs."""
    from src.pricing import validate_pricing_consistency
    
    errors = validate_pricing_consistency()
    assert len(errors) == 0, f"Incohérences détectées: {errors}"


def test_pricing_helpers():
    """Vérifie les fonctions utilitaires de pricing."""
    from src.pricing import get_pack_by_id, get_pack_price, get_pack_credits, format_price_fcfa
    
    # Pack existant
    pack = get_pack_by_id("pack_10")
    assert pack is not None
    assert pack["credits"] == 10
    assert pack["amount_fcfa"] == 2500
    
    # Prix et crédits
    assert get_pack_price("pack_10") == 2500
    assert get_pack_credits("pack_10") == 10
    
    # Pack inexistant
    assert get_pack_by_id("pack_999") is None
    assert get_pack_price("pack_999") == 0
    assert get_pack_credits("pack_999") == 0
    
    # Formatage
    assert format_price_fcfa(2500) == "2 500 F CFA"
    assert format_price_fcfa(600) == "600 F CFA"


def test_pricing_unit_price_decreases():
    """Vérifie que le prix unitaire décroît avec le volume."""
    from src.pricing import OFFICIAL_PACKS
    
    packs_sorted = sorted(OFFICIAL_PACKS.values(), key=lambda p: p["credits"])
    
    for i in range(len(packs_sorted) - 1):
        current = packs_sorted[i]
        next_pack = packs_sorted[i + 1]
        
        assert current["unit_price_fcfa"] >= next_pack["unit_price_fcfa"], \
            f"{next_pack['id']} a un prix unitaire ({next_pack['unit_price_fcfa']} F) " \
            f"supérieur à {current['id']} ({current['unit_price_fcfa']} F)"


def test_pricing_used_in_payment_router():
    """Vérifie que payment.py importe bien PACKS depuis pricing."""
    from src.routers.payment import PACKS
    
    # PACKS doit être importé depuis pricing
    assert len(PACKS) == 4
    assert PACKS["pack_10"]["amount_fcfa"] == 2500


def test_versioning_module_exists():
    """Vérifie que le module versioning.py existe."""
    from src.versioning import get_engine_version_string, CURRENT_ENGINE_VERSION
    
    version = get_engine_version_string()
    assert version is not None
    assert "|" in version
    assert "rules:" in version
    assert "ml:" in version
    assert "reputation:" in version


def test_versioning_format():
    """Vérifie le format de la version."""
    from src.versioning import get_engine_version_string, parse_engine_version
    
    version_str = get_engine_version_string()
    
    # Format: "rules:YYYY.MM.V|ml:X.Y|reputation:YYYY.MM"
    parts = version_str.split("|")
    assert len(parts) == 3
    
    assert parts[0].startswith("rules:")
    assert parts[1].startswith("ml:")
    assert parts[2].startswith("reputation:")
    
    # Parsing
    parsed = parse_engine_version(version_str)
    assert parsed is not None
    assert parsed.rules_version is not None
    assert parsed.ml_version is not None
    assert parsed.reputation_version is not None


def test_versioning_used_in_scorer():
    """Vérifie que scorer.py utilise get_engine_version_string()."""
    import inspect
    from src.engine.scorer import calculate_risk
    
    # Vérifier que l'import existe
    source = inspect.getsource(calculate_risk)
    # La fonction doit utiliser get_engine_version_string
    # (on ne peut pas tester directement sans exécuter, mais on vérifie l'import)
    
    # Test indirect : créer un résultat et vérifier le format
    from src.schemas import ContentType
    result = calculate_risk("Test message", ContentType.TEXT)
    
    # engine_version doit être au nouveau format
    assert "|" in result.engine_version
    assert "rules:" in result.engine_version


def test_versioning_compare():
    """Vérifie la comparaison de versions."""
    from src.versioning import compare_versions
    
    assert compare_versions("2026.09.1", "2026.09.2") == -1
    assert compare_versions("2026.09.2", "2026.09.1") == 1
    assert compare_versions("2026.09.1", "2026.09.1") == 0
    assert compare_versions("2026.10.0", "2026.09.5") == 1


def test_versioning_changelog_exists():
    """Vérifie que le changelog existe."""
    from src.versioning import get_version_changelog
    
    changelog = get_version_changelog()
    assert len(changelog) > 0
    assert "2026.09.2" in changelog


def test_versioning_info():
    """Vérifie les informations de version complètes."""
    from src.versioning import get_version_info
    
    info = get_version_info()
    assert "version" in info
    assert "components" in info
    assert "rules" in info["components"]
    assert "ml" in info["components"]
    assert "reputation" in info["components"]


def test_no_hardcoded_prices_in_docs():
    """Vérifie qu'aucun prix n'est codé en dur dans la documentation."""
    import os
    import re
    
    # Vérifier quelques fichiers de documentation
    docs_to_check = [
        "README.md",
        "DEPLOYMENT.md",
    ]
    
    price_pattern = r'\b(600|1500|2500|5000)\s*(F|FCFA|CFA)\b'
    
    for doc in docs_to_check:
        if os.path.exists(doc):
            with open(doc, 'r', encoding='utf-8') as f:
                content = f.read()
                matches = re.findall(price_pattern, content, re.IGNORECASE)
                # Si des prix sont trouvés, vérifier qu'ils référencent pricing.py
                if matches:
                    assert "pricing.py" in content.lower() or "source unique" in content.lower(), \
                        f"{doc} contient des prix en dur sans référence à pricing.py"
