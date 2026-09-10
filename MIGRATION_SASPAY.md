                                      # 🔄 GUIDE DE MIGRATION CHARIOW → SASPAY

**Date** : 2026-09-09  
**Version** : 1.0.0  
**Objectif** : Migration complète et sécurisée du système de paiement SûrCheck AI

---

## 📋 TABLE DES MATIÈRES

1. [Vue d'ensemble](#vue-densemble)
2. [Prérequis](#prérequis)
3. [Phase 1 : Configuration Sandbox](#phase-1--configuration-sandbox)
4. [Phase 2 : Tests & Validation](#phase-2--tests--validation)
5. [Phase 3 : Déploiement Production](#phase-3--déploiement-production)
6. [Phase 4 : Monitoring](#phase-4--monitoring)
7. [Rollback d'urgence](#rollback-durgence)
8. [FAQ & Troubleshooting](#faq--troubleshooting)

---

## 🎯 VUE D'ENSEMBLE

### Pourquoi migrer ?

- **Compatibilité étendue** : Support natif MTN, Moov, Wave, Orange Money, Djamo
- **Modernité API** : Architecture REST moderne vs interface Chariow vieillissante
- **Coûts optimisés** : Frais de transaction potentiellement réduits
- **Indépendance** : Diversification des providers de paiement (résilience)

### Architecture de migration

```
┌─────────────────────────────────────────────────┐
│          Interface PaymentProvider              │
│         (Contrat commun inchangé)               │
└────────────┬────────────────────┬────────────────┘
             │                    │
    ┌────────▼────────┐  ┌────────▼────────┐
    │ ChariowProvider │  │ SasPayProvider  │
    │   (Actuel)      │  │   (Nouveau)     │
    └─────────────────┘  └─────────────────┘
             │                    │
             └──────────┬─────────┘
                        │
                ┌───────▼────────┐
                │  payment.py    │
                │ (Inchangé ✓)   │
                └────────────────┘
```

**✅ Garanties** :
- Aucun changement dans `payment.py` (logique métier)
- Aucun changement dans `credit_service.py`
- Aucun changement dans la base de données
- Aucun changement dans le frontend
- **Switch instantané** via variable d'environnement `PAYMENT_PROVIDER`

---

## 🔧 PRÉREQUIS

### 1. Compte SasPay Sandbox

1. Créer un compte sur [application.saspay.me](https://application.saspay.me)
2. Compléter le profil (entreprise : SûrCheck AI, pays : Bénin)
3. Accéder à **Dashboard → Développeur → API Keys**
4. Copier la clé **Sandbox** : `sk_test_xxxxxxxxxxxxx`

### 2. Configuration Webhook SasPay

1. Dans le dashboard SasPay : **Webhooks → Nouveau webhook**
2. URL webhook : `https://[VOTRE_URL_RAILWAY].up.railway.app/api/v1/payment/webhook`
3. Événements à écouter :
   - ✅ `payment.succeeded`
   - ✅ `payment.failed`
   - ✅ `payment.cancelled`
   - ✅ `payment.refunded`
4. Copier le **Secret du webhook** fourni par SasPay

### 3. Vérification Code

Confirmer que tous les fichiers sont présents :

```bash
# Backend
apps/api/src/services/saspay_provider.py       # ✓ Provider SasPay
apps/api/src/services/chariow_provider.py      # ✓ Provider Chariow (conservé)
apps/api/src/services/payment_provider.py      # ✓ Interface abstraite
apps/api/src/routers/payment.py                # ✓ Router modifié
apps/api/src/config.py                         # ✓ Config étendue

# Documentation
SASPAY_API_ANALYSIS.md                         # ✓ Analyse API
CHARIOW_TO_SASPAY_MAPPING.md                   # ✓ Mapping détaillé
MIGRATION_SASPAY.md                            # ✓ Ce guide

# Configuration
.env.example                                   # ✓ Template complet
```

---

## 🧪 PHASE 1 : CONFIGURATION SANDBOX

### Étape 1.1 : Variables d'environnement Sandbox

Ajouter dans Railway → **Variables → RAW Editor** :

```env
# Activer SasPay en mode sandbox
PAYMENT_PROVIDER=saspay

# Clés SasPay Sandbox (sk_test_* = pas d'argent réel)
SASPAY_API_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxx
SASPAY_BASE_URL=https://api.saspay.me/api/v1
SASPAY_WEBHOOK_SECRET=<<SECRET_RECU_LORS_CREATION_WEBHOOK>>

# ⚠️ Garder Chariow configuré pour rollback instantané
CHARIOW_API_KEY=sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7
CHARIOW_BASE_URL=https://api.chariow.com/v1
CHARIOW_WEBHOOK_SECRET=whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz
```

### Étape 1.2 : Redéployer l'API

```bash
# Railway redéploie automatiquement après modification des variables
# Ou forcer un redéploiement :
git commit --allow-empty -m "chore: Activation SasPay Sandbox"
git push origin main
```

### Étape 1.3 : Vérifier le provider actif

```bash
# Tester l'endpoint health
curl https://[VOTRE_URL_RAILWAY].up.railway.app/health

# Vérifier les logs Railway
# Devrait afficher : "Provider de paiement actif : SasPay (Softpay Mobile Money)"
```

---

## ✅ PHASE 2 : TESTS & VALIDATION

### Test 1 : Création checkout MTN Bénin

**Objectif** : Vérifier la détection réseau et le push USSD direct

```bash
curl -X POST https://[VOTRE_URL_RAILWAY].up.railway.app/api/v1/payment/checkout \
  -H "Authorization: Bearer [VOTRE_TOKEN_JWT]" \
  -H "Content-Type: application/json" \
  -d '{
    "pack_id": "pack_1",
    "phone_number": "97505050",
    "country_code": "BJ"
  }'
```

**Résultat attendu** :

```json
{
  "step": "payment",
  "checkout_url": null,
  "transaction_id": "uuid-xxxxx",
  "sale_id": "saspay-payment-id",
  "amount_fcfa": 600,
  "credits": 1,
  "label": "Analyse unique",
  "message": "Payment pushed successfully"
}
```

**✅ Validation** :
- `checkout_url` doit être `null` (MTN = push USSD direct)
- `step` = `"payment"` (pas de redirection)
- Vérifier dans logs Railway : `network: mtn_bj` détecté automatiquement

### Test 2 : Réception webhook payment.succeeded

**Déclencheur** : Compléter un paiement test dans le dashboard SasPay Sandbox

**Vérification** :

1. Logs Railway doivent afficher :
   ```
   Webhook saspay reçu : event=successful.sale | sale=xxx | user=xxx
   ```

2. Vérifier dans Supabase → `user_credits` :
   - Solde utilisateur incrémenté de `+1` crédit
   - Nouveau record dans `payment_transactions` avec `provider=saspay`, `status=successful`

3. Vérifier dans Supabase → `credit_transactions` :
   - Transaction type `purchase` enregistrée
   - `sale_id` correspond au paiement SasPay

**✅ Validation** :
- Crédit ajouté ✓
- Transaction enregistrée ✓
- Déduplication fonctionne (renvoyer le même webhook → aucun doublon)

### Test 3 : Signature webhook invalide

**Objectif** : Vérifier la sécurité du webhook

```bash
curl -X POST https://[VOTRE_URL_RAILWAY].up.railway.app/api/v1/payment/webhook \
  -H "Content-Type: application/json" \
  -H "x-saspay-signature: signature_invalide_bidon" \
  -d '{"event": "payment.succeeded", "data": {"id": "fake"}}'
```

**Résultat attendu** :

```json
{
  "detail": "Signature de webhook invalide."
}
```

HTTP Status : `401 Unauthorized`

**✅ Validation** : Webhooks non signés sont rejetés ✓

### Test 4 : Pack 10 crédits (Moov Bénin)

```bash
curl -X POST https://[VOTRE_URL_RAILWAY].up.railway.app/api/v1/payment/checkout \
  -H "Authorization: Bearer [VOTRE_TOKEN_JWT]" \
  -H "Content-Type: application/json" \
  -d '{
    "pack_id": "pack_10",
    "phone_number": "66123456",
    "country_code": "BJ"
  }'
```

**✅ Validation** :
- Réseau détecté : `moov_bj` (préfixe 66)
- Montant correct : `2500 FCFA`
- Crédits : `10`

### Test 5 : Rollback instantané vers Chariow

```bash
# Dans Railway → Variables
PAYMENT_PROVIDER=chariow

# Redéployer (automatique)
# Tester un checkout
curl -X POST [...]/payment/checkout [...]
```

**✅ Validation** :
- Logs : `"Provider de paiement actif : Chariow"`
- Checkout fonctionne avec l'ancienne API Chariow
- **Aucune modification code nécessaire** ✓

---

## 🚀 PHASE 3 : DÉPLOIEMENT PRODUCTION

### ⚠️ CHECKLIST PRÉ-PRODUCTION

- [ ] **Sandbox validé** : Tous les tests Phase 2 passent
- [ ] **Webhook signature** : Mécanisme vérifié et documenté
- [ ] **Détection réseau** : Préfixes MTN/Moov testés et validés
- [ ] **Compte SasPay Production** : KYC complété et approuvé
- [ ] **Clé API Live** : `sk_live_xxxxx` générée
- [ ] **Webhook Production** : URL configurée avec secret live
- [ ] **Backup Chariow** : Configuration conservée pour rollback
- [ ] **Monitoring** : Logs Railway + alertes configurées
- [ ] **Documentation utilisateurs** : Communication prévue si changements visibles

### Étape 3.1 : Obtenir clés Production SasPay

1. Compléter le **KYC** (Know Your Customer) dans le dashboard SasPay
   - Documents entreprise requis
   - Validation peut prendre 2-5 jours ouvrés
2. Une fois approuvé, générer la clé **Live** : `sk_live_xxxxxxxxxxxxx`
3. Créer un webhook de production avec URL Railway

### Étape 3.2 : Mise à jour variables Production

```env
# ⚠️ ATTENTION : Clés LIVE = Argent RÉEL

PAYMENT_PROVIDER=saspay

# Clés SasPay Production
SASPAY_API_KEY=sk_live_xxxxxxxxxxxxxxxxxxxxx
SASPAY_BASE_URL=https://api.saspay.me/api/v1
SASPAY_WEBHOOK_SECRET=<<SECRET_WEBHOOK_PRODUCTION>>

# Backup Chariow (GARDER pour rollback)
CHARIOW_API_KEY=sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7
CHARIOW_BASE_URL=https://api.chariow.com/v1
CHARIOW_WEBHOOK_SECRET=whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz
```

### Étape 3.3 : Déploiement progressif (recommandé)

**Option A : Switch complet immédiat**
- Changer `PAYMENT_PROVIDER=saspay`
- Redéployer
- Tous les nouveaux paiements utilisent SasPay

**Option B : Migration progressive** (plus sûr)
1. **Jour 1-3** : SasPay actif, surveillance intensive
2. **Jour 4-7** : Analyse des métriques (taux succès, latence, erreurs)
3. **Jour 8+** : Stabilisation, désactivation Chariow si tout OK

### Étape 3.4 : Communication utilisateurs

**Si changements visibles** (ex: nouveaux réseaux supportés) :

```
📢 Amélioration du système de paiement SûrCheck AI

Nous avons élargi nos options de paiement Mobile Money :
✅ MTN Bénin
✅ Moov Bénin
✅ Wave (nouveau)
✅ Orange Money (nouveau)
✅ Djamo (nouveau)

Vos crédits et historique restent inchangés.
```

---

## 📊 PHASE 4 : MONITORING

### Métriques clés à surveiller

#### 1. Taux de succès paiements

```sql
-- Comparer Chariow vs SasPay (7 derniers jours)
SELECT 
  provider,
  COUNT(*) as total_transactions,
  SUM(CASE WHEN status = 'successful' THEN 1 ELSE 0 END) as successful,
  ROUND(100.0 * SUM(CASE WHEN status = 'successful' THEN 1 ELSE 0 END) / COUNT(*), 2) as success_rate
FROM payment_transactions
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY provider;
```

**Target** : `success_rate >= 85%` (mobile money standard)

#### 2. Latence moyenne checkout

```sql
-- Temps moyen entre création et paiement
SELECT 
  provider,
  AVG(EXTRACT(EPOCH FROM (processed_at - created_at))) as avg_seconds
FROM payment_transactions
WHERE status = 'successful'
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY provider;
```

**Target** : `avg_seconds <= 180` (3 minutes max pour paiement mobile)

#### 3. Erreurs webhooks

```bash
# Railway Logs → Filtrer par "Webhook saspay rejeté"
# Alerte si > 5 rejets/heure = problème signature
```

#### 4. Détection réseau

```sql
-- Vérifier distribution réseaux détectés
SELECT 
  metadata->>'network' as network,
  COUNT(*) as count
FROM payment_transactions
WHERE provider = 'saspay'
  AND created_at >= NOW() - INTERVAL '7 days'
GROUP BY network
ORDER BY count DESC;
```

**Validation** : MTN/Moov doivent représenter ~80-90% des transactions au Bénin

### Alertes recommandées

1. **Taux succès < 80%** → Vérifier API SasPay status
2. **Webhook rejets > 10/jour** → Vérifier secret webhook
3. **Erreur "SASPAY_API_KEY manquant"** → Configuration Railway corrompue
4. **Latence > 5min** → Problème réseau SasPay ou opérateur

---

## 🚨 ROLLBACK D'URGENCE

### Scénarios nécessitant un rollback

- Taux de succès SasPay < 60% pendant > 2h
- API SasPay indisponible (status 5xx répétés)
- Problème de détection réseau (mauvais réseaux détectés)
- Bug critique découvert en production

### Procédure de rollback (< 2 minutes)

#### Étape 1 : Switch immédiat vers Chariow

```bash
# Railway → Variables → RAW Editor
PAYMENT_PROVIDER=chariow
```

Railway redéploie automatiquement (30-60 secondes).

#### Étape 2 : Vérification

```bash
# Tester checkout
curl https://[URL_RAILWAY]/api/v1/payment/checkout \
  -H "Authorization: Bearer [TOKEN]" \
  -d '{"pack_id": "pack_1", "phone_number": "97505050", "country_code": "BJ"}'

# Vérifier logs
# Doit afficher : "Provider de paiement actif : Chariow"
```

#### Étape 3 : Communication

Si rollback en heures ouvrées, informer utilisateurs :

```
⚠️ Maintenance technique en cours

Nous effectuons une maintenance sur notre système de paiement.
Le service reste disponible via MTN et Moov Bénin.
Retour à la normale sous 24h.
```

#### Étape 4 : Post-mortem

1. Identifier la cause racine dans les logs Railway
2. Corriger le code si nécessaire
3. Retester en sandbox avant nouvelle migration
4. Documenter l'incident

---

## ❓ FAQ & TROUBLESHOOTING

### Q1 : Puis-je utiliser les deux providers en parallèle ?

**Non**. Le système utilise un seul provider actif à la fois défini par `PAYMENT_PROVIDER`.

**Workaround** : Déployer deux instances Railway séparées (staging SasPay + prod Chariow).

### Q2 : Les anciens paiements Chariow restent-ils accessibles ?

**Oui**. Toutes les transactions sont stockées en base avec le champ `provider`.
L'historique reste intact et consultable.

### Q3 : Comment tester sans dépenser d'argent ?

Utiliser les clés **Sandbox** SasPay : `sk_test_xxxxx`.
Les paiements sandbox n'utilisent pas d'argent réel.

### Q4 : Erreur "network invalid" avec SasPay

**Cause** : Préfixe téléphone non reconnu.

**Solution** :
1. Vérifier le numéro dans les logs : `detect_mobile_money_network()`
2. Ajouter le préfixe manquant dans `saspay_provider.py` :

```python
# Exemple : Ajouter préfixe 70 pour MTN
mtn_prefixes = {
    "40", "41", ..., "70",  # Ajouter ici
}
```

### Q5 : Webhook signature toujours invalide

**Diagnostic** :

```bash
# Vérifier le secret configuré
echo $SASPAY_WEBHOOK_SECRET

# Tester manuellement la signature
python3 << EOF
import hmac, hashlib
secret = "votre_secret"
body = b'{"event":"payment.succeeded"}'
sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
print(f"Signature attendue: {sig}")
EOF
```

**Solutions** :
1. Copier-coller le secret **exact** depuis dashboard SasPay (pas d'espaces)
2. Vérifier format du header : `x-saspay-signature` (minuscules)
3. Si format différent, documenter et adapter dans `saspay_provider.py`

### Q6 : checkout_url non vide pour MTN/Moov

**Cause** : SasPay peut renvoyer une URL même pour push direct (comportement API).

**Impact** : Aucun. Le frontend doit gérer les deux cas :
- `checkout_url` vide → Afficher "En attente de validation sur votre téléphone"
- `checkout_url` non vide → Rediriger l'utilisateur

**Code frontend** (déjà implémenté) :

```typescript
if (response.checkout_url) {
  window.location.href = response.checkout_url;
} else {
  setStep('pending'); // Attente push USSD
}
```

### Q7 : Montants décimaux SasPay vs entiers Chariow

**Gestion automatique** :

- SasPay API attend : `"2500.00"` (string décimal)
- Chariow API attend : `2500` (int)
- Notre code convertit automatiquement dans chaque provider

**Validation** :

```python
# saspay_provider.py ligne ~140
amount = float(amount_str)  # "2500" → 2500.0
payload["amount"] = f"{amount:.2f}"  # 2500.0 → "2500.00"
```

### Q8 : Que deviennent les product_id Chariow ?

**SasPay n'utilise pas de product_id**.

Le montant et la description sont envoyés directement :
- `amount` : Extrait de `custom_metadata["amount_fcfa"]`
- `description` : Généré depuis `pack["label"]`

Les `product_id` Chariow restent dans la config pour le rollback.

---

## 📚 RESSOURCES COMPLÉMENTAIRES

### Documentation projet

- **SASPAY_API_ANALYSIS.md** : Comparaison détaillée APIs
- **CHARIOW_TO_SASPAY_MAPPING.md** : Mapping technique complet
- **DEPLOYMENT.md** : Architecture globale SûrCheck AI
- **.env.example** : Template configuration complète

### Documentation externe

- **SasPay Docs** : [docs.saspay.me](https://docs.saspay.me)
- **Dashboard SasPay** : [application.saspay.me](https://application.saspay.me)
- **Support SasPay** : support@saspay.me
- **Railway Docs** : [docs.railway.app](https://docs.railway.app)

### Support technique SûrCheck AI

En cas de problème bloquant :

1. **Rollback immédiat** vers Chariow (procédure ci-dessus)
2. Consulter logs Railway détaillés
3. Vérifier status API : [status.saspay.me](https://status.saspay.me) (si disponible)
4. Contacter équipe DevOps avec :
   - Timestamp incident
   - Logs Railway concernés
   - Transaction IDs affectés

---

## ✅ CHECKLIST FINALE MIGRATION

### Avant migration

- [ ] Compte SasPay créé et KYC validé
- [ ] Clés sandbox testées et validées
- [ ] Tous les tests Phase 2 réussis
- [ ] Webhook production configuré
- [ ] Variables Railway préparées (sans appliquer)
- [ ] Équipe DevOps prévenue
- [ ] Fenêtre de maintenance définie (si nécessaire)

### Pendant migration

- [ ] Variables Railway mises à jour (`PAYMENT_PROVIDER=saspay`)
- [ ] Redéploiement surveillé (logs en temps réel)
- [ ] Premier checkout test production réussi
- [ ] Webhook production reçu et traité
- [ ] Crédit ajouté correctement en base

### Après migration (J+1 à J+7)

- [ ] Taux de succès ≥ 85%
- [ ] Aucune erreur webhook répétée
- [ ] Latence acceptable (< 3min moyenne)
- [ ] Détection réseau correcte (logs vérifiés)
- [ ] Aucun doublon crédit détecté
- [ ] Monitoring actif et alertes configurées
- [ ] Documentation mise à jour si changements
- [ ] Équipe commerciale informée des nouveaux réseaux

### Stabilisation (J+8+)

- [ ] Performance stable sur 7 jours
- [ ] Feedback utilisateurs positif
- [ ] Comparaison métriques Chariow vs SasPay favorable
- [ ] Décision : conserver SasPay ou rollback définitif

---

## 🎉 CONCLUSION

Cette migration a été conçue pour être :

- **Sans risque** : Rollback instantané à tout moment
- **Sans interruption** : Zéro downtime, switch transparent
- **Réversible** : Architecture multi-provider conservée
- **Évolutive** : Ajout de nouveaux providers facilité

**Bonne migration ! 🚀**

---

**Dernière mise à jour** : 2026-09-09  
**Auteur** : Équipe DevOps SûrCheck AI  
**Version document** : 1.0.0
