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
    ("Service MTN: Votre portefeuille sera suspendu dans 24h. Composez le *880# et entrez votre PIN pour éviter le blocage.", "Mobile Money"),
    ("Transfert Moov Money de 75000 F effectué par erreur vers votre numéro. Remboursez immédiatement au 66123456 avant litige.", "Mobile Money"),

    # 2. Scénarios Faux Recrutement
    ("L'UNICEF recrute urgemment 50 agents de terrain a Cotonou et Parakou. Salaire: 350.000 FCFA. Envoyez 5.000 FCFA de frais de dossier par Momo.", "Faux emploi"),
    ("Offre d'emploi PNUD Benin. Postes disponibles immédiatement. Veuillez transferer la caution d'inscription de 10.000 F au tresorier avant l'entretien.", "Faux emploi"),
    ("Recrutement direct au Port Autonome de Cotonou. Tous diplômes acceptés. Envoyez vos frais de visite médicale au 66000000.", "Faux emploi"),
    ("Avis de recrutement ambassade de France. Inscription gratuite mais caution remboursable de 7.500 FCFA demandée.", "Faux emploi"),
    ("La BCEAO recrute 100 agents. Dépôt de dossier: 15.000 FCFA. Salaire garanti 400.000 FCFA/mois. Contactez le DRH au 95000000.", "Faux emploi"),
    ("Recrutement ONG internationale Bénin. Envoyez frais administratifs 8.000 F avant entretien. Poste assuré.", "Faux emploi"),

    # 3. Scénarios Faux Investissement
    ("Multipliez vos sous en 24 heures ! Investissez 20.000 FCFA et recevez 100.000 FCFA par MTN Mobile Money. Plateforme certifiée et garantie.", "Faux investissement"),
    ("Tontine VIP en ligne: Deposez 50.000 F aujourd'hui, gagnez 250.000 F demain. Ne ratez pas cette opportunité unique.", "Faux investissement"),
    ("Trading automatisé sans risque pour le Bénin. Envoyez vos fonds et recevez vos gains chaque matin sur votre compte Momo.", "Faux investissement"),
    ("Investissement Bitcoin garanti. Minimum 30.000 FCFA, retour 150.000 F en 72h. Plateforme Binance certifiée.", "Faux investissement"),
    ("Forex automatique Bénin: Doublez votre capital chaque semaine. Inscription 10.000 F, gains illimités.", "Faux investissement"),

    # 4. Scénarios Faux Cadeau / Loterie
    ("Félicitations ! Votre numéro a été tiré au sort lors de la tombola annuelle MTN Bénin. Vous gagnez 1.000.000 FCFA. Contactez vite le 96000000.", "Faux cadeau"),
    ("Promo spéciale indépendance: Moov Bénin vous offre 10 Go d'internet et 50.000 FCFA. Cliquez sur ce lien pour réclamer votre cadeau.", "Faux cadeau"),
    ("Vous avez été sélectionné pour recevoir une subvention présidentielle de 200.000 FCFA. Réclamez avant ce soir 23h59.", "Faux cadeau"),
    ("Tirage au sort WhatsApp Bénin: Vous êtes l'heureux gagnant de 500.000 FCFA. Envoyez vos coordonnées pour retrait.", "Faux cadeau"),
    ("Loterie nationale Bénin: Votre ticket a gagné 2.000.000 FCFA. Frais de traitement 15.000 F à envoyer pour déblocage.", "Faux cadeau"),

    # 5. Scénarios Phishing / Liens
    ("Alerte sécurité: Connexion inhabituelle à votre compte bancaire BOA. Cliquez sur http://boa-securite-benin.com pour confirmer vos identifiants.", "Phishing"),
    ("Votre colis DHL est bloqué en douane à Cotonou. Payez les frais de dédouanement de 3.000 FCFA sur http://bit.ly/dhl-bj-tax pour débloquer.", "Phishing"),
    ("FedEx: Votre paquet est en attente. Frais de livraison 5.000 F à payer sur short.io/livraison-bj avant retour expéditeur.", "Phishing"),
    ("Notification Ecobank: Compte bloqué pour activité suspecte. Débloquez sur tinyurl.com/ecobank-bj avec vos codes.", "Phishing"),

    # 6. Scénarios Arnaque Colis/Douane (nouvellement détectés)
    ("Votre colis Amazon est retenu à la douane de Cotonou. Régularisez les frais de 8.000 FCFA pour libération.", "Arnaque colis/douane"),
    ("Chronopost Bénin: Paquet bloqué. Envoyez frais de traitement 6.500 F au 97111111 pour réception.", "Arnaque colis/douane"),
    ("DHL Express: Livraison en attente. Payez taxes douanières 12.000 FCFA sur notre lien sécurisé.", "Arnaque colis/douane"),

    # 7. Scénarios Crypto/Investissement (nouvellement détectés)
    ("Investissez dans la cryptomonnaie avec rendement garanti 300%. Dépôt minimum 25.000 FCFA sur Binance Bénin.", "Faux investissement crypto"),
    ("Bitcoin automatique: Multipliez x10 votre capital en 1 mois. Plateforme sécurisée et certifiée.", "Faux investissement crypto"),
    ("Trading Forex Bénin: Formation gratuite + capital de départ. Versez caution 20.000 F remboursable.", "Faux investissement crypto"),

    # 8. Scénarios Visa/Immigration (nouvellement détectés)
    ("Visa Canada garanti en 30 jours. Frais de dossier ambassade: 45.000 FCFA. Places limitées.", "Arnaque visa/immigration"),
    ("Bourse d'études USA: Vous êtes présélectionné. Envoyez frais administratifs 35.000 F pour validation finale.", "Arnaque visa/immigration"),
    ("Programme immigration France: Dossier accepté. Versez frais consulaires 50.000 FCFA pour rendez-vous.", "Arnaque visa/immigration"),

    # 9. Scénarios Héritage/Fonds bloqués (nouvellement détectés)
    ("Cher bénéficiaire, vous héritez de 5 millions de dollars d'un défunt. Contactez notre notaire pour déblocage des fonds.", "Arnaque à l'héritage"),
    ("Banque Centrale: Fonds de 3.5 millions USD bloqués à votre nom. Frais de transfert 25.000 FCFA pour libération.", "Arnaque à l'héritage"),
    ("Testament: Vous êtes désigné héritier d'une fortune au Bénin. Frais notariaux 40.000 F requis.", "Arnaque à l'héritage"),

    # 10. Scénarios Urgence Médicale/Sentimentale (nouvellement détectés)
    ("Maman c'est moi, mon téléphone est cassé. Je suis à l'hôpital, urgence médicale. Envoie 30.000 F vite.", "Urgence médicale suspecte"),
    ("Papa besoin urgent de 50.000 FCFA pour opération chirurgicale. Mon numéro ne marche plus, envoie au 66999999.", "Urgence médicale suspecte"),
    ("Accident grave de ton frère. Frais médicaux urgents 75.000 F. Transfert immédiat requis à l'hôpital.", "Urgence médicale suspecte"),

    # 11. Messages Légitimes (Contre-exemples variés pour éviter les faux positifs)
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
    ("Rendez-vous chez le médecin confirmé pour lundi 10h. N'oublie pas ton carnet de santé.", "Légitime"),
    ("La réunion du conseil d'administration est reportée au vendredi 15. Ordre du jour inchangé.", "Légitime"),
    ("Salut, j'ai trouvé un bon restaurant à Cotonou. On y va ce weekend ?", "Légitime"),
    ("Ton colis est arrivé à la poste d'Akpakpa. Tu peux le retirer avec ta pièce d'identité.", "Légitime"),
    ("Confirmation de votre inscription à la formation Excel. Début des cours le 20 septembre à l'UAC.", "Légitime"),
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

