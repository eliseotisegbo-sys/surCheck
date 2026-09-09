# 🚀 Guide de Déploiement Production — SûrCheck AI

Architecture de production :
- **Backend (FastAPI)** → **[Railway](https://railway.app)** via Dockerfile
- **Frontend (Next.js)** → **[Vercel](https://vercel.com)** (connecté à GitHub)
- **Base de données & Auth** → **[Supabase](https://supabase.com)** (déjà configuré)
- **Paiements & Webhooks** → **[Chariow](https://chariow.com)**

---

## 📋 Prérequis

- Dépôt GitHub : `https://github.com/eliseotisegbo-sys/surCheck`
- Compte **Vercel** (déjà connecté à GitHub ✅)
- Compte **Railway** (inscription gratuite sur railway.app)

---

## Étape 1 — Backend FastAPI sur Railway

### 1.1 Créer le service
1. Aller sur **[railway.app](https://railway.app)** → **New Project** → **Deploy from GitHub repo**
2. Sélectionner `eliseotisegbo-sys/surCheck`
3. Dans **Settings** du service :
   - **Root Directory** : `apps/api`
   - **Builder** : `Dockerfile` (auto-détecté depuis `apps/api/Dockerfile`)
4. Dans **Networking** → **Generate Domain** → noter l'URL générée

### 1.2 Variables d'environnement Railway

> **Méthode rapide** : dans Railway → Variables → cliquer sur **RAW Editor** et coller le bloc ci-dessous.

Ouvrir le fichier [`.env.example`](file:///c:/SûrCheck/.env.example), copier la **Section 1** et remplacer les 3 valeurs marquées `<<CHANGER>>` :

| Variable | Où trouver la valeur |
|---|---|
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → **service_role** |
| `DATABASE_URL` | Supabase → Settings → Database → **Transaction Pooler** (port 6543) |
| `JWT_SECRET_KEY` | Générer sur [randomkeygen.com](https://randomkeygen.com) → "256-bit WEP Keys" |

```env
ENVIRONMENT=production
VERSION=v1.0.0
API_PREFIX=/api/v1
CORS_ORIGINS=["https://surcheck-ai.vercel.app","https://surcheck.bj"]
APP_URL=https://surcheck-ai.vercel.app
SUPABASE_URL=https://lhxbzflectkuysaklvji.supabase.co
SUPABASE_ANON_KEY=sb_publishable_59E__jIIWr3HRG3XkV4Rcg_U0KZdYNH
SUPABASE_SERVICE_ROLE_KEY=<<VOTRE_CLE_SERVICE_ROLE_SUPABASE>>
DATABASE_URL=postgresql://postgres.lhxbzflectkuysaklvji:<<VOTRE_MOT_DE_PASSE_DB>>@aws-0-eu-west-3.pooler.supabase.com:6543/postgres
JWT_SECRET_KEY=<<GENERER_CLE_64_CHARS_ALEATOIRE>>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
PHONE_HASH_SALT=surcheck_bj_secure_salt_2026_antigravity_trust
CHARIOW_API_KEY=sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7
CHARIOW_BASE_URL=https://api.chariow.com/v1
CHARIOW_WEBHOOK_SECRET=whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz
CHARIOW_PRODUCT_PACK_1=prd_ltwqdexr
CHARIOW_PRODUCT_PACK_5=prd_c7ju43kh
CHARIOW_PRODUCT_PACK_10=prd_060n1o9q
CHARIOW_PRODUCT_PACK_25=prd_9v1hutfu
CREDIT_PACK_1_FCFA=600
CREDIT_PACK_5_FCFA=1500
CREDIT_PACK_10_FCFA=2500
CREDIT_PACK_25_FCFA=5000
```

---

## Étape 2 — Frontend Next.js sur Vercel

### 2.1 Importer le projet
1. Aller sur **[vercel.com/dashboard](https://vercel.com/dashboard)** → **Add New... → Project**
2. Importer `eliseotisegbo-sys/surCheck`
3. Configurer :
   - **Root Directory** → cliquer `Edit` → sélectionner **`apps/web`**
   - **Framework Preset** : `Next.js` (auto-détecté)
   - **Build Command** : `next build --webpack` *(important pour compatibilité)*

### 2.2 Variables d'environnement Vercel

Dans **Environment Variables** (avant de cliquer Deploy), ajouter ces 5 variables :

| Variable | Valeur |
|---|---|
| `INTERNAL_API_URL` | `https://<<URL_RAILWAY>>.up.railway.app` *(URL obtenue à l'étape 1.1)* |
| `NEXT_PUBLIC_API_URL` | `/api/v1` |
| `NEXT_PUBLIC_APP_NAME` | `SûrCheck AI` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://lhxbzflectkuysaklvji.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `sb_publishable_59E__jIIWr3HRG3XkV4Rcg_U0KZdYNH` |

4. Cliquer **Deploy** → site en ligne en ~2 min.

---

## Étape 3 — Webhook Chariow (déjà configuré ✅)

Le secret `CHARIOW_WEBHOOK_SECRET` est déjà renseigné dans le `.env.example`.

Si Railway vous attribue une nouvelle URL, mettre à jour dans **app.chariow.com → Pulses → votre webhook** :
```
https://<<URL_RAILWAY>>.up.railway.app/api/v1/payment/webhook
```

---

## Étape 4 — Mettre à jour CORS après déploiement Vercel

Une fois l'URL Vercel connue (ex: `https://surcheck-xyz.vercel.app`) :
1. Sur Railway → Variables → modifier `CORS_ORIGINS` :
   ```json
   ["https://surcheck-xyz.vercel.app","https://surcheck.bj"]
   ```
2. Railway redémarre automatiquement le service.

---

## Étape 5 — Vérifications finales

```bash
# 1. Santé API
curl https://<<URL_RAILWAY>>.up.railway.app/health
# → {"status":"healthy","engine_version":"v1.0.0","environment":"production"}

# 2. Packs disponibles
curl https://<<URL_RAILWAY>>.up.railway.app/api/v1/payment/packs
# → {"packs":[{"id":"pack_1","credits":1,"amount_fcfa":600,...},...]}
```

| Point de contrôle | URL |
|---|---|
| Santé API | `https://<<URL_RAILWAY>>.up.railway.app/health` |
| Frontend | `https://surcheck-ai.vercel.app` |
| Swagger *(dev uniquement)* | `http://localhost:8000/docs` |
| Packs crédits | `https://<<URL_RAILWAY>>.up.railway.app/api/v1/payment/packs` |

> **Note** : Swagger/Redoc sont automatiquement désactivés en `ENVIRONMENT=production`.

---

## ✅ Récapitulatif des secrets à renseigner

| # | Variable | Source |
|---|---|---|
| 1 | `SUPABASE_SERVICE_ROLE_KEY` | Supabase → Settings → API → service_role |
| 2 | `DATABASE_URL` (mot de passe) | Supabase → Settings → Database → Transaction Pooler |
| 3 | `JWT_SECRET_KEY` | Générer sur randomkeygen.com |
| 4 | `INTERNAL_API_URL` | URL Railway générée à l'étape 1.1 |

**Tous les autres champs sont déjà pré-remplis dans [`.env.example`](file:///c:/SûrCheck/.env.example).**
