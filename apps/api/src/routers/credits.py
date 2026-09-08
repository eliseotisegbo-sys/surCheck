"""Router des crédits et déblocage d'analyses pour SûrCheck AI.
Fournit le solde, l'historique des opérations financières et l'action atomique de déblocage.
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..routers.auth import get_current_user
from ..services.credit_service import credit_service
from ..services.supabase_db import supabase_db

logger = logging.getLogger("surcheck.credits_router")

router = APIRouter(prefix="", tags=["Crédits & Analyses"])


# ─── SCHÉMAS ─────────────────────────────────────────────────────────────────

class UnlockAnalysisResponse(BaseModel):
    unlocked: bool
    message: str
    remaining_credits: int
    analysis_id: str


# ─── ENDPOINTS CRÉDITS ───────────────────────────────────────────────────────

@router.get("/credits")
async def get_my_credits(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Retourne le solde actuel de crédits de l'utilisateur connecté."""
    user_id = str(current_user["id"])
    balance = await credit_service.get_user_balance(user_id)
    return {
        "user_id": user_id,
        "credits_balance": balance,
        "free_quota": current_user.get("free_analyses_quota", 0),
    }


@router.get("/credits/transactions")
async def get_my_credit_transactions(
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Retourne le journal des transactions de crédits (achats et consommations)."""
    user_id = str(current_user["id"])
    transactions = await credit_service.get_user_transactions(user_id, limit=30)
    return {
        "user_id": user_id,
        "transactions": transactions,
    }


# ─── DÉBLOCAGE D'ANALYSE COMPLÈTE ────────────────────────────────────────────

@router.post("/analyses/{analysis_id}/unlock", response_model=UnlockAnalysisResponse)
async def unlock_complete_analysis(
    analysis_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Débloque l'analyse complète en consommant de façon atomique 1 crédit.

    Protection anti-double débit :
    - Si l'analyse est déjà débloquée pour cet utilisateur, ne débite aucun crédit.
    - Vérifie que le solde est supérieur ou égal à 1.
    """
    user_id = str(current_user["id"])

    # Vérification que l'analyse existe dans la base
    try:
        import httpx
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(
                f"{supabase_db.url}/rest/v1/analyses?id=eq.{analysis_id}&select=id",
                headers=supabase_db._get_headers(),
            )
            if res.status_code != 200 or not res.json():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Analyse introuvable.",
                )
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Erreur vérification existence analyse: {e}")

    # Consommation atomique via CreditService
    unlocked, message, remaining_balance = await credit_service.consume_credit_for_analysis(
        user_id=user_id,
        analysis_id=analysis_id,
    )

    if not unlocked:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=message,
        )

    return UnlockAnalysisResponse(
        unlocked=True,
        message=message,
        remaining_credits=remaining_balance,
        analysis_id=analysis_id,
    )


@router.get("/analyses/{analysis_id}/status")
async def get_analysis_unlock_status(
    analysis_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """Vérifie si une analyse a déjà été débloquée pour l'utilisateur connecté."""
    user_id = str(current_user["id"])
    unlocked = await credit_service.is_analysis_unlocked(user_id, analysis_id)
    return {
        "analysis_id": analysis_id,
        "is_unlocked": unlocked,
    }
