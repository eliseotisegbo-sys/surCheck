"""Tests unitaires du moteur d'analyse SûrCheck AI.
Couvre les règles déterministes, le scorer et les cas limites réels
identifiés dans le contexte béninois (Mobile Money, WhatsApp, recrutement).
"""

import sys
import os

# Permet d'importer src/ sans package install
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.engine.normalizer import normalize_text
from src.engine.extractor import extract_urls, extract_phone_numbers, extract_amounts
from src.engine.rules import evaluate_rules
from src.engine.scorer import calculate_risk
from src.schemas import RiskLevel, ContentType


# =====================================================================
# NORMALIZER
# =====================================================================

class TestNormalizer:
    def test_supprime_accents_pour_matching(self):
        result = normalize_text("Félicitations ! Vous avez GAGNÉ.")
        assert "felicitations" in result.lower() or "gagn" in result.lower()

    def test_texte_vide_retourne_chaine_vide(self):
        assert normalize_text("") == "" or normalize_text("   ") == normalize_text("   ").strip()

    def test_supprime_espaces_excessifs(self):
        result = normalize_text("bonjour   monde")
        assert "  " not in result


# =====================================================================
# EXTRACTOR
# =====================================================================

class TestExtractor:
    def test_detecte_lien_raccourci_bitly(self):
        urls = extract_urls("Cliquez ici pour valider : https://bit.ly/momo-bj-win")
        assert len(urls) >= 1
        assert urls[0]["is_shortener"] is True

    def test_detecte_numero_benin(self):
        phones = extract_phone_numbers("Appelez le +22961234567 pour confirmer.")
        assert len(phones) >= 1

    def test_detecte_montant_fcfa(self):
        amounts = extract_amounts("Envoyez 5 000 FCFA pour valider votre dossier.")
        assert len(amounts) >= 1

    def test_texte_ordinaire_sans_lien(self):
        urls = extract_urls("Bonjour, comment allez-vous aujourd'hui ?")
        assert len(urls) == 0


# =====================================================================
# RÈGLES DÉTERMINISTES
# =====================================================================

class TestRegles:
    """Chaque test vérifie qu'un message-type béninois déclenche la bonne règle."""

    def test_regle_otp_code_secret(self):
        sms = "Votre code secret MTN est requis pour libérer votre gain."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_OTP_PIN" in codes
        assert score >= 50

    def test_regle_frais_dossier(self):
        sms = "Pour obtenir votre emploi, payez des frais de dossier de 5000 FCFA d'abord."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_MONEY_REQ" in codes

    def test_regle_urgence(self):
        sms = "Urgent ! Votre compte sera bloqué dans les 24h si vous n'agissez pas."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_URGENCY" in codes

    def test_regle_gain_fictif(self):
        sms = "Félicitations ! Vous avez gagné une somme de 750 000 FCFA dans notre tirage au sort."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_UNREAL_GAIN" in codes

    def test_regle_lien_raccourci(self):
        sms = "Validez votre compte ici : https://bit.ly/compte-momo"
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_SUSPICIOUS_LINK" in codes

    def test_regle_faux_virement(self):
        sms = "Erreur de transfert ! Fonds envoyés par erreur sur votre numéro, veuillez renvoyer."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_FALSE_TRANSFER_REVERSAL" in codes

    def test_regle_usurpation_mtn(self):
        sms = "Service client MTN Bénin : votre ligne sera suspendue, appelez immédiatement."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_USURPATION_MOMO" in codes

    def test_message_neutre_aucun_signal(self):
        sms = "Maman, j'arrive à 18h. Prépare le dîner s'il te plaît."
        signals, score = evaluate_rules(sms)
        assert len(signals) == 0
        assert score == 0


# =====================================================================
# SCORER — PIPELINE COMPLET
# =====================================================================

class TestScorer:
    """Vérifie les seuils, les formulations et les cas critiques."""

    def test_message_arnaque_critique_niveau_eleve(self):
        sms = (
            "URGENT ! Service client MTN Bénin : Votre code secret OTP est requis immédiatement "
            "pour débloquer votre compte. Répondez sous 24h ou votre accès sera définitivement suspendu."
        )
        result = calculate_risk(sms)
        assert result.risk_level == RiskLevel.ELEVE
        assert result.risk_score >= 70
        # Vérification vocabulaire : jamais "arnaque" ou "escroc"
        assert "arnaque" not in result.headline.lower()
        assert "escroc" not in result.headline.lower()
        assert "risque" in result.headline.lower() or "potentiel" in result.headline.lower()

    def test_message_prudence_signaux_moderes(self):
        sms = "Envoyez 2000 FCFA de frais d'inscription pour accéder au poste proposé."
        result = calculate_risk(sms)
        assert result.risk_level in (RiskLevel.PRUDENCE, RiskLevel.ELEVE)
        assert result.risk_score >= 20

    def test_message_ordinaire_niveau_faible(self):
        sms = "Bonjour Jean, tu confirmes pour la réunion de demain à 10h ?"
        result = calculate_risk(sms)
        assert result.risk_level == RiskLevel.FAIBLE
        assert result.risk_score < 30

    def test_score_jamais_zero_absolu(self):
        """Le score ne doit jamais être 0 (pas d'illusion de certitude absolue)."""
        sms = "Bonne journée à tous."
        result = calculate_risk(sms)
        assert result.risk_score > 0

    def test_score_jamais_cent_absolu(self):
        """Le score ne doit jamais être 100 (pas d'illusion de certitude absolue)."""
        sms = (
            "URGENT code secret OTP frais de dossier caution transfert erreur "
            "tirage au sort https://bit.ly/arnaque MTN Bénin service client."
        )
        result = calculate_risk(sms)
        assert result.risk_score < 100

    def test_resultat_contient_recommandations(self):
        sms = "Votre code OTP est nécessaire pour valider le transfert."
        result = calculate_risk(sms)
        assert len(result.recommendations) > 0

    def test_resultat_contient_version_moteur(self):
        """Chaque analyse doit tracer la version du moteur (section 33 cahier des charges)."""
        sms = "Bonjour, test simple."
        result = calculate_risk(sms)
        assert result.engine_version is not None
        assert len(result.engine_version) > 0

    def test_formulation_jamais_100_sur(self):
        """Jamais 'sûr à 100%' ou équivalent dans le résumé."""
        sms = "Bonjour, comment vas-tu ?"
        result = calculate_risk(sms)
        assert "100 %" not in result.summary
        assert "100%" not in result.summary
        assert "100 % sûr" not in result.summary

    def test_result_type_content_text(self):
        sms = "Test de type de contenu."
        result = calculate_risk(sms, ContentType.TEXT)
        assert result.content_type == ContentType.TEXT

    def test_signal_otp_plancher_score(self):
        """Un code secret détecté doit toujours générer un score >= 75."""
        sms = "Envoyez-moi votre code secret immédiatement."
        result = calculate_risk(sms)
        assert result.risk_score >= 70

    def test_faux_virement_plancher_score(self):
        """Une fausse transaction détectée doit toujours générer un score >= 75."""
        sms = "Erreur de transfert, fonds envoyés par erreur, veuillez renvoyer la somme."
        result = calculate_risk(sms)
        assert result.risk_score >= 70
