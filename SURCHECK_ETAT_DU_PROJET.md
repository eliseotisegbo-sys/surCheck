# Rapport d'Activités — SûrCheck AI

## Dernière mise à jour : 2026-09-08

---

## 🔒 Phase 8 — Sécurité & Performance (Complète)

### Backend FastAPI
- **Rate Limiting** (`slowapi 0.1.10`) : Limiteur global 120 req/min par IP, désactivé en mode test automatisé (`TESTING=1`)
- **Security Headers Middleware** : `X-Content-Type-Options`, `X-Frame-Options: DENY`, `X-XSS-Protection`, `Referrer-Policy`, `Permissions-Policy`
- **HSTS** (`Strict-Transport-Security`) : Activé uniquement en `ENVIRONMENT=production` (max-age=63072000)
- **Swagger/Redoc désactivé** en production (`docs_url=None`, `redoc_url=None`, `openapi_url=None`)
- **CORS strict** : `CORS_ORIGINS` parseable depuis JSON en variable d'environnement Railway/Vercel
- `config.py` : `model_post_init` pour parser `CORS_ORIGINS` depuis env JSON ou CSV

### Frontend Next.js
- **Security Headers** dans `next.config.ts` : `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`, `Strict-Transport-Security`
- `API_BASE_URL` : Fallback propre sur `/api/v1` (rewrite Next.js) au lieu d'un hôte hardcodé
- `INTERNAL_API_URL` : Nouvelle variable d'env pour piloter le rewrite côté serveur

---

## 🚀 Phase 9 — Configuration & Déploiement (Complète)

### Fichiers de déploiement créés
| Fichier | Description |
|---|---|
| `apps/api/Dockerfile` | Image Python 3.12-slim avec tesseract-ocr-fra, healthcheck intégré |
| `apps/api/Procfile` | Commande de démarrage pour Railway/Heroku |
| `apps/api/railway.json` | Config Railway : Dockerfile builder, healthcheck sur `/health`, restart policy |
| `apps/web/vercel.json` | Config minimale Vercel (framework: nextjs) |
| `apps/web/.env.example` | Template des variables d'env pour Vercel |
| `DEPLOYMENT.md` | Guide de déploiement complet étape par étape |

### Architecture de production
```
[Utilisateur Bénin]
      ↓  HTTPS
[Vercel Edge Network]
  apps/web (Next.js 16)
      ↓  Rewrite /api/v1/:path*
[Railway Container]
  apps/api (FastAPI + Uvicorn)
  → Rate Limiting (SlowAPI)
  → Security Headers
  → CORS strict
      ↓
[Supabase PostgreSQL]
  + Auth, Storage, RLS

[Chariow Webhooks]  → /api/v1/payment/webhook
```

### Variables d'environnement à renseigner
**Railway (Backend)** :
- `ENVIRONMENT=production`
- `JWT_SECRET_KEY` (robuste, unique)
- `SUPABASE_SERVICE_ROLE_KEY`
- `CHARIOW_WEBHOOK_SECRET`
- `CORS_ORIGINS` (JSON array avec URL Vercel)
- `APP_URL` (URL Vercel)

**Vercel (Frontend)** :
- `INTERNAL_API_URL` (URL Railway)
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`

---

## ✅ Résultats Tests Finaux (Phase 8)

```
45 tests passés / 0 échecs
Platform: Python 3.12.1 / pytest 9.1.1
```

| Suite | Tests | Statut |
|---|---|---|
| `test_admin_moderation.py` | 3 | ✅ PASS |
| `test_api.py` | 9 | ✅ PASS |
| `test_chariow_credits.py` | 9 | ✅ PASS |
| `test_engine.py` | 24 | ✅ PASS |

---

## 📦 Commits Git

| Hash | Description |
|---|---|
| `7210d10` | `feat: Phase 6-7 — Chariow payment system, credits model & admin moderation panel` |
| *(en cours)* | `feat: Phase 8 — Sécurité renforcée, Rate Limiting, Security Headers & configuration déploiement` |

---

## 🔗 URLs de Production (à compléter après déploiement)

| Service | URL |
|---|---|
| Backend Railway | `https://_____.up.railway.app` |
| Frontend Vercel | `https://surcheck-ai.vercel.app` |
| Webhook Chariow | `https://_____.up.railway.app/api/v1/payment/webhook` |
| Swagger (dev only) | `http://localhost:8000/docs` |
