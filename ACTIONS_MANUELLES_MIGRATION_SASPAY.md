# 📋 ACTIONS MANUELLES REQUISES - MIGRATION SASPAY

**Date** : 2026-09-09  
**Statut code** : ✅ Pushé sur GitHub (commit `dc340da`)  
**Statut migration** : ⏳ En attente actions manuelles

---

## ✅ CE QUI EST DÉJÀ FAIT (automatique)

- ✅ Code SasPay implémenté et testé
- ✅ Configuration `.env` préparée avec clé LIVE
- ✅ Documentation complète créée
- ✅ Code pushé sur GitHub
- ✅ Tests d'intégration rédigés

**Provider actif actuel** : `PAYMENT_PROVIDER="chariow"` (sécurisé)

---

## 🎯 ACTIONS MANUELLES REQUISES (VOUS)

### ═══════════════════════════════════════════════════════════
### **ACTION 1 : Créer un compte SasPay Sandbox** 🔐
### ═══════════════════════════════════════════════════════════

**Pourquoi ?** Votre clé actuelle est LIVE (`sk_live_*`). Pour tester sans dépenser d'argent réel, vous devez obtenir une clé SANDBOX.

#### Étapes :

1. **Aller sur** : https://application.saspay.me/

2. **Se connecter** avec votre compte SasPay existant

3. **Accéder à** : `Dashboard → Développeur → API Keys`

4. **Trouver ou générer** une clé **Test/Sandbox** :
   - Format : `sk_test_xxxxxxxxxxxxxxxxxxxxx`
   - Cette clé permet de tester sans argent réel

5. **Copier** la clé `sk_test_xxxxx`

#### Après cette action :

**Modifier le fichier `.env` local** :

```env
# Remplacer temporairement la clé LIVE par la clé TEST
SASPAY_API_KEY="sk_test_xxxxxxxxxxxxx"  # Collez votre clé test ici
```

**⚠️ NE PAS commiter ce changement** (`.env` est dans `.gitignore`)

---

### ═══════════════════════════════════════════════════════════
### **ACTION 2 : Configurer le webhook SasPay** 🔔
### ═══════════════════════════════════════════════════════════

**Pourquoi ?** SasPay doit savoir où envoyer les notifications de paiement.

#### Étapes :

1. **Toujours sur** : https://application.saspay.me/

2. **Aller dans** : `Dashboard → Webhooks` (ou `Développeur → Webhooks`)

3. **Cliquer** : `Créer un webhook` / `Ajouter un webhook`

4. **Remplir le formulaire** :

   | Champ | Valeur |
   |-------|--------|
   | **Nom** | `SûrCheck AI Production` |
   | **URL** | `https://surcheck-production.up.railway.app/api/v1/payment/webhook` |
   | **Événements à écouter** | ☑️ `payment.succeeded`<br>☑️ `payment.failed`<br>☑️ `payment.cancelled`<br>☑️ `payment.refunded` |
   | **Mode** | Test/Sandbox (pour l'instant) |

   **⚠️ Remplacez** `surcheck-production.up.railway.app` par votre vraie URL Railway

5. **Valider** / `Créer`

6. **Copier le "Secret du webhook"** affiché (format : `whsec_xxxxx` ou autre)

#### Après cette action :

**Modifier le fichier `.env` local** :

```env
# Ajouter le secret du webhook
SASPAY_WEBHOOK_SECRET="whsec_xxxxxxxxxxxxx"  # Collez le secret ici
```

---

### ═══════════════════════════════════════════════════════════
### **ACTION 3 : Mettre à jour les variables Railway** 🚂
### ═══════════════════════════════════════════════════════════

**Pourquoi ?** Railway doit avoir les nouvelles variables d'environnement SasPay.

#### Étapes :

1. **Aller sur** : https://railway.app/

2. **Sélectionner** votre projet SûrCheck AI

3. **Cliquer** sur le service **Backend API** (FastAPI)

4. **Aller dans** : `Variables` (onglet)

5. **Cliquer** : `RAW Editor` (en haut à droite)

6. **Ajouter ces lignes** en bas du fichier (sans écraser l'existant) :

```env
# ═══ SASPAY CONFIGURATION (Sandbox) ═══
PAYMENT_PROVIDER=saspay
SASPAY_API_KEY=sk_test_xxxxxxxxxxxxx
SASPAY_BASE_URL=https://api.saspay.me/api/v1
SASPAY_WEBHOOK_SECRET=whsec_xxxxxxxxxxxxx
```

**⚠️ Remplacez** :
- `sk_test_xxxxxxxxxxxxx` par votre clé test (ACTION 1)
- `whsec_xxxxxxxxxxxxx` par votre secret webhook (ACTION 2)

7. **Cliquer** : `Save` / `Update Variables`

8. **Attendre** le redéploiement automatique (30-60 secondes)

---

### ═══════════════════════════════════════════════════════════
### **ACTION 4 : Vérifier que SasPay est actif** ✅
### ═══════════════════════════════════════════════════════════

**Pourquoi ?** Confirmer que le switch vers SasPay a fonctionné.

#### Étapes :

1. **Aller sur** : https://railway.app/ → Votre projet → Backend

2. **Cliquer** sur l'onglet `Deployments`

3. **Cliquer** sur le dernier déploiement (tout en haut)

4. **Cliquer** sur `View Logs`

5. **Chercher dans les logs** (au démarrage de l'API) :

```
Provider de paiement actif : SasPay (Softpay Mobile Money)
```

**✅ SI VOUS VOYEZ CE MESSAGE** : SasPay est actif !

**❌ SI VOUS VOYEZ "Chariow"** : Les variables Railway n'ont pas été prises en compte. Vérifier ACTION 3.

---

### ═══════════════════════════════════════════════════════════
### **ACTION 5 : Tester un paiement sandbox** 🧪
### ═══════════════════════════════════════════════════════════

**Pourquoi ?** Valider que tout fonctionne avant d'activer en production.

#### Option A : Via l'interface web (recommandé)

1. **Aller sur** : https://sur-check.vercel.app/ (ou votre URL Vercel)

2. **Se connecter** avec un compte test

3. **Aller sur** : `Compte` ou `Acheter des crédits`

4. **Sélectionner** : Pack 1 crédit (600 FCFA)

5. **Entrer** : Numéro de téléphone test MTN : `97505050`

6. **Cliquer** : `Payer`

7. **Observer** :
   - Vérifier que le checkout se crée
   - Vérifier dans les logs Railway : recherche de `network: mtn_bj`

#### Option B : Via curl (technique)

```bash
# 1. Obtenir un token JWT (remplacer EMAIL et PASSWORD)
TOKEN=$(curl -X POST https://surcheck-production.up.railway.app/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "votre_email@test.com", "password": "votre_password"}' \
  | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

# 2. Créer un checkout SasPay
curl -X POST https://surcheck-production.up.railway.app/api/v1/payment/checkout \
  -H "Authorization: Bearer $TOKEN" \
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
  "label": "Analyse unique"
}
```

**✅ SI `checkout_url` est `null`** : Parfait ! MTN push direct détecté.

---

### ═══════════════════════════════════════════════════════════
### **ACTION 6 : Simuler un paiement réussi** 💳
### ═══════════════════════════════════════════════════════════

**Pourquoi ?** Tester que les crédits sont bien ajoutés après paiement.

#### Étapes :

1. **Aller sur** : https://application.saspay.me/

2. **Chercher** : `Dashboard → Transactions` ou `Paiements`

3. **Trouver** le paiement que vous venez de créer (ACTION 5)

4. **Cliquer** dessus pour voir les détails

5. **Chercher** un bouton comme :
   - `Simuler succès` / `Mark as successful`
   - `Test webhook` / `Envoyer webhook`

6. **Cliquer** pour simuler le paiement réussi

7. **Vérifier dans Railway Logs** :

```
Webhook saspay reçu : event=successful.sale | sale=xxx | user=xxx
```

8. **Vérifier dans Supabase** :
   - Table `user_credits` : Solde +1 crédit
   - Table `payment_transactions` : Status `successful`, provider `saspay`

**✅ SI LE CRÉDIT EST AJOUTÉ** : Migration sandbox réussie !

---

### ═══════════════════════════════════════════════════════════
### **ACTION 7 : Passer en production** 🚀
### ═══════════════════════════════════════════════════════════

**Quand ?** Après avoir validé ACTION 6 avec succès.

**⚠️ ATTENTION** : À partir de maintenant, les paiements seront réels.

#### Étapes :

1. **Sur SasPay** : https://application.saspay.me/
   - Compléter le **KYC** (Know Your Customer) si pas déjà fait
   - Attendre validation (2-5 jours ouvrés)

2. **Générer clé Production** :
   - `Dashboard → API Keys`
   - Copier la clé **Live** : `sk_live_xxxxx` (vous l'avez déjà dans votre fichier `.env` local !)

3. **Créer webhook Production** :
   - Même processus qu'ACTION 2, mais sélectionner mode **Production**
   - Copier le nouveau secret production

4. **Mettre à jour Railway** :

```env
# ═══ SASPAY CONFIGURATION (PRODUCTION) ═══
PAYMENT_PROVIDER=saspay
SASPAY_API_KEY=sk_live_xxxxxxxxxxxxxxxxxxxxx  # Votre clé LIVE (voir fichier .env local)
SASPAY_BASE_URL=https://api.saspay.me/api/v1
SASPAY_WEBHOOK_SECRET=whsec_production_secret
```

5. **Surveiller** les premiers paiements :
   - Railway Logs : Vérifier `event=successful.sale`
   - Supabase : Vérifier crédits ajoutés
   - Taux de succès : Doit être ≥ 85%

---

### ═══════════════════════════════════════════════════════════
### **ROLLBACK D'URGENCE** 🆘
### ═══════════════════════════════════════════════════════════

**Si problème en production, retour immédiat vers Chariow :**

1. **Railway → Variables → RAW Editor**

2. **Modifier** :
```env
PAYMENT_PROVIDER=chariow
```

3. **Save** → Redéploiement automatique (< 2 minutes)

4. **Vérifier logs** : `Provider de paiement actif : Chariow`

**✅ Chariow reprend immédiatement** (aucun changement code nécessaire)

---

## 📊 RÉCAPITULATIF DES ACTIONS

| # | Action | Plateforme | Temps estimé | Critique |
|---|--------|------------|--------------|----------|
| 1 | Obtenir clé sandbox | application.saspay.me | 5 min | ⚠️ Oui |
| 2 | Configurer webhook | application.saspay.me | 5 min | ⚠️ Oui |
| 3 | Variables Railway | railway.app | 5 min | ⚠️ Oui |
| 4 | Vérifier activation | railway.app (logs) | 2 min | ✅ Validation |
| 5 | Tester checkout | Interface web ou curl | 5 min | ✅ Validation |
| 6 | Simuler paiement | application.saspay.me | 5 min | ✅ Validation |
| 7 | Production | application.saspay.me + railway.app | 10 min | 🚀 Final |

**Temps total** : ~35 minutes

---

## 🎯 CHECKLIST DE VALIDATION

Cochez au fur et à mesure :

- [ ] ACTION 1 : Clé sandbox obtenue (`sk_test_xxxxx`)
- [ ] ACTION 2 : Webhook configuré, secret copié
- [ ] ACTION 3 : Variables Railway mises à jour
- [ ] ACTION 4 : Logs Railway affichent "SasPay"
- [ ] ACTION 5 : Checkout créé avec succès
- [ ] ACTION 6 : Crédit ajouté après simulation paiement
- [ ] ACTION 7 : Production activée (KYC validé)
- [ ] Monitoring actif (taux succès surveillé)

---

## 📞 BESOIN D'AIDE ?

**Logs Railway ne montrent pas "SasPay" ?**
- Vérifier que `PAYMENT_PROVIDER=saspay` est bien dans les variables
- Forcer un redéploiement : `git commit --allow-empty -m "Force redeploy" && git push`

**Webhook signature invalide ?**
- Vérifier que `SASPAY_WEBHOOK_SECRET` correspond au secret du webhook
- Tester manuellement avec curl (voir MIGRATION_SASPAY.md FAQ Q5)

**Réseau non détecté ?**
- Vérifier les préfixes dans `saspay_provider.py` ligne 50-90
- Ajouter le préfixe manquant dans `mtn_prefixes` ou `moov_prefixes`

**Autre problème ?**
- Consulter : `MIGRATION_SASPAY.md` section "FAQ & Troubleshooting"
- Vérifier Railway logs détaillés
- Faire un rollback temporaire vers Chariow si bloquant

---

**📧 Support** : Tous les guides sont dans le repo (MIGRATION_SASPAY.md, SASPAY_API_ANALYSIS.md)

**🎉 Bonne migration !**
