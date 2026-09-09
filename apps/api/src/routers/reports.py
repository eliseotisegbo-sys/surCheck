"""Router pour le signalement communautaire et la modération des risques.
Respecte la minimisation des données et le masquage des numéros.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from ..schemas import CreateReportRequest, ReportResponse, ReportStatus, ReportType
from ..engine.reputation import (
    normalize_phone_number,
    hash_phone_number,
    mask_phone_number,
    mask_url,
    hash_url,
)
from ..engine.normalizer import normalize_url

from ..services.supabase_db import supabase_db

router = APIRouter(prefix="/reports", tags=["Signalement Communautaire"])

IN_MEMORY_REPORTS = []


class UpdateReportStatusRequest(BaseModel):
    status: ReportStatus
    moderation_notes: Optional[str] = None


@router.post("", response_model=ReportResponse, status_code=status.HTTP_201_CREATED)
async def submit_report(request: CreateReportRequest):
    """Enregistre un signalement communautaire.
    Le numéro ou lien est normalisé, haché et masqué avant indexation.
    """
    if request.report_type == ReportType.PHONE:
        normalized = normalize_phone_number(request.target)
        target_hash = hash_phone_number(normalized)
        target_masked = mask_phone_number(normalized)
    elif request.report_type == ReportType.URL:
        normalized = normalize_url(request.target)
        target_hash = hash_url(normalized)
        target_masked = mask_url(normalized)
    else:
        target_hash = hash_phone_number(request.target[:50])
        target_masked = "Extrait de message masqué"

    report_id = str(uuid.uuid4())
    now = datetime.now()

    report_entry = {
        "id": report_id,
        "target_masked": target_masked,
        "target_hash": target_hash,
        "report_type": request.report_type,
        "category": request.category,
        "description": request.description,
        "evidence_url": request.evidence_url,
        "status": ReportStatus.NOUVEAU,
        "created_at": now,
    }
    IN_MEMORY_REPORTS.append(report_entry)

    # Persistance asynchrone Supabase
    await supabase_db.save_report(request)

    return ReportResponse(
        id=report_id,
        target_masked=target_masked,
        report_type=request.report_type,
        category=request.category,
        status=ReportStatus.NOUVEAU,
        message="Signalement enregistré. Il sera examiné par l'équipe de modération.",
        created_at=now,
    )


@router.get("", response_model=List[ReportResponse])
async def list_reports():
    """Liste les signalements enregistrés (avec cibles masquées)."""
    return [
        ReportResponse(
            id=r["id"],
            target_masked=r["target_masked"],
            report_type=r["report_type"],
            category=r["category"],
            status=r["status"],
            message="",
            created_at=r["created_at"],
        )
        for r in IN_MEMORY_REPORTS
    ]


@router.patch("/{report_id}/status")
async def update_report_status(report_id: str, payload: UpdateReportStatusRequest):
    """Met à jour le statut de modération d'un signalement."""
    for report in IN_MEMORY_REPORTS:
        if report["id"] == report_id:
            report["status"] = payload.status
            report["moderation_notes"] = payload.moderation_notes
            return {
                "status": "success",
                "message": f"Statut mis à jour : {payload.status.value}",
            }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Signalement introuvable."
    )
