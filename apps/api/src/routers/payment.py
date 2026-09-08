"""Router de paiement Chariow pour SûrCheck AI.
Gère les sessions de checkout, la réception des Pulses (webhooks signés HMAC-SHA256),
l'attribution idempotente des crédits et la traçabilité des transactions.

Conforme aux directives du document technique Chariow + Crédits SûrCheck :
- PostgreSQL est la seule source de vérité pour le solde.
- Le serveur détermine lui-même le nombre de crédits selon le pack côté serveur.
- Déduplication stricte basée sur x-pulse-delivery-id et external_sale_id.
"""

import hashlib
import json
import logging
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..config import settings
from ..routers.auth import get_current_user
from ..services.chariow_provider import chariow_provider
from ..services.credit_service import credit_service
from ..services.supabase_db import supabase_db

logger = logging.getLogger("surcheck.payment")

router = APIRouter(prefix="/payment", tags=["Paiement"])

# ─── PACKS OFFICIELS SÛRCHECK ────────────────────────────────────────────────

PACKS = {
    "pack_1": {
        "id": "pack_1",
        "credits": 1,
        "amount_fcfa": settings.CREDIT_PACK_1_FCFA,
        "label": "Analyse unique",
        "unit_price": 600,
        "product_id": settings.CHARIOW_PRODUCT_PACK_1,
        "popular": False,
        "description": "1 analyse complète immédiate (600 FCFA)",
    },
    "pack_5": {
        "id": "pack_5",
        "credits": 5,
        "amount_fcfa": settings.CREDIT_PACK_5_FCFA,
        "label": "Petit pack",
        "unit_price": 300,
        "product_id": settings.CHARIOW_PRODUCT_PACK_5,
        "popular": False,
        "description": "5 analyses complètes réutilisables (300 F / analyse)",
    },
    "pack_10": {
        "id": "pack_10",
        "credits": 10,
        "amount_fcfa": settings.CREDIT_PACK_10_FCFA,
        "label": "Pack recommandé",
        "unit_price": 250,
        "product_id": settings.CHARIOW_PRODUCT_PACK_10,
        "popular": True,
        "description": "10 analyses complètes (250 F / analyse) — Le plus populaire",
    },
    "pack_25": {
        "id": "pack_25",
        "credits": 25,
        "amount_fcfa": settings.CREDIT_PACK_25_FCFA,
        "label": "Gros pack",
        "unit_price": 200,
        "product_id": settings.CHARIOW_PRODUCT_PACK_25,
        "popular": False,
        "description": "25 analyses complètes (200 F / analyse)",
    },
}



# ─── SCHÉMAS ─────────────────────────────────────────────────────────────────

class CheckoutRequest(BaseModel):
    pack_id: str = Field(..., description="pack_1, pack_5, pack_10 ou pack_25")
    phone_number: Optional[str] = Field(None, description="Numéro de téléphone pour Mobile Money")
    country_code: Optional[str] = Field("BJ", description="Code pays ISO-2 (BJ pour Bénin)")
    analysis_id: Optional[str] = Field(None, description="ID de l'analyse à débloquer si paiement direct")


class CheckoutResponse(BaseModel):
    step: str
    checkout_url: Optional[str] = None
    transaction_id: str
    sale_id: Optional[str] = None
    amount_fcfa: int
    credits: int
    label: str
    message: Optional[str] = None


# ─── ENDPOINTS PUBLICS & CLIENTS ─────────────────────────────────────────────

@router.get("/packs")
async def list_packs():
    """Retourne la grille tarifaire officielle des packs de crédits SûrCheck."""
    return {
        "packs": list(PACKS.values()),
        "currency": "XOF",
        "note": "Tarifs TTC en FCFA. Paiement sécurisé via Mobile Money (MTN, Moov Bénin) opéré par Chariow.",
    }


@router.post("/checkout", response_model=CheckoutResponse)
@router.post("/initiate", response_model=CheckoutResponse)
async def create_checkout_session(
    body: CheckoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Crée une session de checkout sécurisée auprès de Chariow.

    Le serveur valide le pack, force le montant et les crédits depuis sa propre configuration
    et injecte des métadonnées cryptographiquement isolées pour le traitement du Pulse ultérieur.
    """
    pack = PACKS.get(body.pack_id)
    if not pack:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Pack inconnu. Valeurs acceptées : {', '.join(PACKS.keys())}",
        )

    if not settings.CHARIOW_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Le service de paiement est en cours de configuration. Veuillez réessayer ultérieurement.",
        )

    user_id = str(current_user["id"])
    user_email = current_user.get("email", "")
    user_name = current_user.get("name", "Utilisateur SûrCheck")
    name_parts = user_name.split()
    first_name = name_parts[0] if name_parts else "Client"
    last_name = name_parts[-1] if len(name_parts) > 1 else "SûrCheck"

    internal_order_ref = str(uuid.uuid4())

    # Détermination de l'URL de retour client
    redirect_url = f"{settings.APP_URL}/paiement/success?order_ref={internal_order_ref}"
    if body.analysis_id:
        redirect_url += f"&analysis_id={body.analysis_id}"

    # Métadonnées serveur (max 10 clés, 255 chars chacune)
    custom_metadata = {
        "surcheck_user_id": user_id,
        "credit_pack": body.pack_id,
        "credits": str(pack["credits"]),
        "internal_order_ref": internal_order_ref,
    }
    if body.analysis_id:
        custom_metadata["analysis_id"] = str(body.analysis_id)

    # Enregistrement de la transaction initiale en statut 'pending'
    try:
        import httpx
        async with httpx.AsyncClient(timeout=4.0) as client:
            await client.post(
                f"{supabase_db.url}/rest/v1/payment_transactions",
                headers=supabase_db._get_headers(),
                json={
                    "id": internal_order_ref,
                    "user_id": user_id,
                    "provider": "chariow",
                    "product_id": pack["product_id"],
                    "pack_name": pack["id"],
                    "pack_code": pack["id"],
                    "idempotency_key": internal_order_ref,
                    "amount_fcfa": pack["amount_fcfa"],
                    "credits_purchased": pack["credits"],
                    "status": "pending",
                },
            )
    except Exception as e:
        logger.warning(f"Erreur pré-enregistrement transaction pending: {e}")

    # Appel Chariow
    session = await chariow_provider.create_checkout(
        product_id=pack["product_id"],
        email=user_email,
        first_name=first_name,
        last_name=last_name,
        phone_number=body.phone_number or "00000000",
        country_code=body.country_code or "BJ",
        custom_metadata=custom_metadata,
        redirect_url=redirect_url,
    )

    if session.step == "error":
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=session.message or "Échec de l'initialisation de la session Chariow.",
        )

    # Mise à jour avec external_sale_id si reçu
    if session.sale_id:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=3.0) as client:
                await client.patch(
                    f"{supabase_db.url}/rest/v1/payment_transactions?id=eq.{internal_order_ref}",
                    headers=supabase_db._get_headers(),
                    json={"external_sale_id": session.sale_id},
                )
        except Exception:
            pass

    return CheckoutResponse(
        step=session.step,
        checkout_url=session.checkout_url,
        transaction_id=internal_order_ref,
        sale_id=session.sale_id,
        amount_fcfa=pack["amount_fcfa"],
        credits=pack["credits"],
        label=pack["label"],
        message=session.message,
    )


@router.post("/webhook")
async def handle_chariow_pulse(request: Request):
    """Récepteur officiel des webhooks (Pulses) Chariow.

    Événements surveillés :
    - `successful.sale` : Attribution immédiate et idempotente des crédits + déblocage automatique si analyse liée.
    - `failed.sale` / `abandoned.sale` : Clôture de la transaction en échec.
    - `refunded.sale` : Traçabilité du remboursement.
    """
    raw_body = await request.body()
    headers_dict = dict(request.headers)

    # 1. Vérification de signature cryptographique HMAC-SHA256
    sig_header = (
        request.headers.get("x-chariow-signature")
        or request.headers.get("X-Chariow-Signature")
        or ""
    )
    if not chariow_provider.verify_webhook_signature(raw_body, sig_header):
        logger.warning("Pulse Chariow rejeté : signature cryptographique invalide")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Signature de webhook invalide.",
        )

    # 2. Parsing normalisé de l'événement
    event = chariow_provider.parse_webhook(raw_body, headers_dict)
    logger.info(
        f"Pulse Chariow reçu : event={event.event_name} | sale={event.sale_id} "
        f"| user={event.user_id} | delivery={event.delivery_id}"
    )

    # 3. Traitement selon l'événement
    if event.event_name == "successful.sale":
        if not event.user_id:
            logger.error(f"Pulse successful.sale sans user_id dans custom_metadata : {event.raw_payload}")
            return {"received": True, "error": "user_id missing"}

        # Identifier le pack réel et forcer les crédits depuis le mapping serveur
        pack = PACKS.get(event.pack_id or "")
        credits_to_add = pack["credits"] if pack else event.credits
        amount_fcfa = pack["amount_fcfa"] if pack else event.amount

        success, msg = await credit_service.add_credits_idempotent(
            user_id=event.user_id,
            credits=credits_to_add,
            sale_id=event.sale_id,
            amount_fcfa=amount_fcfa,
            pack_code=event.pack_id or "pack_custom",
            raw_event_id=event.delivery_id,
            raw_payload=event.raw_payload,
        )

        # Si l'achat concernait directement une analyse spécifique (achat direct 300 F)
        custom_meta = event.raw_payload.get("data", {}).get("custom_metadata", {})
        target_analysis_id = custom_meta.get("analysis_id")
        if target_analysis_id and success:
            logger.info(f"Déblocage automatique post-achat de l'analyse {target_analysis_id} pour user {event.user_id}")
            await credit_service.consume_credit_for_analysis(event.user_id, target_analysis_id)

        return {"received": True, "credited": success, "message": msg}

    elif event.event_name in ("failed.sale", "abandoned.sale"):
        if event.transaction_id:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=3.0) as client:
                    await client.patch(
                        f"{supabase_db.url}/rest/v1/payment_transactions?id=eq.{event.transaction_id}",
                        headers=supabase_db._get_headers(),
                        json={"status": "failed", "processed_at": event.delivery_id},
                    )
            except Exception as e:
                logger.warning(f"Erreur mise à jour transaction échouée: {e}")

        return {"received": True, "status": "failed_recorded"}

    elif event.event_name == "refunded.sale":
        logger.warning(f"Alerte Remboursement Chariow reçu pour vente {event.sale_id}")
        # Note : Selon la règle section 25, ne jamais créer de solde négatif sans décision admin
        return {"received": True, "status": "refund_logged"}

    return {"received": True, "status": "ignored"}


@router.get("/{transaction_id}")
async def get_transaction_status(
    transaction_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Permet au frontend de vérifier l'état d'une transaction post-redirection."""
    try:
        import httpx
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(
                f"{supabase_db.url}/rest/v1/payment_transactions?id=eq.{transaction_id}&select=*",
                headers=supabase_db._get_headers(),
            )
            if res.status_code == 200 and res.json():
                tx = res.json()[0]
                # Sécurité : vérifier que la transaction appartient bien à l'utilisateur
                if str(tx.get("user_id")) != str(current_user["id"]):
                    raise HTTPException(status_code=403, detail="Accès non autorisé à cette transaction.")
                return tx
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Erreur recherche transaction {transaction_id}: {e}")

    raise HTTPException(status_code=404, detail="Transaction introuvable.")
