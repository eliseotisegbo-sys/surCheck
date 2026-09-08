"""Implémentation du fournisseur Chariow pour SûrCheck AI.
Conforme à la documentation officielle https://chariow.dev/
Gère l'initiation de Checkout, la validation HMAC-SHA256 des Pulses et la réconciliation.
"""

import hashlib
import hmac
import json
import logging
from typing import Optional, Dict, Any

import httpx

from ..config import settings
from .payment_provider import PaymentProvider, CheckoutSession, WebhookEvent

logger = logging.getLogger("surcheck.chariow")


class ChariowPaymentProvider(PaymentProvider):
    """Fournisseur de paiement Chariow."""

    def __init__(self):
        self.api_key = settings.CHARIOW_API_KEY
        self.base_url = settings.CHARIOW_BASE_URL.rstrip("/")
        self.webhook_secret = settings.CHARIOW_WEBHOOK_SECRET

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def create_checkout(
        self,
        product_id: str,
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        country_code: str,
        custom_metadata: Dict[str, str],
        redirect_url: Optional[str] = None,
    ) -> CheckoutSession:
        """Initie une session Checkout auprès de l'API Chariow."""
        payload: Dict[str, Any] = {
            "product_id": product_id,
            "email": email.strip().lower(),
            "first_name": first_name.strip() or "Client",
            "last_name": last_name.strip() or "SûrCheck",
            "phone": {
                "number": phone_number.strip().replace(" ", "").replace("+", ""),
                "country_code": country_code.upper() or "BJ",
            },
            "custom_metadata": {k: str(v)[:255] for k, v in custom_metadata.items()[:10]},
        }

        if redirect_url:
            payload["redirect_url"] = redirect_url

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/checkout",
                    headers=self._headers(),
                    json=payload,
                )

            data = res.json() if res.content else {}

            if res.status_code not in (200, 201):
                logger.error(f"Erreur API Chariow ({res.status_code}): {res.text}")
                error_msg = (
                    data.get("message")
                    or data.get("error")
                    or f"Erreur Chariow HTTP {res.status_code}"
                )
                return CheckoutSession(
                    step="error",
                    message=error_msg,
                    raw_response=data,
                )

            response_data = data.get("data", data)
            step = response_data.get("step", "payment")
            sale_id = response_data.get("sale_id") or response_data.get("id")

            checkout_url = None
            if step == "payment":
                payment_info = response_data.get("payment", {})
                checkout_url = payment_info.get("checkout_url") or response_data.get("checkout_url")

            return CheckoutSession(
                step=step,
                checkout_url=checkout_url,
                sale_id=sale_id,
                message=data.get("message"),
                raw_response=data,
            )

        except Exception as e:
            logger.error(f"Exception lors de l'appel Checkout Chariow: {e}")
            return CheckoutSession(
                step="error",
                message="Impossible de contacter le serveur de paiement Chariow.",
                raw_response={"error": str(e)},
            )

    def verify_webhook_signature(
        self,
        raw_body: bytes,
        signature_header: str,
    ) -> bool:
        """Valide la signature HMAC-SHA256 du Pulse Chariow (en-tête x-chariow-signature)."""
        if not self.webhook_secret:
            logger.warning("CHARIOW_WEBHOOK_SECRET non configuré — validation signature désactivée (mode dev)")
            return True

        if not signature_header:
            logger.warning("En-tête de signature Chariow manquant")
            return False

        # Format habituel : sha256=<hex_digest> ou direct <hex_digest>
        actual_sig = signature_header
        if actual_sig.startswith("sha256="):
            actual_sig = actual_sig[7:]

        expected_sig = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_sig, actual_sig)

    def parse_webhook(
        self,
        raw_body: bytes,
        headers: Dict[str, str],
    ) -> WebhookEvent:
        """Parse le corps du webhook et extrait les données de vente normalisées."""
        try:
            payload = json.loads(raw_body)
        except Exception:
            payload = {}

        # Identifiant de livraison unique pour déduplication
        delivery_id = (
            headers.get("x-pulse-delivery-id")
            or headers.get("X-Pulse-Delivery-Id")
            or payload.get("id")
            or ""
        )

        event_name = payload.get("event") or payload.get("type") or "unknown"
        data = payload.get("data") or payload.get("entity") or payload

        sale_id = str(data.get("id") or data.get("sale_id") or "")
        product_id = str(data.get("product_id") or "")
        custom_metadata = data.get("custom_metadata") or {}

        user_id = custom_metadata.get("surcheck_user_id") or custom_metadata.get("user_id")
        pack_id = custom_metadata.get("credit_pack") or custom_metadata.get("pack_id")

        try:
            credits = int(custom_metadata.get("credits", 0))
        except (ValueError, TypeError):
            credits = 0

        # Montant
        pricing = data.get("pricing") or {}
        price_val = pricing.get("price") or pricing.get("effective") or data.get("amount") or 0
        if isinstance(price_val, dict):
            amount = int(price_val.get("value", 0))
        else:
            try:
                amount = int(price_val)
            except (ValueError, TypeError):
                amount = 0

        # Statut normalisé
        status_map = {
            "successful.sale": "successful",
            "failed.sale": "failed",
            "abandoned.sale": "abandoned",
            "refunded.sale": "refunded",
        }
        normalized_status = status_map.get(event_name, "unknown")

        return WebhookEvent(
            event_name=event_name,
            delivery_id=delivery_id,
            sale_id=sale_id,
            transaction_id=custom_metadata.get("internal_order_ref"),
            product_id=product_id,
            user_id=user_id,
            pack_id=pack_id,
            credits=credits,
            amount=amount,
            currency="XOF",
            status=normalized_status,
            customer_email=data.get("customer", {}).get("email") or data.get("email"),
            raw_payload=payload,
        )

    async def get_sale(self, sale_id: str) -> Dict[str, Any]:
        """Interroge l'API Sales de Chariow pour vérification ou réconciliation."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{self.base_url}/sales/{sale_id}",
                    headers=self._headers(),
                )
            if res.status_code == 200:
                return res.json()
            return {"error": f"HTTP {res.status_code}", "detail": res.text}
        except Exception as e:
            return {"error": str(e)}


# Instance singleton
chariow_provider = ChariowPaymentProvider()
