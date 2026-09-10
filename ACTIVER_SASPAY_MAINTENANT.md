# ⚡ ACTIVER SASPAY MAINTENANT - GUIDE RAPIDE

**Durée** : 5 minutes  
**URL Railway** : https://surcheck.up.railway.app

---

## 📋 ÉTAPE 1 : COPIER VOS CLÉS (30 secondes)

Ouvrez votre fichier `.env` local et **copiez ces 2 valeurs** :

- Ligne `SASPAY_API_KEY` : `sk_live_xxxxxxxxxxxxx`
- Ligne `SASPAY_WEBHOOK_SECRET` : `xxxxxxxxxxxxx`

**Gardez ces valeurs sous la main** (dans un notepad temporaire).

---

## 🚂 ÉTAPE 2 : CONFIGURER RAILWAY (3 minutes)

### 2.1 Ouvrir Railway

1. Aller sur https://railway.app/
2. Cliquer sur votre projet **SûrCheck AI**
3. Cliquer sur le service **Backend** (FastAPI)
4. Cliquer sur l'onglet **Variables**
5. Cliquer sur **RAW Editor** (en haut à droite)

### 2.2 Ajouter les variables

**Faire défiler tout en bas** et **coller ces lignes** (remplacer les `<...>` par vos vraies valeurs) :

```env
PAYMENT_PROVIDER=saspay
SASPAY_API_KEY=<COLLER_VOTRE_CLE_ICI>
SASPAY_BASE_URL=https://api.saspay.me/api/v1
SASPAY_WEBHOOK_SECRET=<COLLER_VOTRE_SECRET_ICI>
```

### 2.3 Sauvegarder

1. Cliquer **Update Variables** (ou **Save**)
2. **Attendre 60 secondes** (redéploiement automatique)

---

## ✅ ÉTAPE 3 : VÉRIFIER L'ACTIVATION (1 minute)

### 3.1 Ouvrir les logs

1. Sur Railway, cliquer sur **Deployments**
2. Cliquer sur le dernier déploiement (en haut)
3. Cliquer **View Logs**

### 3.2 Chercher ce message

```
Provider de paiement actif : SasPay (Softpay Mobile Money)
```

**✅ Vous voyez ce message ?**  
→ **C'EST BON ! SasPay est actif !**

**❌ Vous voyez "Chariow" ?**  
→ Revérifier l'ÉTAPE 2.2 : `PAYMENT_PROVIDER=saspay` bien présent ?

---

## 🧪 ÉTAPE 4 : TESTER (Optionnel mais recommandé)

1. Aller sur https://sur-check.vercel.app/
2. Se connecter
3. Acheter un pack (le plus petit : 600 FCFA)
4. Entrer votre numéro MTN
5. Valider le paiement sur votre téléphone
6. Vérifier que le crédit est ajouté ✅

---

## 🎉 C'EST FAIT !

**SasPay est maintenant actif sur votre projet !**

Tous les nouveaux paiements utilisent SasPay.

---

## 🆘 POUR REVENIR À CHARIOW

Si problème, retour en 1 minute :

1. Railway → Variables → RAW Editor
2. Changer : `PAYMENT_PROVIDER=chariow`
3. Save → Attendre 60 secondes

✅ Chariow reprend immédiatement

---

## 📊 CE QUI A CHANGÉ

**AVANT** :
- Paiements → Chariow
- Réseaux : MTN, Moov

**MAINTENANT** :
- Paiements → SasPay
- Réseaux : MTN, Moov, Wave, Orange Money, Djamo

**Frontend (Vercel)** : Aucun changement, fonctionne automatiquement ✅

---

## 📚 DOCUMENTATION COMPLÈTE

- **BASCULEMENT_CHARIOW_VERS_SASPAY.md** : Guide détaillé complet
- **MIGRATION_SASPAY.md** : Guide technique approfondi
- **ACTIONS_REQUISES_PRODUCTION.md** : Checklist exhaustive

---

**⚡ Commencez maintenant : ÉTAPE 1 !**
