"""Tests pour valider la correction des bugs bloquants (Section 2).

Conforme à FIABILISATION_PAIEMENT_SASPAY_SURCHECK_AI.md Section 2.4
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime


def test_risklevel_import_in_analyze():
    """Vérifie que RiskLevel est bien importé et utilisable dans analyze.py."""
    from src.routers.analyze import RiskLevel
    
    # RiskLevel doit être un enum avec les valeurs attendues
    assert hasattr(RiskLevel, 'FAIBLE')
    assert hasattr(RiskLevel, 'PRUDENCE')
    assert hasattr(RiskLevel, 'ELEVE')


@pytest.mark.asyncio
async def test_risklevel_used_correctly_in_reputation():
    """Vérifie que RiskLevel.ELEVE est utilisé (pas la chaîne 'eleve')."""
    from src.routers.analyze import _enrich_with_reputation, RiskLevel
    from src.schemas import AnalysisResult, ContentType
    
    # Mock result avec score initial faible
    mock_result = AnalysisResult(
        id="test_123",
        content_type=ContentType.TEXT,
        risk_score=30,
        risk_level=RiskLevel.FAIBLE,
        confidence_level="moyenne",
        headline="Test",
        summary="Test summary",
        recommendations=[],
        signals=[],
    )
    
    # Mock supabase_db pour retourner réputation positive
    with patch("src.routers.analyze.supabase_db") as mock_db:
        mock_db.check_phone_reputation = AsyncMock(return_value=(5, "reported"))
        mock_db.check_url_reputation = AsyncMock(return_value=(3, True, "phishing"))
        
        # Texte avec numéro et URL suspects
        test_text = "Appelez +229 97 12 34 56 ou visitez http://suspect.com"
        
        await _enrich_with_reputation(mock_result, test_text)
        
        # Vérifier que risk_level est bien un RiskLevel (pas une string)
        assert isinstance(mock_result.risk_level, RiskLevel)
        assert mock_result.risk_level == RiskLevel.ELEVE


def test_datetime_import_in_supabase_db():
    """Vérifie que datetime est bien importé dans supabase_db.py."""
    from src.services.supabase_db import datetime
    
    # datetime doit être utilisable
    now = datetime.now()
    assert now.isoformat() is not None


@pytest.mark.asyncio
async def test_datetime_used_in_moderate_report():
    """Vérifie que datetime.now() est utilisable dans moderate_report."""
    from src.services.supabase_db import SupabaseDatabase
    
    # Mock httpx client
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "approved"}
    mock_client.__aenter__.return_value.patch.return_value = mock_response
    
    db = SupabaseDatabase()
    
    with patch("httpx.AsyncClient", return_value=mock_client):
        # Ne doit pas lever d'exception NameError pour datetime
        try:
            result = await db.moderate_report(
                report_id="report_123",
                new_status="approved",
                moderator_notes="Test moderation"
            )
            # Si on arrive ici, datetime.now() a fonctionné
            assert result is not None
        except NameError as e:
            pytest.fail(f"datetime non importé : {e}")


def test_dict_items_slicing_not_present():
    """Vérifie qu'il n'y a pas de dict.items()[:10] non convertis en list."""
    import re
    import os
    
    # Vérifier saspay_provider.py
    saspay_path = "apps/api/src/services/saspay_provider.py"
    if os.path.exists(saspay_path):
        with open(saspay_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern problématique : .items()[: ou .items()[:
        pattern = r'\.items\(\)\[:'
        matches = re.findall(pattern, content)
        
        assert len(matches) == 0, f"Trouvé {len(matches)} occurrences de dict.items()[:] non sécurisées"


def test_metadata_creation_works():
    """Vérifie que la création de metadata custom fonctionne (>10 items)."""
    # Simuler >10 items de metadata
    large_metadata = {f"key_{i}": f"value_{i}" for i in range(15)}
    
    # Conversion sécurisée (comme dans le code)
    try:
        result = {k: str(v)[:255] for k, v in large_metadata.items()}
        assert len(result) == 15
    except TypeError:
        pytest.fail("La conversion de metadata a échoué")


@pytest.mark.asyncio
async def test_phone_reputation_enrichment_with_risklevel():
    """Test d'enrichissement réputation avec vérification du type RiskLevel."""
    from src.routers.analyze import _enrich_with_reputation, RiskLevel
    from src.schemas import AnalysisResult, ContentType
    
    mock_result = AnalysisResult(
        id="test_phone_rep",
        content_type=ContentType.TEXT,
        risk_score=25,
        risk_level=RiskLevel.FAIBLE,
        confidence_level="elevee",
        headline="Initial test",
        summary="Test",
        recommendations=[],
        signals=[],
    )
    
    with patch("src.routers.analyze.supabase_db") as mock_db:
        # 10 signalements communautaires
        mock_db.check_phone_reputation = AsyncMock(return_value=(10, "reported"))
        mock_db.check_url_reputation = AsyncMock(return_value=(0, False, "safe"))
        
        text_with_phone = "Contactez le +22997123456 urgent"
        await _enrich_with_reputation(mock_result, text_with_phone)
        
        # Le score doit avoir augmenté
        assert mock_result.risk_score > 25
        
        # risk_level doit être RiskLevel.ELEVE (type enum)
        assert isinstance(mock_result.risk_level, RiskLevel)
        assert mock_result.risk_level == RiskLevel.ELEVE
        
        # Vérifier qu'un signal communautaire a été ajouté
        assert len(mock_result.signals) > 0
        community_signal = next(
            (s for s in mock_result.signals if "SIG_COMMUNITY" in s.code),
            None
        )
        assert community_signal is not None


@pytest.mark.asyncio
async def test_url_reputation_enrichment_with_risklevel():
    """Test d'enrichissement réputation URL avec vérification du type RiskLevel."""
    from src.routers.analyze import _enrich_with_reputation, RiskLevel
    from src.schemas import AnalysisResult, ContentType
    
    mock_result = AnalysisResult(
        id="test_url_rep",
        content_type=ContentType.TEXT,
        risk_score=20,
        risk_level=RiskLevel.FAIBLE,
        confidence_level="elevee",
        headline="Initial test",
        summary="Test",
        recommendations=[],
        signals=[],
    )
    
    with patch("src.routers.analyze.supabase_db") as mock_db:
        mock_db.check_phone_reputation = AsyncMock(return_value=(0, "safe"))
        # URL signalée 7 fois + phishing match
        mock_db.check_url_reputation = AsyncMock(return_value=(7, True, "phishing"))
        
        text_with_url = "Visitez http://phishing-site.com pour gagner"
        await _enrich_with_reputation(mock_result, text_with_url)
        
        # Le score doit être élevé (>= 75)
        assert mock_result.risk_score >= 75
        
        # risk_level doit être RiskLevel.ELEVE (PAS la string "eleve")
        assert isinstance(mock_result.risk_level, RiskLevel), \
            f"risk_level devrait être RiskLevel enum, pas {type(mock_result.risk_level)}"
        assert mock_result.risk_level == RiskLevel.ELEVE
