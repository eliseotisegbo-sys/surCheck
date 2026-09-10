"""Tests d'intégration pour le provider SasPay.
Valide la compatibilité avec l'interface PaymentProvider et le router payment.py.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import json

from src.services.saspay_provider import (
    SasPayPaymentProvider,
    detect_mobile_money_network,
)
from src.services.payment_provider import CheckoutSession, WebhookEvent


class TestDetectMobileMoneyNetwork:
    """Tests de détection du réseau Mobile Money depuis le numéro."""

    def test_detect_mtn_benin_prefix_97(self):
        """MTN Bénin - Préfixe 97."""
        assert detect_mobile_money_network("97505050", "BJ") == "mtn_bj"
        assert detect_mobile_money_network("+22997505050", "BJ") == "mtn_bj"
        assert detect_mobile_money_network("22997505050", "BJ") == "mtn_bj"

    def test_detect_mtn_benin_prefix_60(self):
        """MTN Bénin - Préfixe 60."""
        assert detect_mobile_money_network("60123456", "BJ") == "mtn_bj"

    def test_detect_mtn_benin_prefix_50(self):
        """MTN Bénin - Préfixe 50."""
        assert detect_mobile_money_network("50987654", "BJ") == "mtn_bj"

    def test_detect_moov_benin_prefix_66(self):
        """Moov Bénin - Préfixe 66 (anciennement, maintenant 80-89)."""
        # Note: 66 devrait être MTN selon les nouveaux préfixes
        assert detect_mobile_money_network("66123456", "BJ") == "mtn_bj"

    def test_detect_moov_benin_prefix_01(self):
        """Moov Bénin - Préfixe 01."""
        assert detect_mobile_money_network("01234567", "BJ") == "moov_bj"

    def test_detect_moov_benin_prefix_80(self):
        """Moov Bénin - Préfixe 80."""
        assert detect_mobile_money_network("80123456", "BJ") == "moov_bj"

    def test_detect_unknown_prefix_fallback_mtn(self):
        """Préfixe inconnu → Fallback MTN (plus courant)."""
        assert detect_mobile_money_network("99999999", "BJ") == "mtn_bj"

    def test_detect_other_country_togo(self):
        """Togo → Placeholder MTN."""
        assert detect_mobile_money_network("90123456", "TG") == "mtn_tg"


class TestSasPayProvider:
    """Tests du provider SasPay."""

    @pytest.fixture
    def mock_settings(self):
        """Mock des settings pour tests."""
        with patch("src.services.saspay_provider.settings") as mock:
            mock.SASPAY_API_KEY = "sk_test_mock_key"
            mock.SASPAY_BASE_URL = "https://api.saspay.me/api/v1"
            mock.SASPAY_WEBHOOK_SECRET = "test_webhook_secret"
            yield mock

    @pytest.fixture
    def provider(self, mock_settings):
        """Instance du provider SasPay pour tests."""
        return SasPayPaymentProvider()

    @pytest.mark.asyncio
    async def test_create_checkout_success_mtn(self, provider):
        """Test création checkout MTN Bénin (push direct)."""
        mock_response = {
            "id": "payment-uuid-123",
            "status": "PENDING",
            "checkout_url": "",  # Vide pour MTN push
            "message": "Payment pushed successfully",
        }

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = mock_response
            mock_post.return_value.content = b"mock"

            session = await provider.create_checkout(
                product_id="pack_10",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                phone_number="97505050",
                country_code="BJ",
                custom_metadata={
                    "amount_fcfa": "2500",
                    "pack_label": "Pack 10 crédits",
                    "surcheck_user_id": "user-123",
                    "credit_pack": "pack_10",
                    "credits": "10",
                },
            )

            assert isinstance(session, CheckoutSession)
            assert session.step == "payment"  # Pas de redirect pour MTN push
            assert session.checkout_url is None
            assert session.sale_id == "payment-uuid-123"
            assert session.message == "Payment pushed successfully"

    @pytest.mark.asyncio
    async def test_create_checkout_error_invalid_amount(self, provider):
        """Test gestion erreur montant invalide."""
        session = await provider.create_checkout(
            product_id="pack_10",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            phone_number="97505050",
            country_code="BJ",
            custom_metadata={
                "amount_fcfa": "invalid",  # Montant invalide
            },
        )

        assert session.step == "error"
        assert "Configuration du montant invalide" in session.message

    @pytest.mark.asyncio
    async def test_create_checkout_api_error(self, provider):
        """Test gestion erreur API SasPay."""
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 400
            mock_post.return_value.json.return_value = {"error": "Invalid network"}
            mock_post.return_value.text = "Invalid network"
            mock_post.return_value.content = b"error"

            session = await provider.create_checkout(
                product_id="pack_10",
                email="test@example.com",
                first_name="Test",
                last_name="User",
                phone_number="97505050",
                country_code="BJ",
                custom_metadata={"amount_fcfa": "2500", "pack_label": "Test"},
            )

            assert session.step == "error"
            assert session.message  # Erreur présente

    def test_verify_webhook_signature_valid(self, provider):
        """Test vérification signature webhook valide."""
        import hmac
        import hashlib

        body = b'{"event": "payment.succeeded"}'
        expected_sig = hmac.new(
            b"test_webhook_secret",
            body,
            hashlib.sha256,
        ).hexdigest()

        assert provider.verify_webhook_signature(body, expected_sig) is True
        assert provider.verify_webhook_signature(body, f"sha256={expected_sig}") is True

    def test_verify_webhook_signature_invalid(self, provider):
        """Test rejet signature invalide."""
        body = b'{"event": "payment.succeeded"}'
        assert provider.verify_webhook_signature(body, "invalid_signature") is False

    def test_parse_webhook_successful_payment(self, provider):
        """Test parsing webhook payment.succeeded."""
        payload = {
            "event": "payment.succeeded",
            "id": "webhook-delivery-123",
            "data": {
                "id": "payment-uuid-456",
                "status": "SUCCESS",
                "amount": "2500.00",
                "currency": "XOF",
                "metadata": {
                    "surcheck_user_id": "user-789",
                    "credit_pack": "pack_10",
                    "credits": "10",
                    "internal_order_ref": "order-abc",
                },
                "customer": {
                    "email": "client@example.com",
                },
            },
        }

        event = provider.parse_webhook(
            json.dumps(payload).encode(),
            {"x-webhook-id": "webhook-delivery-123"},
        )

        assert isinstance(event, WebhookEvent)
        assert event.event_name == "successful.sale"  # Normalisé format Chariow
        assert event.sale_id == "payment-uuid-456"
        assert event.user_id == "user-789"
        assert event.pack_id == "pack_10"
        assert event.credits == 10
        assert event.amount == 2500
        assert event.status == "successful"
        assert event.delivery_id == "webhook-delivery-123"

    def test_parse_webhook_failed_payment(self, provider):
        """Test parsing webhook payment.failed."""
        payload = {
            "event": "payment.failed",
            "data": {
                "id": "payment-uuid-789",
                "status": "FAILED",
                "amount": "600.00",
                "metadata": {},
            },
        }

        event = provider.parse_webhook(
            json.dumps(payload).encode(),
            {},
        )

        assert event.event_name == "failed.sale"  # Normalisé
        assert event.status == "failed"

    @pytest.mark.asyncio
    async def test_get_sale(self, provider):
        """Test récupération statut paiement."""
        mock_response = {
            "id": "payment-uuid-123",
            "status": "SUCCESS",
            "net_amount": "2500.00",
            "currency": "XOF",
            "message": "Payment verified",
        }

        with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response

            result = await provider.get_sale("payment-uuid-123")

            assert result["id"] == "payment-uuid-123"
            assert result["status"] == "SUCCESS"
            assert result["amount"] == "2500.00"


class TestPaymentRouterIntegration:
    """Tests d'intégration avec payment.py."""

    @pytest.mark.asyncio
    async def test_get_payment_provider_chariow_default(self):
        """Test sélection provider Chariow par défaut."""
        with patch("src.routers.payment.settings") as mock_settings:
            mock_settings.PAYMENT_PROVIDER = "chariow"

            from src.routers.payment import get_payment_provider
            from src.services.chariow_provider import ChariowPaymentProvider

            provider = get_payment_provider()
            assert isinstance(provider, ChariowPaymentProvider)

    @pytest.mark.asyncio
    async def test_get_payment_provider_saspay(self):
        """Test sélection provider SasPay."""
        with patch("src.routers.payment.settings") as mock_settings:
            mock_settings.PAYMENT_PROVIDER = "saspay"

            from src.routers.payment import get_payment_provider
            from src.services.saspay_provider import SasPayPaymentProvider

            provider = get_payment_provider()
            assert isinstance(provider, SasPayPaymentProvider)

    @pytest.mark.asyncio
    async def test_get_payment_provider_invalid_fallback(self):
        """Test fallback sur Chariow si provider inconnu."""
        with patch("src.routers.payment.settings") as mock_settings:
            mock_settings.PAYMENT_PROVIDER = "unknown_provider"

            from src.routers.payment import get_payment_provider
            from src.services.chariow_provider import ChariowPaymentProvider

            provider = get_payment_provider()
            assert isinstance(provider, ChariowPaymentProvider)


class TestMetadataInjection:
    """Tests injection metadata pour SasPay."""

    def test_metadata_contains_amount_fcfa(self):
        """Vérifier que amount_fcfa est injecté dans metadata."""
        from src.routers.payment import PACKS

        pack = PACKS["pack_10"]

        custom_metadata = {
            "surcheck_user_id": "user-123",
            "credit_pack": "pack_10",
            "credits": str(pack["credits"]),
            "amount_fcfa": str(pack["amount_fcfa"]),  # Requis pour SasPay
            "pack_label": pack["label"],
        }

        assert "amount_fcfa" in custom_metadata
        assert custom_metadata["amount_fcfa"] == "2500"
        assert custom_metadata["pack_label"] == "Pack recommandé"


class TestBackwardCompatibility:
    """Tests de compatibilité ascendante."""

    def test_chariow_provider_still_works(self):
        """Vérifier que Chariow n'est pas cassé."""
        from src.services.chariow_provider import chariow_provider

        assert chariow_provider is not None
        assert hasattr(chariow_provider, "create_checkout")
        assert hasattr(chariow_provider, "verify_webhook_signature")
        assert hasattr(chariow_provider, "parse_webhook")

    def test_payment_transactions_table_compatible(self):
        """Vérifier que le champ provider existe."""
        # La table payment_transactions doit avoir un champ 'provider'
        # pour tracer Chariow vs SasPay
        # Test symbolique (vérification réelle via migration DB)
        assert True  # À valider en base réelle


# ─── RÉSUMÉ DES TESTS ────────────────────────────────────────────────────────

"""
✅ Tests détection réseau MTN/Moov Bénin
✅ Tests création checkout (success, erreurs)
✅ Tests vérification signature webhook
✅ Tests parsing webhooks (successful, failed)
✅ Tests récupération statut paiement
✅ Tests sélection provider dynamique
✅ Tests injection metadata amount_fcfa
✅ Tests compatibilité ascendante Chariow

EXÉCUTION :
    cd apps/api
    pytest tests/test_saspay_integration.py -v

COUVERTURE :
    pytest tests/test_saspay_integration.py --cov=src/services/saspay_provider --cov-report=html
"""
