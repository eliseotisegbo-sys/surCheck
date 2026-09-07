"""Router pour l'analyse des risques (Textes, Liens).
Conforme aux règles de neutralité et au versioning du moteur.
"""

from fastapi import APIRouter, HTTPException, status
from ..schemas import (
    AnalyzeTextRequest,
    AnalyzeUrlRequest,
    AnalysisResult,
    ContentType,
    AnalysisFeedbackRequest,
)
from ..engine.scorer import calculate_risk
from ..engine.normalizer import normalize_url

router = APIRouter(prefix="/analyze", tags=["Analyse de Risque"])

# Stockage temporaire en mémoire pour tests et démo avant connexion Supabase
IN_MEMORY_ANALYSES = {}
IN_MEMORY_FEEDBACK = []


@router.post("/text", response_model=AnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_text(request: AnalyzeTextRequest):
    """Analyse un message suspect (SMS, WhatsApp, offre d'emploi, etc.).
    Retourne le score (0-100), le niveau (Faible, Prudence, Élevé), les signaux et conseils.
    """
    if not request.content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le contenu du message ne peut pas être vide."
        )

    result = calculate_risk(request.content, content_type=ContentType.TEXT)
    IN_MEMORY_ANALYSES[result.id] = result
    return result


@router.post("/url", response_model=AnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_url(request: AnalyzeUrlRequest):
    """Analyse un lien ou une URL suspecte sans ouvrir la cible sur le serveur.
    Examine la structure, le domaine et les indicateurs de masquage.
    """
    normalized = normalize_url(request.url)
    result = calculate_risk(normalized, content_type=ContentType.URL)
    IN_MEMORY_ANALYSES[result.id] = result
    return result


@router.post("/image", response_model=AnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_image(file: bytes = None):
    """Analyse une capture d'écran de message WhatsApp ou SMS.
    Extrait le texte via OCR éphémère puis exécute le moteur de risque.
    """
    from ..engine.ocr import extract_text_from_image

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier image requis."
        )

    extracted_text, success = extract_text_from_image(file, "image/jpeg")
    if not success or not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Impossible de lire le texte sur cette capture d'écran. Veuillez saisir directement le texte du message."
        )

    result = calculate_risk(extracted_text, content_type=ContentType.IMAGE)
    IN_MEMORY_ANALYSES[result.id] = result
    return result


@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: str):
    """Consulte une analyse passée par son identifiant unique."""
    if analysis_id not in IN_MEMORY_ANALYSES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analyse introuvable ou expirée."
        )
    return IN_MEMORY_ANALYSES[analysis_id]


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(feedback: AnalysisFeedbackRequest):
    """Enregistre le retour utilisateur sur l'utilité de l'évaluation."""
    IN_MEMORY_FEEDBACK.append(feedback.dict())
    return {"status": "success", "message": "Merci pour votre retour."}
