"""Moteur de règles déterministes à coût nul pour SûrCheck AI.
Conforme aux sections 9, 23 et aux règles d'expression neutres et non diffamatoires.
"""

import re
from typing import List, Tuple
from ..schemas import DetectedSignal

# Définition des règles déterministes prioritaires
DEFINED_RULES = [
    {
        "code": "RULE_OTP_PIN",
        "pattern": r"(?i)(code\s*secret|code\s*otp|mot\s*de\s*passe|code\s*de\s*retrait|pin\s*moov|pin\s*mtn|votre\s*pin|mon\s*code)",
        "category": "Sécurité des comptes",
        "weight": 50,
        "title": "Demande d'identifiant secret ou code de validation",
        "advice": "Ne partagez jamais votre code secret ou code OTP. Un opérateur officiel ne vous demandera jamais votre mot de passe.",
    },
    {
        "code": "RULE_MONEY_REQ",
        "pattern": r"(?i)(frais\s*de\s*dossier|frais\s*d['']inscription|caution\s*exig[eé]e|frais\s*de\s*d[eé]blocage|d[eé]p[oô]t\s*pr[eé]alable|commission\s*avant\s*envoi|envoyez\s*(?:d['']abord|rapidement)\s*[0-9]+)",
        "category": "Demande financière",
        "weight": 40,
        "title": "Exigence de versement d'argent préalable",
        "advice": "Refusez tout envoi d'argent ou avance de frais. Les recruteurs sérieux et services officiels ne conditionnent pas une démarche à un paiement Mobile Money.",
    },
    {
        "code": "RULE_URGENCY",
        "pattern": r"(?i)(urgent|imm[eé]diat|dans\s*les\s*24h|imm[eé]diatement|votre\s*compte\s*sera\s*bloqu[eé]|derni[eè]re\s*chance|expire\s*aujourd['']hui|d[eé]lai\s*de\s*rigueur|sous\s*peine\s*de\s*suspension)",
        "category": "Pression psychologique",
        "weight": 30,
        "title": "Pression ou sentiment d'urgence artificielle",
        "advice": "Prenez le temps d'analyser la situation. L'empressement est conçu pour empêcher la vérification rationnelle.",
    },
    {
        "code": "RULE_UNREAL_GAIN",
        "pattern": r"(?i)(tirage\s*au\s*sort|vous\s*avez\s*gagn[eé]|somme\s*de\s*[0-9]+(?:\s*000|\s*millions)|subvention\s*exceptionnelle|aide\s*financi[eè]re\s*accord[eé]e|b[eé]n[eé]ficiaire\s*s[eé]lectionn[eé])",
        "category": "Promesse de gain",
        "weight": 40,
        "title": "Promesse de gain, loterie ou subvention",
        "advice": "Si vous n'avez initié aucune démarche ou souscrit à aucun jeu certifié, vous ne pouvez pas être désigné bénéficiaire.",
    },
    {
        "code": "RULE_SUSPICIOUS_LINK",
        "pattern": r"(?i)(https?://(?:bit\.ly|tinyurl\.com|is\.gd|t\.co|cutt\.ly|rb\.gy|wa\.link|goo\.su)/[a-zA-Z0-9_-]+)",
        "category": "Lien de redirection",
        "weight": 30,
        "title": "Présence d'un lien raccourci ou masqué",
        "advice": "Évitez d'ouvrir les liens courts dont l'adresse finale est cachée. Les organisations officielles communiquent sur leur domaine propre.",
    },
    {
        "code": "RULE_USURPATION_MOMO",
        "pattern": r"(?i)(service\s*client\s*mtn|assistance\s*moov|direction\s*mtn|moov\s*money\s*b[eé]nin|mtn\s*momo\s*bj|agent\s*agr[eé][eé]\s*momo)",
        "category": "Identité d'opérateur",
        "weight": 35,
        "title": "Mention non authentifiée d'un opérateur Mobile Money béninois",
        "advice": "Joignez toujours l'opérateur officiel par le canal direct de votre combiné (ex: 111 pour MTN Bénin, 100 pour Moov Bénin).",
    },
    {
        "code": "RULE_FALSE_TRANSFER_REVERSAL",
        "pattern": r"(?i)(erreur\s*de\s*transfert|veuillez\s*renvoyer|d[eé]p[oô]t\s*erron[eé]|annulation\s*de\s*la\s*transaction|fonds\s*envoy[eé]s\s*par\s*erreur)",
        "category": "Fausse transaction",
        "weight": 35,
        "title": "Scénario de prétendu transfert envoyé par erreur",
        "advice": "Vérifiez votre solde réel via votre menu officiel (*880# ou *855#) sans vous fier aux SMS reçus d'un numéro ordinaire.",
    },
    {
        "code": "RULE_PARCEL_CUSTOMS",
        "pattern": r"(?i)(colis|paquet|envoi|livraison|dhl|fedex|ups|chronopost).*(?:bloqu[eé]|retenu|en\s*attente|douane|d[eé]douanement|frais\s*de\s*livraison|frais\s*de\s*traitement)",
        "category": "Arnaque colis/douane",
        "weight": 40,
        "title": "Arnaque au colis bloqué ou frais de douane frauduleux",
        "advice": "Les vraies entreprises de livraison ne demandent jamais de paiement Mobile Money par SMS. Contactez directement le service client officiel.",
    },
    {
        "code": "RULE_CRYPTO_INVESTMENT",
        "pattern": r"(?i)(bitcoin|crypto|cryptomonnaie|binance|forex|trading\s*automatique|plateforme\s*d['']investissement|investissement\s*garanti|rendement\s*assur[eé]|multipliez\s*vos\s*gains)",
        "category": "Faux investissement crypto",
        "weight": 38,
        "title": "Promesse d'investissement crypto ou trading suspect",
        "advice": "Méfiez-vous des promesses de gains rapides et garantis. Les investissements légitimes comportent toujours des risques clairement mentionnés.",
    },
    {
        "code": "RULE_VISA_IMMIGRATION",
        "pattern": r"(?i)(visa|immigration|ambassade|consulat|green\s*card|bourse\s*[eé]tudes?|[eé]tudes?\s*[aà]\s*l[''][eé]tranger).*(?:garanti|frais|paiement|versement|caution|s[eé]lectionn[eé])",
        "category": "Arnaque visa/immigration",
        "weight": 37,
        "title": "Arnaque visa, immigration ou bourse d'études",
        "advice": "Les ambassades et programmes officiels ne demandent jamais de paiement Mobile Money. Vérifiez sur les sites officiels gouvernementaux.",
    },
    {
        "code": "RULE_INHERITANCE_SCAM",
        "pattern": r"(?i)(h[eé]ritage|h[eé]ritier|notaire|testament|d[eé]c[eé]d[eé]|défunt|fonds?\s*bloqu[eé]s?|millions?\s*de\s*dollars?|banque\s*centrale|transfert\s*international)",
        "category": "Arnaque à l'héritage",
        "weight": 42,
        "title": "Arnaque à l'héritage ou fonds bloqués",
        "advice": "C'est une arnaque classique internationale. Aucun notaire légitime ne vous contactera par SMS pour un héritage inattendu.",
    },
    {
        "code": "RULE_ROMANTIC_EMERGENCY",
        "pattern": r"(?i)(h[oô]pital|urgence\s*m[eé]dicale|accident|maladie\s*grave|op[eé]ration\s*chirurgicale|frais\s*m[eé]dicaux|soins\s*urgents).*(?:besoin\s*d['']aide|envoie|transfert|aide[-\s]moi)",
        "category": "Urgence médicale suspecte",
        "weight": 32,
        "title": "Urgence médicale ou sentimentale suspecte",
        "advice": "Avant tout transfert, appelez la personne directement pour vérifier. Les arnaqueurs ciblent les émotions en simulant des urgences.",
    },
]


def evaluate_rules(text: str) -> Tuple[List[DetectedSignal], int]:
    """Évalue le texte contre les règles déterministes.
    Retourne la liste des signaux détectés et le score brut cumulé.
    """
    detected_signals: List[DetectedSignal] = []
    total_rule_score = 0

    for rule in DEFINED_RULES:
        match = re.search(rule["pattern"], text)
        if match:
            # Récupérer l'extrait ayant déclenché la règle (max 60 caractères)
            start = max(0, match.start() - 10)
            end = min(len(text), match.end() + 10)
            snippet = text[start:end].strip()

            signal = DetectedSignal(
                code=rule["code"],
                title=rule["title"],
                category=rule["category"],
                weight=rule["weight"],
                evidence=f"...{snippet}..." if len(snippet) < len(text) else snippet,
                advice=rule["advice"],
            )
            detected_signals.append(signal)
            total_rule_score += rule["weight"]

    return detected_signals, total_rule_score
