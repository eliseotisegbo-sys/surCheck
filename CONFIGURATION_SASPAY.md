# 🚀 CONFIGURATION SASPAY — SÛRCHECK AI

**Date :** 2026-09-09  
**Provider unique :** SasPay (Softpay Mobile Money)  
**Migration :** Chariow → SasPay TERMINÉE

---

## ✅ MIGRATION COMPLÈTE EFFECTUÉE

SûrCheck utilise maintenant **SasPay comme provider unique** de paiement Mobile Money.

**Changements effectués :**
- ✅ Supprimé tout le code Chariow (provider, tests, config)
- ✅ SasPay est le provider par défaut (plus de switch)
- ✅ Frontend mis à jour (textes UI)
- ✅ Documentation nettoyée (6 fichiers supprimés)
- ✅ Schema DB simplifié (product_id optionnel)

---

## 📋 PRÉREQUIS

### 1. Compte SasPay

**Créer un compte :** https://application.saspay.me

**Modes disponibles :**
- **Sandbox (sk_test_*)** : Tests sans argent réel
- **Production (sk_live_*)** : Paiements réels

### 2. Clés API requises

| Variable | Description | Où trouver |
|----------|-------------|------------|
| `SASPAY_API_KEY` | Clé API (sandbox/prod) | Dashboard → Développeur → API Keys |
| `SASPAY_WEBHOOK_SECRET` | Secret webhook | Dashboard → Webhooks → Secret |

---

## 🔧 CONFIGURATION RAILWAY (Backend)

### Étape 1 : Accéder aux variables

1. https://railway.app → Votre projet SûrCheck
2. Service **API** → Onglet **Variables**
3. Cliquez sur **"RAW Editor"**

### Étape 2 : Configurer les clés SasPay

Ajoutez ces 3 variables :

```env
# ── SasPay API Configuration ──────────────────────────────────────

# Clé API SasPay (remplacer par votre clé)
SASPAY_API_KEY=sk_test_VOTRE_CLE_SANDBOX_OU_sk_live_VOTRE_CLE_PROD

# URL de base API (même URL pour sandbox et production)
SASPAY_BASE_URL=https://api.saspay.me/api/v1

# Secret webhook (récupérer après création webhook)
SASPAY_WEBHOOK_SECRET=VOTRE_SECRET_WEBHOOK
```

### Étape 3 : Sauvegarder

1. Cliquez sur **"Save"**
2. Railway redéploie automatiquement (30-60 secondes)

---

## 🔗 CONFIGURATION WEBHOOK SASPAY

### URL du webhook

```
https://VOTRE_SERVICE.up.railway.app/api/v1/payment/webhook
```

**Remplacer `VOTRE_SERVICE`** par votre URL Railway réelle.

### Étapes de configuration

1. **Dashboard SasPay** → **Webhooks** → **Nouveau webhook**

2. **URL** : Copier l'URL ci-dessus

3. **Événements à surveiller :**
   - ✅ `payment.succeeded` (ou `payment.success`, `payment.completed`)
   - ✅ `payment.failed`
   - ✅ `payment.cancelled`

4. **Secret** : Généré automatiquement → **Copier**

5. **Sauvegarder le webhook**

6. **Copier le secret** dans Railway :
   ```
   SASPAY_WEBHOOK_SECRET=le_secret_copié
   ```

---

## 🧪 TESTS DE VALIDATION

### Test 1 : Vérifier backend démarre

```bash
# Vérifier logs Railway
# Chercher : "Provider de paiement unique : SasPay"
# PAS de mention "Chariow"
```

**✅ Succès :** Logs montrent SasPay actif

### Test 2 : API Packs disponibles

```bash
curl https://VOTRE_SERVICE.up.railway.app/api/v1/payment/packs
```

**Réponse attendue :**
```json
{
  "packs": [
    {"id": "pack_1", "credits": 1, "amount_fcfa": 600, ...},
    {"id": "pack_5", "credits": 5, "amount_fcfa": 1500, ...},
    {"id": "pack_10", "credits": 10, "amount_fcfa": 2500, ...},
    {"id": "pack_25", "credits": 25, "amount_fcfa": 5000, ...}
  ],
  "currency": "XOF",
  "note": "Tarifs TTC en FCFA. Paiement sécurisé via Mobile Money ... opéré par SasPay."
}
```

**✅ Succès :** Note mentionne SasPay (pas Chariow)

### Test 3 : Création checkout (Sandbox)

**Pré-requis :**
- Compte créé sur frontend
- Token JWT valide

```bash
curl -X POST https://VOTRE_SERVICE.up.railway.app/api/v1/payment/checkout \
  -H "Authorization: Bearer VOTRE_TOKEN_JWT" \
  -H "Content-Type: application/json" \
  -d '{
    "pack_id": "pack_1",
    "phone_number": "61234567",
    "country_code": "BJ"
  }'
```

**Réponse attendue (MTN/Moov Bénin) :**
```json
{
  "step": "payment",
  "checkout_url": null,
  "transaction_id": "uuid-...",
  "sale_id": "saspay_sale_id",
  "amount_fcfa": 600,
  "credits": 1,
  "label": "Analyse unique",
  "message": "Payment initiated"
}
```

**Note :** `checkout_url` = `null` pour MTN/Moov (push USSD direct)

**✅ Succès :** Transaction créée, `step` = `"payment"`

### Test 4 : Webhook reçu

**Simuler webhook sandbox :**

```bash
curl -X POST https://VOTRE_SERVICE.up.railway.app/api/v1/payment/webhook \
  -H "Content-Type: application/json" \
  -H "X-SasPay-Signature: test_signature" \
  -d '{
    "event": "payment.succeeded",
    "data": {
      "id": "test_sale_123",
      "status": "SUCCESS",
      "amount": "600.00",
      "metadata": {
        "surcheck_user_id": "user_uuid",
        "credit_pack": "pack_1",
        "credits": "1",
        "internal_order_ref": "transaction_uuid"
      },
      "customer": {
        "email": "test@example.com"
      }
    }
  }'
```

**Vérifier logs Railway :**
```
Webhook SasPay reçu : event=successful.sale | sale=test_sale_123
```

**✅ Succès :** Webhook parsé correctement

---

## 🌍 RÉSEAUX MOBILE MONEY SUPPORTÉS

### Détection automatique par préfixe

| Opérateur | Pays | Préfixes | Code réseau |
|-----------|------|----------|-------------|
| **MTN** | Bénin | 40-49, 50-59, 60-69, 90-99 | `mtn_bj` |
| **Moov** | Bénin | 01-03, 80-89 | `moov_bj` |
| **Wave** | Bénin | - | `wave_bj` |
| **Orange Money** | Autres pays | - | `orange_*` |

**Exemple :**
- Numéro `61234567` → Détecté comme **MTN Bénin**
- Numéro `97123456` → Détecté comme **MTN Bénin**
- Numéro `01234567` → Détecté comme **Moov Bénin**

---

## 🔄 COMPORTEMENT CHECKOUT_URL

### Push USSD direct (MTN/Moov)

**Caractéristiques :**
- `checkout_url` = `null` ou vide
- Push USSD envoyé directement au téléphone
- Utilisateur tape son code secret sur son téléphone
- Pas de redirection navigateur

**Workflow :**
```
1. Frontend appelle /checkout
2. Backend retourne step="payment", checkout_url=null
3. Frontend affiche : "Un code USSD a été envoyé à votre téléphone"
4. Utilisateur valide sur son téléphone
5. Webhook reçu → Crédits ajoutés
```

### Redirection obligatoire (Wave/Orange)

**Caractéristiques :**
- `checkout_url` = URL valide (ex: `https://pay.saspay.me/...`)
- Redirection vers page paiement externe
- Utilisateur entre infos sur page SasPay
- Retour automatique après paiement

**Workflow :**
```
1. Frontend appelle /checkout
2. Backend retourne step="redirect", checkout_url="https://..."
3. Frontend redirige : window.location.href = checkout_url
4. Utilisateur paie sur page SasPay
5. Redirection retour automatique
6. Webhook reçu → Crédits ajoutés
```

---

## 📊 STRUCTURE PACKS

| Pack | Crédits | Prix FCFA | Prix/analyse | Popularité |
|------|---------|-----------|--------------|------------|
| pack_1 | 1 | 600 | 600 F | Standard |
| pack_5 | 5 | 1500 | 300 F | - |
| pack_10 | 10 | 2500 | 250 F | ⭐ Recommandé |
| pack_25 | 25 | 5000 | 200 F | Meilleur rapport |

**Différence vs Chariow :**
- ❌ Pas de `product_id` SasPay
- ✅ Montant explicite envoyé à chaque appel
- ✅ Montants définis dans `config.py` (CREDIT_PACK_*_FCFA)

---

## 🔐 SÉCURITÉ WEBHOOKS

### Mode actuel : Permissif

**Raison :** Format signature SasPay non documenté

**Comportement :**
```python
# saspay_provider.py ligne 260
if not signature_header:
    logger.warning("Mode permissif activé")
    return True  # Accepte sans signature
```

### ⚠️ À sécuriser en production

**Après validation format signature réel :**

1. Documenter format signature SasPay (HMAC-SHA256 ?)
2. Activer vérification stricte :
   ```python
   if not signature_header:
       return False  # Rejeter si pas de signature
   ```
3. Tester avec webhook sandbox réel

---

## 🆘 TROUBLESHOOTING

### Erreur : "SASPAY_API_KEY manquant"

**Cause :** Variable Railway non configurée

**Solution :**
1. Railway → Variables → Vérifier `SASPAY_API_KEY` présent
2. Format : `sk_test_xxx` ou `sk_live_xxx`
3. Redéployer si modifié

### Erreur : "network invalid"

**Cause :** Préfixe téléphone non reconnu

**Solution :**
1. Vérifier préfixe dans `saspay_provider.py` lignes 30-90
2. Ajouter nouveau préfixe si opérateur non supporté
3. Exemple pour Togo : Documenter préfixes MTN/Moov Togo

### Webhook non reçu

**Causes possibles :**
1. URL webhook incorrecte dans dashboard SasPay
2. Événements non cochés (`payment.succeeded`)
3. Secret webhook incorrect dans Railway

**Vérification :**
```bash
# Logs Railway : Chercher "Webhook SasPay reçu"
# Si absent : Problème configuration SasPay
```

### Crédits non ajoutés après paiement

**Vérifier logs Railway :**
```
Webhook SasPay reçu : event=successful.sale | sale=xxx | user=xxx
```

**Si présent mais crédits pas ajoutés :**
- Vérifier `user_id` dans metadata
- Vérifier table `payment_transactions` (statut)
- Vérifier table `user_credits` (solde)

---

## 📚 DOCUMENTATION SASPAY OFFICIELLE

**Site officiel :** https://saspay.me (domaine à vendre - chercher docs alternatives)

**Dashboard :** https://application.saspay.me

**API Base URL :** https://api.saspay.me/api/v1

**Documentation technique :**
- `MIGRATION_SASPAY.md` : Guide migration détaillé (conservé)
- `apps/api/src/services/saspay_provider.py` : Implémentation complète avec commentaires

---

## ✅ CHECKLIST DE VALIDATION

### Configuration

- [ ] ✅ `SASPAY_API_KEY` configuré dans Railway
- [ ] ✅ `SASPAY_BASE_URL` = `https://api.saspay.me/api/v1`
- [ ] ✅ Webhook créé sur dashboard SasPay
- [ ] ✅ `SASPAY_WEBHOOK_SECRET` configuré dans Railway

### Tests

- [ ] ✅ Backend démarre sans erreur
- [ ] ✅ `/api/v1/payment/packs` mentionne SasPay
- [ ] ✅ Création checkout fonctionne (sandbox)
- [ ] ✅ Webhook test parsé correctement
- [ ] ✅ Détection réseau MTN/Moov fonctionne

### Production

- [ ] ⏸️ Passer de `sk_test_*` à `sk_live_*`
- [ ] ⏸️ Tester paiement réel 600 FCFA
- [ ] ⏸️ Vérifier crédits ajoutés après webhook
- [ ] ⏸️ Monitorer logs 24h

---

## 🎯 AVANTAGES SASPAY vs CHARIOW

| Critère | SasPay | Chariow |
|---------|--------|---------|
| **Réseaux supportés** | MTN, Moov, Wave, Orange, Djamo | MTN, Moov |
| **Frais transaction** | À documenter | 565 FCFA minimum |
| **Push USSD direct** | ✅ Oui (MTN/Moov) | ❌ Redirection toujours |
| **Product ID** | ❌ Non (montant explicite) | ✅ Oui |
| **Idempotence** | ✅ Header automatique | ⚠️ À gérer manuellement |
| **Documentation** | ⚠️ Limitée | ✅ Complète |

---

## 📞 SUPPORT

**Questions techniques :**
- Consulter `MIGRATION_SASPAY.md` (guide complet 600+ lignes)
- Consulter `saspay_provider.py` (commentaires détaillés)

**Dashboard SasPay :**
- Support intégré (si disponible)
- Email support (à documenter)

**Logs Railway :**
- Toutes actions tracées avec préfixe `surcheck.payment`
- Chercher : `"SasPay"`, `"webhook"`, `"checkout"`

---

**Dernière mise à jour :** 2026-09-09  
**Migration Chariow → SasPay :** ✅ TERMINÉE  
**Provider actif :** SasPay (unique)
