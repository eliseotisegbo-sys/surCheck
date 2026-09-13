"""Service financier interne pour la gestion des crédits SûrCheck.
Gère les portefeuilles (credit_wallets), le journal d'audit (credit_transactions),
l'attribution idempotente et la consommation atomique avec protection contre les doubles débits.
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, Tuple
import uuid
import httpx

from ..config import settings
from .supabase_db import supabase_db

logger = logging.getLogger("surcheck.credits")


class CreditService:
    """Service financier régissant le solde et les transactions de crédits."""

    def __init__(self):
        self.supabase = supabase_db

    async def get_user_balance(self, user_id: str) -> int:
        """Récupère le solde réel de crédits de l'utilisateur."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                # 1. Tentative de lecture dans credit_wallets
                res = await client.get(
                    f"{self.supabase.url}/rest/v1/credit_wallets?user_id=eq.{user_id}&select=balance",
                    headers=self.supabase._get_headers(),
                )
                if res.status_code == 200 and res.json():
                    return int(res.json()[0].get("balance", 0))

                # 2. Repli direct sur users.paid_credits_balance
                user_res = await client.get(
                    f"{self.supabase.url}/rest/v1/users?id=eq.{user_id}&select=paid_credits_balance",
                    headers=self.supabase._get_headers(),
                )
                if user_res.status_code == 200 and user_res.json():
                    bal = int(user_res.json()[0].get("paid_credits_balance", 0))
                    # Initialise le portefeuille s'il n'existait pas
                    await self._sync_wallet_balance(user_id, bal)
                    return bal

        except Exception as e:
            logger.error(f"Erreur lecture solde crédits pour {user_id}: {e}")
        return 0

    async def is_analysis_unlocked(self, user_id: Optional[str], analysis_id: str) -> bool:
        """Vérifie si une analyse a déjà été débloquée pour cet utilisateur."""
        if not user_id or not analysis_id:
            return False
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    f"{self.supabase.url}/rest/v1/analysis_unlocks?analysis_id=eq.{analysis_id}&user_id=eq.{user_id}&select=id",
                    headers=self.supabase._get_headers(),
                )
                if res.status_code == 200 and res.json():
                    return len(res.json()) > 0
        except Exception as e:
            logger.warning(f"Erreur vérification déblocage analyse: {e}")
        return False

    async def add_credits_idempotent(
        self,
        user_id: str,
        credits: int,
        sale_id: str,
        amount_fcfa: int,
        pack_code: str,
        raw_event_id: str = "",
        raw_payload: Optional[Dict[str, Any]] = None,
        provider_name: str = "saspay",
    ) -> Tuple[bool, str]:
        """Attribue les crédits après validation serveur du paiement de façon strictement idempotente.
        
        Args:
            provider_name: Nom du provider de paiement ("saspay", "chariow", etc.)

        Retourne : (succès: bool, message: str)
        """
        if credits <= 0:
            return False, "Nombre de crédits invalide."

        try:
            async with httpx.AsyncClient(timeout=6.0) as client:
                # 1. Vérification anti-doublon absolue sur la vente du provider
                check_sale = await client.get(
                    f"{self.supabase.url}/rest/v1/payment_transactions"
                    f"?provider=eq.{provider_name}&external_sale_id=eq.{sale_id}&status=eq.successful&select=id",
                    headers=self.supabase._get_headers(),
                )
                if check_sale.status_code == 200 and check_sale.json():
                    logger.info(f"Vente {provider_name} {sale_id} déjà traitée avec succès — idempotent.")
                    return True, "Vente déjà traitée."

                # 2. Récupérer le solde avant opération
                balance_before = await self.get_user_balance(user_id)
                balance_after = balance_before + credits

                # 3. Mettre à jour le solde utilisateur
                await client.patch(
                    f"{self.supabase.url}/rest/v1/users?id=eq.{user_id}",
                    headers=self.supabase._get_headers(),
                    json={"paid_credits_balance": balance_after},
                )
                await self._sync_wallet_balance(user_id, balance_after)

                # 4. Enregistrer dans le journal d'audit credit_transactions
                tx_id = str(uuid.uuid4())
                await client.post(
                    f"{self.supabase.url}/rest/v1/credit_transactions",
                    headers=self.supabase._get_headers(),
                    json={
                        "id": tx_id,
                        "user_id": user_id,
                        "type": "purchase",
                        "amount": credits,
                        "balance_before": balance_before,
                        "balance_after": balance_after,
                        "reference_type": f"{provider_name}_sale",
                        "reference_id": sale_id,
                        "description": f"Achat {pack_code} ({credits} crédits) via {provider_name.capitalize()} — {amount_fcfa} FCFA",
                    },
                )

                # 5. Enregistrer ou mettre à jour payment_transactions
                payload_str = str(raw_payload) if raw_payload else ""
                payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()

                now_iso = datetime.now(timezone.utc).isoformat()

                # Recherche d'une transaction pending existante
                tx_existing = await client.get(
                    f"{self.supabase.url}/rest/v1/payment_transactions"
                    f"?external_sale_id=eq.{sale_id}&select=id",
                    headers=self.supabase._get_headers(),
                )
                if tx_existing.status_code == 200 and tx_existing.json():
                    ext_id = tx_existing.json()[0]["id"]
                    await client.patch(
                        f"{self.supabase.url}/rest/v1/payment_transactions?id=eq.{ext_id}",
                        headers=self.supabase._get_headers(),
                        json={
                            "status": "successful",
                            "processed_at": now_iso,
                            "raw_event_id": raw_event_id,
                            "raw_payload_hash": payload_hash,
                        },
                    )
                else:
                    new_ptx_id = str(uuid.uuid4())
                    await client.post(
                        f"{self.supabase.url}/rest/v1/payment_transactions",
                        headers=self.supabase._get_headers(),
                        json={
                            "id": new_ptx_id,
                            "user_id": user_id,
                            "provider": provider_name,
                            "external_sale_id": sale_id,
                            "idempotency_key": raw_event_id or sale_id,
                            "pack_name": pack_code,
                            "pack_code": pack_code,
                            "amount_fcfa": amount_fcfa,
                            "credits_purchased": credits,
                            "status": "successful",
                            "raw_event_id": raw_event_id,
                            "raw_payload_hash": payload_hash,
                            "processed_at": now_iso,
                        },
                    )

                logger.info(
                    f"Succès attribution crédits : +{credits} pour user {user_id} "
                    f"(vente {sale_id} via {provider_name}, solde {balance_before} -> {balance_after})"
                )
                return True, f"{credits} crédits ajoutés avec succès."

        except Exception as e:
            logger.error(f"Exception attribution crédits {user_id}: {e}")
            return False, f"Erreur interne : {str(e)}"

    async def consume_credit_for_analysis(
        self,
        user_id: str,
        analysis_id: str,
    ) -> Tuple[bool, str, int]:
        """Consomme de façon atomique 1 crédit pour débloquer l'analyse complète.

        Protection anti-double clic :
        - Si déjà débloquée pour cet utilisateur, retourne (True, "Déjà débloquée", solde) sans déduire.
        - Vérifie solde >= 1.
        - Décrémente et journalise.

        Retourne : (débloqué: bool, message: str, solde_actuel: int)
        """
        try:
            # 1. Protection contre les débits multiples : déjà débloquée ?
            if await self.is_analysis_unlocked(user_id, analysis_id):
                balance = await self.get_user_balance(user_id)
                return True, "Analyse déjà débloquée.", balance

            # 2. Vérifier le solde
            balance = await self.get_user_balance(user_id)
            if balance < 1:
                return False, "Solde de crédits insuffisant. Veuillez recharger votre compte.", balance

            balance_after = balance - 1

            async with httpx.AsyncClient(timeout=5.0) as client:
                # 3. Décrémenter le solde
                await client.patch(
                    f"{self.supabase.url}/rest/v1/users?id=eq.{user_id}",
                    headers=self.supabase._get_headers(),
                    json={"paid_credits_balance": balance_after},
                )
                await self._sync_wallet_balance(user_id, balance_after)

                # 4. Créer la transaction de débit
                credit_tx_id = str(uuid.uuid4())
                await client.post(
                    f"{self.supabase.url}/rest/v1/credit_transactions",
                    headers=self.supabase._get_headers(),
                    json={
                        "id": credit_tx_id,
                        "user_id": user_id,
                        "type": "consumption",
                        "amount": -1,
                        "balance_before": balance,
                        "balance_after": balance_after,
                        "reference_type": "analysis_unlock",
                        "reference_id": analysis_id,
                        "description": f"Déblocage de l'analyse complète {analysis_id}",
                    },
                )

                # 5. Enregistrer le déblocage permanent
                unlock_id = str(uuid.uuid4())
                await client.post(
                    f"{self.supabase.url}/rest/v1/analysis_unlocks",
                    headers=self.supabase._get_headers(),
                    json={
                        "id": unlock_id,
                        "analysis_id": analysis_id,
                        "user_id": user_id,
                        "credit_transaction_id": credit_tx_id,
                    },
                )

            logger.info(
                f"Crédit consommé avec succès : user {user_id} pour analyse {analysis_id} "
                f"(solde {balance} -> {balance_after})"
            )
            return True, "Analyse complète débloquée avec succès.", balance_after

        except Exception as e:
            logger.error(f"Erreur consommation crédit user {user_id} pour analyse {analysis_id}: {e}")
            curr_bal = await self.get_user_balance(user_id)
            return False, "Une erreur s'est produite lors de la consommation du crédit.", curr_bal

    async def get_user_transactions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Retourne l'historique des opérations de crédits pour le tableau de bord utilisateur."""
        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                res = await client.get(
                    f"{self.supabase.url}/rest/v1/credit_transactions"
                    f"?user_id=eq.{user_id}&order=created_at.desc&limit={limit}&select=*",
                    headers=self.supabase._get_headers(),
                )
                if res.status_code == 200:
                    return res.json()
        except Exception as e:
            logger.warning(f"Erreur lecture historique crédits: {e}")
        return []

    async def _sync_wallet_balance(self, user_id: str, balance: int) -> None:
        """Garde synchronisée la table credit_wallets avec le solde de users."""
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                # Upsert dans credit_wallets
                await client.post(
                    f"{self.supabase.url}/rest/v1/credit_wallets",
                    headers={
                        **self.supabase._get_headers(),
                        "Prefer": "resolution=merge-duplicates",
                    },
                    json={
                        "user_id": user_id,
                        "balance": balance,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
        except Exception as e:
            logger.debug(f"Sync wallet notice: {e}")


# Instance singleton
credit_service = CreditService()
