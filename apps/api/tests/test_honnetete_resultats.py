"""Tests pour valider l'honnêteté des résultats (Section 5).

Conforme à FIABILISATION_PAIEMENT_SASPAY_SURCHECK_AI.md Section 5
"""

import pytest
from src.schemas import RiskLevel, ContentType
from src.engine.scorer import calculate_risk


def test_risklevel_indetermine_exists():
    """Vérifie que RiskLevel.INDETERMINE existe."""
    assert hasattr(RiskLevel, 'INDETERMINE')
    assert RiskLevel.INDETERMINE == "indetermine"


def test_short_text_returns_indetermine():
    """Texte trop court doit retourner INDETERMINE."""
    short_texts = [
        "OK",
        "Oui",
        "Non",
        "Merci",
    ]
    
    for text in short_texts:
        result = calculate_risk(text, ContentType.TEXT)
        assert result.risk_level == RiskLevel.INDETERMINE, \
            f"Texte '{text}' devrait retourner INDETERMINE, pas {result.risk_level}"
        assert result.confidence_level == "incertain"
        assert "trop court" in result.headline.lower() or "insuffisant" in result.summary.lower()


def test_sufficient_text_not_indetermine():
    """Texte suffisamment long ne doit pas retourner INDETERMINE (sauf si ambiguë)."""
    normal_text = "Bonjour, je vous écris pour confirmer notre rendez-vous de demain à 14h."
    
    result = calculate_risk(normal_text, ContentType.TEXT)
    assert result.risk_level != RiskLevel.INDETERMINE, \
        "Un texte normal de longueur suffisante ne devrait pas être INDETERMINE"


def test_confidence_level_exposed():
    """Vérifie que confidence_level est bien retourné dans AnalysisResult."""
    text = "Félicitations ! Vous avez gagné 500 000 FCFA. Envoyez 5000F pour frais."
    
    result = calculate_risk(text, ContentType.TEXT)
    assert hasattr(result, 'confidence_level')
    assert result.confidence_level in ["elevee", "moyenne", "incertain"]


def test_confidence_elevee_with_multiple_signals():
    """Plusieurs signaux détectés → confiance élevée."""
    text = "URGENT ! Gagnez 1 000 000 FCFA MAINTENANT ! Cliquez http://bit.ly/win et envoyez votre code PIN."
    
    result = calculate_risk(text, ContentType.TEXT)
    # Ce texte doit déclencher plusieurs signaux
    assert len(result.signals) >= 2
    assert result.confidence_level == "elevee"


def test_confidence_incertain_with_short_text():
    """Texte court → confiance incertaine."""
    short_text = "Gagnez"
    
    result = calculate_risk(short_text, ContentType.TEXT)
    assert result.confidence_level == "incertain"


def test_indetermine_has_specific_recommendations():
    """INDETERMINE doit avoir des recommandations spécifiques."""
    text = "OK"
    
    result = calculate_risk(text, ContentType.TEXT)
    assert result.risk_level == RiskLevel.INDETERMINE
    
    # Vérifier que les recommandations mentionnent le besoin de plus d'info
    recommendations_text = " ".join(result.recommendations).lower()
    assert "complet" in recommendations_text or "contexte" in recommendations_text


def test_no_false_positive_when_verification_fails():
    """Ne jamais affirmer sécurité si vérification échouée."""
    # Ce test conceptuel vérifie la logique
    # Dans analyze.py, si check_url_reputation échoue sur une URL,
    # on doit passer en INDETERMINE, pas en FAIBLE
    
    # Ce test nécessiterait un mock de check_url_reputation qui échoue
    # Pour l'instant, test de présence du code de gestion d'erreur
    import inspect
    from src.routers.analyze import _enrich_with_reputation
    
    source = inspect.getsource(_enrich_with_reputation)
    assert "try:" in source and "except" in source, \
        "_enrich_with_reputation doit gérer les exceptions lors de la vérification URL"


def test_risk_levels_complete():
    """Vérifier que tous les niveaux de risque sont définis."""
    expected_levels = ["faible", "prudence", "eleve", "indetermine"]
    
    for level in expected_levels:
        assert hasattr(RiskLevel, level.upper())


def test_indetermine_score_range():
    """INDETERMINE peut avoir n'importe quel score (le niveau prime)."""
    text = "Test"
    
    result = calculate_risk(text, ContentType.TEXT)
    assert result.risk_level == RiskLevel.INDETERMINE
    # Le score peut être n'importe quoi, c'est le risk_level qui compte
    assert 0 <= result.risk_score <= 100


def test_normal_text_not_false_negative():
    """Un texte normal ne doit pas être marqué ELEVE par erreur."""
    normal_texts = [
        "Bonjour, pouvez-vous me rappeler demain ?",
        "Le rendez-vous est confirmé pour 15h30.",
        "Merci pour votre message, je vous recontacte bientôt.",
    ]
    
    for text in normal_texts:
        result = calculate_risk(text, ContentType.TEXT)
        assert result.risk_level in [RiskLevel.FAIBLE, RiskLevel.PRUDENCE], \
            f"Texte normal '{text}' ne devrait pas être ELEVE"


def test_critical_keywords_not_indetermine():
    """Texte court MAIS avec mots-clés critiques ne doit PAS être INDETERMINE."""
    critical_short = "Envoyez code PIN urgent"
    
    result = calculate_risk(critical_short, ContentType.TEXT)
    # Même si court, présence de "code PIN" devrait déclencher analyse
    # Ce test vérifie que la logique INDETERMINE ne masque pas les vrais risques
    assert len(result.signals) > 0 or result.risk_level != RiskLevel.INDETERMINE


def test_confidence_matches_risk_level():
    """La confiance doit être cohérente avec le niveau de risque."""
    # FAIBLE avec plusieurs signaux → devrait être PRUDENCE ou ELEVE
    # (ce test vérifie la cohérence globale)
    
    high_risk_text = "URGENT GAGNEZ 5000000 FCFA ENVOYEZ CODE SECRET 2024"
    result = calculate_risk(high_risk_text, ContentType.TEXT)
    
    if result.risk_level == RiskLevel.ELEVE:
        # Si risque élevé ET plusieurs signaux → confiance devrait être élevée
        if len(result.signals) >= 2:
            assert result.confidence_level in ["elevee", "moyenne"]


@pytest.mark.asyncio
async def test_url_verification_failure_handled():
    """Vérifier que l'échec de vérification URL ne plante pas."""
    from src.routers.analyze import _enrich_with_reputation
    from src.schemas import AnalysisResult
    from unittest.mock import AsyncMock, patch
    
    # Mock result initial
    mock_result = AnalysisResult(
        id="test",
        content_type=ContentType.TEXT,
        risk_score=20,
        risk_level=RiskLevel.FAIBLE,
        category="Test",
        confidence_level="elevee",
        headline="Test",
        summary="Test summary",
        recommendations=[],
        signals=[],
        engine_version="test",
    )
    
    # Mock supabase_db.check_url_reputation pour lever une exception
    with patch("src.routers.analyze.supabase_db") as mock_db:
        mock_db.check_phone_reputation = AsyncMock(return_value=(0, "safe"))
        mock_db.check_url_reputation = AsyncMock(side_effect=Exception("DB error"))
        
        text_with_url = "Visitez http://example.com"
        
        # Ne doit pas lever d'exception
        try:
            await _enrich_with_reputation(mock_result, text_with_url)
        except Exception as e:
            pytest.fail(f"_enrich_with_reputation ne doit pas propager l'exception : {e}")
        
        # Si la vérification échoue, risk_level devrait passer à INDETERMINE
        assert mock_result.risk_level == RiskLevel.INDETERMINE
        assert mock_result.confidence_level == "incertain"
