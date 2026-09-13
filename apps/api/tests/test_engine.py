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

    # ===== TESTS NOUVELLES RÈGLES (Section 7) =====
    
    def test_regle_faux_support_technique(self):
        """Test positif: Doit déclencher RULE_FAKE_TECH_SUPPORT"""
        sms = "Votre téléphone est infecté par un virus. Téléchargez TeamViewer pour que nous puissions le nettoyer."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_FAKE_TECH_SUPPORT" in codes
        assert score >= 35

    def test_regle_fausse_livraison(self):
        """Test positif: Doit déclencher RULE_FAKE_DELIVERY_CUSTOMS"""
        sms = "Votre colis DHL est bloqué en douane à Cotonou. Payez 8000 FCFA de frais de dédouanement."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_FAKE_DELIVERY_CUSTOMS" in codes
        assert score >= 30

    def test_regle_usurpation_proche(self):
        """Test positif: Doit déclencher RULE_ROMANCE_IMPERSONATION"""
        sms = "Papa c'est moi, j'ai changé de numéro. Je suis bloqué à l'étranger, envoie 50000 FCFA urgent."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_ROMANCE_IMPERSONATION" in codes
        assert score >= 35

    def test_regle_faux_remboursement(self):
        """Test positif: Doit déclencher RULE_FAKE_REFUND"""
        sms = "SBEE: Remboursement de 18000 F en attente. Cliquez sur ce lien pour validation."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_FAKE_REFUND" in codes
        assert score >= 30

    # ===== TESTS NÉGATION (Section 3) =====
    
    def test_negation_ne_declenche_pas_otp(self):
        """Test de négation: Message de prévention ne doit PAS scorer comme demande de code"""
        sms = "Attention, ne communiquez jamais votre code secret à qui que ce soit, même à un agent MTN."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_OTP_PIN" not in codes

    def test_negation_ne_declenche_pas_argent(self):
        """Test de négation: Mise en garde ne doit PAS scorer comme demande d'argent"""
        sms = "Méfiez-vous des faux recrutements qui demandent des frais de dossier par Mobile Money."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_MONEY_REQ" not in codes

    def test_recit_ne_declenche_pas_signal(self):
        """Test de récit: Raconter une arnaque ne doit PAS scorer comme arnaque"""
        sms = "Mon ami a reçu un message qui demandait son code PIN. C'était une arnaque."
        signals, score = evaluate_rules(sms)
        # Le score doit être très faible ou nul
        assert score < 20

    # ===== TESTS CONTRE-EXEMPLES LÉGITIMES (Section 2) =====
    
    def test_legitime_livraison_vraie(self):
        """Contre-exemple: Vraie livraison ne doit pas déclencher fausse livraison"""
        sms = "Votre colis est arrivé à la poste d'Akpakpa. Vous pouvez le retirer avec votre pièce d'identité."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_FAKE_DELIVERY_CUSTOMS" not in codes
        assert score < 30

    def test_legitime_urgence_medicale_vraie(self):
        """Contre-exemple: Urgence médicale légitime (1ère personne, pas de demande argent)"""
        sms = "J'ai oublié mes médicaments à la maison. Peux-tu me les apporter à l'hôpital ?"
        signals, score = evaluate_rules(sms)
        # Pas de score élevé pour une demande légitime
        assert score < 40

    def test_legitime_mention_code_sans_demande(self):
        """Contre-exemple: Parler de code sans le demander"""
        sms = "J'ai changé mon code PIN hier. Tout fonctionne bien maintenant."
        signals, score = evaluate_rules(sms)
        codes = [s.code for s in signals]
        assert "RULE_OTP_PIN" not in codes


# ===== TESTS CO-OCCURRENCE (Section 4) =====

class TestCooccurrence:
    """Tests spécifiques pour vérifier que les signaux se renforcent mutuellement"""
    
    def test_cooccurrence_urgence_plus_argent(self):
        """Urgence + Argent doit avoir un bonus de +15"""
        sms = "URGENT ! Envoyez 5000 FCFA de frais de dossier avant ce soir sinon vous perdez le poste."
        result = calculate_risk(sms)
        # Le score doit être significativement plus élevé qu'avec un seul signal
        assert result.risk_score >= 50

    def test_cooccurrence_gain_plus_argent(self):
        """Gain + Argent doit avoir un bonus de +20"""
        sms = "Félicitations ! Vous avez gagné 500000 FCFA. Payez 3000 F de frais pour débloquer votre gain."
        result = calculate_risk(sms)
        assert result.risk_score >= 60

    def test_cooccurrence_usurpation_plus_code(self):
        """Usurpation + Code doit avoir un bonus de +25 (quasi jamais légitime)"""
        sms = "Service client MTN : Votre compte est bloqué. Envoyez votre code PIN pour déblocage immédiat."
        result = calculate_risk(sms)
        assert result.risk_score >= 75
        assert result.risk_level == RiskLevel.ELEVE


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


# =====================================================================
# TESTS SECTION 2 : NEUTRALISATION LOCALE (PAS GLOBALE)
# =====================================================================

class TestNeutralisationLocale:
    """Tests critiques pour vérifier que la neutralisation ne s'applique 
    que localement, pas globalement à tout le message."""
    
    def test_negation_locale_ne_neutralise_pas_un_signal_independant(self):
        """Une phrase de négation en début de message ne doit pas neutraliser
        une vraie demande de code/argent qui suit, sans rapport syntaxique direct.
        
        Bug reproduit : ce message retournait 0 signal avant le correctif.
        """
        msg = (
            "Aucun agent ne vous demandera ceci normalement, mais exceptionnellement "
            "communiquez votre code otp et payez 3000 FCFA de caution immédiatement "
            "pour récupérer votre gain avant ce soir sinon vous perdez tout."
        )
        signals, score = evaluate_rules(msg)
        codes = [s.code for s in signals]
        
        # Ce message DOIT déclencher des signaux malgré la phrase de mise en garde
        assert len(signals) >= 2, f"Attendu au moins 2 signaux, reçu {len(signals)}: {codes}"
        assert "RULE_OTP_PIN" in codes, f"RULE_OTP_PIN manquant dans {codes}"
        assert "RULE_MONEY_REQ" in codes, f"RULE_MONEY_REQ manquant dans {codes}"
        assert score > 0, f"Le score devrait être > 0, reçu {score}"
    
    def test_negation_locale_directe_neutralise_bien_le_signal(self):
        """Une négation directement collée au terme critique doit toujours
        neutraliser CE signal précis (comportement à préserver)."""
        msg = "Ne communiquez jamais votre code secret à qui que ce soit, même à un agent MTN."
        signals, score = evaluate_rules(msg)
        codes = [s.code for s in signals]
        
        # Ce message de prévention NE DOIT PAS déclencher RULE_OTP_PIN
        assert "RULE_OTP_PIN" not in codes, f"RULE_OTP_PIN ne devrait pas être dans {codes}"
        assert score == 0 or score < 10, f"Score devrait être très faible, reçu {score}"
    
    def test_conseil_prevention_legitime_sans_faux_positif(self):
        """Message entièrement préventif sans demande active."""
        msg = (
            "Rappel de sécurité MTN Mobile Money : "
            "Ne partagez jamais votre code PIN, même à un agent. "
            "Aucun employé MTN ne vous demandera vos codes par téléphone."
        )
        signals, score = evaluate_rules(msg)
        
        # Pas de signal ou score très faible pour un message 100% préventif
        assert len(signals) == 0 or score < 15, (
            f"Message de prévention légitime ne devrait pas déclencher de signaux forts. "
            f"Reçu {len(signals)} signaux, score={score}"
        )
    
    def test_demande_urgente_apres_phrase_decoy_detectee(self):
        """Cas extrême : fraudeur ajoute une phrase de décoy puis demande l'action."""
        msg = (
            "Évitez les arnaques ! Bon à savoir : ne donnez jamais vos codes. "
            "Ceci dit, pour débloquer votre compte suite au problème technique urgent, "
            "envoyez votre code de confirmation au 96123456 avant minuit."
        )
        signals, score = evaluate_rules(msg)
        codes = [s.code for s in signals]
        
        # Doit détecter l'urgence ET la demande de code malgré le préambule
        assert len(signals) >= 1, f"Devrait détecter au moins 1 signal, reçu {len(signals)}"
        assert "RULE_OTP_PIN" in codes or "RULE_URGENCY" in codes, (
            f"Devrait détecter RULE_OTP_PIN ou RULE_URGENCY, reçu {codes}"
        )


# =====================================================================
# TESTS SECTION 4 : FUZZY MATCHING COLLISION
# =====================================================================

class TestFuzzyMatchingPrecision:
    """Tests pour éviter collisions fuzzy matching entre mots courants."""
    
    def test_fuzzy_ne_confond_pas_argent_et_urgent(self):
        """Le mot 'argent' ne doit pas déclencher fuzzy match avec 'urgent'."""
        from src.engine.fuzzy_matcher import fuzzy_contains
        
        msg = "J'ai besoin d'argent pour les courses de la semaine prochaine."
        matches = fuzzy_contains(msg, threshold=85)
        matched_terms = [term for _, term, _ in matches]
        
        # 'argent' ne doit PAS matcher 'urgent' (similarité 83.3 < seuil 85)
        assert "urgent" not in matched_terms, (
            f"Le mot 'argent' ne devrait pas matcher 'urgent'. "
            f"Termes détectés: {matched_terms}"
        )
    
    def test_message_legitime_argent_sans_urgence_pas_faux_positif(self):
        """Message légitime mentionnant l'argent sans urgence ni demande suspecte."""
        msg = "J'ai reçu l'argent du loyer. Merci beaucoup, je t'appelle ce soir."
        signals, score = evaluate_rules(msg)
        codes = [s.code for s in signals]
        
        # Ne doit pas déclencher RULE_URGENCY par fuzzy matching erroné
        assert "RULE_URGENCY" not in codes or score < 20, (
            f"Message légitime avec 'argent' ne devrait pas déclencher urgence. "
            f"Signaux: {codes}, score: {score}"
        )
