"""Module de classification Machine Learning (scikit-learn) pour SûrCheck AI.
Utilise TF-IDF et Régression Logistique calibrée sur un corpus béninois et ouest-africain.
"""

from typing import Tuple, Dict
from .normalizer import normalize_text, strip_accents

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

# Corpus d'entraînement initial (Messages réels et synthétiques calibrés pour le Bénin)
TRAINING_DATA = [
    # 1. Scénarios Mobile Money suspects
    ("URGENT: Erreur de transfert MTN Momo de 45.000 FCFA sur votre compte. Veuillez renvoyer le montant au 97000000 sous peine de poursuites.", "Mobile Money"),
    ("Moov Money: Votre compte est temporairement restreint. Cliquez ici pour debloquer votre solde et entrez votre code PIN.", "Mobile Money"),
    ("Votre compte MTN Mobile Money a reçu 150000 FCFA. Pour confirmer la réception appelez vite le service client et validez le code reçu par SMS.", "Mobile Money"),
    ("Bonjour cher client Moov, nous effectuons la mise a jour de votre carte SIM. Envoyez votre code secret pour eviter la coupure.", "Mobile Money"),

    # 2. Scénarios Faux Recrutement
    ("L'UNICEF recrute urgemment 50 agents de terrain a Cotonou et Parakou. Salaire: 350.000 FCFA. Envoyez 5.000 FCFA de frais de dossier par Momo.", "Faux emploi"),
    ("Offre d'emploi PNUD Benin. Postes disponibles immédiatement. Veuillez transferer la caution d'inscription de 10.000 F au tresorier avant l'entretien.", "Faux emploi"),
    ("Recrutement direct au Port Autonome de Cotonou. Tous diplômes acceptés. Envoyez vos frais de visite médicale au 66000000.", "Faux emploi"),
    ("Avis de recrutement ambassade de France. Inscription gratuite mais caution remboursable de 7.500 FCFA demandée.", "Faux emploi"),

    # 3. Scénarios Faux Investissement
    ("Multipliez vos sous en 24 heures ! Investissez 20.000 FCFA et recevez 100.000 FCFA par MTN Mobile Money. Plateforme certifiée et garantie.", "Faux investissement"),
    ("Tontine VIP en ligne: Deposez 50.000 F aujourd'hui, gagnez 250.000 F demain. Ne ratez pas cette opportunité unique.", "Faux investissement"),
    ("Trading automatisé sans risque pour le Bénin. Envoyez vos fonds et recevez vos gains chaque matin sur votre compte Momo.", "Faux investissement"),

    # 4. Scénarios Faux Cadeau / Loterie
    ("Félicitations ! Votre numéro a été tiré au sort lors de la tombola annuelle MTN Bénin. Vous gagnez 1.000.000 FCFA. Contactez vite le 96000000.", "Faux cadeau"),
    ("Promo spéciale indépendance: Moov Bénin vous offre 10 Go d'internet et 50.000 FCFA. Cliquez sur ce lien pour réclamer votre cadeau.", "Faux cadeau"),
    ("Vous avez été sélectionné pour recevoir une subvention présidentielle de 200.000 FCFA. Réclamez avant ce soir 23h59.", "Faux cadeau"),

    # 5. Scénarios Phishing / Liens
    ("Alerte sécurité: Connexion inhabituelle à votre compte bancaire BOA. Cliquez sur http://boa-securite-benin.com pour confirmer vos identifiants.", "Phishing"),
    ("Votre colis DHL est bloqué en douane à Cotonou. Payez les frais de dédouanement de 3.000 FCFA sur http://bit.ly/dhl-bj-tax pour débloquer.", "Phishing"),

    # 6. Messages Légitimes (Contre-exemples variés pour éviter les faux positifs)
    ("Bonjour maman, j'ai bien reçu le virement pour les courses. Merci beaucoup, à ce soir.", "Légitime"),
    ("Salut, tu as envoyé le rapport de réunion au directeur ? Confirme-moi quand c'est fait s'il te plaît.", "Légitime"),
    ("Bonjour monsieur, votre commande de chaussures est prête. La livraison est prévue demain à 14h à Akpakpa.", "Légitime"),
    ("Tu viens à l'église ce dimanche ? On a répétition de chorale à 16 heures.", "Légitime"),
    ("Votre solde bancaire au 05/09 est de 85.000 FCFA. Merci de votre confiance.", "Légitime"),
    ("Le cours d'informatique est déplacé en salle B12 demain matin à 8h. Passez le message.", "Légitime"),
    ("Bonjour Jean, tu confirmes pour la réunion de demain à 10h ?", "Légitime"),
    ("Bonne fête à toi et à toute la famille. Que cette nouvelle année vous apporte la santé et la paix.", "Légitime"),
    ("Papa, s'il te plaît rappelle-moi quand tu seras disponible. C'est urgent pour les médicaments.", "Légitime"),
    ("Le rapport d'activité mensuel est finalisé. Je viens de le déposer sur le bureau de la secrétaire.", "Légitime"),
    ("Bonsoir, peux-tu me faire parvenir les documents de la soutenance par WhatsApp ? Merci d'avance.", "Légitime"),
    ("Bonjour Paul, nous serons là pour le déjeuner vers 13 heures avec les enfants.", "Légitime"),
    ("Merci pour ton accueil chaleureux à Porto-Novo hier. On se recontacte la semaine prochaine.", "Légitime"),
]


class ScamClassifier:
    """Classificateur hybride scikit-learn avec repli algorithmique local."""

    def __init__(self):
        self.pipeline = None
        self.is_trained = False
        if HAS_SKLEARN:
            self.pipeline = Pipeline([
                ("tfidf", TfidfVectorizer(
                    preprocessor=lambda t: normalize_text(strip_accents(t)),
                    ngram_range=(1, 2),
                    min_df=1,
                )),
                ("clf", LogisticRegression(class_weight="balanced", C=1.0, max_iter=300)),
            ])
            self._train_initial_model()

    def _train_initial_model(self):
        """Entraîne le modèle scikit-learn sur le corpus initial."""
        if not HAS_SKLEARN:
            return
        texts, labels = zip(*TRAINING_DATA)
        self.pipeline.fit(texts, labels)
        self.is_trained = True

    def predict(self, text: str) -> Tuple[str, float]:
        """Prédit la catégorie probable et le score de suspicion (0.0 à 1.0)."""
        cleaned = normalize_text(strip_accents(text))

        if HAS_SKLEARN and self.is_trained:
            predicted_category = self.pipeline.predict([cleaned])[0]
            classes = list(self.pipeline.classes_)
            probabilities = self.pipeline.predict_proba([cleaned])[0]

            if "Légitime" in classes:
                legitimate_idx = classes.index("Légitime")
                legit_prob = probabilities[legitimate_idx]
                if predicted_category == "Légitime":
                    risk_probability = max(0.05, min(0.20, 1.0 - legit_prob))
                else:
                    risk_probability = 1.0 - legit_prob
            else:
                risk_probability = 0.5

            return predicted_category, float(risk_probability)

        # Algorithme de repli résilient autonome sans scikit-learn
        suspicious_keywords = {
            "Mobile Money": ["transfert", "momo", "moov", "mtn", "erreur", "renvoyer", "solde", "pin", "bloque"],
            "Faux emploi": ["recrutement", "unicef", "pnud", "dossier", "caution", "frais", "ambassade", "embauche"],
            "Faux investissement": ["multipliez", "tontine", "rendement", "investissez", "gagnez", "vip"],
            "Faux cadeau": ["felicitations", "gagne", "tombola", "loterie", "subvention", "cadeau"],
            "Phishing": ["connexion", "securite", "confirmer", "identifiants", "compte", "douane", "tax"],
        }

        best_category = "Légitime"
        max_matches = 0
        words = cleaned.split()

        for cat, kw_list in suspicious_keywords.items():
            matches = sum(1 for kw in kw_list if kw in cleaned)
            if matches > max_matches:
                max_matches = matches
                best_category = cat

        risk_prob = min(max_matches * 0.25, 0.90) if max_matches > 0 else 0.10
        return best_category, float(risk_prob)


# Instance globale réutilisable
scam_classifier = ScamClassifier()

