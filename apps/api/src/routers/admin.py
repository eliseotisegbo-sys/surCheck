"""Router d'administration et de réconciliation financière pour SûrCheck AI.
Conforme aux sections 24 & 27 du document de cadrage technique.
"""

import logging
from typing import Dict, Any, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from ..routers.auth import get_current_user
from ..services.saspay_provider import saspay_provider
from ..services.supabase_db import supabase_db
from ..config import settings

logger = logging.getLogger("surcheck.admin")

router = APIRouter(prefix="/admin", tags=["Administration & Réconciliation"])


def _require_admin(user: Dict[str, Any]):
    """Vérifie que l'utilisateur a le rôle 'admin' ou 'moderator'."""
    if user.get("role") not in ("admin", "moderator"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )


@router.get("/payments")
async def list_admin_payments(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Statistiques et historique global des transactions de paiement."""
    _require_admin(current_user)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                f"{supabase_db.url}/rest/v1/payment_transactions?order=created_at.desc&limit={limit}&select=*",
                headers=supabase_db._get_headers(),
            )
            transactions = res.json() if res.status_code == 200 else []

        total_collected = sum(
            tx.get("amount_fcfa", 0)
            for tx in transactions
            if tx.get("status") == "successful"
        )
        successful_count = sum(1 for tx in transactions if tx.get("status") == "successful")
        failed_count = sum(1 for tx in transactions if tx.get("status") == "failed")
        pending_count = sum(1 for tx in transactions if tx.get("status") == "pending")

        return {
            "summary": {
                "total_collected_fcfa": total_collected,
                "successful_transactions": successful_count,
                "failed_transactions": failed_count,
                "pending_transactions": pending_count,
                "total_tracked": len(transactions),
            },
            "transactions": transactions,
        }
    except Exception as e:
        logger.error(f"Erreur admin payments: {e}")
        return {"summary": {}, "transactions": []}


@router.get("/credits")
async def list_admin_credits(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Statistiques globales d'utilisation des crédits (vendus vs consommés)."""
    _require_admin(current_user)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(
                f"{supabase_db.url}/rest/v1/credit_transactions?order=created_at.desc&limit={limit}&select=*",
                headers=supabase_db._get_headers(),
            )
            txs = res.json() if res.status_code == 200 else []

        purchased_total = sum(tx.get("amount", 0) for tx in txs if tx.get("type") == "purchase")
        consumed_total = sum(abs(tx.get("amount", 0)) for tx in txs if tx.get("type") == "consumption")

        return {
            "summary": {
                "credits_purchased": purchased_total,
                "credits_consumed": consumed_total,
                "recent_operations": len(txs),
            },
            "transactions": txs,
        }
    except Exception as e:
        logger.error(f"Erreur admin credits: {e}")
        return {"summary": {}, "transactions": []}


@router.get("/payment-reconciliation")
async def reconcile_payments(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Compare les transactions enregistrées côté SasPay et les transactions SûrCheck pour détecter d'éventuels écarts.
    
    Utilise l'API SasPay /transactions/ (documentation: https://docs.saspay.me/api-reference/transactions/list)
    """
    _require_admin(current_user)

    try:
        # 1. Récupérer les transactions côté SasPay
        # API SasPay : GET /api/v1/transactions/ avec pagination par curseur
        async with httpx.AsyncClient(timeout=15.0) as client:
            saspay_res = await client.get(
                f"{saspay_provider.base_url}/transactions/",
                headers=saspay_provider._headers(),
                params={
                    "status": "SUCCESS",  # Filtrer uniquement les transactions réussies
                    "limit": 100,  # Paginer si nécessaire (ajuster selon volume)
                }
            )
            
            if saspay_res.status_code == 200:
                saspay_data = saspay_res.json()
                # SasPay retourne {results: [...], next: cursor, ...}
                saspay_transactions = saspay_data.get("results", saspay_data.get("data", []))
            else:
                logger.warning(f"Erreur récupération SasPay ({saspay_res.status_code}): {saspay_res.text}")
                saspay_transactions = []

        # 2. Récupérer les transactions côté SûrCheck (provider = 'saspay')
        async with httpx.AsyncClient(timeout=5.0) as client:
            db_res = await client.get(
                f"{supabase_db.url}/rest/v1/payment_transactions?provider=eq.saspay&select=external_sale_id,status,amount_fcfa",
                headers=supabase_db._get_headers(),
            )
            db_txs = db_res.json() if db_res.status_code == 200 else []

        db_sale_ids = {
            tx.get("external_sale_id"): tx
            for tx in db_txs
            if tx.get("external_sale_id")
        }

        # 3. Détection des anomalies
        # SasPay utilise "reference" comme identifiant de transaction (équivalent sale_id)
        unmatched_saspay_transactions: List[Dict[str, Any]] = []
        matched_count = 0

        for txn in saspay_transactions:
            # SasPay : champ "reference" ou "id" selon structure réelle de l'API
            txn_id = txn.get("reference") or txn.get("id")
            if txn_id in db_sale_ids:
                matched_count += 1
            else:
                unmatched_saspay_transactions.append({
                    "saspay_transaction_id": txn_id,
                    "customer_email": txn.get("customer_email"),
                    "amount": txn.get("net_amount") or txn.get("amount"),  # Utiliser net_amount (montant reçu)
                    "currency": txn.get("currency", "XOF"),
                    "created_at": txn.get("created_at"),
                    "status": txn.get("status"),
                })

        return {
            "reconciliation_status": "ok" if len(unmatched_saspay_transactions) == 0 else "anomalies_detected",
            "matched_sales_count": matched_count,
            "unmatched_sales_count": len(unmatched_saspay_transactions),
            "unmatched_sales": unmatched_saspay_transactions,
            "total_saspay_transactions_checked": len(saspay_transactions),
            "note": "Réconciliation basée sur l'API SasPay /transactions/. Ajuster pagination si volume > 100 transactions.",
        }

    except Exception as e:
        logger.error(f"Erreur réconciliation: {e}")
        return {
            "reconciliation_status": "error",
            "detail": str(e),
        }


# ─── PHASE 7 : MODÉRATION DES SIGNALEMENTS & JOURNAL D'AUDIT ──────────────────

from pydantic import BaseModel
from typing import Optional
from ..schemas import ReportStatus
from ..routers.reports import IN_MEMORY_REPORTS


class ModerateReportRequest(BaseModel):
    status: ReportStatus
    moderation_notes: Optional[str] = None


@router.get("/stats")
async def get_admin_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Vue d'ensemble et métriques globales pour le tableau de bord d'administration."""
    _require_admin(current_user)

    db_stats = await supabase_db.get_admin_dashboard_stats()

    # Si Supabase n'a pas encore de reports en ligne, compléter avec IN_MEMORY_REPORTS
    if db_stats["reports_total"] == 0 and IN_MEMORY_REPORTS:
        db_stats["reports_total"] = len(IN_MEMORY_REPORTS)
        for r in IN_MEMORY_REPORTS:
            st = r.get("status")
            if isinstance(st, ReportStatus):
                st = st.value
            if st == "nouveau":
                db_stats["reports_nouveau"] += 1
            elif st == "en_verification":
                db_stats["reports_en_verification"] += 1
            elif st == "confirme_elements_suffisants":
                db_stats["reports_confirme"] += 1
            elif st == "non_confirme":
                db_stats["reports_non_confirme"] += 1

    return db_stats


@router.get("/reports")
async def list_admin_reports(
    status_filter: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Récupère la file des signalements communautaires à modérer."""
    _require_admin(current_user)

    reports = await supabase_db.get_admin_reports(
        status_filter=status_filter,
        limit=limit,
        offset=offset,
    )

    # Fallback sur les signalements en mémoire si Supabase renvoie vide
    if not reports and IN_MEMORY_REPORTS:
        filtered = IN_MEMORY_REPORTS
        if status_filter:
            filtered = [
                r for r in IN_MEMORY_REPORTS
                if (r["status"].value if isinstance(r["status"], ReportStatus) else r["status"]) == status_filter
            ]
        reports = filtered[offset : offset + limit]

    return {
        "count": len(reports),
        "status_filter": status_filter,
        "reports": reports,
    }


@router.patch("/reports/{report_id}/moderate")
async def moderate_report(
    report_id: str,
    payload: ModerateReportRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Modère un signalement (passage de 'nouveau' à 'en_verification', 'confirme_elements_suffisants', etc.)

    Consigne automatiquement l'opération dans le journal d'audit inaltérable.
    """
    _require_admin(current_user)

    admin_id = current_user.get("id")
    target_status = payload.status.value if isinstance(payload.status, ReportStatus) else payload.status

    # 1. Mise à jour Supabase
    updated = await supabase_db.moderate_report(
        report_id=report_id,
        new_status=target_status,
        moderation_notes=payload.moderation_notes,
        admin_id=admin_id,
    )

    # 2. Mise à jour synchrone en mémoire également
    for r in IN_MEMORY_REPORTS:
        if r["id"] == report_id:
            r["status"] = payload.status
            r["moderation_notes"] = payload.moderation_notes
            r["moderated_by"] = admin_id

    return {
        "status": "success",
        "message": f"Signalement modéré avec succès (nouveau statut : {target_status}).",
        "report_id": report_id,
        "new_status": target_status,
        "moderated_by": admin_id,
        "notes": payload.moderation_notes,
    }


@router.get("/audit-logs")
async def list_audit_logs(
    limit: int = 50,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Consulte le journal d'audit inaltérable des actions administratives."""
    _require_admin(current_user)

    logs = await supabase_db.get_audit_logs(limit=limit)
    return {
        "count": len(logs),
        "logs": logs,
    }

