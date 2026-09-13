# VALIDATION SECTION 3 : INTÉGRATION SASPAY

**Date** : 9 septembre 2026  
**Status** : ⚠️ PARTIELLEMENT CONFORME - Améliorations requises

---

## ✅ ÉLÉMENTS CONFORMES

### 3.3 Variables d'environnement
- ✅ `SASPAY_API_KEY` configurée dans `.env` et `config.py`
- ✅ `SASPAY_BASE_URL` configurée (https://api.saspay.me/api/v1)
- ✅ `SASPAY_WEBHOOK_SECRET` configurée
- ✅ Valeurs par défaut vides dans `config.py` (conforme section 1.2)

### 3.4 Fichier saspay_provider.py
- ✅ Classe `SasPayPaymentProvider` créée
- ✅ Hérite de `PaymentProvider` (abstraction respectée)
- ✅ Méthode `create_checkout()` implémentée
- ✅ Méthode `parse_webhook()` implémentée
- ✅ Méthode `get_sale()` implémentée
- ✅ Détection réseau Mobile Money (fonction `detect_mobile_money_network`)
- ✅ Gestion metadata limitée à 10 items avec `list(custom_metadata.items())[:10]` ❌ CORRECTION : Pas de limite [:10] dans le code actuel

### 3.5 Provider unique
- ✅ `payment.py` utilise `saspay_provider` comme provider unique (ligne 35)
- ✅ Plus de switch PAYMENT_PROVIDER (simplifié)
- ✅ Variable `PAYMENT_PROVIDER` supprimée de `.env` (obsolète)

### 3.8 Tests
- ❌ **MANQUANT** : `test_saspay_payment.py` n'existe pas
- Tests requis :
  1. Vérification signature HMAC valide/invalide/expirée
  2. Parsing enveloppe `{event, data}`
  3. Utilisation `net_amount` (pas `amount`)
  4. Tests end-to-end sandbox

---

## ⚠️ NON-CONFORMITÉS CRITIQUES

### 3.6 Vérification webhook signature

#### Problème 1 : Pas de validation timestamp

**Document exige** (Section 3.6) :
```python
def verify_webhook_full(self, raw_body: bytes, signature: str, timestamp: str) -> bool:
    """Vérification complète : âge + signature HMAC."""
    if abs(int(time.time()) - int(timestamp)) > WEBHOOK_TOLERANCE_SECONDS:
        return False
    signed = f"{timestamp}.".encode() + raw_body
    expected = hmac.new(self.webhook_secret.encode(), signed, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)
```

**Réalité code actuel** :
- Méthode `verify_webhook_full()` **N'EXISTE PAS**
- `verify_webhook_signature()` ne vérifie PAS l'âge du webhook
- Pas de protection contre replay attacks

**Impact sécurité** : 🔴 CRITIQUE
- Un attaquant peut rejouer un ancien webhook valide
- Pas de détection de webhooks périmés (>5 min)

#### Problème 2 : Mode permissif en production

**Code actuel** (`saspay_provider.py` lignes 240-279) :
```python
# ⚠️ MODE PERMISSIF: Accepter les webhooks sans signature
logger.warning("Mode permissif activé - Webhook accepté malgré signature invalide")
return True
```

**Comportement** :
- Signature manquante → Accepté ✅
- Signature invalide → Accepté ✅ (après warning)
- Aucune signature vérifiée → Accepté ✅

**Impact sécurité** : 🔴 CRITIQUE
- N'importe qui peut envoyer des webhooks forgés
- Aucune protection contre injection malveillante
- Crédits pourraient être ajoutés sans paiement réel

**Justification code** : "SasPay n'envoie pas encore le header de signature correctement"
- ⚠️ À vérifier avec documentation SasPay officielle
- ⚠️ À tester en environnement sandbox réel

#### Problème 3 : Headers timestamp non extraits

**Routeur `payment.py` ligne 296** :
```python
sig_header = request.headers.get("x-saspay-signature") or ""
if not payment_provider.verify_webhook_signature(raw_body, sig_header):
```

**Manque** :
- Pas d'extraction de `X-Webhook-Timestamp` (requis section 3.6)
- `verify_webhook_full()` jamais appelée
- Validation signature basique uniquement

---

## 📋 ACTIONS REQUISES

### Priorité 1 : Sécurité webhook (URGENT)

1. **Ajouter `verify_webhook_full()` dans `saspay_provider.py`** :
   ```python
   import time
   
   WEBHOOK_TOLERANCE_SECONDS = 300  # 5 minutes
   
   def verify_webhook_full(self, raw_body: bytes, signature: str, timestamp: str) -> bool:
       """Vérification complète recommandée par SasPay : âge + signature HMAC."""
       if not self.webhook_secret:
           return True  # Dev mode
       
       try:
           if abs(int(time.time()) - int(timestamp)) > WEBHOOK_TOLERANCE_SECONDS:
               logger.warning("Webhook SasPay rejeté : horodatage hors tolérance (5 min)")
               return False
       except (ValueError, TypeError):
           return False
       
       signed = f"{timestamp}.".encode() + raw_body
       expected = hmac.new(self.webhook_secret.encode(), signed, hashlib.sha256).hexdigest()
       return hmac.compare_digest(expected, signature)
   ```

2. **Modifier `handle_payment_webhook()` dans `payment.py`** :
   ```python
   sig_header = request.headers.get("x-webhook-signature", "")
   timestamp = request.headers.get("x-webhook-timestamp", "")
   
   if not payment_provider.verify_webhook_full(raw_body, sig_header, timestamp):
       logger.warning("Webhook SasPay rejeté : signature ou horodatage invalide")
       raise HTTPException(status_code=401, detail="Signature de webhook invalide.")
   ```

3. **Désactiver mode permissif** une fois format SasPay confirmé

### Priorité 2 : Tests (REQUIS section 3.8)

Créer `apps/api/tests/test_saspay_payment.py` :
- Test signature HMAC valide/invalide
- Test webhook expiré (timestamp >5 min)
- Test parsing événements `transaction.success`, `transaction.failed`, `transaction.cancelled`
- Test utilisation `net_amount` vs `amount`
- Test end-to-end sandbox réel

### Priorité 3 : Documentation

1. **Vérifier documentation SasPay** :
   - Format exact header signature : `X-Webhook-Signature` ou `X-SasPay-Signature` ?
   - Format timestamp : `X-Webhook-Timestamp` ?
   - Algorithme signature : `timestamp.` + `raw_body` → HMAC-SHA256 ?

2. **Créer SASPAY_WEBHOOK_INTEGRATION.md** :
   - Procédure création webhook sur `app.saspay.me`
   - URL webhook : `https://<railway-url>/api/v1/payment/webhook`
   - Événements à activer
   - Récupération `signing_secret`

---

## 📊 SCORE CONFORMITÉ SECTION 3

| Critère | Status | Poids |
|---------|--------|-------|
| Variables .env | ✅ | 10% |
| Fichier saspay_provider.py | ✅ | 20% |
| Provider unique | ✅ | 10% |
| Signature webhook sécurisée | ❌ | **40%** |
| Tests unitaires | ❌ | 20% |

**Total** : 40/100 ⚠️

---

## 🎯 DÉCISION

**La section 3 est PARTIELLEMENT conforme** :
- ✅ Architecture correcte (provider abstrait, SasPay unique)
- ✅ Configuration secrets sécurisée
- ❌ Sécurité webhooks CRITIQUE manquante
- ❌ Tests manquants

**Recommandation** : 
1. Implémenter `verify_webhook_full()` AVANT mise en production
2. Tester format webhooks SasPay en sandbox
3. Désactiver mode permissif
4. Créer tests automatisés

---

**Document généré le 9 septembre 2026**  
**Prochaine validation après implémentation corrections**
