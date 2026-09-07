"""Tests unitaires automatisés pour le moteur d'analyse SûrCheck AI.
Vérifie la calibration, la détection des scénarios béninois et l'absence de faux positifs.
"""

import pytest
from src.engine.normalizer import normalize_text, strip_accents
from src.engine.extractor import extract_phone_numbers, extract_urls
from src.engine.rules import evaluate_rules
from src.engine.scorer import calculate_risk
from src.schemas import RiskLevel, ContentType
from src.engine.reputation import normalize_phone_number, hash_phone_number


def test_normalizer():
    raw = "URGENT: Dépôt Moov @ Cotonou !!"
    normalized = normalize_text(raw, apply_leet=True)
    assert "urgent" in normalized
    assert "moov" in normalized


def test_extractor_benin_phone():
    text = "Veuillez contacter le service client au +229 97 12 34 56 ou par Moov au 0195001122."
    phones = extract_phone_numbers(text)
    assert len(phones) >= 1
    normalized = normalize_phone_number(phones[0])
    assert normalized.startswith("+229")


def test_extractor_shortened_url():
    text = "Votre colis est bloqué, cliquez sur https://bit.ly/momo-bj pour payer."
    urls = extract_urls(text)
    assert len(urls) == 1
    assert urls[0]["is_shortener"] is True


def test_high_risk_otp_demand():
    """Un message demandant un code secret doit être classé en risque Élevé."""
    text = "Bonjour, nous mettons à jour votre compte MTN Mobile Money. Envoyez votre code secret immédiatement."
    result = calculate_risk(text, ContentType.TEXT)
    assert result.risk_score >= 70
    assert result.risk_level == RiskLevel.ELEVE
    assert any(s.code == "RULE_OTP_PIN" for s in result.signals)
    assert "code secret" in result.summary.lower() or "critique" in result.summary.lower()


def test_high_risk_false_transfer():
    """Un message d'erreur de transfert demandant renvoi d'argent."""
    text = "Urgent: Erreur de transfert Moov Money de 50.000 FCFA. Veuillez renvoyer les fonds au 95000000 tout de suite."
    result = calculate_risk(text, ContentType.TEXT)
    assert result.risk_score >= 70
    assert result.risk_level == RiskLevel.ELEVE


def test_low_risk_legitimate_message():
    """Un message de la vie quotidienne sans demande d'argent ni urgence doit être Faible."""
    text = "Salut Paul, je viens d'arriver au bureau. On se voit pour le déjeuner à midi à Cadjèhoun ?"
    result = calculate_risk(text, ContentType.TEXT)
    assert result.risk_score <= 25
    assert result.risk_level == RiskLevel.FAIBLE
    assert len(result.signals) == 0


def test_phone_hashing_consistency():
    """Vérifie que le hachage d'un numéro est reproductible et n'expose pas le numéro en clair."""
    phone = "+22997123456"
    hash1 = hash_phone_number(phone)
    hash2 = hash_phone_number(phone)
    assert hash1 == hash2
    assert phone not in hash1
    assert len(hash1) == 64
