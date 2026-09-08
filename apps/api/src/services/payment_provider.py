"""Interface d'abstraction du fournisseur de paiement pour SûrCheck AI.
Permet d'isoler la logique de checkout (Chariow, FedaPay, etc.)
sans jamais impacter le moteur financier et le portefeuille de crédits PostgreSQL.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel


class CheckoutSession(BaseModel):
    """Représentation unifiée d'une session de checkout créée."""
    step: str  # 'payment', 'completed', 'already_purchased', 'error'
    checkout_url: Optional[str] = None
    sale_id: Optional[str] = None
    message: Optional[str] = None
    raw_response: Dict[str, Any] = {}


class WebhookEvent(BaseModel):
    """Représentation unifiée d'un événement webhook (Pulse)."""
    event_name: str  # 'successful.sale', 'failed.sale', 'abandoned.sale', 'refunded.sale', etc.
    delivery_id: str  # Identifiant unique de livraison (idempotence)
    sale_id: str  # Identifiant unique de vente (ex: sal_xxxxx)
    transaction_id: Optional[str] = None
    product_id: Optional[str] = None
    user_id: Optional[str] = None
    pack_id: Optional[str] = None
    credits: int = 0
    amount: int = 0
    currency: str = "XOF"
    status: str  # 'successful', 'failed', 'abandoned', 'refunded', 'unknown'
    customer_email: Optional[str] = None
    raw_payload: Dict[str, Any] = {}


class PaymentProvider(ABC):
    """Contrat abstrait pour tout prestataire de paiement connecté à SûrCheck."""

    @abstractmethod
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
        """Initie une session de paiement auprès de la passerelle."""
        pass

    @abstractmethod
    def verify_webhook_signature(
        self,
        raw_body: bytes,
        signature_header: str,
    ) -> bool:
        """Vérifie cryptographiquement l'authenticité de la requête webhook."""
        pass

    @abstractmethod
    def parse_webhook(
        self,
        raw_body: bytes,
        headers: Dict[str, str],
    ) -> WebhookEvent:
        """Parse et normalise l'événement reçu."""
        pass

    @abstractmethod
    async def get_sale(self, sale_id: str) -> Dict[str, Any]:
        """Récupère les détails d'une vente pour réconciliation."""
        pass
