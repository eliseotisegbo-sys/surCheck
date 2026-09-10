# 🚀 ACTIONS MANUELLES - ACTIVATION SASPAY PRODUCTION

**URL Railway** : https://surcheck.up.railway.app  
**Clé SasPay LIVE** : Voir fichier `.env` local (ligne `SASPAY_API_KEY`)  
**Mode** : Production directe (argent réel)

---

## ⚠️ IMPORTANT

Vous allez activer SasPay **directement en production** avec votre clé LIVE.  
Les paiements seront **réels** dès l'activation.

**Rollback disponible** : Si problème, retour à Chariow en < 2 minutes (voir fin du document)

---

## 📋 ACTION 1 : CONFIGURER LE WEBHOOK SASPAY

**Temps** : 5 minutes

### Étapes détaillées :

1. **Aller sur** : https://application.saspay.me/

2. **Se connecter** avec votre compte SasPay

3. **Naviguer vers** : `Dashboard → Webhooks` (ou `Développeur → Webhooks`)

4. **Cliquer** : `Créer un webhook` / `Nouveau webhook` / `Add Webhook`

5. **Remplir le formulaire** :

   | Champ | Valeur exacte à copier-coller |
   |-------|-------------------------------|
   | **Nom** | `SûrCheck AI Production` |
   | **URL du webhook** | `https://surcheck.up.railway.app/api/v1/payment/webhook` |
   | **Mode** | **Production** / Live (PAS sandbox !) |
   | **Événements** | Cocher les cases :<br>☑️ `payment.succeeded`<br>☑️ `payment.failed`<br>☑️ `payment.cancelled`<br>☑️ `payment.refunded` |

6. **Valider** / `Créer le webhook`

7. **⚠️ IMPORTANT** : SasPay va afficher un **Secret de webhook**
   - Format possible : `whsec_xxxxxxxxxxxxx` ou autre
   - **COPIEZ-LE IMMÉDIATEMENT** (il ne sera peut-être plus affiché)

8. **Notez le secret ici** (temporaire, vous allez le coller dans Railway) :

   ```
   Secret webhook : _________________________________
   ```

---

## 📋 ACTION 2 : METTRE À JOUR LES VARIABLES RAILWAY

**Temps** : 5 minutes

### Étapes détaillées :

1. **Aller sur** : https://railway.app/

2. **Se connecter** si nécessaire

3. **Sélectionner** votre projet : **SûrCheck AI**

4. **Cliquer** sur le service : **Backend API** (celui qui fait tourner FastAPI/Python)

5. **Cliquer** sur l'onglet : **Variables** (en haut)

6. **Cliquer** : **RAW Editor** (bouton en haut à droite)

7. **Faire défiler** jusqu'en bas du fichier (ne pas effacer l'existant !)

8. **Ajouter ces lignes** à la fin :

```env
# ═══════════════════════════════════════════════════════════
# SASPAY - ACTIVATION PRODUCTION
# ═══════════════════════════════════════════════════════════

PAYMENT_PROVIDER=saspay
SASPAY_API_KEY=<VOIR_FICHIER_.ENV_LOCAL>
SASPAY_BASE_URL=https://api.saspay.me/api/v1
SASPAY_WEBHOOK_SECRET=REMPLACER_PAR_LE_SECRET_DE_ACTION_1
```

9. **⚠️ IMPORTANT** : Remplacer `REMPLACER_PAR_LE_SECRET_DE_ACTION_1` par le secret que vous avez copié à l'ACTION 1

10. **Cliquer** : `Update Variables` / `Save` (bouton en haut à droite)

11. **Attendre** : Railway va redéployer automatiquement (30-90 secondes)
    - Vous verrez un indicateur de progression
    - Attendez le message "Deployment successful" ou équivalent

---

## 📋 ACTION 3 : VÉRIFIER L'ACTIVATION

**Temps** : 2 minutes

### Étapes détaillées :

1. **Toujours sur Railway**, cliquer sur l'onglet : **Deployments**

2. **Cliquer** sur le dernier déploiement (tout en haut de la liste)

3. **Cliquer** : `View Logs` / `Logs`

4. **Chercher dans les logs** (au démarrage) :

```
✅ À CHERCHER : "Provider de paiement actif : SasPay (Softpay Mobile Money)"
```

### Résultat attendu :

**✅ SI VOUS VOYEZ CE MESSAGE** :
- SasPay est **activé** et **opérationnel**
- Passez à ACTION 4 pour tester

**❌ SI VOUS VOYEZ "Provider de paiement actif : Chariow"** :
- Les variables n'ont pas été prises en compte
- Vérifier ACTION 2, ligne `PAYMENT_PROVIDER=saspay`
- Forcer un redéploiement si nécessaire

**❌ SI VOUS VOYEZ "SASPAY_API_KEY non configuré"** :
- La clé n'a pas été ajoutée correctement
- Revérifier ACTION 2, ligne `SASPAY_API_KEY=...`

---

## 📋 ACTION 4 : TESTER UN PREMIER PAIEMENT

**Temps** : 5 minutes

### Option A : Test via l'interface web (recommandé)

1. **Aller sur** : https://sur-check.vercel.app/

2. **Se connecter** avec votre compte (ou en créer un test)

3. **Aller dans** : `Mon compte` ou `Acheter des crédits`

4. **Sélectionner** : **Pack 1 crédit** (600 FCFA - le moins cher pour tester)

5. **Entrer un numéro MTN Bénin** :
   - Votre numéro : `97XXXXXX` (préfixe MTN)
   - Ou un numéro test : `97505050`

6. **Cliquer** : `Payer` / `Acheter`

7. **Observer** :
   - Le système devrait créer un checkout
   - Vous devriez recevoir un push USSD sur votre téléphone
   - ⚠️ **CE PAIEMENT EST RÉEL** (600 FCFA seront débités si validé)

8. **Valider le paiement** sur votre téléphone (code PIN)

9. **Attendre** quelques secondes

10. **Vérifier** :
    - Votre solde SûrCheck : Devrait afficher **+1 crédit**
    - Si le crédit apparaît ✅ : **Migration réussie !**

### Option B : Test via Supabase (vérification backend)

1. **Aller sur** : https://supabase.com/dashboard

2. **Sélectionner** : Projet SûrCheck AI

3. **Aller dans** : `Table Editor`

4. **Ouvrir la table** : `payment_transactions`

5. **Chercher** la dernière transaction (triez par `created_at` décroissant)

6. **Vérifier** :
   - `provider` = `saspay` ✅
   - `status` = `successful` ✅
   - `amount_fcfa` = `600` ✅

7. **Ouvrir la table** : `user_credits`

8. **Chercher** votre utilisateur

9. **Vérifier** :
   - Colonne `balance` a augmenté de +1 ✅

---

## 📋 ACTION 5 : SURVEILLER LES PREMIERS PAIEMENTS

**Temps** : Continu (premières 24-48h)

### Métriques à surveiller :

1. **Taux de succès des paiements**
   - Cible : **≥ 85%** (standard Mobile Money)
   - Si < 80% → Investiguer (logs Railway)

2. **Logs Railway**
   - Chercher : `Webhook saspay reçu : event=successful.sale`
   - Si erreurs répétées : Vérifier `SASPAY_WEBHOOK_SECRET`

3. **Supabase - Table `payment_transactions`**
   - Vérifier que `provider=saspay` apparaît
   - Vérifier ratio `successful` vs `failed`

4. **Feedback utilisateurs**
   - Surveiller si des utilisateurs signalent des échecs de paiement
   - Vérifier compatibilité Moov Bénin (préfixes 01, 02, 03, 80-89)

### Alertes à configurer (optionnel) :

- Webhook rejetés > 5/heure → Problème signature
- Taux succès < 70% pendant 2h → Problème API SasPay
- Erreurs "network invalid" → Préfixes téléphone manquants

---

## 🆘 ROLLBACK D'URGENCE VERS CHARIOW

**Si problème critique, retour immédiat en < 2 minutes**

### Quand faire un rollback ?

- Taux de succès < 50% pendant > 1 heure
- API SasPay indisponible (erreurs 5xx répétées)
- Bug critique découvert en production
- Utilisateurs bloqués massivement

### Procédure de rollback :

1. **Railway** → Votre projet → Backend → **Variables** → **RAW Editor**

2. **Modifier UNIQUEMENT cette ligne** :
   ```env
   PAYMENT_PROVIDER=chariow
   ```
   (Passer de `saspay` à `chariow`)

3. **Save** → Redéploiement automatique (30-60 secondes)

4. **Vérifier logs** : `Provider de paiement actif : Chariow`

5. **✅ Chariow reprend immédiatement**
   - Aucun changement code
   - Aucune perte de données
   - Tous les packs fonctionnent

6. **Investiguer le problème** en parallèle (logs Railway + Supabase)

7. **Corriger et retester** avant de réactiver SasPay

---

## ✅ CHECKLIST DE VALIDATION

Cochez au fur et à mesure :

- [ ] **ACTION 1** : Webhook créé, secret copié
- [ ] **ACTION 2** : Variables Railway mises à jour (PAYMENT_PROVIDER, SASPAY_API_KEY, SASPAY_WEBHOOK_SECRET)
- [ ] **ACTION 3** : Logs Railway affichent "SasPay"
- [ ] **ACTION 4** : Premier paiement test réussi, crédit ajouté
- [ ] **ACTION 5** : Monitoring actif (taux succès surveillé)

---

## 📊 RÉCAPITULATIF

| Action | Plateforme | Temps | Critique |
|--------|------------|-------|----------|
| 1. Créer webhook | application.saspay.me | 5 min | ⚠️ OUI |
| 2. Variables Railway | railway.app | 5 min | ⚠️ OUI |
| 3. Vérifier activation | railway.app (logs) | 2 min | ✅ Validation |
| 4. Test paiement | sur-check.vercel.app | 5 min | ✅ Validation |
| 5. Monitoring | Continu | 48h | 📊 Surveillance |

**Temps total initial** : ~15 minutes

---

## 🎯 COMMENCEZ MAINTENANT

**Étape suivante** : ACTION 1 - Créer le webhook sur https://application.saspay.me/

---

## 📞 TROUBLESHOOTING RAPIDE

| Problème | Solution rapide |
|----------|-----------------|
| Webhook signature invalide | Vérifier `SASPAY_WEBHOOK_SECRET` correspond au secret SasPay |
| Logs montrent "Chariow" | Vérifier `PAYMENT_PROVIDER=saspay` dans Railway |
| "network invalid" | Vérifier préfixe téléphone dans `saspay_provider.py` lignes 50-90 |
| Crédit non ajouté | Vérifier logs Railway : `event=successful.sale` reçu ? |
| Checkout échoue | Vérifier `SASPAY_API_KEY` valide et mode production |

---

## 📚 DOCUMENTATION COMPLÈTE

Pour plus de détails :

- **MIGRATION_SASPAY.md** : Guide technique complet (600+ lignes)
- **SASPAY_API_ANALYSIS.md** : Analyse API détaillée
- **CHARIOW_TO_SASPAY_MAPPING.md** : Transformations techniques

---

**🚀 Bonne activation ! La migration est prête.**

**⚠️ Rappel** : Les paiements sont réels dès l'activation (clé LIVE).
