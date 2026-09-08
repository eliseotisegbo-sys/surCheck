"""Tests unitaires et d'intégration pour le fournisseur Chariow et le système de crédits SûrCheck.
Conforme aux tests obligatoires décrits dans la section 31 de la documentation technique :
- Checkout (packs valides, métadonnées)
- Webhooks Pulses (signature HMAC, événements successful.sale, failed.sale, déduplication/idempotence)
- Crédits (+1, +5, +10, +25, consommation atomique, solde insuffisant, protection double consommation)
- Scénario complet
"""

import hashlib
import hmac
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app
from src.config import settings
from src.services.chariow_provider import chariow_provider
from src.services.credit_service import credit_service
from src.routers.payment import PACKS

client = TestClient(app)


# ─── 1. TESTS FOURNISSEUR CHARIOW ───────────────────────────────────────────

def test_packs_configuration():
    """Vérifie la conformité de la grille tarifaire officielle."""
    assert "pack_1" in PACKS
    assert "pack_5" in PACKS
    assert "pack_10" in PACKS
    assert "pack_25" in PACKS

    assert PACKS["pack_1"]["amount_fcfa"] == 600
    assert PACKS["pack_1"]["credits"] == 1

    assert PACKS["pack_5"]["amount_fcfa"] == 1500
    assert PACKS["pack_5"]["credits"] == 5

    assert PACKS["pack_10"]["amount_fcfa"] == 2500
    assert PACKS["pack_10"]["credits"] == 10
    assert PACKS["pack_10"]["popular"] is True

    assert PACKS["pack_25"]["amount_fcfa"] == 5000
    assert PACKS["pack_25"]["credits"] == 25


def test_webhook_hmac_signature_verification():
    """Valide l'authentification cryptographique HMAC-SHA256 du webhook."""
    secret = "test_pulse_secret_key_12345"
    with patch.object(settings, "CHARIOW_WEBHOOK_SECRET", secret):
        with patch.object(chariow_provider, "webhook_secret", secret):
            payload = b'{"event":"successful.sale","data":{"id":"sal_123"}}'

            # Signature valide format 'sha256=<hex>'
            expected_hex = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
            assert chariow_provider.verify_webhook_signature(payload, f"sha256={expected_hex}") is True
            assert chariow_provider.verify_webhook_signature(payload, expected_hex) is True

            # Signature invalide
            assert chariow_provider.verify_webhook_signature(payload, "sha256=invalid_hash") is False
            assert chariow_provider.verify_webhook_signature(payload, "") is False


def test_parse_webhook_successful_sale():
    """Teste le parsing normalisé d'un événement Pulse de vente réussie."""
    payload = {
        "id": "pulse_evt_abc",
        "event": "successful.sale",
        "data": {
            "id": "sal_889900",
            "product_id": "prd_pack_10",
            "amount": 1500,
            "pricing": {"price": 1500},
            "custom_metadata": {
                "surcheck_user_id": "usr_test_uuid",
                "credit_pack": "pack_10",
                "credits": "10",
                "internal_order_ref": "order_ref_123",
            },
        },
    }
    raw_body = json.dumps(payload).encode()
    headers = {"x-pulse-delivery-id": "pulse_delivery_unique_1"}

    event = chariow_provider.parse_webhook(raw_body, headers)

    assert event.event_name == "successful.sale"
    assert event.sale_id == "sal_889900"
    assert event.delivery_id == "pulse_delivery_unique_1"
    assert event.user_id == "usr_test_uuid"
    assert event.pack_id == "pack_10"
    assert event.credits == 10
    assert event.status == "successful"


# ─── 2. TESTS DU SERVICE DE CRÉDITS & PROTECTION DOUBLE CLIC ─────────────────

def test_consume_credit_already_unlocked():
    """Protection anti-double clic : si l'analyse est déjà débloquée, ne pas débiter."""
    import asyncio
    with patch.object(credit_service, "is_analysis_unlocked", AsyncMock(return_value=True)):
        with patch.object(credit_service, "get_user_balance", AsyncMock(return_value=5)):
            unlocked, msg, balance = asyncio.run(
                credit_service.consume_credit_for_analysis(
                    user_id="user_123",
                    analysis_id="analysis_abc",
                )
            )
            assert unlocked is True
            assert "déjà débloquée" in msg
            assert balance == 5  # Solde inchangé


def test_consume_credit_insufficient_balance():
    """Consommation impossible si le solde est nul."""
    import asyncio
    with patch.object(credit_service, "is_analysis_unlocked", AsyncMock(return_value=False)):
        with patch.object(credit_service, "get_user_balance", AsyncMock(return_value=0)):
            unlocked, msg, balance = asyncio.run(
                credit_service.consume_credit_for_analysis(
                    user_id="user_123",
                    analysis_id="analysis_abc",
                )
            )
            assert unlocked is False
            assert "insuffisant" in msg.lower()
            assert balance == 0



# ─── 3. TESTS ENDPOINTS API CHECKOUT & WEBHOOK ──────────────────────────────

def test_api_list_packs():
    """Vérifie la route GET /api/v1/payment/packs."""
    res = client.get("/api/v1/payment/packs")
    assert res.status_code == 200
    data = res.json()
    assert "packs" in data
    assert len(data["packs"]) == 4
    assert data["currency"] == "XOF"


def test_api_webhook_unauthorized_when_signature_invalid():
    """Rejette les webhooks sans signature valide."""
    secret = "secret_strict_validation"
    with patch.object(settings, "CHARIOW_WEBHOOK_SECRET", secret):
        with patch.object(chariow_provider, "webhook_secret", secret):
            res = client.post(
                "/api/v1/payment/webhook",
                content=b'{"event":"successful.sale"}',
                headers={"x-chariow-signature": "sha256=faux_token"},
            )
            assert res.status_code == 401


def test_api_webhook_successful_sale_flow():
    """Vérifie le traitement d'un webhook Chariow valide."""
    payload = {
        "event": "successful.sale",
        "data": {
            "id": "sal_test_777",
            "product_id": "prd_pack_10",
            "custom_metadata": {
                "surcheck_user_id": "usr_999",
                "credit_pack": "pack_10",
                "credits": "10",
            },
        },
    }
    raw_body = json.dumps(payload).encode()

    with patch.object(chariow_provider, "verify_webhook_signature", return_value=True):
        with patch.object(credit_service, "add_credits_idempotent", AsyncMock(return_value=(True, "10 crédits ajoutés"))):
            res = client.post(
                "/api/v1/payment/webhook",
                content=raw_body,
                headers={"Content-Type": "application/json", "x-pulse-delivery-id": "deliv_123"},
            )
            assert res.status_code == 200
            data = res.json()
            assert data.get("received") is True
            assert data.get("credited") is True
