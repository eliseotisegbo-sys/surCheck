# SûrCheck — Intégration Chariow API + modèle de paiement par crédits

> Document technique destiné à Antigravity pour intégrer le système de monétisation de SûrCheck.
>
> Version : 1.0 — 8 septembre 2026

---

## 1. Objectif

SûrCheck est une plateforme mobile-first d’aide à la décision face aux messages, liens, numéros et contenus potentiellement frauduleux.

Le parcours commercial retenu est :

**Analyse rapide gratuite → score + signaux → recommandation complète payante → crédits → packs → réutilisation.**

Le paiement doit rester séparé du moteur d’analyse : Chariow sert de couche de checkout/paiement, tandis que **PostgreSQL reste la source de vérité pour les crédits SûrCheck**.

Le cahier des charges impose déjà un paiement confirmé côté serveur, un identifiant de transaction unique, l’idempotence et l’absence de clés secrètes dans le frontend.

---

# 2. Modèle commercial final

## 2.1 Analyse rapide gratuite

L’utilisateur peut lancer une analyse sans paiement et, lorsque cela est possible, sans créer de compte avant la première valeur.

Entrées prévues :

- message ou SMS ;
- lien/URL ;
- capture d’écran ;
- numéro selon les fonctionnalités activées.

Résultat gratuit :

- score de risque ;
- niveau : Faible / Prudence / Élevé ;
- principaux signaux détectés ;
- catégorie probable ;
- avertissement de sécurité essentiel.

**Cette analyse gratuite ne consomme aucun crédit.**

Le système ne doit jamais masquer une alerte de sécurité importante uniquement pour pousser au paiement.

---

# 3. Analyse complète : 300 FCFA

Après le résultat gratuit, afficher un appel à l’action clair :

> **Vous voulez savoir exactement quoi faire ?**
>
> **Obtenir l'analyse complète — 300 FCFA**

L’analyse complète doit apporter une valeur supplémentaire réelle :

- explication détaillée des signaux ;
- recommandation personnalisée ;
- actions à faire maintenant ;
- actions à éviter ;
- informations complémentaires disponibles ;
- analyse approfondie du numéro ou du lien lorsque les sources autorisées le permettent ;
- niveau d’incertitude lorsque les éléments sont insuffisants.

### Règle

**1 analyse complète = 1 crédit**

L’utilisateur peut :

1. payer directement 300 FCFA ;
2. utiliser 1 crédit déjà disponible.

---

# 4. Packs de crédits

Les offres retenues pour le lancement :

| Offre | Prix | Crédits | Coût unitaire |
|---|---:|---:|---:|
| Analyse unique | 300 FCFA | 1 | 300 F |
| Petit pack | 1 000 FCFA | 5 | 200 F |
| Pack recommandé | 1 500 FCFA | 10 | 150 F |
| Gros pack | 3 000 FCFA | 25 | 120 F |

Le pack de 10 crédits peut être mis en avant comme **« Le plus populaire »**.

### Règles des crédits

- 1 crédit = 1 analyse complète.
- Une analyse rapide gratuite = 0 crédit.
- Les crédits achetés n’expirent pas.
- Les crédits sont attachés au compte SûrCheck, pas au navigateur.
- Les crédits ne doivent jamais être modifiables par le frontend.
- Toute attribution ou consommation doit être enregistrée dans un journal.
- Une consommation doit être atomique afin d'éviter les doubles débits.

---

# 5. Parcours utilisateur

```text
Utilisateur
    ↓
Analyse rapide gratuite
    ↓
Score + niveau + signaux
    ↓
Veut savoir quoi faire ?
    ↓
300 FCFA OU 1 crédit
    ↓
Analyse complète
    ↓
Crédit consommé si nécessaire
    ↓
Recommandation
    ↓
Solde affiché
    ↓
Proposition de pack
```

Si l’utilisateur refuse le paiement :

```text
Quitter SûrCheck
    ↓
Revenir plus tard
    ↓
Nouvelle analyse rapide gratuite
    ↓
Nouvelle analyse complète : 300 FCFA
```

Si l’utilisateur possède des crédits :

```text
Analyse rapide
    ↓
Analyse complète
    ↓
-1 crédit
```

---

# 6. Vente de crédits quand l'utilisateur n'a rien à analyser

SûrCheck peut afficher :

> **Vous n'avez rien à vérifier aujourd'hui ?**
>
> Gardez quelques analyses en réserve.
>
> Le jour où vous recevez un message suspect, revenez sur SûrCheck avant d'envoyer votre argent.

CTA :

**Acheter mes crédits**

L’objectif est de transformer un besoin occasionnel en portefeuille de crédits réutilisable.

---

# 7. Chariow : rôle exact dans l'architecture

Chariow ne doit pas gérer le solde interne des crédits SûrCheck.

Chariow doit :

1. recevoir la demande de paiement ;
2. créer la session checkout ;
3. permettre au client de payer ;
4. notifier SûrCheck lorsqu'une vente est finalisée ;
5. fournir les identifiants de vente et les informations nécessaires à la réconciliation.

SûrCheck doit ensuite :

1. vérifier la vente ;
2. identifier le pack acheté ;
3. vérifier que la transaction n'a pas déjà été traitée ;
4. créditer le compte ;
5. enregistrer l'opération ;
6. afficher le nouveau solde.

**PostgreSQL est la source de vérité du portefeuille de crédits.**

---

# 8. Documentation officielle Chariow à utiliser

Documentation développeur :

https://chariow.dev/

API de base :

```text
https://api.chariow.com/v1
```

Introduction API :

https://chariow.dev/api-reference/introduction

Authentification :

https://chariow.dev/fr/introduction/authentication

Produits :

https://chariow.dev/fr/guides/products

Checkout :

https://chariow.dev/fr/guides/checkout

Référence Checkout :

https://chariow.dev/api-reference/checkout/init-checkout

Ventes :

https://chariow.dev/fr/guides/sales

Pulses/Webhooks :

https://chariow.dev/fr/guides/pulses

Bonnes pratiques :

https://chariow.dev/fr/guides/best-practices

Documentation officielle Chariow sur l'API :

https://help.chariow.com/en/articles/259-developer-documentation-and-api

---

# 9. Création et sécurité de la clé API Chariow

Dans Chariow :

**Paramètres → Clés API → Créer une clé API**

La clé complète n'est affichée qu'une fois.

Ne jamais :

- mettre la clé dans Next.js côté client ;
- mettre la clé dans un fichier public ;
- mettre la clé dans Git ;
- mettre la clé dans un prompt ou une documentation publique ;
- envoyer la clé dans une réponse API au navigateur.

La clé doit être une variable d'environnement côté serveur.

Exemple :

```env
CHARIOW_API_KEY=sk_live_xxxxxxxxx
CHARIOW_BASE_URL=https://api.chariow.com/v1
CHARIOW_WEBHOOK_SECRET=xxxxxxxxx
```

Utiliser une clé différente pour développement et production.

---

# 10. Appel Checkout Chariow

L'API Chariow utilise l'authentification Bearer.

Exemple de principe côté serveur :

```http
POST https://api.chariow.com/v1/checkout
Authorization: Bearer <CHARIOW_API_KEY>
Content-Type: application/json
```

Payload conceptuel :

```json
{
  "product_id": "prd_xxxxx",
  "email": "client@example.com",
  "first_name": "Prenom",
  "last_name": "Nom",
  "phone": {
    "number": "XXXXXXXX",
    "country_code": "BJ"
  },
  "redirect_url": "https://surcheck.example/checkout/success?sale={sale_id}",
  "custom_metadata": {
    "surcheck_user_id": "usr_xxxxx",
    "credit_pack": "pack_10",
    "credits": "10",
    "internal_order_ref": "sc_order_xxxxx"
  }
}
```

### Important

Le serveur SûrCheck doit générer lui-même :

- `internal_order_ref` ;
- l'identifiant utilisateur ;
- le pack demandé ;
- le nombre de crédits.

Ne jamais faire confiance au frontend pour définir le nombre de crédits à attribuer.

---

# 11. Mapping des produits Chariow

Créer dans Chariow les offres correspondant aux packs.

Exemple de configuration interne :

```text
pack_1
price = 300 XOF
credits = 1

pack_5
price = 1000 XOF
credits = 5

pack_10
price = 1500 XOF
credits = 10

pack_25
price = 3000 XOF
credits = 25
```

Dans SûrCheck, conserver un mapping sécurisé :

```text
CHARIOW_PRODUCT_PACK_1=prd_xxx
CHARIOW_PRODUCT_PACK_5=prd_xxx
CHARIOW_PRODUCT_PACK_10=prd_xxx
CHARIOW_PRODUCT_PACK_25=prd_xxx
```

Le serveur doit déterminer le nombre de crédits à partir du **product_id Chariow connu côté serveur**, et non à partir d'une valeur envoyée librement par le navigateur.

---

# 12. Attention au type de produit Chariow

La documentation actuelle de Chariow indique que l'API Checkout prend en charge notamment :

- produits téléchargeables ;
- cours ;
- licences ;
- bundles.

Les produits Service, Coaching et « prix libre » ne sont pas pris en charge par l'API Checkout publique.

Pour SûrCheck, valider avec Chariow le type de produit le plus approprié pour représenter un pack de crédits numériques.

**Ne pas supposer qu'un type non supporté fonctionnera.**

---

# 13. Point critique : achats répétés d'un même pack

La documentation Checkout de Chariow expose un état :

```text
already_purchased
```

qui signifie que le client possède déjà le produit.

C'est un point critique pour SûrCheck, car notre modèle exige qu'un utilisateur puisse acheter plusieurs fois des crédits au fil du temps.

### Avant la mise en production

Tester explicitement :

1. utilisateur achète Pack 10 ;
2. paiement confirmé ;
3. crédits ajoutés ;
4. même utilisateur revient ;
5. il tente d'acheter à nouveau Pack 10 ;
6. vérifier le comportement réel de Chariow.

**Ne pas contourner artificiellement une restriction Chariow.**

Si Chariow bloque effectivement les achats répétés du même produit, mettre l'intégration en pause pour ce flux et demander à Chariow quel mécanisme officiel ils recommandent pour des achats répétitifs de produits numériques/crédits.

L'architecture SûrCheck doit donc isoler Chariow derrière un `PaymentProvider`, afin de pouvoir changer de prestataire sans réécrire le système de crédits.

---

# 14. Réponse Checkout à gérer

L'API Checkout peut renvoyer différents états.

Le backend doit gérer au minimum :

```text
payment
completed
already_purchased
erreur
```

Pour un produit payant :

```text
step = payment
```

Le serveur récupère :

```text
payment.checkout_url
```

Puis le frontend redirige l'utilisateur vers cette URL.

### Ne jamais créditer à ce stade.

Le checkout créé ne signifie pas que le paiement est finalisé.

---

# 15. Redirection après paiement

Utiliser une `redirect_url` vers SûrCheck.

Exemple :

```text
https://surcheck.example/checkout/success?sale={sale_id}
```

Cette page doit seulement informer l'utilisateur :

> **Paiement en cours de vérification…**

Elle ne doit pas attribuer les crédits elle-même.

Le crédit est attribué uniquement après confirmation serveur.

---

# 16. Webhook / Pulse Chariow

Configurer un Pulse Chariow vers :

```text
POST /api/v1/webhooks/chariow
```

ou, selon l'architecture :

```text
POST /api/v1/webhooks/payment/chariow
```

Événement principal :

```text
successful.sale
```

Événements utiles à surveiller :

```text
successful.sale
failed.sale
abandoned.sale
refunded.sale
```

Le webhook doit être traité côté backend.

---

# 17. Traitement du webhook

Flux obligatoire :

```text
Chariow
   ↓
POST /api/v1/webhooks/chariow
   ↓
Valider l'authenticité du webhook
   ↓
Extraire sale.id
   ↓
Vérifier si sale.id existe déjà
   ↓
Si déjà traité → répondre sans recréditer
   ↓
Sinon :
   ↓
Vérifier le statut de vente
   ↓
Identifier le produit
   ↓
Déterminer le pack côté serveur
   ↓
Identifier l'utilisateur SûrCheck
   ↓
Transaction PostgreSQL
   ↓
Créer payment_transaction
   ↓
Ajouter les crédits
   ↓
Créer credit_transaction
   ↓
Marquer la vente comme traitée
   ↓
Commit
```

---

# 18. Idempotence obligatoire

Chaque vente Chariow doit avoir une contrainte unique.

Exemple :

```text
provider = chariow
external_transaction_id = sal_xxxxx
```

Contrainte :

```text
UNIQUE(provider, external_transaction_id)
```

Si Chariow envoie deux fois le même webhook :

```text
1er webhook → +10 crédits
2e webhook → aucun nouveau crédit
```

Jamais :

```text
1er webhook → +10
2e webhook → +10
```

---

# 19. Tables PostgreSQL

## `payment_transactions`

Champs recommandés :

```text
id
user_id
provider
external_sale_id
external_transaction_id
product_id
pack_code
amount
currency
status
raw_event_id
raw_payload_hash
processed_at
created_at
updated_at
```

Contraintes :

```text
UNIQUE(provider, external_sale_id)
```

et si disponible :

```text
UNIQUE(provider, external_transaction_id)
```

---

## `credit_wallets`

```text
id
user_id
balance
created_at
updated_at
```

Un utilisateur possède un portefeuille.

---

## `credit_transactions`

```text
id
user_id
wallet_id
type
amount
balance_before
balance_after
reference_type
reference_id
description
created_at
```

Types possibles :

```text
purchase
consumption
refund
bonus
admin_adjustment
expiration
```

Pour le modèle actuel :

```text
expiration = jamais
```

---

# 20. Consommation d'un crédit

Lorsqu'un utilisateur demande l'analyse complète :

```text
Analyse gratuite
      ↓
Utilisateur clique "Voir l'analyse complète"
      ↓
Backend vérifie le solde
      ↓
Solde >= 1 ?
      ↓
Oui
      ↓
Transaction PostgreSQL
      ↓
balance = balance - 1
      ↓
Créer credit_transaction
      ↓
Générer/débloquer l'analyse complète
```

La décrémentation doit être atomique.

Ne jamais faire :

```text
GET balance
frontend balance - 1
POST nouveau balance
```

Faire l'opération côté serveur avec une transaction SQL.

---

# 21. Protection contre les doubles clics

Si l'utilisateur clique deux fois rapidement sur :

**« Voir mon analyse complète »**

il ne doit consommer qu'un seul crédit pour une seule analyse.

Utiliser :

- identifiant unique de l'analyse ;
- verrouillage/transaction PostgreSQL ;
- contrainte d'unicité lorsque nécessaire ;
- traitement serveur idempotent.

---

# 22. Paiement direct de 300 FCFA

Le paiement direct et les crédits doivent utiliser le même moteur.

Deux chemins :

### Chemin A — utilisateur sans crédit

```text
Analyse gratuite
→ Obtenir l'analyse complète
→ Checkout Chariow 300 F
→ Paiement
→ Webhook
→ Déblocage de cette analyse
```

### Chemin B — utilisateur avec crédit

```text
Analyse gratuite
→ Utiliser 1 crédit
→ -1 crédit
→ Déblocage immédiat
```

Pour éviter les incohérences, créer un `premium_access` ou une réservation liée à l'analyse.

Exemple :

```text
analysis_id
user_id
access_type = purchase | credit
payment_transaction_id
credit_transaction_id
status
```

---

# 23. Cas où le paiement réussit mais la réponse utilisateur échoue

Exemple :

```text
Client paie
↓
Chariow confirme
↓
Webhook reçu
↓
Crédits ajoutés
↓
Téléphone fermé avant l'affichage
```

Au retour, SûrCheck doit pouvoir retrouver :

```text
Solde = 10 crédits
```

Le système ne doit jamais dépendre de la page « merci ».

---

# 24. Réconciliation

Ajouter une tâche d'administration permettant de comparer périodiquement :

```text
Ventes Chariow
        VS
Transactions SûrCheck
        VS
Crédits attribués
```

Utiliser l'API Sales Chariow pour récupérer les ventes et contrôler les éventuelles anomalies.

Cas à détecter :

- vente Chariow réussie sans transaction SûrCheck ;
- transaction SûrCheck sans vente correspondante ;
- double attribution ;
- montant inattendu ;
- produit inattendu ;
- remboursement ;
- utilisateur introuvable.

---

# 25. Remboursement

Un remboursement ne doit pas être ignoré.

Si Chariow émet un événement de remboursement :

```text
refunded.sale
```

SûrCheck doit rechercher la transaction correspondante.

Règle à définir :

- si les crédits n'ont pas été utilisés : retirer les crédits correspondants ;
- si les crédits ont déjà été consommés : créer un cas à traiter par le système de remboursement/administration ;
- ne jamais créer un solde négatif sans règle explicite.

Cette politique doit être validée avant production.

---

# 26. Dashboard utilisateur

Afficher simplement :

```text
Mes crédits

10 crédits disponibles

[ Acheter des crédits ]
```

Puis :

```text
Historique

+10 crédits
Pack 10 — 1 500 FCFA

-1 crédit
Analyse complète

-1 crédit
Analyse complète
```

---

# 27. Dashboard administrateur

Sections :

### Paiements

- total encaissé ;
- paiements réussis ;
- paiements échoués ;
- paiements abandonnés ;
- remboursements ;
- commissions/frais lorsque disponibles.

### Crédits

- crédits vendus ;
- crédits consommés ;
- crédits restants ;
- achats par pack ;
- utilisateurs payants.

### Contrôle

- doublons ;
- webhooks en erreur ;
- transactions non réconciliées ;
- ajustements administratifs ;
- activité anormale.

---

# 28. Variables d'environnement

Prévoir :

```env
CHARIOW_API_KEY=
CHARIOW_BASE_URL=https://api.chariow.com/v1

CHARIOW_PRODUCT_PACK_1=
CHARIOW_PRODUCT_PACK_5=
CHARIOW_PRODUCT_PACK_10=
CHARIOW_PRODUCT_PACK_25=

CHARIOW_WEBHOOK_SECRET=

APP_URL=
DATABASE_URL=
```

Ne jamais committer les vraies valeurs.

Fournir uniquement :

```text
.env.example
```

---

# 29. Architecture logicielle recommandée

Créer une abstraction :

```text
PaymentProvider
```

Puis :

```text
ChariowPaymentProvider
```

Interface conceptuelle :

```text
createCheckout()
handleWebhook()
verifySale()
getSale()
refund()
reconcile()
```

Le reste de SûrCheck ne doit pas dépendre directement de Chariow.

Architecture :

```text
SûrCheck
   │
   ├── CreditService
   │
   ├── PaymentService
   │      │
   │      └── PaymentProvider
   │              │
   │              └── ChariowPaymentProvider
   │
   └── PostgreSQL
```

Cela permettra plus tard d'ajouter :

```text
FedaPayPaymentProvider
```

ou un autre prestataire sans modifier le portefeuille de crédits.

---

# 30. Endpoints SûrCheck à prévoir

```http
POST /api/v1/checkout
```

Crée une intention de paiement.

```http
POST /api/v1/webhooks/chariow
```

Reçoit les événements Chariow.

```http
GET /api/v1/credits
```

Retourne le solde.

```http
GET /api/v1/credits/transactions
```

Retourne l'historique.

```http
POST /api/v1/analyses/{analysis_id}/unlock
```

Débloque une analyse complète avec un crédit si disponible.

```http
GET /api/v1/payment/{transaction_id}
```

Retourne l'état d'une transaction pour affichage utilisateur.

Admin :

```http
GET /api/v1/admin/payments
GET /api/v1/admin/credits
GET /api/v1/admin/payment-reconciliation
```

---

# 31. Tests obligatoires

Antigravity doit écrire des tests pour :

### Checkout

- produit valide ;
- produit inexistant ;
- utilisateur incomplet ;
- erreur Chariow ;
- checkout réussi ;
- `already_purchased`.

### Webhook

- vente réussie ;
- vente échouée ;
- vente abandonnée ;
- remboursement ;
- webhook dupliqué ;
- payload invalide ;
- événement inconnu.

### Crédits

- +1 ;
- +5 ;
- +10 ;
- +25 ;
- consommation ;
- solde insuffisant ;
- double consommation ;
- transaction concurrente.

### Scénario complet

```text
Utilisateur
→ analyse gratuite
→ achat 10 crédits
→ paiement Chariow
→ webhook
→ +10 crédits
→ analyse complète
→ -1
→ solde 9
```

---

# 32. Règles de sécurité non négociables

1. Le frontend ne confirme jamais un paiement.
2. Le frontend ne modifie jamais le solde.
3. Les clés API restent côté serveur.
4. Le webhook est validé avant traitement.
5. Chaque vente possède un identifiant unique.
6. Les webhooks sont idempotents.
7. Les crédits sont modifiés uniquement dans une transaction serveur.
8. Les opérations financières sont journalisées.
9. Les erreurs de paiement ne doivent jamais attribuer de crédits.
10. Les remboursements doivent être suivis.
11. Les logs ne doivent pas exposer les secrets.
12. Le système doit pouvoir être audité.

---

# 33. Devise

Chariow documente actuellement le **Franc CFA BCEAO (XOF)** parmi ses devises disponibles.

Pour le marché béninois, vérifier dans la boutique Chariow avant création définitive que la devise principale et le parcours de paiement correspondent bien au besoin.

Ne pas coder de conversion manuelle dans SûrCheck si Chariow prend déjà en charge la conversion.

---

# 34. Frais Chariow

Les informations publiques actuelles de Chariow indiquent un modèle avec commission sur les ventes plutôt qu'un abonnement mensuel, avec des taux qui évoluent selon le volume cumulé.

Avant le lancement commercial, Antigravity ne doit pas coder un montant net attendu sans tenir compte des frais réels applicables au compte.

Le chiffre d'affaires brut SûrCheck et le montant réellement reçu doivent être suivis séparément.

---

# 35. Ce qui ne doit PAS être fait

Ne pas :

- attribuer 10 crédits dès que le frontend reçoit `success` ;
- mettre `CHARIOW_API_KEY` dans Next.js client ;
- faire confiance à `credits` envoyé par le navigateur ;
- consommer un crédit avant validation de la transaction lorsqu'il s'agit d'un paiement ;
- créer deux crédits à partir du même webhook ;
- supprimer l'historique financier ;
- modifier directement `balance` sans journal ;
- supposer que les achats répétés du même produit Chariow sont autorisés ;
- dépendre uniquement de la `redirect_url` pour confirmer un paiement.

---

# 36. Ordre d'implémentation Antigravity

## Étape 1
Créer les tables :

- `credit_wallets`
- `credit_transactions`
- `payment_transactions`

## Étape 2
Créer `PaymentProvider`.

## Étape 3
Créer `ChariowPaymentProvider`.

## Étape 4
Créer le checkout serveur.

## Étape 5
Créer le webhook Chariow.

## Étape 6
Implémenter l'idempotence.

## Étape 7
Implémenter le portefeuille de crédits.

## Étape 8
Implémenter la consommation atomique.

## Étape 9
Connecter le paywall de l'analyse complète.

## Étape 10
Créer les packs.

## Étape 11
Créer le dashboard utilisateur.

## Étape 12
Créer le dashboard admin.

## Étape 13
Tester les scénarios de paiement.

## Étape 14
Tester les achats répétés du même pack avec Chariow.

## Étape 15
Effectuer une réconciliation réelle en environnement de test.

## Étape 16
Passer en production uniquement après validation.

---

# 37. Architecture finale

```text
                    SÛRCHECK
                       │
             ┌─────────┴─────────┐
             │                   │
      Analyse gratuite      Compte utilisateur
             │                   │
      Score + signaux       Portefeuille crédits
             │                   │
             └─────────┬─────────┘
                       │
               Analyse complète
                 300 F / 1 crédit
                       │
             ┌─────────┴─────────┐
             │                   │
        Paiement direct      Crédit existant
             │                   │
          Chariow              -1
             │
          Checkout
             │
          Paiement
             │
      Webhook Chariow
             │
      Vérification serveur
             │
       Idempotence
             │
       PostgreSQL
             │
        + crédits
             │
       Journal financier
```

---

# 38. Décision produit finale

Le modèle retenu est :

**GRATUIT**
→ analyse rapide.

**300 FCFA**
→ analyse complète ponctuelle.

**CRÉDITS**
→ 1 crédit = 1 analyse complète.

**PACKS**
→ 5 / 10 / 25 crédits.

**PAS D'EXPIRATION**
→ les crédits restent disponibles.

**UPSELL**
→ proposer un pack après une analyse complète et lorsque le solde est faible.

**ABONNEMENT**
→ pas au lancement ; seulement après observation d'un usage régulier.

---

# 39. Instruction finale à Antigravity

> Implémente ce système comme un système financier interne fiable, et non comme un simple bouton de paiement.
>
> Chariow est le prestataire de checkout et la source externe des événements de vente. PostgreSQL est la source de vérité du portefeuille SûrCheck.
>
> Aucun crédit ne doit être attribué à partir du frontend ou d'une simple redirection de paiement.
>
> Toute attribution doit venir d'une confirmation serveur fiable, être idempotente, être transactionnelle et être enregistrée dans `payment_transactions` et `credit_transactions`.
>
> Avant de finaliser l'intégration, tester explicitement le cas où un même utilisateur tente d'acheter plusieurs fois le même pack Chariow. La documentation Chariow expose actuellement un état `already_purchased`; ne pas supposer que le rachat est autorisé. Si ce comportement bloque notre modèle, demander au support Chariow la méthode officiellement supportée avant de mettre cette partie en production.
>
> Ne jamais exposer les secrets. Ne jamais faire confiance au navigateur pour le prix, le pack, le nombre de crédits ou le statut du paiement.
>
> Construire le système de manière modulaire afin que Chariow puisse être remplacé ou complété par un autre prestataire de paiement sans réécrire le système de crédits.

---

# 40. Sources officielles consultées

- Chariow — Developer Documentation & API : https://help.chariow.com/en/articles/259-developer-documentation-and-api
- Chariow Developers — API Introduction : https://chariow.dev/api-reference/introduction
- Chariow Developers — Authentication : https://chariow.dev/fr/introduction/authentication
- Chariow Developers — Checkout : https://chariow.dev/fr/guides/checkout
- Chariow Developers — Initiate Checkout : https://chariow.dev/api-reference/checkout/init-checkout
- Chariow Developers — Pulses/Webhooks : https://chariow.dev/fr/guides/pulses
- Chariow Developers — Sales : https://chariow.dev/fr/guides/sales
- Chariow Developers — Best Practices : https://chariow.dev/fr/guides/best-practices
- Chariow — Gestion des clés API : https://help.chariow.com/fr/articles/222-gerer-vos-cles-api-sur-chariow
- Chariow — Devises : https://help.chariow.com/fr/articles/69-comment-fonctionnent-les-devises-sur-chariow
- Chariow — Tarification : https://help.chariow.com/fr/articles/64-quelle-est-la-tarification-appliquee-sur-chariow

---

## Note

Ce document complète le cahier des charges SûrCheck AI. Il ne le remplace pas.

Le cahier des charges reste la référence pour le moteur de risque, la sécurité, la confidentialité, la modération, l'architecture générale et les fonctionnalités d'analyse.
