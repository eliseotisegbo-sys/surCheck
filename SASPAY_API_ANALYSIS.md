# ANALYSE COMPLÈTE API SASPAY POUR SURCHECK AI

**Date** : 2026-09-09  
**Source** : Documentation SasPay fournie par le client  
**Objectif** : Migration Chariow → SasPay sans casser l'architecture existante

---

## 📊 VUE D'ENSEMBLE API SASPAY

### Base URL
```
Production: https://api.saspay.me/api/v1
Test: https://api.saspay.me/api/v1 (avec clés sk_test_)
```

### Authentification
```http
Authorization: Bearer sk_test_xxxxxxxxxxxxxxxx
```

**Types de clés :**
- `sk_test_...` : Mode test sans argent réel
- `sk_live_...` : Production avec argent réel

---

## 🔑 ENDPOINTS PRINCIPAUX

### 1. Liste des pays et réseaux supportés
```http
GET https://api.saspay.me/api/v1/countries/
```

**Aucune authentification requise**

Réponse attendue : Liste des réseaux par pays (ex: `mtn_bj` pour MTN Bénin)

---

### 2. Encaisser un paiement (Softpay - Direct Push)

```http
POST https://api.saspay.me/api/v1/payments/softpay/
Authorization: Bearer sk_test_xxxxxxxxxxxxxxxx
Content-Type: application/json
Idempotency-Key: 3fa85f64-5717-4562-b3fc-2c963f66afa6 (optionnel mais recommandé)
```

**Body JSON :**
```json
{
  "amount": "2500.00",
  "currency": "XOF",
  "country": "BJ",
  "network": "mtn_bj",
  "description": "Abonnement mensuel",
  "customer": {
    "email": "client@example.com",
    "first_name": "Awa",
    "last_name": "Sossou",
    "phone": "+22997505050"
  }
}
```

**Réponse succès :**
```json
{
  "message": "Payment pushed successfully",
  "id": "b1f2c3d4-...",
  "status": "PENDING",
  "checkout_url": ""
}
```

**Notes importantes :**
- `checkout_url` vide pour MTN/Moov (push direct USSD)
- `checkout_url` NON vide pour Wave, Orange Money, Djamo, cartes bancaires → redirection obligatoire
- Sans `Idempotency-Key`, un retry réseau crée un 2ème paiement réel

---

### 3. Vérifier le statut d'un paiement

```http
GET https://api.saspay.me/api/v1/payments/{payment_id}/verify/
Authorization: Bearer sk_test_xxxxxxxxxxxxxxxx
```

**Réponse succès :**
```json
{
  "message": "Payment transaction fetched successfully",
  "id": "b1f2c3d4-...",
  "status": "SUCCESS",
  "net_amount": "2500.00",
  "currency": "XOF"
}
```

**Statuts possibles :**
- `PENDING` : En attente de validation client
- `SUCCESS` : Paiement confirmé
- `FAILED` : Échec du paiement
- `CANCELLED` : Annulé par le client

---

### 4. Webhooks (Notifications temps réel)

**Configuration :** À configurer dans le dashboard SasPay

**Format événement (présumé d'après documentation standard) :**
```json
{
  "event": "payment.succeeded",
  "data": {
    "id": "b1f2c3d4-...",
    "amount": "2500.00",
    "currency": "XOF",
    "status": "SUCCESS",
    "customer": {
      "email": "client@example.com",
      "phone": "+22997505050"
    },
    "metadata": {
      "surcheck_user_id": "...",
      "credit_pack": "pack_10"
    }
  }
}
```

**⚠️ Signature webhook :** Documentation incomplète - à vérifier dans dashboard SasPay

---

## 📋 COMPARAISON DÉTAILLÉE CHARIOW vs SASPAY

| Aspect | Chariow | SasPay | Compatibilité |
|--------|---------|--------|---------------|
| **Base URL** | `https://api.chariow.com/v1` | `https://api.saspay.me/api/v1` | ✅ Équivalent |
| **Auth** | `Bearer sk_xxx` | `Bearer sk_test_xxx / sk_live_xxx` | ✅ Identique |
| **Checkout** | `/checkout` (POST) | `/payments/softpay/` (POST) | ⚠️ Différent |
| **Vérification** | `/sales/{id}` (GET) | `/payments/{id}/verify/` (GET) | ⚠️ Différent |
| **Webhook** | Pulses (événements) | Webhooks standard | ✅ Compatible |
| **Signature webhook** | HMAC-SHA256 `x-chariow-signature` | ❓ À documenter | ⚠️ À vérifier |
| **Idempotence** | Implicite | Header `Idempotency-Key` | ✅ Meilleur |
| **Réseaux** | MTN, Moov (BJ) | MTN, Moov, Wave, Orange, Djamo | ✅ Plus large |
| **Pays** | BJ uniquement | Multi-pays (BJ, TG, CI, SN, BF) | ✅ Meilleur |
| **Redirect URL** | `redirect_url` | ❓ À documenter | ⚠️ À vérifier |
| **Métadonnées** | `custom_metadata` (max 10 clés) | Probablement `metadata` | ⚠️ À mapper |

---

## 🔄 MAPPING DES CHAMPS

### Création Checkout

| Chariow | SasPay | Transformation |
|---------|--------|----------------|
| `product_id` | ❌ N/A | Gérer côté serveur via `metadata` |
| `email` | `customer.email` | Déplacer dans objet `customer` |
| `first_name` | `customer.first_name` | Déplacer dans objet `customer` |
| `last_name` | `customer.last_name` | Déplacer dans objet `customer` |
| `phone.number` | `customer.phone` | Format complet `+229...` |
| `phone.country_code` | `country` | Séparé (ex: "BJ") |
| `custom_metadata` | `metadata` (présumé) | Renommer |
| `redirect_url` | ❓ | À documenter |
| ❌ N/A | `amount` | **Nouveau** : montant explicite requis |
| ❌ N/A | `currency` | **Nouveau** : "XOF" |
| ❌ N/A | `network` | **Nouveau** : "mtn_bj", "moov_bj" |
| ❌ N/A | `description` | **Nouveau** : description transaction |

### Réponse Checkout

| Chariow | SasPay | Mapping |
|---------|--------|---------|
| `data.step` | ❌ N/A | Déduire de `checkout_url` (vide = direct, non-vide = redirect) |
| `data.sale_id` | `id` | Direct |
| `data.payment.checkout_url` | `checkout_url` | Direct |
| `message` | `message` | Direct |

### Webhook Event

| Chariow | SasPay (présumé) | Mapping |
|---------|------------------|---------|
| `event` (ex: "successful.sale") | `event` (ex: "payment.succeeded") | Mapper les noms |
| `x-pulse-delivery-id` | Header webhook ID | À documenter |
| `x-chariow-signature` | Header signature | À documenter |
| `data.id` | `data.id` | Direct |
| `data.custom_metadata` | `data.metadata` | Renommer |
| `data.pricing.price.value` | `data.amount` | Simplifier |

---

## ⚠️ POINTS D'ATTENTION CRITIQUES

### 1. **Montant explicite requis**
**Chariow** : Le montant est implicite via `product_id` (défini dans dashboard)  
**SasPay** : Le montant DOIT être envoyé dans chaque requête `softpay`

**Impact** : Modifier la logique pour envoyer `amount` depuis les PACKS côté serveur

---

### 2. **Sélection du réseau Mobile Money**
**Chariow** : Automatique selon le numéro de téléphone  
**SasPay** : DOIT spécifier `network` ("mtn_bj", "moov_bj")

**Impact** : Ajouter logique de détection du réseau depuis le numéro (ex: 97xxx = MTN, 66xxx = Moov)

---

### 3. **checkout_url comportement différent**
**Chariow** : Retourne toujours un URL (même vide)  
**SasPay** :
- Vide (`""`) pour MTN/Moov Bénin → Push USSD direct
- Non vide pour Wave, Orange, Djamo → Redirection OBLIGATOIRE

**Impact** : Le frontend DOIT rediriger si `checkout_url` non vide, sinon paiement échoue

---

### 4. **Idempotence explicite**
**Chariow** : Implicite (déduplication interne)  
**SasPay** : Header `Idempotency-Key` REQUIS pour éviter doublons

**Impact** : Générer UUID unique par tentative et l'envoyer en header

---

### 5. **Webhooks à documenter**
- Format exact de signature (HMAC? JWT?)
- Nom du header de signature
- Événements disponibles (`payment.succeeded`, `payment.failed` ?)
- Structure exacte du payload

**Action** : Tests réels en sandbox pour documenter

---

## 🔧 STRATÉGIE D'IMPLÉMENTATION

### Phase 1 : Provider SasPay (SANS casser Chariow)
```python
# apps/api/src/services/saspay_provider.py
class SasPayPaymentProvider(PaymentProvider):
    async def create_checkout(...):
        # Mapper les champs
        # Ajouter amount, currency, network
        # Envoyer Idempotency-Key
        # POST /payments/softpay/
    
    def verify_webhook_signature(...):
        # À implémenter selon tests réels
    
    def parse_webhook(...):
        # Mapper événements SasPay → format unifié
    
    async def get_sale(...):
        # GET /payments/{id}/verify/
```

### Phase 2 : Configuration
```python
# apps/api/src/config.py
SASPAY_API_KEY: str = os.getenv("SASPAY_API_KEY", "")
SASPAY_BASE_URL: str = os.getenv("SASPAY_BASE_URL", "https://api.saspay.me/api/v1")
SASPAY_WEBHOOK_SECRET: str = os.getenv("SASPAY_WEBHOOK_SECRET", "")
```

### Phase 3 : Switch dans payment.py
```python
# Choisir provider selon variable d'environnement
PAYMENT_PROVIDER = os.getenv("PAYMENT_PROVIDER", "chariow")

if PAYMENT_PROVIDER == "saspay":
    from .services.saspay_provider import saspay_provider as payment_provider
else:
    from .services.chariow_provider import chariow_provider as payment_provider
```

---

## ✅ AVANTAGES SASPAY vs CHARIOW

1. ✅ **Plus de réseaux** : Wave, Orange Money, Djamo en plus de MTN/Moov
2. ✅ **Multi-pays** : Expansion Togo, Côte d'Ivoire, Sénégal, Burkina Faso facilitée
3. ✅ **Idempotence explicite** : Meilleur contrôle des doublons
4. ✅ **Transparence montant** : Montant visible dans chaque requête (audit facilité)

---

## ⚠️ DÉFIS SASPAY vs CHARIOW

1. ⚠️ **Sélection réseau manuelle** : Détection automatique à implémenter
2. ⚠️ **Webhooks non documentés** : Nécessite tests sandbox
3. ⚠️ **Redirect obligatoire** : Frontend doit gérer `checkout_url` non vide
4. ⚠️ **Pas de concept "product"** : Gérer packs côté serveur uniquement

---

## 📝 PROCHAINES ACTIONS

1. ✅ Document d'analyse créé
2. ⏳ Créer mapping détaillé des transformations
3. ⏳ Implémenter `saspay_provider.py`
4. ⏳ Tester en sandbox SasPay
5. ⏳ Documenter webhooks réels
6. ⏳ Créer guide de migration

---

**Status** : Analyse complète - Prêt pour implémentation
