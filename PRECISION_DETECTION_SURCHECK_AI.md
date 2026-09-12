# PRÉCISION DE DÉTECTION — SÛRCHECK AI
## Lexique exhaustif, gestion de la négation, fuzzy matching et scoring de co-occurrence

**Objectif de ce document** : fournir à Antigravity tout le matériel nécessaire pour rendre le moteur `rules.py` / `classifier.py` / `scorer.py` beaucoup plus précis sur les messages collés (SMS, WhatsApp, Facebook), sans jamais changer le vocabulaire de sortie (toujours « risque potentiel », jamais « escroc »).

Ce document ne remplace pas `AMELIORATION_DETECTION_SURCHECK_AI.md` (architecture 4 couches déjà validée). Il le complète avec le contenu concret : les mots, les expressions, les règles de négation et les techniques anti-contournement qui manquaient.

Ce fichier est un **prompt Antigravity autonome** : chaque section 2 à 9 correspond à un module de code à créer ou modifier, avec le contenu exact à utiliser.

---

# 1. DIAGNOSTIC DES LIMITES ACTUELLES

En l'état (`rules.py`, `classifier.py`), le moteur a 4 faiblesses précises :

1. **Rigidité lexicale** : chaque règle est UNE regex avec UNE liste fermée de mots. Un message qui dit « fré2 de dossié » ou « FRAIS  D O S S I E R » (espacé pour contourner) ne matche rien.
2. **Aucune négation** : « n'envoyez jamais votre code secret » déclenche `RULE_OTP_PIN` exactement comme « envoyez votre code secret ». Le message de PRÉVENTION est scoré comme un message de FRAUDE.
3. **Corpus ML minuscule** : 26 exemples d'entraînement (13 frauduleux, 13 légitimes) pour un classificateur censé généraliser à des milliers de formulations béninoises réelles.
4. **Catégories manquantes** : colis/douane, faux support technique, romance/usurpation d'identité, crypto/investissement moderne, sextortion — présentes dans le cahier des charges (section 24) mais absentes du code de règles actuel (`rules.py` n'a que 7 règles).

Les sections suivantes corrigent ces 4 points un par un.

---

# 2. LEXIQUE COMPLET PAR CATÉGORIE

Chaque catégorie ci-dessous fournit : **signaux forts** (poids élevé, quasi jamais légitimes), **signaux faibles** (poids modéré, doivent se combiner avec d'autres), **variantes locales/argot**, et **contre-exemples légitimes** (ne doivent jamais scorer haut à eux seuls).

Pour chaque terme, prévoir dans le code une normalisation qui gère : accents retirés, espaces multiples, tirets, points entre lettres, chiffres remplaçant des lettres (voir section 5).

## 2.1 Demande de code secret / OTP / PIN (déjà partiellement couvert — à enrichir)

**Signaux forts (poids 45-55)**
```
code secret, code confidentiel, code otp, code pin, mot de passe, mdp,
code de retrait, code de validation, code de confirmation, code d'activation,
code de déblocage, code de vérification, numéro de code, votre code,
donnez-moi le code, communiquez le code, dictez le code, lisez-moi le code,
code reçu par sms, code à 4 chiffres, code à 6 chiffres, pin momo,
pin mtn, pin moov, ussd *880#, ussd *855#, code marchand,
tapez le code que vous avez reçu, partagez le code, le code que vous venez de recevoir
```

**Variantes locales / orales retranscrites**
```
le code la, donne moi le code la, envoie le code que tu as reçu,
je vais te dicter un code tu me le donnes, c'est quoi le code sms,
lis moi ce qui est écrit dans le message
```

**Contre-exemples légitimes (NE DOIT PAS scorer comme OTP_PIN)**
```
j'ai changé mon code, mon code ne marche plus, j'ai oublié mon code
  (parlé à la première personne, sans demande adressée à l'interlocuteur)
le code postal, le code de la route, code vestimentaire, code source
```
→ Règle d'implémentation : le signal ne doit se déclencher que si le message contient une **structure de demande** (impératif, "envoie/donne/dicte/partage/communique" + code) et PAS une structure de constat personnel ("j'ai perdu mon code", "mon code est bloqué").

## 2.2 Demande d'argent / frais préalables

**Signaux forts (poids 30-40)**
```
frais de dossier, frais d'inscription, frais de traitement, frais de dossier médical,
frais de visite médicale, caution, caution remboursable, caution de garantie,
frais de déblocage, dépôt préalable, avance, acompte obligatoire,
commission avant retrait, frais d'activation, frais de transfert international,
frais de dédouanement, frais de douane, taxe d'importation, frais de livraison anticipés,
payer avant de recevoir, envoyer d'abord, verser une somme pour débloquer,
frais de notaire, frais de transfert de fonds, frais bancaires à votre charge,
paiement des formalités, régularisation à payer, frais de conversion de devise
```

**Signaux faibles (poids 10-15, à combiner)**
```
petit montant, juste une petite somme, ce n'est pas grand-chose,
symbolique, remboursable après, vous serez remboursé,
c'est pour couvrir les frais
```

**Variantes locales**
```
il faut cotiser un peu, envoie small small, c'est juste pour les papiers,
frais de dossier la, tu dois payer avant qu'on débloque,
paie d'abord après tu reçois le gros lot
```

**Contre-exemples légitimes**
```
frais de scolarité (facture d'établissement identifié, contexte école connue),
facture d'électricité, quittance de loyer, frais de transport pour venir au travail
```
→ Ces contre-exemples ne doivent pas être exclus en dur ; ils doivent simplement ne pas matcher les patterns ci-dessus (ils ne contiennent pas "débloquer", "avant de recevoir", "caution remboursable").

## 2.3 Urgence artificielle / pression psychologique

**Signaux forts (poids 20-25)**
```
urgent, très urgent, immédiat, immédiatement, dans l'heure, dans les 24h,
dans les prochaines minutes, avant ce soir, avant minuit, dernier délai,
dernière chance, offre expire, expire aujourd'hui, compte sera bloqué,
compte sera suspendu, ligne sera coupée, accès sera fermé définitivement,
ne tardez pas, agissez maintenant, réagissez vite, réponse exigée sous,
délai de rigueur, passé ce délai vous perdrez, sans suite immédiate vous serez pénalisé
```

**Signaux faibles**
```
rapidement, dès que possible, avant qu'il ne soit trop tard,
ne ratez pas cette occasion, dépêchez-vous
```

**Variantes locales**
```
fais vite vite, ya pas le temps, on n'a plus le temps, c'est aujourd'hui même,
si tu tardes tu vas rater ça, ce soir c'est la dernière heure
```

## 2.4 Promesse de gain irréaliste / faux cadeau / loterie

**Signaux forts (poids 25-30)**
```
félicitations vous avez gagné, tirage au sort, vous êtes l'heureux gagnant,
sélectionné au hasard, bénéficiaire sélectionné, subvention exceptionnelle,
aide financière accordée, don de la fondation, cadeau surprise,
gain de X FCFA, jackpot, cagnotte débloquée, prime exceptionnelle,
vous avez été tiré au sort parmi, promo anniversaire opérateur,
offre exclusive réservée, vous faites partie des heureux élus
```

**Variantes locales**
```
tu as gagné oh, félicitations tonton/tantie tu es choisi,
c'est ton jour de chance, dieu t'a béni aujourd'hui,
MTN/Moov te fait ce cadeau pour la fête de l'indépendance
```

**Contre-exemples légitimes**
```
tu as gagné le match, vous avez gagné le pari (contexte sportif explicite),
félicitations pour ton mariage/ta réussite (contexte social explicite sans demande d'action financière)
```

## 2.5 Usurpation d'opérateur Mobile Money / institution

**Signaux forts (poids 25-30)**
```
service client mtn, assistance moov, direction générale mtn bénin,
moov money bénin officiel, mtn momo bj, agent agréé momo,
conseiller bancaire, service sécurité banque, cellule anti-fraude,
département technique orange, hotline officielle, numéro vert,
notification officielle mtn, alerte sécurité moov,
service de vérification de compte, centre d'appel officiel
```

**Signaux de contexte aggravant**
```
appel depuis un numéro non officiel se présentant comme un service client,
demande d'informations que l'opérateur connaît déjà (nom, solde, dernière transaction)
```

**Contre-exemples légitimes**
```
j'ai appelé le service client mtn (l'utilisateur relate SA démarche, pas une sollicitation reçue),
le service client m'a confirmé
```

## 2.6 Faux emploi / recrutement frauduleux

**Signaux forts (poids 30-35)**
```
recrutement urgent, poste à pourvoir immédiatement, salaire très attractif,
aucune expérience requise, travail à domicile bien payé, embauche immédiate,
recrutement ong, recrutement ambassade, recrutement unicef, recrutement pnud,
recrutement croix rouge, poste au port autonome, recrutement fonction publique,
kit de démarrage à payer, uniforme à votre charge, frais de formation obligatoire,
caution de matériel, dossier à constituer contre paiement,
visite médicale payante avant embauche, test d'aptitude payant
```

**Variantes locales**
```
grosse boîte cherche personnel, on recrute sans diplôme, salaire en dollars,
travail à l'étranger tout frais payé, visa garanti si tu payes le dossier
```

**Contre-exemples légitimes**
```
offre d'emploi publiée sur un site connu avec entretien classique sans paiement,
candidature envoyée par l'utilisateur (contexte actif, pas reçu passivement)
```

## 2.7 Faux investissement / crypto / trading

**Signaux forts (poids 35-45)**
```
doublez votre argent, multipliez votre mise, rendement garanti,
investissement sans risque, trading automatique, robot de trading,
gains quotidiens garantis, crypto-monnaie garantie, bitcoin doublé,
forex sans expérience, plateforme certifiée international,
retour sur investissement de X% par jour, tontine vip en ligne,
parrainage rémunéré, système pyramidal déguisé, mlm crypto,
mining garanti, staking à haut rendement, pool d'investissement fermé
```

**Variantes locales**
```
tu mets 10 tu retires 50, business qui rapporte vite, argent qui travaille pour toi,
groupe whatsapp d'investissement, chef d'équipe qui gère ton argent,
dépose et regarde ton argent grandir
```

**Contre-exemples légitimes**
```
discussion générale sur la bourse ou l'épargne sans promesse de rendement garanti,
mention d'une banque ou institution de microfinance agréée connue localement
```

## 2.8 Phishing / faux site / lien suspect

**Signaux forts (poids 30-45, cumulable avec RULE_SUSPICIOUS_LINK)**
```
connexion inhabituelle détectée, votre compte a été suspendu cliquez ici,
confirmez vos identifiants, mettez à jour vos informations bancaires,
vérifiez votre compte sous peine de fermeture, cliquez pour débloquer,
votre carte a été bloquée cliquez ici, sécurisez votre compte maintenant,
document à télécharger en urgence, formulaire de vérification d'identité en ligne
```

**Signaux techniques (URL)**
```
domaines contenant : -secure, -verify, -confirm, -support, -momo, -mtn, -moov
concaténés avec un mot générique (ex: mtn-secure-bj.com), sous-domaines
excessifs, extensions rares (.xyz, .top, .click, .info) combinées à un
vocabulaire de marque connue, IP brute à la place d'un nom de domaine
```

## 2.9 Faux support technique

**Signaux forts (poids 30-40) — CATÉGORIE À AJOUTER AU MOTEUR**
```
votre téléphone est infecté, virus détecté sur votre appareil,
support microsoft vous contacte, votre licence windows a expiré,
nous avons détecté une activité suspecte sur votre appareil,
installez cette application pour sécuriser votre téléphone,
donnez-nous accès à distance, téléchargez teamviewer/anydesk pour qu'on vous aide,
votre compte google a été piraté contactez-nous immédiatement,
technicien va se connecter à votre appareil, partagez votre écran avec nous
```

## 2.10 Fausse livraison / faux colis / douane

**Signaux forts (poids 25-35) — CATÉGORIE À AJOUTER AU MOTEUR**
```
votre colis est bloqué en douane, colis en attente de dédouanement,
frais de douane à régler avant livraison, livreur en route payez d'abord,
colis retourné à l'expéditeur sauf paiement, taxe d'importation impayée,
votre commande dhl/ups/fedex nécessite une action, adresse incorrecte
cliquez pour corriger, paiement complémentaire requis pour réception
```

## 2.11 Faux remboursement / faux reçu

**Signaux forts (poids 25-35) — CATÉGORIE À AJOUTER AU MOTEUR**
```
remboursement en attente cliquez pour recevoir, trop-perçu à rembourser,
erreur de facturation en votre faveur, remboursement bloqué action requise,
reçu de paiement en pièce jointe suspecte, preuve de virement falsifiée,
capture d'écran de reçu envoyée sans transaction réelle confirmée
```

## 2.12 Usurpation d'identité / arnaque au proche / romance

**Signaux forts (poids 30-40) — CATÉGORIE À AJOUTER AU MOTEUR**
```
c'est moi j'ai changé de numéro envoie-moi de l'argent, urgence familiale
envoie vite, je suis bloqué à l'étranger aide-moi financièrement,
je t'aime je veux te rencontrer mais j'ai besoin d'argent pour le billet,
mon compte est bloqué envoie sur ton compte je te rembourse après,
je suis à l'hôpital besoin d'argent immédiatement, militaire en mission
besoin d'aide financière pour permission, officier en opération à l'étranger
```

**Signaux de contexte aggravant**
```
relation démarrée uniquement en ligne, refus systématique d'appel vidéo,
demande financière récurrente et croissante, histoire personnelle
dramatique répétitive (décès, accident, hôpital, douane, blocage bancaire)
```

## 2.13 Sextorsion / chantage

**Signaux forts (poids 40-50) — CATÉGORIE À AJOUTER AU MOTEUR, traiter avec prudence**
```
menace de diffusion de photos/vidéos, capture d'écran de votre webcam,
paiement pour éviter la publication, envoyez de l'argent ou je publie,
j'ai accès à vos contacts et je vais tout partager, délai avant publication
```
→ Pour cette catégorie : le moteur doit systématiquement orienter vers les ressources d'aide et l'OCRC, ne jamais afficher de détail qui identifie ou décrit le contenu de la menace elle-même (respect de la vie privée et non-facilitation).

---

# 3. GESTION DE LA NÉGATION ET DU CONTEXTE (CORRECTION CRITIQUE)

C'est la faille la plus grave actuellement : le moteur ne distingue pas une **demande frauduleuse** d'une **mise en garde ou d'un récit**.

## 3.1 Marqueurs de négation à détecter avant le mot-clé (fenêtre de 0 à 6 mots avant le signal)

```
ne ... jamais, ne ... pas, n'envoyez pas, ne donnez pas, ne communiquez pas,
ne partagez jamais, évitez de, refusez de, ne cliquez pas, ne répondez pas,
attention à, méfiez-vous de, ne tombez pas dans, ne vous laissez pas avoir par,
aucun agent ne vous demandera, personne ne doit vous demander, il est interdit de donner
```

## 3.2 Marqueurs de récit / narration (troisième personne ou passé, sans demande active)

```
quelqu'un m'a demandé, on m'a demandé, j'ai reçu un message qui disait,
un individu a tenté de, une personne prétendant être, ils ont essayé de,
mon ami a reçu, ma sœur a été contactée par
```

## 3.3 Règle d'implémentation (à donner telle quelle à Antigravity)

Pour chaque règle de `rules.py`, avant de valider un match :

1. Extraire une fenêtre de **8 tokens avant** le match du pattern principal.
2. Si cette fenêtre contient un marqueur de négation (liste 3.1) OU un marqueur de récit (liste 3.2) **ET** qu'aucun second signal fort n'est présent ailleurs dans le message, alors :
   - Ne pas ajouter le poids de la règle au score.
   - Optionnel : ajouter un signal neutre distinct `SIG_CONTENU_PREVENTIF` (poids 0, catégorie "Contenu de sensibilisation") pour que l'interface puisse afficher un message différent si pertinent (ex: ne pas afficher "risque élevé" pour un message qui *parle* d'une arnaque sans en être une).
3. Si la négation ne porte que sur une partie du message (ex: "ne donnez jamais votre code, mais confirmez votre numéro de compte ici : lien"), le second segment doit être évalué indépendamment — ne pas neutraliser tout le message sur la base d'une seule négation partielle.

Ceci doit être implémenté comme une fonction `has_negation_before(text, match_start, window=8)` dans `normalizer.py` ou un nouveau module `context.py`, appelée par `evaluate_rules()` dans `rules.py` avant d'ajouter chaque signal.

---

# 4. SCORING DE CO-OCCURRENCE (SIGNAUX FAIBLES QUI SE RENFORCENT)

Actuellement, chaque règle contribue indépendamment. Il manque une logique de **renforcement mutuel** : deux signaux faibles présents ensemble sont souvent plus révélateurs que leur somme simple.

## 4.1 Paires/combinaisons à bonifier

| Combinaison de signaux | Bonus de score | Justification |
|---|---|---|
| Urgence + demande d'argent | +15 | Schéma classique "payez vite avant qu'il ne soit trop tard" |
| Promesse de gain + demande d'argent | +20 | Schéma "payez pour débloquer votre gain" — quasi toujours frauduleux |
| Usurpation d'opérateur + demande de code | +25 | Combinaison qui ne se produit jamais légitimement |
| Lien raccourci + urgence | +15 | Phishing typique |
| Contact "romance" + demande d'argent récurrente (mentionnée 2 fois) | +20 | Signature d'arnaque sentimentale |
| Faux support technique + demande d'accès à distance | +25 | Signature quasi certaine de prise de contrôle malveillante |

## 4.2 Implémentation

Dans `scorer.py`, après l'évaluation des règles individuelles (`evaluate_rules`), ajouter une fonction `apply_cooccurrence_bonus(signals: List[DetectedSignal]) -> int` qui :
1. Construit l'ensemble des `code` présents dans `signals`.
2. Compare cet ensemble à une table de combinaisons prédéfinie (celle ci-dessus, encodée en dur).
3. Retourne un bonus additif à ajouter à `rule_score` avant la pondération 70/30 avec le ML.
4. Chaque bonus appliqué doit être tracé dans `analysis_features` (nouveau champ `cooccurrence_bonus` ou entrée synthétique dans les signaux) pour garder la traçabilité exigée par la section 33 du cahier des charges.

---

# 5. DÉTECTION DE L'OBFUSCATION (CONTOURNEMENT VOLONTAIRE OU INVOLONTAIRE)

Les utilisateurs qui rédigent des messages frauduleux évitent parfois volontairement les filtres ; les utilisateurs légitimes font des fautes de frappe. Il faut couvrir les deux.

## 5.1 Normalisation à renforcer dans `normalizer.py`

En plus de `strip_accents` et `normalize_text` existants, ajouter :

1. **Suppression des espaces/points/tirets internes suspects entre lettres isolées** : `c o d e  s e c r e t` → `code secret` ; `c.o.d.e s-e-c-r-e-t` → `code secret`. Regex : détecter des séquences de lettres isolées séparées par des espaces/points/tirets et les recoller si la reconstruction forme un mot du lexique.
2. **Application systématique du leetspeak** (`LEET_SUBS` déjà présent dans `normalizer.py` mais actuellement `apply_leet=False` par défaut) : l'activer par défaut dans le pipeline de matching des règles (garder le texte original pour l'affichage des extraits, mais matcher sur la version leet-normalisée).
3. **Tolérance aux caractères répétés** : `urrrgent`, `viiiite` → réduire toute répétition de plus de 2 caractères identiques consécutifs à 2 caractères avant matching.
4. **Émojis comme substituts** : mapper les émojis fréquemment utilisés comme substituts visuels (💰 → argent, ⚠️/🚨 → urgence, 🎁 → cadeau, 🔒 → sécurité/code) pour les inclure dans le calcul de co-occurrence, sans leur donner de poids seuls.

## 5.2 Fuzzy matching (tolérance aux fautes de frappe et variantes)

Pour les termes les plus critiques (section 2.1 et 2.2), ajouter en complément des regex exactes une comparaison par **distance de Levenshtein ≤ 2** sur chaque token du message contre le lexique de référence, avec bibliothèque `rapidfuzz` (légère, rapide, adaptée à un pipeline temps réel).

```python
# Exemple de squelette pour rules.py ou un nouveau module fuzzy_matcher.py
from rapidfuzz import fuzz

CRITICAL_TERMS = ["code secret", "code otp", "frais de dossier", "caution", "urgent"]

def fuzzy_contains(text: str, terms: list[str], threshold: int = 85) -> list[str]:
    matched = []
    tokens_window = _sliding_windows(text, max_words=3)  # fenêtres de 1 à 3 mots
    for window in tokens_window:
        for term in terms:
            if fuzz.ratio(window, term) >= threshold:
                matched.append(term)
    return matched
```

Le fuzzy matching doit être limité aux termes critiques (pas toute la base lexicale) pour rester performant et éviter les faux positifs sur des mots courts.

---

# 6. EXPANSION DU CORPUS ML (`classifier.py`)

Le corpus actuel (26 exemples) est trop petit. Objectif : **au moins 300 exemples par catégorie principale**, avec un ratio frauduleux/légitime proche de 1:1.

## 6.1 Stratégie de constitution du corpus

1. **Générer des variations systématiques** à partir des modèles de phrases de la section 2 : pour chaque expression-signal, produire 5 à 10 reformulations (registre différent, avec/sans fautes, avec/sans expressions locales).
2. **Ajouter les contre-exemples légitimes** de chaque sous-section 2.x comme exemples "Légitime" dans `TRAINING_DATA`.
3. **Couvrir les 6 nouvelles catégories** (2.9 à 2.13) qui n'ont aujourd'hui aucun exemple ML alors que les règles vont les détecter — sans exemples ML, le classificateur ne peut pas les distinguer d'un message légitime.
4. **Ajouter des cas ambigus / limites** (ex: un vrai message d'un livreur qui demande légitimement une confirmation d'adresse) étiquetés "Légitime" pour réduire les faux positifs sur la catégorie livraison.

## 6.2 Format à respecter (identique à l'existant)

```python
TRAINING_DATA = [
    # ... existant ...
    # 7. Faux support technique (NOUVELLE CATÉGORIE)
    ("Votre téléphone est infecté par un virus. Téléchargez immédiatement cette application pour le nettoyer sinon vos données seront perdues.", "Faux support technique"),
    ("Nous sommes le support Microsoft, votre licence a expiré, donnez-nous accès à distance pour la renouveler gratuitement.", "Faux support technique"),
    # 8. Fausse livraison (NOUVELLE CATÉGORIE)
    ("Votre colis est bloqué à la douane de Cotonou. Payez 3500 FCFA de frais de dédouanement pour le débloquer immédiatement.", "Fausse livraison"),
    # 9. Usurpation / romance (NOUVELLE CATÉGORIE)
    ("Bonjour c'est moi, j'ai changé de numéro suite à un vol. Peux-tu m'envoyer 15000 FCFA en urgence, je te rembourse dès demain.", "Usurpation identité"),
    # ... continuer selon le même schéma pour chaque catégorie de la section 2 ...
]
```

## 6.3 Rééquilibrage du modèle

Avec l'ajout de nouvelles catégories, vérifier que `LogisticRegression(class_weight="balanced")` reste pertinent (déjà présent dans le code — le conserver), et envisager de passer `C=1.0` à une valeur légèrement inférieure (`C=0.7`) une fois le corpus élargi, pour limiter le surapprentissage sur des formulations trop spécifiques.

---

# 7. NOUVELLES RÈGLES DÉTERMINISTES À AJOUTER DANS `rules.py`

À ajouter dans `DEFINED_RULES`, sur le modèle exact des règles existantes (avec gestion de la négation de la section 3 appliquée à toutes, anciennes et nouvelles) :

```python
{
    "code": "RULE_FAKE_TECH_SUPPORT",
    "pattern": r"(?i)(virus\s*d[eé]tect[eé]|t[eé]l[eé]phone\s*infect[eé]|support\s*microsoft|licence\s*windows\s*expir[eé]e|acc[eè]s\s*[aà]\s*distance|teamviewer|anydesk|partagez\s*votre\s*[eé]cran)",
    "category": "Faux support technique",
    "weight": 35,
    "title": "Sollicitation d'un faux support technique avec accès à distance",
    "advice": "N'installez aucune application de prise de contrôle à distance suite à un message non sollicité. Un support technique légitime ne vous contacte jamais spontanément.",
},
{
    "code": "RULE_FAKE_DELIVERY_CUSTOMS",
    "pattern": r"(?i)(colis\s*bloqu[eé]\s*(?:en\s*)?douane|frais\s*de\s*d[eé]douanement|frais\s*de\s*douane\s*[aà]\s*payer|taxe\s*d['']importation|colis\s*retourn[eé]\s*sauf\s*paiement)",
    "category": "Fausse livraison",
    "weight": 30,
    "title": "Demande de paiement pour débloquer un colis en douane",
    "advice": "Vérifiez directement auprès du transporteur officiel via son site ou numéro connu avant tout paiement lié à un colis.",
},
{
    "code": "RULE_ROMANCE_IMPERSONATION",
    "pattern": r"(?i)(j['']ai\s*chang[eé]\s*de\s*num[eé]ro.*envoie|bloqu[eé]\s*[aà]\s*l['']?[eé]tranger.*aide|je\s*suis\s*[aà]\s*l['']h[oô]pital.*besoin\s*d['']argent|militaire\s*en\s*mission.*permission)",
    "category": "Usurpation identité",
    "weight": 35,
    "title": "Scénario d'urgence personnelle avec demande d'argent immédiate",
    "advice": "Contactez la personne par un autre canal connu (appel vocal direct, autre membre de la famille) avant tout envoi d'argent.",
},
{
    "code": "RULE_FAKE_REFUND",
    "pattern": r"(?i)(remboursement\s*en\s*attente|trop[\s-]per[cç]u\s*[aà]\s*rembourser|erreur\s*de\s*facturation\s*en\s*votre\s*faveur|remboursement\s*bloqu[eé])",
    "category": "Faux remboursement",
    "weight": 30,
    "title": "Prétendu remboursement nécessitant une action immédiate",
    "advice": "Un remboursement légitime ne nécessite jamais de communiquer un code secret ou de payer des frais pour le débloquer.",
},
```

Chaque nouvelle règle doit être ajoutée en parallèle dans `seeds.sql` (table `risk_rules`) pour rester cohérente avec la base Supabase, en suivant le format déjà utilisé (`rule_code`, `pattern`, `category`, `score_weight`, `explanation_template`, `recommendation_text`).

---

# 8. PIPELINE OCR — PRÉCISION SUR LE TEXTE EXTRAIT

Le module `ocr.py` transmet le texte extrait tel quel au moteur de scoring. Deux problèmes de précision spécifiques :

1. **Texte OCR fragmenté** : Tesseract peut couper des mots ("cod e secr et"). Appliquer la même normalisation de recollement que la section 5.1 systématiquement sur toute sortie OCR avant scoring (pas seulement en option).
2. **Confusions de caractères fréquentes en OCR français** (captures compressées WhatsApp) : `0`/`O`, `1`/`l`/`I`, `5`/`S`, `8`/`B`. Ajouter une passe de correction ciblée uniquement sur les tokens qui, une fois corrigés, matchent un terme du lexique critique (éviter de corriger tout le texte pour ne pas introduire d'erreurs ailleurs).
3. **Score de confiance OCR** : `pytesseract` peut retourner un score de confiance par mot (`image_to_data` au lieu de `image_to_string`). Utiliser cette donnée pour abaisser le `confidence_level` global de l'analyse à `"incertain"` si la confiance OCR moyenne est basse, plutôt que de présenter un score de risque ferme sur un texte mal reconnu.

---

# 9. TABLE DE PRIORITÉ D'IMPLÉMENTATION

| Priorité | Action | Fichier(s) concerné(s) | Impact attendu |
|---|---|---|---|
| 1 | Gestion de la négation (section 3) | `normalizer.py` / `rules.py` | Élimine les faux positifs les plus visibles (messages de prévention scorés comme frauduleux) |
| 2 | Ajout des 4 nouvelles règles déterministes (section 7) | `rules.py`, `seeds.sql` | Couvre les scénarios du cahier des charges (24) actuellement non détectés |
| 3 | Expansion du lexique existant (section 2.1 à 2.8) | `rules.py` (regex enrichies) | Réduit les faux négatifs sur formulations locales/variantes |
| 4 | Recollement des espacements/leetspeak actif par défaut (section 5.1) | `normalizer.py` | Contre l'obfuscation volontaire |
| 5 | Scoring de co-occurrence (section 4) | `scorer.py` | Affine la précision sur les combinaisons de signaux faibles |
| 6 | Expansion du corpus ML (section 6) | `classifier.py` | Améliore la généralisation du modèle ML, notamment pour les nouvelles catégories |
| 7 | Fuzzy matching sur termes critiques (section 5.2) | nouveau `fuzzy_matcher.py` | Tolérance aux fautes de frappe, gain marginal mais utile |
| 8 | Amélioration pipeline OCR (section 8) | `ocr.py` | Fiabilise l'analyse d'images |

---

# 10. VALIDATION APRÈS IMPLÉMENTATION

Pour chaque catégorie ajoutée ou enrichie, ajouter dans `test_engine.py` (suivant le format déjà existant dans `TestRegles` et `TestScorer`) :

1. Au moins 2 tests positifs (le signal doit se déclencher) par nouvelle règle.
2. Au moins 1 test de négation par règle sensible (le signal ne doit PAS se déclencher sur une phrase de mise en garde contenant les mêmes mots-clés).
3. Au moins 1 test de contre-exemple légitime par catégorie (aucun signal ne doit se déclencher).
4. Un test de co-occurrence vérifiant qu'une combinaison de deux signaux faibles produit bien le bonus attendu et un score final cohérent.

Exemple de test de non-régression pour la négation (section 3), à ajouter :

```python
def test_negation_ne_declenche_pas_otp(self):
    """Un message de prévention ne doit jamais scorer comme une demande de code."""
    sms = "Attention, ne communiquez jamais votre code secret à qui que ce soit, même à un agent MTN."
    signals, score = evaluate_rules(sms)
    codes = [s.code for s in signals]
    assert "RULE_OTP_PIN" not in codes
```

---

**Fin du document.** Ce fichier peut être collé directement dans Antigravity avec l'instruction : *"Implémente les sections 2 à 9 de ce document dans l'ordre de priorité de la section 9, en respectant REGLES_ANTIGRAVITY_SURCHECK_AI.md pour le vocabulaire de sortie et l'architecture existante."*
