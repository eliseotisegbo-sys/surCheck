"""Schémas Pydantic stricts pour les requêtes et réponses de l'API SûrCheck AI.
Conformes au Cahier des Charges et aux règles rédactionnelles.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    FAIBLE = "faible"
    PRUDENCE = "prudence"
    ELEVE = "eleve"
    INDETERMINE = "indetermine"


class ContentType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    URL = "url"


class ReportStatus(str, Enum):
    NOUVEAU = "nouveau"
    EN_VERIFICATION = "en_verification"
    CONFIRME_ELEMENTS_SUFFISANTS = "confirme_elements_suffisants"
    NON_CONFIRME = "non_confirme"
    CONTESTE = "conteste"
    RETIRE = "retire"


class ReportType(str, Enum):
    PHONE = "phone"
    URL = "url"
    MESSAGE = "message"
    PAGE = "page"


# --- ANALYSE ---

class AnalyzeTextRequest(BaseModel):
    content: str = Field(
        ...,
        min_length=3,
        max_length=15000,
        description="Le message texte, SMS ou message WhatsApp à vérifier.",
        examples=["Félicitations, votre numéro MTN a gagné 500 000 FCFA. Envoyez votre code secret pour valider."]
    )
    user_id: Optional[str] = Field(None, description="Identifiant utilisateur si authentifié")


class AnalyzeUrlRequest(BaseModel):
    url: str = Field(
        ...,
        min_length=4,
        max_length=2048,
        description="L'URL ou le lien suspect à analyser.",
        examples=["https://bit.ly/momo-promo-bj"]
    )
    user_id: Optional[str] = Field(None, description="Identifiant utilisateur si authentifié")


class DetectedSignal(BaseModel):
    code: str = Field(..., description="Code unique de la règle ou du signal détecté")
    title: str = Field(..., description="Intitulé factuel et neutre du signal")
    category: str = Field(..., description="Catégorie (Pression, Argent, Code, etc.)")
    weight: int = Field(..., description="Pondération dans le calcul du score")
    evidence: Optional[str] = Field(None, description="Extrait anonymisé ayant déclenché le signal")
    advice: str = Field(..., description="Conseil réflexe associé à ce signal")


class AnalysisResult(BaseModel):
    id: str = Field(..., description="Identifiant unique de l'analyse")
    content_type: ContentType
    risk_score: int = Field(..., ge=0, le=100, description="Score de risque de 0 à 100")
    risk_level: RiskLevel = Field(..., description="Niveau de risque : faible, prudence ou eleve")
    category: str = Field(..., description="Catégorie identifiée (Mobile Money, Phishing, Faux emploi, etc.)")
    confidence_level: str = Field(..., description="Niveau de certitude : elevee, moyenne, incertain")
    headline: str = Field(..., description="Formulation neutre et conforme aux règles juridiques")
    summary: str = Field(..., description="Explication factuelle du résultat")
    signals: List[DetectedSignal] = Field(default_factory=list, description="Liste des signaux détectés")
    recommendations: List[str] = Field(default_factory=list, description="Actions concrètes recommandées")
    engine_version: str = Field(..., description="Version du moteur d'analyse pour traçabilité")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# --- SIGNALEMENT COMMUNAUTAIRE ---

class CreateReportRequest(BaseModel):
    report_type: ReportType = Field(..., description="Type de cible signalée")
    target: str = Field(..., min_length=2, max_length=500, description="Numéro, lien ou extrait suspect")
    category: str = Field(..., description="Catégorie de la tentative suspectée")
    description: str = Field(..., min_length=5, max_length=3000, description="Contexte et détails sans diffamation")
    evidence_url: Optional[str] = Field(None, description="Preuve éventuelle (capture d'écran hébergée)")


class ReportResponse(BaseModel):
    id: str
    target_masked: str
    report_type: ReportType
    category: str
    status: ReportStatus
    message: str
    created_at: datetime


# --- FEEDBACK ---

class AnalysisFeedbackRequest(BaseModel):
    analysis_id: str
    is_helpful: bool
    perceived_accuracy: Optional[str] = None
    user_comment: Optional[str] = None


# --- AUTHENTIFICATION ---

class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_name: str
    user_email: str
    free_quota: int
    paid_credits: int
