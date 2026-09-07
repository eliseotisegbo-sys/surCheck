# RÈGLES ET ÉTAT D'ESPRIT — ANTIGRAVITY POUR SÛRCHECK AI

**Objectif de ce fichier** : servir de charte de comportement pour l'éditeur/agent Antigravity pendant toute la construction de SûrCheck AI. Il complète le cahier des charges (vision, fonctionnalités, architecture, base de données, moteur de risque, monétisation) sans le répéter. Il fixe uniquement **comment** le produit doit être pensé, écrit, dessiné et codé pour qu'il paraisse conçu par une équipe humaine expérimentée à Cotonou — pas généré.

Toute sortie d'Antigravity (code, texte d'interface, e-mails, wireframes, README, messages d'erreur) doit être confrontée à ce fichier avant validation.

---

## 1. ÉTAT D'ESPRIT GÉNÉRAL

1. **SûrCheck n'est pas un projet démo, c'est un produit de confiance.** L'utilisateur cible est une personne au Bénin qui hésite avant d'envoyer de l'argent. Chaque écran doit réduire son anxiété, pas l'impressionner.
2. **Chaque décision doit pouvoir se justifier par le cahier des charges**, jamais par « c'est ce qui se fait d'habitude » ou « c'est plus simple à générer ainsi ». Si Antigravity ne trouve pas de justification produit à un choix, il doit s'arrêter et demander plutôt que d'appliquer un standard générique.
3. **Construire pour le Bénin d'abord**, pas pour un marché occidental générique : connexions parfois lentes, écrans modestes, data mobile chère, usage majoritairement WhatsApp/Facebook/TikTok, mélange français/expressions locales.
4. **Sobriété avant esthétique.** Un produit anti-arnaque qui a l'air « flashy » ou « startup gadget » détruit sa propre crédibilité. La confiance visuelle passe par la retenue, pas par la démonstration.
5. **Aucune fonctionnalité, aucun texte, aucun composant ne doit donner l'impression d'avoir été copié-collé d'un template générique.** Chaque écran doit avoir une raison d'exister propre à SûrCheck (score de risque, signaux, catégories, historique, signalement, réputation modérée).
6. **Avant de coder, inspecter l'existant.** Ne jamais réécrire un module qui fonctionne. Travailler module par module, tester, vérifier types/lint, documenter, committer après chaque étape — exactement l'ordre du plan à 14 jours du cahier des charges.
7. **En cas de doute entre « rapide à générer » et « cohérent avec le produit », toujours choisir la cohérence.** Un MVP peut être incomplet ; il ne doit jamais paraître incohérent ou générique.

---

## 2. INTERDICTION DES SIGNES VISUELS D'IA (DESIGN)

Ces règles s'appliquent à **tout** ce qu'Antigravity produit visuellement : landing page, formulaire d'analyse, page de résultat, historique, signalement, dashboard admin, e-mails.

### 2.1 Formes et contours
- Interdiction des coins arrondis systématiques et exagérés (`border-radius` uniforme à 16–24px partout). Chaque composant doit avoir un rayon justifié par sa fonction (ex. : carte de résultat = léger arrondi pour la lisibilité ; bouton d'action critique = arrondi minimal, presque droit, pour signaler le sérieux).
- Pas de « bulles » ou « pilules » par défaut sur les badges de risque. Le badge de niveau (Faible/Prudence/Élevé) doit avoir une forme sobre, pas un style « app ludique ».
- Éviter les cartes flottantes avec ombres portées excessives (`box-shadow` doux et généralisé partout). L'ombre doit exister seulement là où elle aide à la hiérarchie (ex. : la carte de score principale), pas sur chaque bloc.

### 2.2 Couleurs
- Pas de dégradés multicolores décoratifs (violet-rose-bleu, etc.) qui n'ont aucun sens fonctionnel.
- La palette doit être **fonctionnelle et restreinte** : une couleur neutre dominante (fond, texte), une couleur de marque, et les trois couleurs de niveau de risque (Faible / Prudence / Élevé) clairement différenciées et accessibles (contraste AA minimum). Aucune autre couleur ne doit apparaître sans rôle précis.
- Ne jamais utiliser des couleurs « IA par défaut » (violet/indigo pastel générique associé aux produits SaaS génériques) sans lien avec la promesse du produit (sécurité, vérification, confiance).
- Un même niveau de risque doit toujours porter la même couleur, partout dans l'app (cohérence système, pas cohérence esthétique).

### 2.3 Animations et éléments « vivants »
- Interdiction des gros points clignotants, pulsations lumineuses ou indicateurs « live » non justifiés par une donnée réelle (ex. : ne pas simuler un compteur d'utilisateurs « en ligne » ou un point vert clignotant décoratif).
- Toute animation doit avoir une fonction claire : chargement réel de l'analyse, transition d'état du score, apparition progressive des signaux détectés. Pas d'animation "pour faire moderne".
- Pas de micro-interactions génériques copiées de templates (confettis, checkmarks animés génériques, illustrations 3D isométriques interchangeables).

### 2.4 Typographie et densité
- Éviter les textes trop serrés (`line-height` faible, `letter-spacing` négatif systématique) qui donnent un rendu dense et impersonnel de type export automatique.
- Une seule famille de police pour le texte courant, une éventuelle deuxième pour les titres — jamais plus, et jamais une police « tech générique » choisie par défaut sans intention (Antigravity doit motiver le choix : lisibilité sur petit écran, poids de fichier réduit pour connexions lentes).
- La hiérarchie typographique (titres, score, signaux, conseils) doit être pensée pour un utilisateur qui lit vite sur un petit écran, pas pour remplir une maquette.
- Aucune icône générique de type « pack d'icônes IA » sans lien direct avec le sens (ex. : ne pas mettre une fusée pour « analyser », un bouclier bleu générique pour tout et n'importe quoi). Les icônes doivent illustrer précisément : argent, urgence, code secret, lien, numéro, signalement.

### 2.5 Mise en page
- Ne pas empiler des sections génériques type « landing SaaS » (Hero → Features en 3 colonnes → Testimonials → Pricing → CTA) sans lien avec le parcours réel décrit dans le cahier des charges (landing → analyse sans friction → score → signaux → recommandation → signalement/partage → rapport payant).
- Chaque page doit correspondre à une étape précise du parcours utilisateur, pas à une structure de page web générique.
- Le design mobile-first n'est pas une contrainte esthétique : c'est une contrainte de service (utilisateur pressé, souvent en train de décider avant de payer). Prioriser toujours l'action la plus utile en haut d'écran.

---

## 3. INTERDICTION DES SIGNES TEXTUELS D'IA (RÉDACTION)

Toutes les interfaces, tous les messages système, e-mails, textes marketing générés par Antigravity doivent respecter :

1. **Pas de tirets cadratins (—) en remplacement de virgules ou de points** dans les textes destinés à l'utilisateur final. Utiliser une ponctuation naturelle en français courant.
2. **Pas de phrases génériques universelles** du type « Dans le monde numérique d'aujourd'hui... », « Grâce à notre technologie de pointe... », « Nous sommes ravis de vous présenter... ». Chaque phrase doit dire quelque chose de concret sur le risque, le signal ou l'action à mener.
3. **Pas de formulations répétées telles quelles à partir de la demande de l'utilisateur.** Si un texte demande « écris un message qui explique le score de risque », le résultat ne doit pas recopier la structure de la consigne mot pour mot ; il doit être reformulé et intégré naturellement à l'écran.
4. **Respecter strictement le registre imposé par le cahier des charges** (section 6) : jamais « escroc », jamais « c'est une arnaque confirmée ». Toujours :
   - « Risque potentiel détecté »
   - « Plusieurs signaux nécessitent une vérification »
   - « Signalement communautaire non confirmé »
   - « Vérifiez avant toute transaction »
   - « Aucun signal majeur détecté dans les éléments analysés » (jamais « 100 % sûr »)
5. **Langage simple, direct, destiné au grand public béninois**, sans jargon technique ni anglicismes inutiles. Pas de ton « corporate » froid ni de ton trop enthousiaste façon publicité.
6. **Varier la formulation d'un écran à l'autre** : ne pas réutiliser la même phrase-modèle pour chaque catégorie de risque avec juste le mot changé (éviter l'effet gabarit visible).
7. **Pas de disclaimers légaux génériques copiés d'un template** ; les mentions de confidentialité, de non-garantie et de consentement doivent être écrites spécifiquement pour SûrCheck (données collectées, durée de conservation, anonymisation, statut de simple aide à la décision).

---

## 4. ARCHITECTURE ET SÉCURITÉ : ADAPTER, NE PAS COPIER UN STANDARD GÉNÉRIQUE

Le cahier des charges impose une stack précise (Next.js + TypeScript + Tailwind, FastAPI/Python, PostgreSQL, scikit-learn, Vercel). Antigravity ne doit jamais remplacer ces choix par un « stack standard » différent sous prétexte de facilité, et ne doit jamais appliquer une architecture générique sans l'adapter aux contraintes réelles du produit.

### 4.1 Ce qu'il ne faut jamais faire
- Copier une architecture microservices complexe « par défaut » alors que le MVP doit rester simple, découplé mais pas sur-ingénieré.
- Appliquer un système d'authentification générique (OAuth multi-fournisseurs, SSO entreprise) alors que le produit vise un utilisateur grand public avec inscription/connexion simple.
- Utiliser une architecture de sécurité générique de type « entreprise » sans l'adapter aux vrais risques du produit : ici, les risques prioritaires sont l'abus de signalement (spam/diffamation), l'exposition de numéros de téléphone bruts, la fraude sur les paiements côté client, et l'ouverture non contrôlée d'URLs suspectes côté serveur.
- Suivre aveuglément un tutoriel ou un boilerplate Next.js/FastAPI standard sans respecter le pipeline moteur d'analyse propre à SûrCheck (normalisation → extraction → règles → ML → réputation → agrégation/calibration → explication).

### 4.2 Ce qu'il faut systématiquement faire
- Toute confirmation de paiement vient exclusivement du webhook serveur du prestataire (jamais du navigateur), avec traitement idempotent et identifiant de transaction unique.
- Les clés secrètes restent uniquement en variables d'environnement côté serveur, jamais exposées côté client.
- Les numéros signalés sont normalisés par pays et hachés/empreintés avant stockage exploitable, pour limiter l'exposition du numéro brut.
- Le serveur applicatif n'ouvre jamais directement une URL arbitraire fournie par un utilisateur : passage par un service de réputation ou un environnement isolé.
- Rate limiting par IP/compte, anti-spam des signalements, quotas d'analyse, validation stricte de taille/type des fichiers uploadés (images pour l'OCR), aucun upload exécutable accepté.
- Chaque analyse enregistre les signaux, les scores intermédiaires et la version du moteur utilisée (traçabilité et reproductibilité), conformément à la section 33 du cahier des charges.
- Les statuts de modération suivent précisément le workflow défini : nouveau → en vérification → confirmé par éléments suffisants / non confirmé / contesté / retiré. Pas de raccourci « approuvé/rejeté » simplifié à l'excès.
- Les tables (`users`, `analyses`, `reports`, `reported_numbers`, `reported_urls`, `risk_rules`, `analysis_features`, `analysis_feedback`, `payment_transactions`, `scam_patterns`, `reputation_events`, `admin_audit_logs`) sont respectées telles que définies, sans ajout de champs génériques non justifiés ni simplification qui casserait l'audit.

---

## 5. COHÉRENCE SANS PRÉCÉDENT : CE QUE CELA SIGNIFIE CONCRÈTEMENT

« Cohérent sans précédent » ne veut pas dire « spectaculaire » : cela veut dire qu'aucun écran, aucun texte, aucune décision technique ne doit pouvoir être confondu avec un produit générique. Concrètement, avant de valider un module, Antigravity doit vérifier :

- [ ] Ce texte pourrait-il apparaître à l'identique dans n'importe quelle autre application ? → Si oui, le réécrire.
- [ ] Cette couleur, cette forme, cette animation a-t-elle une fonction précise dans le parcours de vérification d'un risque ? → Si non, la supprimer.
- [ ] Ce choix d'architecture est-il justifié par une contrainte réelle du cahier des charges (coût, latence, confidentialité, marché béninois) ? → Si non, revenir au choix spécifié.
- [ ] Le vocabulaire respecte-t-il strictement les formulations imposées (jamais d'accusation, toujours « risque potentiel », « signal », « vérification ») ?
- [ ] Le composant / la fonctionnalité fait-il partie du MVP défini, ou anticipe-t-il une fonctionnalité listée en section 19/39 comme « à ne pas construire avant validation » (app native, assistant WhatsApp automatisé, réseau social, IA propriétaire complexe) ?

---

## 6. RAPPEL DE MÉTHODE (DÉVELOPPEMENT)

- Inspecter l'existant avant de coder, ne jamais réécrire inutilement.
- Travailler module par module dans l'ordre : landing → analyse texte → scoring explicable → OCR image → URL → historique → signalement → admin/modération → paiement/webhook → sécurité/analytics/déploiement.
- Tester chaque module, vérifier types et lint, gérer les erreurs, documenter, committer après chaque étape importante.
- Ne jamais promettre une sécurité absolue dans le code, les messages ou la documentation. Toujours distinguer risque, preuve et signalement.
