"""Moteur de règles déterministes à coût nul pour SûrCheck AI.
Conforme aux sections 9, 23 et aux règles d'expression neutres et non diffamatoires.
"""

import re
from typing import List, Tuple
from ..schemas import DetectedSignal
from .normalizer import has_negation_before, has_narrative_context, normalize_text
from .fuzzy_matcher import enhance_rules_with_fuzzy

# Définition des règles déterministes prioritaires
DEFINED_RULES = [
    {
        "code": "RULE_OTP_PIN",
        "pattern": r"(?i)(code\s*secret|code\s*confidentiel|code\s*otp|code\s*pin|mot\s*de\s*passe|mdp|code\s*de\s*retrait|code\s*de\s*validation|code\s*de\s*confirmation|code\s*d['']activation|code\s*de\s*d[eé]blocage|code\s*de\s*v[eé]rification|num[eé]ro\s*de\s*code|votre\s*code|donnez[-\s]moi\s*le\s*code|communiquez\s*le\s*code|dictez\s*le\s*code|lisez[-\s]moi\s*le\s*code|code\s*re[cç]u\s*par\s*sms|code\s*[aà]\s*4\s*chiffres|code\s*[aà]\s*6\s*chiffres|pin\s*momo|pin\s*mtn|pin\s*moov|ussd\s*\*880|ussd\s*\*855|code\s*marchand|tapez\s*le\s*code\s*que\s*vous\s*avez\s*re[cç]u|partagez\s*le\s*code|le\s*code\s*que\s*vous\s*venez\s*de\s*recevoir|le\s*code\s*la|donne\s*moi\s*le\s*code\s*la|envoie\s*le\s*code\s*que\s*tu\s*as\s*re[cç]u|je\s*vais\s*te\s*dicter\s*un\s*code|c['']est\s*quoi\s*le\s*code\s*sms|lis\s*moi\s*ce\s*qui\s*est\s*[eé]crit\s*dans\s*le\s*message)",
        "category": "Sécurité des comptes",
        "weight": 50,
        "title": "Demande d'identifiant secret ou code de validation",
        "advice": "Ne partagez jamais votre code secret ou code OTP. Un opérateur officiel ne vous demandera jamais votre mot de passe.",
    },
    {
        "code": "RULE_MONEY_REQ",
        "pattern": r"(?i)(frais\s*de\s*dossier|frais\s*d['']inscription|frais\s*de\s*traitement|frais\s*de\s*dossier\s*m[eé]dical|frais\s*de\s*visite\s*m[eé]dicale|caution|caution\s*remboursable|caution\s*de\s*garantie|frais\s*de\s*d[eé]blocage|d[eé]p[oô]t\s*pr[eé]alable|avance|acompte\s*obligatoire|commission\s*avant\s*retrait|frais\s*d['']activation|frais\s*de\s*transfert\s*international|frais\s*de\s*d[eé]douanement|frais\s*de\s*douane|taxe\s*d['']importation|frais\s*de\s*livraison\s*anticip[eé]s|payer\s*avant\s*de\s*recevoir|envoyer\s*d['']abord|verser\s*une\s*somme\s*pour\s*d[eé]bloquer|frais\s*de\s*notaire|frais\s*bancaires\s*[aà]\s*votre\s*charge|paiement\s*des\s*formalit[eé]s|r[eé]gularisation\s*[aà]\s*payer|frais\s*de\s*conversion\s*de\s*devise|petit\s*montant|juste\s*une\s*petite\s*somme|ce\s*n['']est\s*pas\s*grand[-\s]chose|symbolique|remboursable\s*apr[eè]s|vous\s*serez\s*rembours[eé]|c['']est\s*pour\s*couvrir\s*les\s*frais|il\s*faut\s*cotiser\s*un\s*peu|envoie\s*small\s*small|c['']est\s*juste\s*pour\s*les\s*papiers|frais\s*de\s*dossier\s*la|tu\s*dois\s*payer\s*avant\s*qu['']on\s*d[eé]bloque|paie\s*d['']abord\s*apr[eè]s\s*tu\s*re[cç]ois\s*le\s*gros\s*lot)",
        "category": "Demande financière",
        "weight": 40,
        "title": "Exigence de versement d'argent préalable",
        "advice": "Refusez tout envoi d'argent ou avance de frais. Les recruteurs sérieux et services officiels ne conditionnent pas une démarche à un paiement Mobile Money.",
    },
    {
        "code": "RULE_URGENCY",
        "pattern": r"(?i)(urgent|tr[eè]s\s*urgent|imm[eé]diat|imm[eé]diatement|dans\s*l['']heure|dans\s*les\s*24h|dans\s*les\s*prochaines\s*minutes|avant\s*ce\s*soir|avant\s*minuit|dernier\s*d[eé]lai|derni[eè]re\s*chance|offre\s*expire|expire\s*aujourd['']hui|compte\s*sera\s*bloqu[eé]|compte\s*sera\s*suspendu|ligne\s*sera\s*coup[eé]e|acc[eè]s\s*sera\s*ferm[eé]\s*d[eé]finitivement|ne\s*tardez\s*pas|agissez\s*maintenant|r[eé]agissez\s*vite|r[eé]ponse\s*exig[eé]e\s*sous|d[eé]lai\s*de\s*rigueur|pass[eé]\s*ce\s*d[eé]lai\s*vous\s*perdrez|sans\s*suite\s*imm[eé]diate\s*vous\s*serez\s*p[eé]nalis[eé]|rapidement|d[eè]s\s*que\s*possible|avant\s*qu['']il\s*ne\s*soit\s*trop\s*tard|ne\s*ratez\s*pas\s*cette\s*occasion|d[eé]p[eê]chez[-\s]vous|fais\s*vite\s*vite|ya\s*pas\s*le\s*temps|on\s*n['']a\s*plus\s*le\s*temps|c['']est\s*aujourd['']hui\s*m[eê]me|si\s*tu\s*tardes\s*tu\s*vas\s*rater\s*[cç]a|ce\s*soir\s*c['']est\s*la\s*derni[eè]re\s*heure)",
        "category": "Pression psychologique",
        "weight": 30,
        "title": "Pression ou sentiment d'urgence artificielle",
        "advice": "Prenez le temps d'analyser la situation. L'empressement est conçu pour empêcher la vérification rationnelle.",
    },
    {
        "code": "RULE_UNREAL_GAIN",
        "pattern": r"(?i)(f[eé]licitations\s*vous\s*avez\s*gagn[eé]|tirage\s*au\s*sort|vous\s*[eê]tes\s*l['']heureux\s*gagnant|s[eé]lectionn[eé]\s*au\s*hasard|b[eé]n[eé]ficiaire\s*s[eé]lectionn[eé]|subvention\s*exceptionnelle|aide\s*financi[eè]re\s*accord[eé]e|don\s*de\s*la\s*fondation|cadeau\s*surprise|gain\s*de\s*[0-9]+\s*(?:fcfa|f\s*cfa)|jackpot|cagnotte\s*d[eé]bloqu[eé]e|prime\s*exceptionnelle|vous\s*avez\s*[eé]t[eé]\s*tir[eé]\s*au\s*sort\s*parmi|promo\s*anniversaire\s*op[eé]rateur|offre\s*exclusive\s*r[eé]serv[eé]e|vous\s*faites\s*partie\s*des\s*heureux\s*[eé]lus|somme\s*de\s*[0-9]+(?:\s*000|\s*millions)|tu\s*as\s*gagn[eé]\s*oh|f[eé]licitations\s*(?:tonton|tantie)\s*tu\s*es\s*choisi|c['']est\s*ton\s*jour\s*de\s*chance|dieu\s*t['']a\s*b[eé]ni\s*aujourd['']hui|(?:mtn|moov)\s*te\s*fait\s*ce\s*cadeau\s*pour\s*la\s*f[eê]te)",
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
        "pattern": r"(?i)(service\s*client\s*mtn|assistance\s*moov|direction\s*(?:g[eé]n[eé]rale\s*)?mtn|moov\s*money\s*b[eé]nin\s*officiel|mtn\s*momo\s*bj|agent\s*agr[eé][eé]\s*momo|conseiller\s*bancaire|service\s*s[eé]curit[eé]\s*banque|cellule\s*anti[-\s]fraude|d[eé]partement\s*technique\s*orange|hotline\s*officielle|num[eé]ro\s*vert|notification\s*officielle\s*mtn|alerte\s*s[eé]curit[eé]\s*moov|service\s*de\s*v[eé]rification\s*de\s*compte|centre\s*d['']appel\s*officiel)",
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
        "pattern": r"(?i)((colis|paquet|envoi|livraison|commande)\s*(?:bloqu[eé]|retenu|en\s*attente)|(?:dhl|fedex|ups|chronopost|ems|dhl\s*express).*(?:douane|d[eé]douanement|frais|paiement|bloqu[eé])|frais\s*de\s*livraison.*(?:anticip[eé]s|compl[eé]mentaires|[aà]\s*r[eé]gler)|votre\s*(?:colis|commande)\s*(?:dhl|ups|fedex|chronopost).*action\s*requise)",
        "category": "Arnaque colis/douane",
        "weight": 40,
        "title": "Arnaque au colis bloqué ou frais de douane frauduleux",
        "advice": "Les vraies entreprises de livraison ne demandent jamais de paiement Mobile Money par SMS. Contactez directement le service client officiel.",
    },
    {
        "code": "RULE_CRYPTO_INVESTMENT",
        "pattern": r"(?i)(bitcoin|crypto|cryptomonnaie|binance|forex|trading\s*automatique|plateforme\s*d['']investissement|investissement\s*garanti|rendement\s*assur[eé]|multipliez\s*vos\s*gains|doublez\s*votre\s*argent|multipliez\s*votre\s*mise|rendement\s*garanti|investissement\s*sans\s*risque|robot\s*de\s*trading|gains\s*quotidiens\s*garantis|crypto[-\s]monnaie\s*garantie|bitcoin\s*doubl[eé]|forex\s*sans\s*exp[eé]rience|plateforme\s*certifi[eé]e\s*international|retour\s*sur\s*investissement\s*de\s*[0-9]+%\s*par\s*jour|tontine\s*vip\s*en\s*ligne|parrainage\s*r[eé]mun[eé]r[eé]|syst[eè]me\s*pyramidal|mlm\s*crypto|mining\s*garanti|staking\s*[aà]\s*haut\s*rendement|pool\s*d['']investissement\s*ferm[eé]|tu\s*mets\s*10\s*tu\s*retires\s*50|business\s*qui\s*rapporte\s*vite|argent\s*qui\s*travaille\s*pour\s*toi|groupe\s*whatsapp\s*d['']investissement|chef\s*d[''][eé]quipe\s*qui\s*g[eè]re\s*ton\s*argent|d[eé]pose\s*et\s*regarde\s*ton\s*argent\s*grandir)",
        "category": "Faux investissement crypto",
        "weight": 38,
        "title": "Promesse d'investissement crypto ou trading suspect",
        "advice": "Méfiez-vous des promesses de gains rapides et garantis. Les investissements légitimes comportent toujours des risques clairement mentionnés.",
    },
    {
        "code": "RULE_VISA_IMMIGRATION",
        "pattern": r"(?i)((visa|immigration|ambassade|consulat|green\s*card|carte\s*verte)\s*(?:garanti|rapide|express|facilit[eé])|bourse\s*[eé]tudes?\s*(?:[aà]\s*l[''][eé]tranger|internationale|usa|canada|europe)|programme\s*d[''][eé]change.*(?:inscription|frais|paiement)|travail\s*[aà]\s*l[''][eé]tranger.*(?:visa|caution|frais)|recrutement.*(?:canada|usa|europe|france).*frais)",
        "category": "Arnaque visa/immigration",
        "weight": 37,
        "title": "Arnaque visa, immigration ou bourse d'études",
        "advice": "Les ambassades et programmes officiels ne demandent jamais de paiement Mobile Money. Vérifiez sur les sites officiels gouvernementaux.",
    },
    {
        "code": "RULE_INHERITANCE_SCAM",
        "pattern": r"(?i)(h[eé]ritage|h[eé]ritier|notaire|testament|d[eé]c[eé]d[eé]|d[eé]funt|fonds?\s*bloqu[eé]s?|millions?\s*de\s*(?:dollars?|euros?|fcfa)|banque\s*centrale|transfert\s*international|fond(?:s)?\s*(?:dormant|non\s*r[eé]clam[eé])|b[eé]n[eé]ficiaire\s*d['']un\s*h[eé]ritage|succession\s*[aà]\s*r[eé]clamer|avocat\s*mandataire|ex[eé]cuteur\s*testamentaire)",
        "category": "Arnaque à l'héritage",
        "weight": 42,
        "title": "Arnaque à l'héritage ou fonds bloqués",
        "advice": "C'est une arnaque classique internationale. Aucun notaire légitime ne vous contactera par SMS pour un héritage inattendu.",
    },
    {
        "code": "RULE_ROMANTIC_EMERGENCY",
        "pattern": r"(?i)((h[oô]pital|urgence\s*m[eé]dicale|accident|maladie\s*grave|op[eé]ration\s*chirurgicale|intervention\s*m[eé]dicale)\s*(?:urgente?|imm[eé]diate?)?.*(?:besoin\s*d['']aide|envoie|transfert|aide[-\s]moi|argent)|frais\s*m[eé]dicaux.*(?:urgent|imm[eé]diat|aujourd['']hui)|soins\s*urgents.*(?:argent|transfert|aide))",
        "category": "Urgence médicale suspecte",
        "weight": 32,
        "title": "Urgence médicale ou sentimentale suspecte",
        "advice": "Avant tout transfert, appelez la personne directement pour vérifier. Les arnaqueurs ciblent les émotions en simulant des urgences.",
    },
    {
        "code": "RULE_FAKE_TECH_SUPPORT",
        "pattern": r"(?i)(virus\s*d[eé]tect[eé]|t[eé]l[eé]phone\s*infect[eé]|appareil\s*infect[eé]|support\s*microsoft|licence\s*windows\s*expir[eé]e|activit[eé]\s*suspecte\s*sur\s*votre\s*appareil|acc[eè]s\s*[aà]\s*distance|teamviewer|anydesk|partagez\s*votre\s*[eé]cran|compte\s*google\s*pirat[eé]|technicien\s*va\s*se\s*connecter)",
        "category": "Faux support technique",
        "weight": 35,
        "title": "Sollicitation d'un faux support technique avec accès à distance",
        "advice": "N'installez aucune application de prise de contrôle à distance suite à un message non sollicité. Un support technique légitime ne vous contacte jamais spontanément par SMS.",
    },
    {
        "code": "RULE_FAKE_DELIVERY_CUSTOMS",
        "pattern": r"(?i)(colis\s*bloqu[eé]\s*(?:en\s*)?douane|frais\s*de\s*d[eé]douanement|frais\s*de\s*douane\s*[aà]\s*(?:payer|r[eé]gler)|taxe\s*d['']importation|colis\s*retourn[eé]\s*sauf\s*paiement|livraison.*paiement\s*compl[eé]mentaire|adresse\s*incorrecte.*cliquez|livreur\s*en\s*route.*payez)",
        "category": "Fausse livraison",
        "weight": 30,
        "title": "Demande de paiement pour débloquer un colis en douane",
        "advice": "Vérifiez directement auprès du transporteur officiel via son site ou numéro connu avant tout paiement lié à un colis. Les vrais transporteurs ne demandent jamais de paiement Mobile Money par SMS.",
    },
    {
        "code": "RULE_ROMANCE_IMPERSONATION",
        "pattern": r"(?i)(j['']ai\s*chang[eé]\s*de\s*num[eé]ro.*(?:envoie|transfert|argent)|bloqu[eé]\s*[aà]\s*l['']?[eé]tranger.*(?:aide|argent|transfert)|je\s*suis\s*[aà]\s*l['']h[oô]pital.*(?:besoin\s*d['']argent|envoie)|militaire\s*en\s*mission.*permission|officier.*op[eé]ration.*besoin\s*(?:d[''])?aide)",
        "category": "Usurpation identité",
        "weight": 35,
        "title": "Scénario d'urgence personnelle avec demande d'argent immédiate",
        "advice": "Contactez la personne par un autre canal connu (appel vocal direct sur son ancien numéro, autre membre de la famille) avant tout envoi d'argent. Les arnaqueurs usurpent l'identité de proches.",
    },
    {
        "code": "RULE_FAKE_REFUND",
        "pattern": r"(?i)(remboursement\s*en\s*attente|trop[\s-]per[cç]u\s*[aà]\s*rembourser|erreur\s*de\s*facturation\s*en\s*votre\s*faveur|remboursement\s*bloqu[eé].*action\s*requise|re[cç]u\s*de\s*paiement.*pi[eè]ce\s*jointe|preuve\s*de\s*virement)",
        "category": "Faux remboursement",
        "weight": 30,
        "title": "Prétendu remboursement nécessitant une action immédiate",
        "advice": "Un remboursement légitime ne nécessite jamais de communiquer un code secret ou de payer des frais pour le débloquer. Vérifiez directement auprès de l'organisation concernée.",
    },
]


def evaluate_rules(text: str) -> Tuple[List[DetectedSignal], int]:
    """Évalue le texte contre les règles déterministes.
    Retourne la liste des signaux détectés et le score brut cumulé.
    
    Gère la négation et le contexte narratif pour éviter les faux positifs
    sur les messages de prévention. Applique la normalisation anti-obfuscation
    et le fuzzy matching pour tolérer les fautes de frappe.
    """
    detected_signals: List[DetectedSignal] = []
    total_rule_score = 0
    
    # Normaliser le texte pour contrer l'obfuscation (leetspeak, espacement, etc.)
    # Garder le texte original pour l'affichage des extraits
    text_normalized = normalize_text(text, apply_leet=True)
    
    # Vérifier si tout le message est dans un contexte narratif/préventif
    is_narrative = has_narrative_context(text)
    
    # Fuzzy matching pour détecter variantes avec fautes de frappe
    fuzzy_categories = enhance_rules_with_fuzzy(text_normalized, threshold=85)

    for rule in DEFINED_RULES:
        # Matcher sur le texte normalisé pour détecter les contournements
        match = re.search(rule["pattern"], text_normalized)
        
        # Vérifier aussi le fuzzy matching comme signal additionnel
        fuzzy_match = False
        if rule["code"] == "RULE_OTP_PIN" and "OTP" in fuzzy_categories:
            fuzzy_match = True
        elif rule["code"] == "RULE_MONEY_REQ" and "MONEY_REQ" in fuzzy_categories:
            fuzzy_match = True
        elif rule["code"] == "RULE_URGENCY" and "URGENCY" in fuzzy_categories:
            fuzzy_match = True
        elif rule["code"] == "RULE_UNREAL_GAIN" and "GAIN" in fuzzy_categories:
            fuzzy_match = True
        elif rule["code"] == "RULE_USURPATION_MOMO" and "USURPATION" in fuzzy_categories:
            fuzzy_match = True
        
        if match or fuzzy_match:
            # Déterminer la position pour la vérification de négation
            if match:
                match_position = match.start()
            else:
                # Fuzzy match : utiliser position approximative (milieu du texte)
                match_position = len(text) // 2
            
            # Vérifier la négation locale avant ce match spécifique
            has_local_negation = has_negation_before(text, match_position)
            
            # Si négation détectée ET contexte narratif global, ne pas compter ce signal
            if has_local_negation or is_narrative:
                # Signal détecté mais neutralisé (contenu préventif)
                continue
            
            # Récupérer l'extrait du texte ORIGINAL (non normalisé) pour l'affichage
            if match:
                start = max(0, match.start() - 10)
                end = min(len(text_normalized), match.end() + 10)
                snippet = text[start:end].strip() if len(text) > start else text[:60]
            else:
                # Fuzzy match : extraire contexte central
                snippet = text[:60] if len(text) > 60 else text

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
