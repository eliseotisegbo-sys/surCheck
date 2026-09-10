# AUDIT SÛRCHECK AI — ÉCARTS AU CAHIER DES CHARGES & AUX RÈGLES ANTIGRAVITY
**Document de travail à usage d'Antigravity** — à coller tel quel comme prompt de correction.
Date de l'audit : 09/09/2026. Sources croisées : `Cahier_des_charges_SurCheck_AI_Complet.docx`, `REGLES_ANTIGRAVITY_SURCHECK_AI.md`, `SuCheck_Chariow_API_Modele_Paiement_Credits_Antigravity.md`, et l'intégralité du code fourni (apps/api, apps/web, packages/database, docs de déploiement).

---

## COMMENT UTILISER CE FICHIER

Chaque point est classé par gravité. Corrige dans cet ordre : 🔴 CRITIQUE (sécurité / crash) → 🟠 MAJEUR (écart produit/cahier des charges) → 🟡 MODÉRÉ (incohérence produit/juridique) → 🟢 MINEUR (qualité de code). Pour chaque point : *Constat* → *Preuve* → *Correctif attendu*. Respecte `REGLES_ANTIGRAVITY_SURCHECK_AI.md` section 6 (inspecter l'existant, module par module, tests, commit).

---

## 🔴 1. SÉCURITÉ CRITIQUE — SECRETS RÉELS EXPOSÉS DANS LE DÉPÔT

C'est la priorité absolue, avant tout autre correctif. Le cahier des charges (section 34) et `REGLES_ANTIGRAVITY` (4.2) exigent : *« Les clés secrètes restent uniquement en variables d'environnement côté serveur, jamais exposées côté client »* et *« Ne jamais exposer les secrets »* (doc Chariow, section 32/35). Ces règles sont violées à plusieurs endroits versionnés dans le dépôt :

1. **`.env.example` contient de vrais secrets en clair**, ajoutés après la section "FIN DU FICHIER" :
   - `mot_de_passe= Ge5ZNjlSDRT9cw1t` (mot de passe DB Supabase)
   - `JWT_SECRET_KEY= 8a027971-87c1-4053-ada5-d15f7517a455`
   - `SUPABASE_SERVICE_ROLE_KEY= eyJhbGciOi...` (clé d'accès admin complet à la base)
   → Ce fichier porte pourtant l'avertissement explicite *« NE JAMAIS COMMITTER CE FICHIER AVEC DES SECRETS RÉELS »* juste au-dessus. Le fichier se contredit lui-même.
2. **`APIChariow.md`** contient la clé API Chariow réelle en clair : `sk_o0xs5yj1_...`.
3. **`apps/api/src/config.py`** code cette même clé Chariow **en valeur par défaut** (`CHARIOW_API_KEY: str = os.getenv("CHARIOW_API_KEY", "sk_o0xs5yj1_...")`), ainsi que l'URL et la clé anonyme Supabase, et un `PHONE_HASH_SALT` par défaut. Si la variable d'environnement n'est pas positionnée en production, c'est ce secret versionné qui sera utilisé silencieusement.
4. **`RAILWAY_DEPLOYMENT.md`** et **`DEPLOYMENT.md`** exposent en clair `CHARIOW_WEBHOOK_SECRET=whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz` ainsi que les `CHARIOW_PRODUCT_PACK_*`.
5. Ces fichiers sont visiblement déjà poussés sur un dépôt GitHub public (`DEPLOYMENT_SUMMARY.md` référence `github.com/eliseotisegbo-sys/surCheck`), donc ces secrets doivent être considérés comme **compromis**.

### Correctifs obligatoires
- [ ] Retirer immédiatement tout secret réel de `.env.example`, `APIChariow.md`, `RAILWAY_DEPLOYMENT.md`, `DEPLOYMENT.md`. Ne laisser que des placeholders (`<<REMPLACER>>`), comme le fait déjà correctement le reste de `.env.example`.
- [ ] **Régénérer/révoquer** : `JWT_SECRET_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `CHARIOW_API_KEY`, `CHARIOW_WEBHOOK_SECRET`, mot de passe DB Supabase. Tous ces secrets doivent être considérés grillés.
- [ ] Supprimer les valeurs par défaut secrètes dans `config.py` (`CHARIOW_API_KEY`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `PHONE_HASH_SALT`, `CHARIOW_WEBHOOK_SECRET`) : lever une erreur explicite au démarrage si la variable d'env est absente en production, plutôt que d'utiliser un fallback codé en dur.
- [ ] Ajouter ces fichiers sensibles à un nettoyage d'historique Git (`git filter-repo` / BFG) si le dépôt est public, sinon les secrets restent visibles dans l'historique même après suppression du fichier.
- [ ] Auditer `apps/web/src/lib/supabase.ts` : la clé anonyme en dur en fallback est moins grave (elle est publique par design), mais retirer quand même le hardcoding et exiger la variable d'environnement.

---

## 🔴 2. BUGS BLOQUANTS — CRASHS AU RUNTIME (non détectés car masqués par les tests)

Le cahier des charges impose de *« tester chaque module »* (section 6 REGLES) — ces bugs prouvent que certains chemins ne sont testés qu'avec des mocks qui masquent le défaut réel.

### 2.1 `apps/api/src/services/supabase_db.py` → `NameError` sur `datetime`
- **Constat** : `moderate_report()` appelle `datetime.now().isoformat()` mais `datetime` n'est **jamais importé** dans ce fichier (seuls `hashlib`, `logging`, `typing`, `httpx` le sont).
- **Preuve** : `test_admin_moderation.py` mocke entièrement `supabase_db.moderate_report`, donc le vrai code n'est jamais exécuté par les tests → le bug est invisible en CI mais plantera en production dès la première modération réelle.
- **Correctif** : ajouter `from datetime import datetime, timezone` en tête de `supabase_db.py`.

### 2.2 `apps/api/src/services/chariow_provider.py` → `TypeError` sur `dict_items` non sliçable
- **Constat** : `create_checkout()` contient `custom_metadata.items()[:10]` — `dict.items()` renvoie un `dict_items`, qui **ne supporte pas le slicing**. Cette ligne lève systématiquement une `TypeError` dès qu'un checkout est créé.
- **Preuve** : `test_chariow_credits.py` teste `parse_webhook` et `verify_webhook_signature` mais ne teste jamais `create_checkout()` de bout en bout avec un vrai dict → le bug n'est pas couvert.
- **Correctif** : remplacer par `dict(list(custom_metadata.items())[:10])`, ou plus simplement limiter en amont le nombre de clés avant l'appel.
- **Impact produit** : **le parcours d'achat de crédits est actuellement cassé** — `POST /api/v1/payment/checkout` plante à chaque appel réel. C'est une régression totale du flux de paiement, la fonctionnalité la plus sensible du produit (argent réel).

### 2.3 `apps/api/src/routers/analyze.py` → `NameError` sur `RiskLevel`
- **Constat** : `_enrich_with_reputation()` référence `RiskLevel.ELEVE`, mais `RiskLevel` n'est **pas importé** dans ce fichier (seuls `AnalyzeTextRequest, AnalyzeUrlRequest, AnalysisResult, ContentType, AnalysisFeedbackRequest` le sont depuis `..schemas`).
- **Impact** : dès qu'un numéro ou une URL déjà signalés par la communauté est détecté dans un message analysé (cas d'usage central du produit — section 26/27 du cahier des charges), l'endpoint `/analyze/text` et `/analyze/url` **plantent** au lieu de renvoyer le résultat enrichi.
- **Correctif** : ajouter `RiskLevel` à l'import `from ..schemas import (...)`.

### 2.4 `apps/api/src/routers/analyze.py` → endpoint `/analyze/image` non fonctionnel côté FastAPI
- **Constat** : la signature `async def analyze_image(file: bytes = None):` ne déclare pas de dépendance `UploadFile = File(...)`. FastAPI ne saura pas parser un envoi multipart réel : cet endpoint ne peut **pas** recevoir de fichier tel quel depuis un vrai client HTTP.
- **Correctif** : `async def analyze_image(file: UploadFile = File(...)):`, lire `await file.read()`, et transmettre le vrai `file.content_type` à `extract_text_from_image()` au lieu du `"image/jpeg"` codé en dur (qui contredit la validation `ALLOWED_MIME_TYPES` déjà écrite dans `ocr.py` mais jamais réellement appliquée sur le type reçu).

---

## 🟠 3. ÉCART PRODUIT MAJEUR — LA FONCTIONNALITÉ OCR EST SIMULÉE CÔTÉ FRONT

- **Constat** : dans `apps/web/src/app/page.tsx`, l'onglet « Capture d'écran » n'appelle **jamais** l'endpoint `/analyze/image`. Le code fabrique une fausse chaîne de texte à partir du **nom du fichier** :
  ```ts
  contentToAnalyze = `Capture d'écran importée : ${selectedImage.name}. Vérification des motifs suspects.`;
  ```
  puis l'envoie à `checkContent(..., "text")`. Le score de risque affiché à l'utilisateur **ne dépend jamais du contenu réel de l'image**, uniquement du nom du fichier choisi.
- **Gravité produit** : ceci est trompeur pour l'utilisateur final — exactement le type de faux positif/négatif dangereux que le cahier des charges (section 35) demande explicitement de tester et d'éviter (« faux négatif sur une demande de code, phishing... »). Un utilisateur qui importe une capture d'arnaque réelle peut recevoir un score « Faible » basé sur rien.
- **Correctif attendu** :
  - [ ] Appeler réellement `POST /api/v1/analyze/image` avec le fichier en `FormData`, une fois 2.4 corrigé côté backend.
  - [ ] Ajouter un état de chargement spécifique « Extraction du texte de l'image… » distinct de l'analyse texte.
  - [ ] Si l'OCR échoue (Tesseract absent, cf. `ocr.py` `HAS_OCR=False` en fallback), **afficher clairement à l'utilisateur** que l'image n'a pas pu être lue plutôt que de générer un faux score — ne jamais donner un résultat basé sur une donnée fictive.

---

## 🟠 4. ÉCART PRODUIT MAJEUR — INCOHÉRENCE DES NUMÉROS D'URGENCE OPÉRATEURS

Le cahier des charges (section 40) et les REGLES imposent la rigueur factuelle sur tout contenu de sécurité. Or le produit affiche **trois versions différentes** du numéro Moov Money selon l'écran :

| Emplacement | Numéro MTN | Numéro Moov |
|---|---|---|
| `page.tsx` — plan d'action débloqué | 111 | **123** |
| `page.tsx` — pied de page | 111 | **100** |
| `guide_reflexe_surcheck.html` | 111 | **123** |
| `compte/page.tsx` (implicite, non contredit) | — | — |

- **Correctif** : fixer une seule source de vérité (une constante partagée `OPERATOR_CONTACTS` dans `apps/web/src/lib/`) et l'utiliser partout (page principale, footer, guide PDF). Vérifier le vrai numéro officiel Moov Bénin avant publication — ne jamais laisser deux valeurs contradictoires dans un contenu à vocation de sécurité financière.

---

## 🟠 5. ÉCART PRODUIT MAJEUR — SURPROMESSE JURIDIQUE : « ATTESTATION CERTIFIÉE / DOCUMENT OFFICIEL OPPOSABLE »

Le cahier des charges section 40 est explicite : **« Ne jamais promettre la sécurité absolue »**, et REGLES 3.4 impose le registre strict (« risque potentiel », jamais d'affirmation catégorique). Or dans `page.tsx`, la section de paywall promet :

> *« Attestation certifiée : Document officiel opposable avec empreinte cryptographique. »*
> *« Analyse complète débloquée & certifiée SûrCheck »* / *« Réf : ... • Certifié Bénin »*

- **Problème** : rien dans le code ne génère de document juridiquement « opposable », ni d'empreinte cryptographique (pas de signature, pas de hachage vérifiable exposé à l'utilisateur, pas de PDF signé). C'est une promesse commerciale non tenue par l'implémentation, et le terme « opposable » a un sens juridique précis (valable devant un tiers/tribunal) que SûrCheck ne peut pas garantir — un outil d'aide à la décision non professionnel ne peut pas se prévaloir de ce statut.
- **Correctif attendu** :
  - [ ] Retirer « officiel opposable », « certifié », « Certifié Bénin » de tout texte utilisateur tant qu'aucune fonctionnalité réelle (génération PDF signé + hash vérifiable + mention légale claire de simple aide à la décision) n'existe.
  - [ ] Si cette fonctionnalité est réellement souhaitée (rapport téléchargeable avec hash SHA-256 affiché pour preuve d'intégrité), l'implémenter réellement plutôt que de l'annoncer par un simple texte marketing.

---

## 🟠 6. ÉCART PRODUIT MAJEUR — LE GUIDE HTML IMITE UN DOCUMENT GOUVERNEMENTAL OFFICIEL

- **Constat** : `apps/web/public/guide_reflexe_surcheck.html` s'auto-titre **« SûrCheck AI — République du Bénin »**, avec un liseré tricolore aux couleurs du drapeau béninois en haut de page, un badge « Guide Réflexe Citoyen », une référence façon administrative (« Réf. SC-BJ/2026-PUB »), et un pied de page « Cotonou, République du Bénin ».
- **Gravité** : SûrCheck est un produit **privé**, pas une émanation de l'État béninois. Présenter un document avec les couleurs nationales et la mention « République du Bénin » en en-tête peut être perçu comme une usurpation d'autorité publique, ce qui est en contradiction frontale avec REGLES 2.5 (sobriété, ne rien présenter de façon trompeuse) et avec le principe cahier des charges de ne jamais sur-affirmer une légitimité que le produit n'a pas (section 6, section 40).
- **Correctif attendu** :
  - [ ] Retirer la mention « République du Bénin » du titre et du pied de page.
  - [ ] Retirer ou clarifier fortement le liseré tricolore et le badge « Réf. SC-BJ/... » qui imitent une numérotation administrative officielle.
  - [ ] Ajouter une mention explicite et visible « SûrCheck AI est une initiative privée, non affiliée à l'État béninois » si le contenu doit rester à vocation citoyenne/préventive.
  - [ ] Vérifier et sourcer publiquement le numéro « Police / OCRC Cotonou : 21 30 08 62 » avant toute diffusion — une information d'urgence erronée est un risque direct pour l'utilisateur.

---

## 🟠 7. ÉCART CAHIER DES CHARGES — GRILLE TARIFAIRE INCOHÉRENTE SELON 3 SOURCES DIFFÉRENTES

Le cahier des charges principal, le document Chariow, et le code réellement déployé donnent **trois grilles tarifaires différentes**, jamais réconciliées :

| Source | Analyse unique | Pack 5 | Pack 10/20 | Pack 25/50 |
|---|---|---|---|---|
| Cahier des charges §13 (original) | — | 100 FCFA | 300 FCFA (20) | 500 FCFA (50) |
| Cahier des charges §29 (complément) | 100–200 FCFA | — | — | — |
| `SuCheck_Chariow...md` §4 | 300 FCFA | 1000 FCFA | 1500 FCFA (10) | 3000 FCFA (25) |
| `config.py` / code déployé réel | **600 FCFA** | 1500 FCFA | 2500 FCFA (10) | 5000 FCFA (25) |

- **Impact** : la documentation produit ne reflète plus du tout le produit réellement en vente (le prix réel facturé, 600 FCFA, est le double de ce qu'annonce le document de référence Chariow, lui-même déjà différent du cahier des charges d'origine).
- **Correctif** :
  - [ ] Choisir **une seule grille tarifaire officielle**, documentée à un seul endroit (source de vérité), et mettre à jour tous les autres documents pour qu'ils y renvoient au lieu de dupliquer des chiffres.
  - [ ] Mettre à jour le cahier des charges principal (sections 13 et 29) pour refléter les tarifs réels post-contrainte Chariow (minimum 565 FCFA), avec justification écrite du changement (traçabilité produit).

---

## 🟠 8. ÉCART CAHIER DES CHARGES — FONCTIONNALITÉS DÉCRITES MAIS ABSENTES DU CODE

1. **Vérification externe PhishTank/OpenPhish (section 7, 9 « Niveau 3 »)** : aucune intégration n'existe dans le code. La colonne `phishing_feed_match` existe dans `packages/database/schema.sql` mais n'est jamais écrite par aucun job ou appel API. → soit implémenter l'intégration (avec vérification des CGU des APIs comme demandé en section 15), soit retirer la mention du cahier des charges tant que ce n'est pas construit, pour ne pas prétendre à une fonctionnalité fictive.
2. **`GET /api/v1/reputation/phone/{hash}` (section 32, endpoint explicitement listé au cahier des charges)** : absent de tous les routers (`analyze.py`, `reports.py`, `credits.py`, `admin.py`, `auth.py`, `payment.py`). La réputation n'est utilisée qu'en interne pendant l'analyse, jamais exposée en lecture directe. → créer l'endpoint public manquant ou documenter formellement sa suppression du périmètre MVP.
3. **Case à cocher de consentement avant inscription et avant signalement** : la mémoire produit indique qu'un texte de consentement en case à cocher a été rédigé pour les CGU, mais **aucune case à cocher n'existe** dans `compte/page.tsx` (inscription) ni dans la modale de signalement de `page.tsx`. Le cahier des charges section 6 exige explicitement de « prévoir consentement ». → ajouter une checkbox obligatoire liée aux CGU/à la politique de confidentialité sur ces deux formulaires, avec lien vers le texte réel.
4. **Pages CGU / Politique de confidentialité publiées** : aucune route (`/cgu`, `/confidentialite`, etc.) ni lien de navigation ne pointe vers un texte légal dans l'app, malgré le fait qu'un texte CGU complet ait été rédigé (par ailleurs encore en attente d'email de contact et de date de publication d'après le contexte projet). → créer la page et le lien avant toute mise en production réelle, ne serait-ce que pour la conformité minimale mentionnée en pied de page (« Conformité APDP Bénin »), qui est aujourd'hui une simple mention textuelle sans preuve/lien.

---

## 🟡 9. INCOHÉRENCES DE CODE — RÉPUTATION / HACHAGE

1. **`apps/api/src/routers/reports.py`** utilise `hash_phone_number(request.target)` **même pour un signalement de type URL** (`elif request.report_type == ReportType.URL: target_hash = hash_phone_number(request.target)`), alors que `apps/api/src/services/supabase_db.py` utilise pour les URLs une fonction dédiée (`normalize_url` + `sha256` propre). Résultat : le hash calculé pour une même URL diffère selon qu'il transite par le cache mémoire (`IN_MEMORY_REPORTS`, utilisé par `reports.py`) ou par la persistance Supabase (`save_report`, dans `supabase_db.py`). Les recherches de réputation (`check_url_reputation`) ne retrouveront donc **jamais** les signalements créés par ce chemin en mémoire — cassant silencieusement la fonctionnalité de réputation communautaire pour les URLs.
   - **Correctif** : dans `reports.py`, réutiliser exactement la même logique de normalisation/hachage que `supabase_db.py` (idéalement, extraire une fonction unique partagée `hash_url()` dans `engine/reputation.py` et l'appeler des deux côtés).
2. **`country_code` codé en dur à `"+229"`** dans `supabase_db._increment_reported_number()`, quel que soit le numéro réellement signalé. Cela casse directement la stratégie d'expansion multi-pays du cahier des charges (sections 4, 17, 24 : Togo, Côte d'Ivoire, Sénégal, Burkina Faso) : un numéro togolais signalé sera étiqueté comme béninois. → dériver le `country_code` réel à partir du numéro normalisé (`normalize_phone_number` doit retourner aussi l'indicatif détecté), pas d'une constante.
3. **Poids des règles déterministes non alignés avec le cahier des charges section 9** : le cahier des charges donne à titre d'exemple « Demande d'argent : +25 » et « Urgence artificielle : +15 », mais le code (`engine/rules.py`, `engine/scorer.py`, et sa copie dupliquée côté client `lib/engine.ts`) utilise +35 et +20 respectivement. Ce n'est pas nécessairement un bug (les exemples du cahier n'étaient peut-être pas figés), mais **aucune note de justification produit n'accompagne cet écart**, ce qui viole REGLES 1.2 (« chaque décision doit pouvoir se justifier par le cahier des charges »). → soit aligner les poids, soit documenter formellement (changelog produit + mise à jour du cahier des charges) pourquoi ils ont été recalibrés.
4. **Duplication de moteur de règles** : le moteur de scoring existe en double, une fois côté backend (`apps/api/src/engine/rules.py`) et une fois côté frontend (`apps/web/src/lib/engine.ts`) comme filet de repli hors-ligne. Les deux listes de règles sont déjà légèrement désynchronisées dans les commentaires/regex (ex. `RULE_FALSE_TRANSFER` côté front vs `RULE_FALSE_TRANSFER_REVERSAL` côté back) et devront être maintenues manuellement en parallèle à chaque évolution — risque de dérive silencieuse. → documenter clairement ce choix architectural assumé (fallback résilient volontaire, cf. `CHANGELOG.md`) et ajouter un test de non-régression qui compare les deux jeux de règles à chaque build pour détecter toute désynchronisation.

---

## 🟡 10. INCOHÉRENCE CÔTÉ FRONT — SIGNALEMENT NON AUTHENTIFIÉ

- **Constat** : dans `page.tsx`, la modale de signalement (`submitReport`) appelle directement `fetch("/api/v1/reports", ...)` sans passer par `submitReport()` de `apps/web/src/lib/api.ts`, qui gère pourtant déjà l'ajout du token JWT (`buildHeaders()`). Résultat : même un utilisateur connecté envoie un signalement **anonyme** (`user_id` toujours `null` côté serveur), ce qui casse la traçabilité prévue par le schéma (`reports.user_id`).
- **Correctif** : remplacer l'appel `fetch` inline par l'import et l'utilisation de `submitReport()` depuis `@/lib/api`.

---

## 🟢 11. QUALITÉ DE CODE / COHÉRENCE MINEURE

- [ ] `apps/api/src/schemas.py` : `ReportStatus.CONTESTE = "conteste"` — l'accent est absent alors que le workflow décrit dans le cahier des charges et `REGLES` écrit systématiquement « contesté » avec accent. Vérifier la cohérence d'affichage côté admin (si l'accent est ajouté seulement à l'affichage, très bien ; sinon uniformiser).
- [ ] `apps/api/src/routers/reports.py` : le `ReportType.PAGE` est défini dans l'enum mais traité de façon identique à `MESSAGE` dans la logique de hachage/masquage (`else` générique) — aucune distinction fonctionnelle réelle entre « signaler un message » et « signaler une page », alors que le cahier des charges section 5C les distingue explicitement. Décider soit de les fusionner formellement dans le schéma, soit d'implémenter un traitement différencié (ex. capture d'URL de la page plutôt que texte libre).
- [ ] Deux fichiers `REGLES_ANTIGRAVITY_SURCHECK_AI.md` strictement identiques existent à la racine et dans `.agents/rules/` — source de vérité dupliquée, risque de divergence future si l'un est mis à jour sans l'autre.
- [ ] `.gitignore` local `apps/web/.gitignore` ignore `.env*` sans exception `!.env.example`, contrairement au `.gitignore` racine qui a l'exception. Vérifier qu'aucun fichier `.env.example` local à `apps/web` n'est accidentellement exclu du suivi Git.
- [ ] `paiement/page.tsx` : le solde de crédits est affiché deux fois avec deux sources potentiellement désynchronisées (`creditsBalance` state vs `user.paid_credits` du cache local) — factoriser sur une seule source après le premier fetch réseau.

---

## PLAN D'ACTION PRIORISÉ (à exécuter dans cet ordre)

1. **Sécurité** (section 1) — révoquer/régénérer tous les secrets exposés, nettoyer les fichiers versionnés, supprimer les fallbacks secrets codés en dur.
2. **Bugs bloquants** (section 2) — corriger les 4 crashs runtime (`datetime`, `dict_items[:10]`, `RiskLevel`, `UploadFile`). Le paiement (2.2) est la priorité n°1 métier : c'est un flux financier cassé en production.
3. **OCR simulé** (section 3) — ne jamais afficher un score basé sur des données fictives.
4. **Numéros d'urgence contradictoires** (section 4) — corriger avant toute campagne d'acquisition (section 36/38 du cahier des charges : recrutement des 20-50 premiers testeurs).
5. **Surpromesses juridiques et imitation d'autorité publique** (sections 5 et 6) — corriger avant toute diffusion publique du guide et de l'écran de résultat payant.
6. **Grille tarifaire** (section 7) — fixer une source de vérité unique.
7. **Fonctionnalités manquantes du cahier des charges** (section 8) — endpoint réputation, PhishTank/OpenPhish, consentement RGPD/APDP, pages CGU.
8. **Cohérence réputation/hachage et multi-pays** (section 9).
9. **Signalement non authentifié** (section 10).
10. **Nettoyage qualité de code** (section 11).

Chaque correctif doit être testé unitairement (`pytest` côté API, test manuel côté web), documenté dans `CHANGELOG.md`, et commité séparément conformément à REGLES section 6 (« committer après chaque étape importante »).
