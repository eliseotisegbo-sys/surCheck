"""Implémentation du fournisseur SasPay pour SûrCheck AI.
Conforme à la documentation SasPay pour paiements Mobile Money en Afrique de l'Ouest.
Gère Softpay (push direct), vérification webhooks et réconciliation transactions.
"""

import hashlib
import hmac
import json
import logging
import re
import uuid
from typing import Optional, Dict, Any

import httpx

from ..config import settings
from .payment_provider import PaymentProvider, CheckoutSession, WebhookEvent

logger = logging.getLogger("surcheck.saspay")


def detect_mobile_money_network(phone: str, country_code: str) -> str:
    """Détecte le réseau Mobile Money depuis le numéro de téléphone.
    
    Args:
        phone: Numéro de téléphone (avec ou sans indicatif)
        country_code: Code pays ISO-2 (BJ, TG, CI, SN, BF)
    
    Returns:
        Code réseau SasPay (ex: mtn_bj, moov_bj)
    """
    # Nettoyer le numéro (garder uniquement les chiffres)
    digits = re.sub(r'[^\d]', '', phone)
    
    # Retirer l'indicatif pays si présent
    if country_code == "BJ" and digits.startswith("229"):
        digits = digits[3:]
    elif country_code == "TG" and digits.startswith("228"):
        digits = digits[3:]
    elif country_code == "CI" and digits.startswith("225"):
        digits = digits[3:]
    elif country_code == "SN" and digits.startswith("221"):
        digits = digits[3:]
    elif country_code == "BF" and digits.startswith("226"):
        digits = digits[3:]
    
    if country_code == "BJ":
        # Bénin - Détection basée sur les préfixes officiels
        first_two = digits[:2] if len(digits) >= 2 else ""
        
        # MTN Bénin: 40-49, 50-59, 60-69, 90-99
        mtn_prefixes = {
            "40", "41", "42", "43", "44", "45", "46", "47", "48", "49",
            "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
            "60", "61", "62", "63", "64", "65", "66", "67", "68", "69",
            "90", "91", "92", "93", "94", "95", "96", "97", "98", "99"
        }
        
        # Moov Bénin: 01, 02, 03, 80-89
        moov_prefixes = {
            "01", "02", "03",
            "80", "81", "82", "83", "84", "85", "86", "87", "88", "89"
        }
        
        if first_two in mtn_prefixes:
            return "mtn_bj"
        elif first_two in moov_prefixes:
            return "moov_bj"
        else:
            # Par défaut MTN (plus courant au Bénin)
            logger.warning(f"Préfixe inconnu pour BJ: {first_two}, fallback MTN")
            return "mtn_bj"
    
    elif country_code == "TG":
        # Togo (à documenter selon besoins)
        # TODO: Ajouter préfixes réels MTN/Moov Togo
        return "mtn_tg"
    
    elif country_code == "CI":
        # Côte d'Ivoire (à documenter selon besoins)
        return "mtn_ci"
    
    elif country_code == "SN":
        # Sénégal (à documenter selon besoins)
        return "orange_sn"
    
    elif country_code == "BF":
        # Burkina Faso (à documenter selon besoins)
        return "orange_bf"
    
    # Fallback générique
    logger.warning(f"Pays non supporté pour détection réseau: {country_code}")
    return f"mtn_{country_code.lower()}"


class SasPayPaymentProvider(PaymentProvider):
    """Fournisseur de paiement SasPay."""

    def __init__(self):
        self.api_key = settings.SASPAY_API_KEY
        self.base_url = settings.SASPAY_BASE_URL.rstrip("/")
        self.webhook_secret = settings.SASPAY_WEBHOOK_SECRET

    def _headers(self, idempotency_key: Optional[str] = None) -> Dict[str, str]:
        """Construit les headers HTTP pour requêtes SasPay."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Header Idempotency-Key requis pour éviter doublons
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        
        return headers

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
        """Initie un paiement Softpay (push direct) auprès de l'API SasPay.
        
        Note: SasPay nécessite le montant explicite, contrairement à Chariow
        qui utilisait product_id. Le montant est extrait des métadonnées.
        """
        # ⚠️ CRITIQUE: SasPay nécessite le montant explicite
        # On le récupère depuis custom_metadata (injecté par payment.py via PACKS)
        amount_str = custom_metadata.get("amount_fcfa", "0")
        try:
            amount = float(amount_str)
        except (ValueError, TypeError):
            logger.error(f"Montant invalide dans metadata: {amount_str}")
            return CheckoutSession(
                step="error",
                message="Configuration du montant invalide côté serveur.",
                raw_response={"error": "invalid_amount"},
            )
        
        # Détection automatique du réseau Mobile Money
        network = detect_mobile_money_network(phone_number, country_code)
        
        # Générer clé d'idempotence unique (évite doublons sur retry réseau)
        idempotency_key = custom_metadata.get("internal_order_ref") or str(uuid.uuid4())
        
        # Formater téléphone avec indicatif pays complet
        clean_phone = re.sub(r'[^\d]', '', phone_number)
        if not clean_phone.startswith("229") and country_code == "BJ":
            clean_phone = f"229{clean_phone}"
        formatted_phone = f"+{clean_phone}"
        
        # Description lisible de la transaction
        pack_label = custom_metadata.get("pack_label", "Crédits SûrCheck AI")
        description = f"{pack_label} - Analyse anti-arnaque"
        
        # Construction payload SasPay (structure différente de Chariow)
        payload: Dict[str, Any] = {
            "amount": f"{amount:.2f}",  # Format décimal requis
            "currency": "XOF",
            "country": country_code.upper(),
            "network": network,
            "description": description,
            "customer": {
                "email": email.strip().lower(),
                "first_name": first_name.strip() or "Client",
                "last_name": last_name.strip() or "SûrCheck",
                "phone": formatted_phone,
            },
            "metadata": {
                # Stocker TOUTES les métadonnées dans metadata (SasPay n'a pas de product_id)
                **{k: str(v)[:255] for k, v in custom_metadata.items()},
                "redirect_url": redirect_url or "",  # Stocker l'URL de retour en metadata
            }
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/payments/softpay/",
                    headers=self._headers(idempotency_key=idempotency_key),
                    json=payload,
                )

            data = res.json() if res.content else {}

            if res.status_code not in (200, 201):
                logger.error(f"Erreur API SasPay ({res.status_code}): {res.text}")
                error_msg = (
                    data.get("message")
                    or data.get("error")
                    or data.get("detail")
                    or f"Erreur SasPay HTTP {res.status_code}"
                )
                return CheckoutSession(
                    step="error",
                    message=error_msg,
                    raw_response=data,
                )

            # Extraction données réponse
            payment_id = data.get("id", "")
            status = data.get("status", "PENDING")
            checkout_url = data.get("checkout_url", "")
            
            # ⚠️ DIFFÉRENCE MAJEURE: checkout_url comportement
            # - Vide ("") pour MTN/Moov Bénin → Push USSD direct (pas de redirect)
            # - Non vide pour Wave/Orange/Djamo → Redirection OBLIGATOIRE
            step = "redirect" if checkout_url else "payment"
            
            return CheckoutSession(
                step=step,
                checkout_url=checkout_url if checkout_url else None,
                sale_id=payment_id,
                message=data.get("message", "Payment initiated"),
                raw_response=data,
            )

        except httpx.TimeoutException:
            logger.error("Timeout lors de l'appel SasPay Softpay")
            return CheckoutSession(
                step="error",
                message="Le serveur de paiement SasPay ne répond pas. Veuillez réessayer.",
                raw_response={"error": "timeout"},
            )
        except Exception as e:
            logger.error(f"Exception lors de l'appel Softpay SasPay: {e}")
            return CheckoutSession(
                step="error",
                message="Impossible de contacter le serveur de paiement SasPay.",
                raw_response={"error": str(e)},
            )

    def verify_webhook_signature(
        self,
        raw_body: bytes,
        signature_header: str,
    ) -> bool:
        """Valide la signature cryptographique du webhook SasPay.
        
        ⚠️ ATTENTION: Mécanisme de signature SasPay à documenter en sandbox.
        Implémentation temporaire basée sur HMAC-SHA256 (comme Chariow).
        À ajuster selon documentation officielle SasPay.
        """
        if not self.webhook_secret:
            logger.warning("SASPAY_WEBHOOK_SECRET non configuré — validation signature désactivée (mode dev)")
            return True

        if not signature_header:
            logger.warning("En-tête de signature SasPay manquant")
            return False

        # Format présumé: sha256=<hex_digest> ou direct <hex_digest>
        actual_sig = signature_header
        if actual_sig.startswith("sha256="):
            actual_sig = actual_sig[7:]

        # Calcul HMAC-SHA256 (à valider avec documentation SasPay)
        expected_sig = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        is_valid = hmac.compare_digest(expected_sig, actual_sig)
        
        if not is_valid:
            logger.warning(f"Signature webhook SasPay invalide. Expected: {expected_sig[:10]}..., Got: {actual_sig[:10]}...")
        
        return is_valid

    def parse_webhook(
        self,
        raw_body: bytes,
        headers: Dict[str, str],
    ) -> WebhookEvent:
        """Parse le webhook SasPay et le normalise au format unifié WebhookEvent.
        
        Mapping événements SasPay → Format unifié Chariow pour compatibilité.
        """
        try:
            payload = json.loads(raw_body)
        except Exception:
            payload = {}

        # Identifiant de livraison unique pour déduplication
        # Header présumé: x-webhook-id ou x-saspay-webhook-id
        delivery_id = (
            headers.get("x-webhook-id")
            or headers.get("x-saspay-webhook-id")
            or headers.get("X-Webhook-Id")
            or payload.get("id")
            or ""
        )

        # Nom de l'événement (format présumé: payment.succeeded, payment.failed, etc.)
        event_name_raw = payload.get("event") or payload.get("type") or "unknown"
        
        # Extraction données paiement
        data = payload.get("data") or payload
        payment_id = str(data.get("id") or "")
        status_raw = data.get("status", "PENDING")
        
        # Métadonnées custom (renommé de custom_metadata chez Chariow)
        metadata = data.get("metadata") or {}
        
        user_id = metadata.get("surcheck_user_id") or metadata.get("user_id")
        pack_id = metadata.get("credit_pack") or metadata.get("pack_id")
        
        try:
            credits = int(metadata.get("credits", 0))
        except (ValueError, TypeError):
            credits = 0

        # Montant (format string "2500.00" chez SasPay)
        amount_str = data.get("net_amount") or data.get("amount") or "0"
        try:
            amount = int(float(amount_str))
        except (ValueError, TypeError):
            amount = 0

        # Email client
        customer = data.get("customer") or {}
        customer_email = customer.get("email") or data.get("email")

        # ⚠️ MAPPING ÉVÉNEMENTS: SasPay → Format unifié (compatible Chariow)
        event_mapping = {
            "payment.succeeded": "successful.sale",
            "payment.success": "successful.sale",
            "payment.completed": "successful.sale",
            "payment.failed": "failed.sale",
            "payment.cancelled": "abandoned.sale",
            "payment.canceled": "abandoned.sale",
            "payment.refunded": "refunded.sale",
        }
        normalized_event = event_mapping.get(event_name_raw, event_name_raw)

        # ⚠️ MAPPING STATUTS: SasPay (MAJUSCULES) → Format unifié (minuscules)
        status_mapping = {
            "SUCCESS": "successful",
            "COMPLETED": "successful",
            "PENDING": "pending",
            "FAILED": "failed",
            "CANCELLED": "abandoned",
            "CANCELED": "abandoned",
            "REFUNDED": "refunded",
        }
        normalized_status = status_mapping.get(status_raw, "unknown")

        return WebhookEvent(
            event_name=normalized_event,
            delivery_id=delivery_id,
            sale_id=payment_id,
            transaction_id=metadata.get("internal_order_ref"),
            product_id=None,  # SasPay n'a pas de concept product_id
            user_id=user_id,
            pack_id=pack_id,
            credits=credits,
            amount=amount,
            currency="XOF",
            status=normalized_status,
            customer_email=customer_email,
            raw_payload=payload,
        )

    async def get_sale(self, sale_id: str) -> Dict[str, Any]:
        """Interroge l'API SasPay pour vérifier le statut d'un paiement.
        
        Équivalent de GET /sales/{id} chez Chariow.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{self.base_url}/payments/{sale_id}/verify/",
                    headers=self._headers(),
                )
            
            if res.status_code == 200:
                data = res.json()
                
                # Normaliser la réponse au format attendu
                return {
                    "id": data.get("id"),
                    "status": data.get("status"),
                    "amount": data.get("net_amount") or data.get("amount"),
                    "currency": data.get("currency", "XOF"),
                    "message": data.get("message"),
                    "raw": data,
                }
            
            return {
                "error": f"HTTP {res.status_code}",
                "detail": res.text,
                "raw": {}
            }
            
        except Exception as e:
            logger.error(f"Erreur vérification paiement SasPay {sale_id}: {e}")
            return {"error": str(e), "raw": {}}


# Instance singleton
saspay_provider = SasPayPaymentProvider()
