# 🚀 Guide de Déploiement Production — SûrCheck AI

Ce guide détaille pas-à-pas le déploiement de **SûrCheck AI** en production avec une architecture robuste, sécurisée et économique :
- **Backend (FastAPI)** : Déployé sur **[Railway](https://railway.app)** (ou **Render** / **Koyeb**) via Dockerfile.
- **Frontend (Next.js)** : Déployé sur **[Vercel](https://vercel.com)** (connecté à votre GitHub).
- **Base de données & Auth** : **[Supabase](https://supabase.com)** (PostgreSQL managé).
- **Paiements & Webhooks** : **[Chariow](https://chariow.com)** (Checkout Mobile Money & Cartes).

---

## 📋 Prérequis

1. Votre dépôt GitHub : `https://github.com/eliseotisegbo-sys/surCheck`
2. Votre compte **Vercel** (déjà connecté à GitHub)
3. Un compte **Railway** (ou Render) gratuit

---

## Étape 1 : Déploiement du Backend FastAPI (Railway)

### 1.1 Création du service sur Railway
1. Rendez-vous sur **[railway.app](https://railway.app)** et connectez-vous avec GitHub.
2. Cliquez sur **« + New Project »** -> **« Deploy from GitHub repo »**.
3. Sélectionnez le dépôt `eliseotisegbo-sys/surCheck`.
4. Dans les paramètres de configuration du service (**Settings**) :
   - **Root Directory** : `apps/api`
   - **Builder** : `Dockerfile` (Railway détecte automatiquement `apps/api/Dockerfile`)
5. Dans l'onglet **Networking** :
   - Cliquez sur **« Generate Domain »** (vous obtiendrez une URL du type `https://surcheck-api-production.up.railway.app`).

### 1.2 Variables d'environnement Backend (Railway -> Variables)
Ajoutez les variables suivantes dans l'onglet **Variables** de votre service Railway :

```env
ENVIRONMENT=production
VERSION=v1.0.0
PROJECT_NAME=SûrCheck AI API
API_PREFIX=/api/v1

# CORS - Ajoutez votre URL Vercel ici dès qu'elle est connue
CORS_ORIGINS=["https://surcheck-ai.vercel.app","http://localhost:3000"]

# Supabase
SUPABASE_URL=https://lhxbzflectkuysaklvji.supabase.co
SUPABASE_ANON_KEY=sb_publishable_59E__jIIWr3HRG3XkV4Rcg_U0KZdYNH
SUPABASE_SERVICE_ROLE_KEY=votre_cle_service_role_supabase_ici

# Sécurité & Hachage
PHONE_HASH_SALT=surcheck_bj_secure_salt_2026_antigravity_trust
JWT_SECRET_KEY=cle_secrete_ultra_robuste_surcheck_jwt_prod_2026

# Chariow (Paiement & Webhook)
CHARIOW_API_KEY=sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7
CHARIOW_BASE_URL=https://api.chariow.com/v1
CHARIOW_WEBHOOK_SECRET=votre_secret_webhook_chariow_ici

# Identifiants produits Chariow
CHARIOW_PRODUCT_PACK_1=prd_pack_1
CHARIOW_PRODUCT_PACK_5=prd_pack_5
CHARIOW_PRODUCT_PACK_10=prd_pack_10
CHARIOW_PRODUCT_PACK_25=prd_pack_25

# Tarifs FCFA
CREDIT_PACK_1_FCFA=600
CREDIT_PACK_5_FCFA=1500
CREDIT_PACK_10_FCFA=2500
CREDIT_PACK_25_FCFA=5000

# URL publique du frontend (redirection post-paiement)
APP_URL=https://surcheck-ai.vercel.app
```

---

## Étape 2 : Déploiement du Frontend Next.js (Vercel)

### 2.1 Importation du projet sur Vercel
1. Rendez-vous sur **[vercel.com/dashboard](https://vercel.com/dashboard)**.
2. Cliquez sur **« Add New... »** -> **« Project »**.
3. Sélectionnez le dépôt `eliseotisegbo-sys/surCheck` et cliquez sur **« Import »**.
4. Configurez les options suivantes :
   - **Framework Preset** : `Next.js`
   - **Root Directory** : Cliquez sur `Edit` et sélectionnez **`apps/web`**
   - **Build Command** : Laisser par défaut (`next build`)
   - **Output Directory** : Laisser par défaut (`.next`)

### 2.2 Variables d'environnement Frontend (Vercel -> Environment Variables)
Ajoutez les variables suivantes dans la section **Environment Variables** avant de cliquer sur **« Deploy »** :

| Variable | Valeur recommandée |
|---|---|
| `NEXT_PUBLIC_APP_NAME` | `SûrCheck AI` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://lhxbzflectkuysaklvji.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `sb_publishable_59E__jIIWr3HRG3XkV4Rcg_U0KZdYNH` |
| `INTERNAL_API_URL` | `https://votre-backend-railway.up.railway.app` *(URL obtenue à l'étape 1)* |
| `NEXT_PUBLIC_API_URL` | `/api/v1` *(utilise le rewrite sécurisé Next.js)* |

5. Cliquez sur **« Deploy »**. Votre site sera en ligne en moins de 2 minutes sur une URL du type `https://surcheck-ai.vercel.app`.

---

## Étape 3 : Configuration du Webhook Chariow

Dès que votre backend Railway est en ligne :
1. Connectez-vous sur votre tableau de bord **[Chariow](https://chariow.com)**.
2. Allez dans **Paramètres** -> **Webhooks** (ou **Pulses**).
3. Ajoutez l'URL de votre webhook de production :
   ```
   https://votre-backend-railway.up.railway.app/api/v1/payment/webhook
   ```
4. Événement à écouter : `sale.successful` (ou `sale.completed`).
5. Récupérez la clé secrète du webhook et renseignez-la dans `CHARIOW_WEBHOOK_SECRET` sur Railway.

---

## Étape 4 : Vérification Finale en Ligne

1. **Santé de l'API** :
   Visitez `https://votre-backend-railway.up.railway.app/health` -> doit répondre `{"status": "healthy"}`.
2. **Frontend** :
   Visitez `https://votre-app-vercel.vercel.app` -> vérifiez l'interface d'analyse et les packs de paiement.
3. **Sécurité** :
   Les en-têtes CSP, HSTS, X-Frame-Options et le Rate Limiting (SlowAPI) sont actifs automatiquement.
