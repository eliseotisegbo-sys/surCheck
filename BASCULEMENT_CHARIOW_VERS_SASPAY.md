# 🔄 PROCESSUS DE BASCULEMENT CHARIOW → SASPAY

**Date** : 2026-09-10  
**Objectif** : Activer SasPay sur Railway et Vercel en production  
**Durée** : 15 minutes

---

## ✅ PRÉREQUIS (Déjà fait chez vous)

- ✅ Code SasPay pushé sur GitHub
- ✅ Webhook SasPay créé (secret dans fichier `.env` local)
- ✅ Clé LIVE SasPay (voir fichier `.env` local)
- ✅ URL Railway : `https://surcheck.up.railway.app`

---

## 🚂 PARTIE 1 : BASCULEMENT RAILWAY (Backend FastAPI)

### Étape 1 : Ouvrir Railway

1. **Aller sur** : https://railway.app/
2. **Se connecter**
3. **Sélectionner** votre projet : **SûrCheck AI**
4. **Cliquer** sur le service **Backend** (celui avec FastAPI/Python)

### Étape 2 : Accéder aux variables d'environnement

1. **Cliquer** sur l'onglet : **Variables** (en haut)
2. **Cliquer** : **RAW Editor** (bouton en haut à droite)

### Étape 3 : Ajouter les variables SasPay

**Faire défiler tout en bas** du fichier et **ajouter ces lignes** :

```env
# ═══════════════════════════════════════════════════════════
# SASPAY - ACTIVATION PRODUCTION
# ═══════════════════════════════════════════════════════════

PAYMENT_PROVIDER=saspay
SASPAY_API_KEY=<COPIER_DEPUIS_FICHIER_.ENV_LOCAL>
SASPAY_BASE_URL=https://api.saspay.me/api/v1
SASPAY_WEBHOOK_SECRET=<COPIER_DEPUIS_FICHIER_.ENV_LOCAL>
```

### Étape 4 : Sauvegarder et redéployer

1. **Cliquer** : **Update Variables** / **Save Changes** (bouton en haut à droite)
2. **Attendre** : Railway va redéployer automatiquement
   - Vous verrez : "Deploying..." puis "Active"
   - Durée : 30-90 secondes

### Étape 5 : Vérifier l'activation

1. **Rester sur Railway**, cliquer sur l'onglet : **Deployments**
2. **Cliquer** sur le déploiement le plus récent (tout en haut)
3. **Cliquer** : **View Logs** / **Logs**
4. **Chercher** dans les logs au démarrage :

```
✅ VOUS DEVEZ VOIR :
Provider de paiement actif : SasPay (Softpay Mobile Money)
```

**❌ SI VOUS VOYEZ "Chariow"** :
- Revérifier Étape 3 : `PAYMENT_PROVIDER=saspay` bien présent ?
- Forcer redéploiement : Deployments → ⋮ (trois points) → Redeploy

### ✅ RAILWAY EST PRÊT

Le backend utilise maintenant SasPay !

---

## 🌐 PARTIE 2 : VÉRIFICATION VERCEL (Frontend Next.js)

**Bonne nouvelle** : **AUCUNE modification nécessaire sur Vercel !**

Le frontend communique avec le backend via l'API. Le changement de provider est **transparent**.

### Vérification optionnelle (2 min)

1. **Aller sur** : https://vercel.com/dashboard
2. **Sélectionner** : Projet **SûrCheck AI** (ou nom de votre projet frontend)
3. **Cliquer** : **Deployments**
4. **Vérifier** : Dernier déploiement actif (statut "Ready")

**Rien à faire ici** ✅

---

## 🧪 PARTIE 3 : TEST DE VALIDATION

### Test 1 : Vérifier que l'API répond

**Dans votre navigateur**, aller sur :

```
https://surcheck.up.railway.app/health
```

**Résultat attendu** :

```json
{
  "status": "healthy",
  "version": "v1.0.0",
  "environment": "production"
}
```

✅ **Si vous voyez ce JSON** : API en ligne

---

### Test 2 : Vérifier les packs disponibles

**Dans votre navigateur**, aller sur :

```
https://surcheck.up.railway.app/api/v1/payment/packs
```

**Résultat attendu** :

```json
{
  "packs": [
    {
      "id": "pack_1",
      "credits": 1,
      "amount_fcfa": 600,
      "label": "Analyse unique",
      ...
    },
    ...
  ],
  "currency": "XOF"
}
```

✅ **Si vous voyez la liste des packs** : Endpoint paiement fonctionnel

---

### Test 3 : Créer un checkout réel (⚠️ PAIEMENT RÉEL)

1. **Aller sur** : https://sur-check.vercel.app/

2. **Se connecter** avec votre compte

3. **Aller dans** : `Mon compte` ou `Acheter des crédits`

4. **Sélectionner** : **Pack 1 crédit** (600 FCFA)

5. **Entrer** :
   - **Numéro MTN** : Votre vrai numéro MTN Bénin (97XXXXXX)
   - OU un numéro test si vous en avez

6. **Cliquer** : `Payer` / `Acheter`

7. **Observer** :
   - Le système crée un checkout
   - Vous devriez recevoir un **push USSD** sur votre téléphone
   - Message type : "Confirmez le paiement de 600 FCFA vers SûrCheck AI"

8. **Valider** le paiement sur votre téléphone (code PIN)

9. **Attendre** 5-10 secondes

10. **Vérifier** :
    - Rechargez la page si besoin
    - Votre solde devrait afficher : **+1 crédit** ✅

---

### Test 4 : Vérifier en base de données (Supabase)

1. **Aller sur** : https://supabase.com/dashboard

2. **Sélectionner** : Projet **SûrCheck AI**

3. **Cliquer** : **Table Editor**

4. **Ouvrir** : Table `payment_transactions`

5. **Chercher** : Dernière transaction (triez par `created_at` décroissant)

6. **Vérifier** :
   - `provider` = **`saspay`** ✅
   - `status` = **`successful`** ✅
   - `amount_fcfa` = **`600`** ✅
   - `pack_code` = **`pack_1`** ✅

7. **Ouvrir** : Table `user_credits`

8. **Chercher** : Votre utilisateur

9. **Vérifier** :
   - `balance` a augmenté de **+1** ✅

10. **Ouvrir** : Table `credit_transactions`

11. **Chercher** : Dernière transaction

12. **Vérifier** :
    - `transaction_type` = **`purchase`** ✅
    - `amount` = **`1`** ✅
    - `provider` = **`saspay`** ✅

---

### ✅ SI TOUS LES TESTS PASSENT

**🎉 MIGRATION RÉUSSIE !**

SasPay est maintenant **actif en production** sur Railway et le frontend fonctionne correctement.

---

## 📊 PARTIE 4 : MONITORING (48 premières heures)

### Logs Railway à surveiller

**Railway → Deployments → Dernier déploiement → View Logs**

**Logs positifs à chercher** :

```
✅ Provider de paiement actif : SasPay (Softpay Mobile Money)
✅ Webhook saspay reçu : event=successful.sale | sale=xxx | user=xxx
✅ Crédit ajouté pour user_id=xxx : 1 crédit(s)
```

**Logs d'erreur à surveiller** :

```
❌ Webhook saspay rejeté : signature cryptographique invalide
❌ Erreur API SasPay (502)
❌ network invalid
```

### Métriques Supabase

**Table `payment_transactions`** :

```sql
-- Taux de succès SasPay (dernières 24h)
SELECT 
  COUNT(*) FILTER (WHERE status = 'successful') as success,
  COUNT(*) FILTER (WHERE status = 'failed') as failed,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'successful') / COUNT(*), 2) as success_rate
FROM payment_transactions
WHERE provider = 'saspay'
  AND created_at >= NOW() - INTERVAL '24 hours';
```

**Cible** : `success_rate >= 85%`

### Alertes à surveiller

- ⚠️ Taux succès < 80% pendant 2h → Problème API ou réseau
- ⚠️ Webhooks rejetés > 5/heure → Vérifier `SASPAY_WEBHOOK_SECRET`
- ⚠️ Erreurs "network invalid" → Préfixes téléphone manquants

---

## 🆘 ROLLBACK D'URGENCE VERS CHARIOW

**Si problème critique, retour immédiat en < 2 minutes**

### Quand faire un rollback ?

- Taux de succès < 50% pendant > 1 heure
- API SasPay indisponible (5xx répétés)
- Bug critique bloquant les utilisateurs
- Plaintes massives utilisateurs

### Procédure :

1. **Railway** → Projet SûrCheck → Backend → **Variables** → **RAW Editor**

2. **Chercher la ligne** :
   ```env
   PAYMENT_PROVIDER=saspay
   ```

3. **Modifier en** :
   ```env
   PAYMENT_PROVIDER=chariow
   ```

4. **Save** → Redéploiement automatique (30-60 sec)

5. **Vérifier logs** : 
   ```
   Provider de paiement actif : Chariow
   ```

6. **✅ Chariow reprend immédiatement**

7. **Tester** : Créer un checkout → Doit utiliser Chariow

### Après rollback :

- Investiguer la cause (logs Railway + Supabase)
- Corriger le problème si possible
- Documenter l'incident
- Retenter l'activation SasPay après correction

---

## 📋 CHECKLIST COMPLÈTE

### Avant activation

- [x] Code SasPay pushé sur GitHub
- [x] Webhook SasPay créé
- [x] Clé LIVE récupérée
- [x] Secret webhook récupéré

### Activation Railway

- [ ] Variables ajoutées (PAYMENT_PROVIDER, SASPAY_API_KEY, etc.)
- [ ] Redéploiement terminé
- [ ] Logs affichent "SasPay"

### Tests

- [ ] Endpoint `/health` répond
- [ ] Endpoint `/api/v1/payment/packs` répond
- [ ] Checkout créé avec succès
- [ ] Push USSD reçu sur téléphone
- [ ] Paiement validé
- [ ] Crédit ajouté (+1)
- [ ] Supabase : `provider=saspay` présent
- [ ] Supabase : `status=successful`

### Monitoring

- [ ] Logs Railway surveillés (webhooks reçus)
- [ ] Taux succès calculé (≥85%)
- [ ] Feedback utilisateurs collecté
- [ ] Aucune erreur répétée

---

## 🎯 RÉSUMÉ VISUEL

```
┌─────────────────────────────────────────────────────┐
│  AVANT (Chariow actif)                              │
├─────────────────────────────────────────────────────┤
│  Railway : PAYMENT_PROVIDER=chariow                 │
│  Vercel  : Aucune modification                      │
│  Paiements → Chariow API                            │
└─────────────────────────────────────────────────────┘
                        ⬇️
                BASCULEMENT (15 min)
                        ⬇️
┌─────────────────────────────────────────────────────┐
│  APRÈS (SasPay actif)                               │
├─────────────────────────────────────────────────────┤
│  Railway : PAYMENT_PROVIDER=saspay                  │
│           + SASPAY_API_KEY                          │
│           + SASPAY_BASE_URL                         │
│           + SASPAY_WEBHOOK_SECRET                   │
│  Vercel  : Aucune modification (transparent)        │
│  Paiements → SasPay API                             │
└─────────────────────────────────────────────────────┘
```

---

## 📞 AIDE & TROUBLESHOOTING

### Problème : Logs Railway montrent toujours "Chariow"

**Solution** :
- Vérifier que `PAYMENT_PROVIDER=saspay` est bien dans les variables
- Pas de faute de frappe, pas d'espace avant/après
- Forcer un redéploiement manuel si besoin

### Problème : Webhook signature invalide

**Solution** :
- Vérifier que `SASPAY_WEBHOOK_SECRET` correspond exactement au secret SasPay
- Pas d'espace, pas de guillemets en trop
- Régénérer un nouveau webhook si besoin

### Problème : "network invalid" lors du checkout

**Solution** :
- Le préfixe téléphone n'est pas reconnu
- Vérifier fichier `apps/api/src/services/saspay_provider.py` lignes 50-90
- Ajouter le préfixe manquant dans `mtn_prefixes` ou `moov_prefixes`

### Problème : Crédit non ajouté après paiement

**Solution** :
- Vérifier Railway Logs : webhook reçu ? `event=successful.sale` ?
- Vérifier Supabase : transaction enregistrée ?
- Si webhook non reçu → Vérifier URL webhook sur SasPay
- Si webhook rejeté → Vérifier `SASPAY_WEBHOOK_SECRET`

---

## ✅ VOUS ÊTES PRÊT

**Prochaine étape** : Commencer par **PARTIE 1 - Étape 1** (Ouvrir Railway)

**Temps estimé** : 15 minutes

**Niveau de risque** : Faible (rollback instantané disponible)

**🚀 Bonne activation !**
