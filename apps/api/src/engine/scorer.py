"""Moteur d'agrégation, de calibration et d'explication du score SûrCheck AI.
Conforme aux sections 9, 21, 23 et 33 du Cahier des Charges.
"""

import uuid
from typing import List
from ..schemas import AnalysisResult, RiskLevel, ContentType, DetectedSignal
from .normalizer import normalize_text
from .extractor import extract_urls, extract_phone_numbers, extract_amounts
from .rules import evaluate_rules
from .classifier import scam_classifier


def calculate_risk(text: str, content_type: ContentType = ContentType.TEXT) -> AnalysisResult:
    """Exécute le pipeline d'analyse hybride complet :
    1. Normalisation
    2. Extraction d'entités
    3. Règles déterministes
    4. Modèle ML scikit-learn
    5. Agrégation et calibration
    6. Explications factuelles
    """
    cleaned_text = normalize_text(text)

    # 1. Extraction d'entités
    extracted_urls = extract_urls(text)
    extracted_phones = extract_phone_numbers(text)
    extracted_amounts = extract_amounts(text)

    # 2. Évaluation des règles déterministes
    signals, rule_score = evaluate_rules(text)

    # 3. Évaluation du modèle ML
    ml_category, ml_risk_prob = scam_classifier.predict(text)
    ml_score = int(ml_risk_prob * 100)

    # 4. Signaux supplémentaires liés aux entités
    for url_data in extracted_urls:
        if url_data["is_shortener"]:
            # Vérifier si pas déjà capturé par la règle
            if not any(s.code == "RULE_SUSPICIOUS_LINK" for s in signals):
                signals.append(DetectedSignal(
                    code="SIG_SHORT_URL",
                    title="Lien raccourci masquant l'adresse finale",
                    category="Lien suspect",
                    weight=25,
                    evidence=url_data["url"],
                    advice="Méfiez-vous des liens raccourcis envoyés par SMS ou WhatsApp.",
                ))
                rule_score += 25

    # 5. Agrégation pondérée (Règles déterministes = 70%, Modèle ML = 30%)
    if rule_score > 0:
        raw_score = int((rule_score * 0.70) + (ml_score * 0.30))
    else:
        if ml_category == "Légitime":
            raw_score = min(ml_score, 18)
        else:
            raw_score = int(ml_score * 0.85)

    # Si une règle critique de code secret ou fausse transaction est déclenchée, plancher à 75
    critical_codes = {"RULE_OTP_PIN", "RULE_FALSE_TRANSFER_REVERSAL"}
    if any(s.code in critical_codes for s in signals):
        raw_score = max(raw_score, 75)

    # Bornage strict entre 0 et 100 (sans jamais afficher 0 absolu ou 100 absolu pour éviter l'illusion de certitude absolue)
    if len(signals) == 0 and (ml_category == "Légitime" or ml_score <= 25):
        final_score = min(max(raw_score, 5), 22)
    else:
        final_score = min(max(raw_score, 10), 96)

    # 6. Détermination du niveau de risque
    if final_score >= 70:
        risk_level = RiskLevel.ELEVE
        headline = "Risque potentiel élevé détecté"
        summary = (
            "Plusieurs indicateurs critiques ont été identifiés dans ce contenu. "
            "Il est fortement recommandé de ne pas effectuer de transfert et de ne communiquer aucun code."
        )
    elif final_score >= 30:
        risk_level = RiskLevel.PRUDENCE
        headline = "Plusieurs signaux nécessitent une vérification"
        summary = (
            "Des éléments inhabituels ou des formulations suspectes ont été relevés. "
            "Une vérification préalable auprès de la source officielle est indispensable avant tout engagement."
        )
    else:
        risk_level = RiskLevel.FAIBLE
        headline = "Aucun signal majeur détecté dans les éléments analysés"
        summary = (
            "L'analyse n'a pas mis en évidence de demande de code, d'urgence artificielle ou de lien malveillant connu. "
            "Restez néanmoins vigilant lors de tout échange financier."
        )

    # Détermination de la catégorie principale
    if ml_category != "Légitime":
        final_category = ml_category
    elif signals:
        final_category = signals[0].category
    else:
        final_category = "Message ordinaire"

    # Recommandations concrètes d'action ("Que faire maintenant ?")
    recommendations: List[str] = []
    if risk_level == RiskLevel.ELEVE:
        recommendations.append("Ne communiquez jamais votre code secret, mot de passe ou code OTP.")
        recommendations.append("N'envoyez aucun frais ni caution par Mobile Money.")
        recommendations.append("En cas de doute sur un prétendu agent, appelez le numéro vert officiel de l'opérateur (111 pour MTN, 100 pour Moov).")
    elif risk_level == RiskLevel.PRUDENCE:
        recommendations.append("Vérifiez l'identité de l'expéditeur par un canal indépendant avant de poursuivre.")
        recommendations.append("Ne cliquez pas sur les liens reçus d'un numéro inconnu.")
        recommendations.append("Si une somme d'argent vous est demandée pour un recrutement, refusez immédiatement.")
    else:
        recommendations.append("Conservez toujours vos identifiants confidentiels.")
        recommendations.append("Vérifiez toujours votre solde réel sur votre téléphone (*880# ou *855#) en cas de message de transfert.")

    # Niveau de confiance
    if len(text.strip().split()) < 4:
        confidence = "incertain"
    elif len(signals) >= 2 or risk_level == RiskLevel.FAIBLE:
        confidence = "elevee"
    else:
        confidence = "moyenne"

    return AnalysisResult(
        id=str(uuid.uuid4()),
        content_type=content_type,
        risk_score=final_score,
        risk_level=risk_level,
        category=final_category,
        confidence_level=confidence,
        headline=headline,
        summary=summary,
        signals=signals,
        recommendations=recommendations,
        engine_version="v1.0.0",
    )
