"""Router pour l'analyse des risques (Textes, Liens).
Conforme aux règles de neutralité et au versioning du moteur.
"""

from fastapi import APIRouter, HTTPException, status, File, UploadFile
from ..schemas import (
    AnalyzeTextRequest,
    AnalyzeUrlRequest,
    AnalysisResult,
    ContentType,
    AnalysisFeedbackRequest,
    RiskLevel,
)
from ..engine.scorer import calculate_risk
from ..engine.normalizer import normalize_url

from ..services.supabase_db import supabase_db
from ..engine.extractor import extract_phone_numbers, extract_urls
from ..schemas import DetectedSignal

router = APIRouter(prefix="/analyze", tags=["Analyse de Risque"])

# Cache local rapide en mémoire (fallback)
IN_MEMORY_ANALYSES = {}
IN_MEMORY_FEEDBACK = []


async def _enrich_with_reputation(result: AnalysisResult, text: str):
    """Enrichit les signaux d'analyse avec la réputation communautaire réelle de Supabase."""
    phones = extract_phone_numbers(text)
    for p in phones:
        rep_count, rep_status = await supabase_db.check_phone_reputation(p)
        if rep_count > 0:
            result.signals.append(
                DetectedSignal(
                    code="SIG_COMMUNITY_REPORT_PHONE",
                    title="Numéro déjà signalé par la communauté",
                    category="Signalement communautaire",
                    weight=min(40, 20 + rep_count * 5),
                    evidence=f"{p} (signalé {rep_count} fois)",
                    advice="Ce numéro a fait l'objet de signalements récents. Redoublez de vigilance.",
                )
            )
            result.risk_score = min(96, result.risk_score + 20)
            if result.risk_score >= 70:
                result.risk_level = RiskLevel.ELEVE
                result.headline = "Risque potentiel élevé détecté"

    urls = extract_urls(text)
    for u in urls:
        try:
            rep_count, phishing_match, rep_status = await supabase_db.check_url_reputation(u["url"])
            if rep_count > 0 or phishing_match:
                result.signals.append(
                    DetectedSignal(
                        code="SIG_COMMUNITY_REPORT_URL",
                        title="Lien ou domaine déjà signalé comme suspect",
                        category="Lien malveillant",
                        weight=45,
                        evidence=u["url"][:40],
                        advice="N'ouvrez pas ce lien et ne renseignez aucune coordonnée bancaire ou personnelle.",
                    )
                )
                result.risk_score = max(result.risk_score, 75)
                result.risk_level = RiskLevel.ELEVE
                result.headline = "Risque potentiel élevé détecté"
        except Exception as e:
            # Si vérification URL impossible, passer en INDETERMINE pour honnêteté (Section 5.3)
            import logging
            logger = logging.getLogger("surcheck.analyze")
            logger.warning(f"Vérification URL échouée pour {u['url'][:30]}: {e}")
            
            # Ne pas forcer un verdict positif si la vérification a échoué
            if result.risk_level == RiskLevel.FAIBLE:
                result.risk_level = RiskLevel.INDETERMINE
                result.confidence_level = "incertain"
                result.summary += " Nous n'avons pas pu vérifier complètement ce lien."


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
    await _enrich_with_reputation(result, request.content)

    # Persistance Supabase (asynchrone) + Cache mémoire
    IN_MEMORY_ANALYSES[result.id] = result
    await supabase_db.save_analysis(result, request.content, user_id=request.user_id)

    return result


@router.post("/url", response_model=AnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_url(request: AnalyzeUrlRequest):
    """Analyse un lien ou une URL suspecte sans ouvrir la cible sur le serveur.
    Examine la structure, le domaine et les indicateurs de masquage.
    """
    normalized = normalize_url(request.url)
    result = calculate_risk(normalized, content_type=ContentType.URL)
    await _enrich_with_reputation(result, request.url)

    IN_MEMORY_ANALYSES[result.id] = result
    await supabase_db.save_analysis(result, request.url, user_id=request.user_id)

    return result


@router.post("/image", response_model=AnalysisResult, status_code=status.HTTP_200_OK)
async def analyze_image(file: UploadFile = File(...)):
    """Analyse une capture d'écran de message WhatsApp ou SMS.
    Extrait le texte via OCR éphémère puis exécute le moteur de risque.
    """
    from ..engine.ocr import extract_text_from_image

    if not file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fichier image requis."
        )

    # Lire le contenu du fichier uploadé
    image_bytes = await file.read()
    content_type = file.content_type or "image/jpeg"

    extracted_text, success, ocr_confidence = extract_text_from_image(image_bytes, content_type)
    if not success or not extracted_text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Impossible de lire le texte sur cette capture d'écran. Veuillez saisir directement le texte du message."
        )

    result = calculate_risk(extracted_text, content_type=ContentType.IMAGE)
    
    # Ajuster le niveau de confiance si l'OCR a une faible confiance
    if ocr_confidence < 0.6:
        result.confidence_level = "incertain"
    elif ocr_confidence < 0.8 and result.confidence_level == "elevee":
        result.confidence_level = "moyenne"
    
    await _enrich_with_reputation(result, extracted_text)

    IN_MEMORY_ANALYSES[result.id] = result
    await supabase_db.save_analysis(result, extracted_text)

    return result


@router.get("/{analysis_id}", response_model=AnalysisResult)
async def get_analysis(analysis_id: str):
    """Consulte une analyse passée par son identifiant unique."""
    if analysis_id in IN_MEMORY_ANALYSES:
        return IN_MEMORY_ANALYSES[analysis_id]

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Analyse introuvable ou expirée."
    )


@router.post("/feedback", status_code=status.HTTP_201_CREATED)
async def submit_feedback(feedback: AnalysisFeedbackRequest):
    """Enregistre le retour utilisateur sur l'utilité de l'évaluation."""
    IN_MEMORY_FEEDBACK.append(feedback.model_dump())
    await supabase_db.save_feedback(feedback)
    return {"status": "success", "message": "Merci pour votre retour."}
