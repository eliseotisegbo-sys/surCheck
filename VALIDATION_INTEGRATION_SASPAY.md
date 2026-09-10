# ✅ VALIDATION INTÉGRATION SASPAY - CHECKLIST COMPLÈTE

**Date** : 2026-09-10  
**Status** : Variables configurées sur Railway ✅

---

## 📋 CONFIGURATION ACTUELLE

### Variables Railway (confirmées) :

```env
✅ PAYMENT_PROVIDER=saspay
✅ SASPAY_API_KEY=<VOIR_FICHIER_.ENV_LOCAL>
✅ SASPAY_BASE_URL=https://api.saspay.me/api/v1
✅ SASPAY_WEBHOOK_SECRET=<VOIR_FICHIER_.ENV_LOCAL>
```

### URL Production :
- **Backend Railway** : https://surcheck.up.railway.app
- **Frontend Vercel** : https://sur-check.vercel.app
- **Webhook SasPay** : https://surcheck.up.railway.app/api/v1/payment/webhook

---

## 🧪 TESTS À EFFECTUER (Ordre recommandé)

### ✅ TEST 1 : Vérifier activation SasPay dans les logs

**Action** :
1. https://railway.app/ → SûrCheck AI → Backend
2. Deployments → Dernier déploiement → View Logs

**Chercher** :
```
Provider de paiement actif : SasPay (Softpay Mobile Money)
```

**Résultat** : [ ] Confirmé ✅ / [ ] Non trouvé ❌

---

### ✅ TEST 2 : Vérifier que l'API répond

**Action** :  
Ouvrir dans le navigateur : https://surcheck.up.railway.app/health

**Résultat attendu** :
```json
{
  "status": "healthy",
  "version": "v1.0.0",
  "environment": "production"
}
```

**Résultat** : [ ] API en ligne ✅ / [ ] Erreur ❌

---

### ✅ TEST 3 : Vérifier endpoint packs

**Action** :  
Ouvrir dans le navigateur : https://surcheck.up.railway.app/api/v1/payment/packs

**Résultat attendu** :
```json
{
  "packs": [
    {"id": "pack_1", "credits": 1, "amount_fcfa": 600, ...},
    {"id": "pack_10", "credits": 10, "amount_fcfa": 2500, ...}
  ],
  "currency": "XOF"
}
```

**Résultat** : [ ] Packs affichés ✅ / [ ] Erreur ❌

---

### ✅ TEST 4 : Créer un checkout test (PAIEMENT RÉEL)

**⚠️ ATTENTION** : Ce test utilise de l'argent réel (600 FCFA minimum)

**Action** :
1. https://sur-check.vercel.app/
2. Se connecter
3. Aller dans section paiement/crédits
4. Sélectionner : **Pack 1 crédit** (600 FCFA)
5. Entrer : Numéro MTN Bénin (97XXXXXX)
6. Cliquer : Acheter/Payer

**Résultat attendu** :
- [ ] Checkout créé sans erreur
- [ ] Push USSD reçu sur téléphone (< 30 sec)
- [ ] Message : "Validez 600 FCFA vers SûrCheck AI"

**Résultat** : [ ] Checkout OK ✅ / [ ] Erreur ❌

---

### ✅ TEST 5 : Valider le paiement

**Action** :
1. Sur téléphone : Composer code USSD ou valider notification
2. Entrer : Code PIN MTN Money
3. Confirmer : Paiement 600 FCFA
4. Attendre : 10-15 secondes

**Résultat** : [ ] Paiement validé ✅ / [ ] Refusé ❌

---

### ✅ TEST 6 : Vérifier crédit ajouté

**Action A - Frontend** :
1. https://sur-check.vercel.app/
2. Actualiser la page
3. Vérifier : Solde de crédits

**Résultat** : [ ] +1 crédit ✅ / [ ] Aucun changement ❌

**Action B - Logs Railway** :
1. Railway → Backend → Deployments → View Logs
2. Chercher :
```
Webhook saspay reçu : event=successful.sale | sale=xxx | user=xxx
```

**Résultat** : [ ] Webhook reçu ✅ / [ ] Aucun log ❌

---

### ✅ TEST 7 : Vérifier en base de données

**Action** :
1. https://supabase.com/dashboard
2. Projet SûrCheck AI → Table Editor

**Table `payment_transactions`** :
- [ ] `provider` = `saspay` ✅
- [ ] `status` = `successful` ✅
- [ ] `amount_fcfa` = `600` ✅
- [ ] `credits_purchased` = `1` ✅

**Table `user_credits`** :
- [ ] `balance` augmenté de +1 ✅

**Table `credit_transactions`** :
- [ ] `transaction_type` = `purchase` ✅
- [ ] `amount` = `1` ✅

**Résultat** : [ ] Tout correct ✅ / [ ] Incohérences ❌

---

## 🎉 RÉSULTAT FINAL

### Si TOUS les tests sont ✅ :

**🎉 INTÉGRATION SASPAY COMPLÈTE ET FONCTIONNELLE !**

Vous avez :
- ✅ SasPay actif en production
- ✅ Webhook fonctionnel
- ✅ Détection réseau automatique (MTN/Moov)
- ✅ Crédits ajoutés correctement
- ✅ Base de données synchronisée
- ✅ Frontend transparent (aucun changement)

**Migration réussie ! 🚀**

---

### Si des tests échouent :

#### ❌ Logs montrent "Chariow" au lieu de "SasPay"

**Solution** :
1. Railway → Variables → Vérifier `PAYMENT_PROVIDER=saspay`
2. Deployments → Menu (⋮) → Redeploy
3. Attendre 60 secondes
4. Refaire TEST 1

---

#### ❌ Webhook non reçu (pas de log)

**Solution** :
1. https://application.saspay.me/ → Webhooks
2. Vérifier URL : `https://surcheck.up.railway.app/api/v1/payment/webhook`
3. Vérifier événements cochés : `payment.succeeded`, `payment.failed`, etc.
4. Vérifier mode : **Production** (pas sandbox)
5. Régénérer webhook si besoin → Copier nouveau secret
6. Railway → Variables → Mettre à jour `SASPAY_WEBHOOK_SECRET`

---

#### ❌ Webhook rejeté (signature invalide)

**Solution** :
1. Vérifier Railway Variables :
   ```
   SASPAY_WEBHOOK_SECRET=<DOIT_CORRESPONDRE_AU_SECRET_SASPAY>
   ```
2. Doit correspondre EXACTEMENT au secret du dashboard SasPay
3. Pas d'espace, pas de guillemets en trop
4. Redéployer après modification

---

#### ❌ Crédit non ajouté

**Diagnostic** :
1. Railway Logs → Webhook reçu ? `event=successful.sale` ?
2. Supabase → `payment_transactions` → Transaction enregistrée ?
3. Supabase → `user_credits` → Balance mise à jour ?

**Solution selon le blocage** :
- Si webhook non reçu → Voir solution "Webhook non reçu"
- Si webhook rejeté → Voir solution "Webhook rejeté"
- Si transaction en DB mais crédit non ajouté → Vérifier logs erreur dans Railway

---

## 📊 MONITORING POST-ACTIVATION

### Métriques à surveiller (48h) :

#### 1. Taux de succès (cible ≥ 85%)

**Requête SQL Supabase** :
```sql
SELECT 
  COUNT(*) as total_transactions,
  COUNT(*) FILTER (WHERE status = 'successful') as successful,
  COUNT(*) FILTER (WHERE status = 'failed') as failed,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'successful') / COUNT(*), 2) as success_rate
FROM payment_transactions
WHERE provider = 'saspay'
  AND created_at >= NOW() - INTERVAL '24 hours';
```

**Action si < 85%** : Investiguer logs Railway pour identifier cause

---

#### 2. Webhooks reçus

**Railway Logs** → Chercher régulièrement :
```
✅ Webhook saspay reçu : event=successful.sale
```

**Action si aucun webhook** : Vérifier configuration webhook SasPay

---

#### 3. Erreurs répétées

**Railway Logs** → Surveiller :
```
❌ Webhook saspay rejeté : signature cryptographique invalide
❌ Erreur API SasPay (502)
❌ network invalid
```

**Action si erreurs** : Voir solutions ci-dessus

---

#### 4. Répartition réseaux

**Requête SQL Supabase** :
```sql
SELECT 
  metadata->>'network' as network,
  COUNT(*) as count
FROM payment_transactions
WHERE provider = 'saspay'
  AND created_at >= NOW() - INTERVAL '24 hours'
GROUP BY network
ORDER BY count DESC;
```

**Vérification** : MTN et Moov doivent apparaître (selon utilisation)

---

## 🆘 ROLLBACK D'URGENCE

### Quand ?
- Taux succès < 50% pendant > 1h
- API SasPay indisponible (5xx répétés)
- Bug critique bloquant utilisateurs

### Comment ? (< 2 minutes)

1. **Railway** → Backend → **Variables** → **RAW Editor**
2. **Modifier** :
   ```env
   PAYMENT_PROVIDER=chariow
   ```
3. **Save** → Redéploiement (60 sec)
4. **Vérifier logs** : `Provider de paiement actif : Chariow`
5. **✅ Chariow reprend immédiatement**

### Après rollback :
- Investiguer cause (logs + Supabase)
- Corriger problème
- Documenter incident
- Retenter activation après correction

---

## 📞 SUPPORT

### Logs Railway à partager en cas de problème :
- Démarrage application : `Provider de paiement actif : ...`
- Webhooks : `Webhook saspay reçu : ...`
- Erreurs : Stack traces complètes

### Données Supabase à vérifier :
- Table `payment_transactions` : Dernières lignes
- Table `user_credits` : Solde utilisateur
- Table `credit_transactions` : Dernières transactions

---

## ✅ CHECKLIST FINALE

**Configuration** :
- [x] Variables Railway ajoutées
- [x] Webhook SasPay configuré
- [x] Secret webhook mis à jour

**Tests** :
- [ ] TEST 1 : Logs montrent "SasPay"
- [ ] TEST 2 : API /health répond
- [ ] TEST 3 : Endpoint /packs répond
- [ ] TEST 4 : Checkout créé
- [ ] TEST 5 : Paiement validé
- [ ] TEST 6 : Crédit ajouté
- [ ] TEST 7 : Base de données correcte

**Monitoring** :
- [ ] Taux succès surveillé (≥85%)
- [ ] Webhooks reçus confirmés
- [ ] Aucune erreur répétée
- [ ] Feedback utilisateurs OK

---

**🎯 PROCHAINE ACTION** : Effectuer les tests 1-7 et cocher les cases ✅

**Bonne validation ! 🚀**
