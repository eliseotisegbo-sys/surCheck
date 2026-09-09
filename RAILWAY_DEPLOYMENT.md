# 🚂 Guide de déploiement Railway - Backend FastAPI SûrCheck AI

Ce guide vous accompagne étape par étape pour déployer le backend FastAPI sur Railway.

---

## 📋 Prérequis

### ✅ Avant de commencer, assurez-vous d'avoir :

- [x] Un compte GitHub avec le repo `eliseotisegbo-sys/surCheck`
- [x] Un compte Railway (gratuit) → [railway.app](https://railway.app)
- [x] Les 3 secrets Supabase récupérés :
  - `SUPABASE_SERVICE_ROLE_KEY`
  - `DATABASE_URL` (avec mot de passe)
  - `JWT_SECRET_KEY` (généré)

### 🔑 Récupération des secrets Supabase

#### 1. SUPABASE_SERVICE_ROLE_KEY

1. Allez sur [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Sélectionnez votre projet : **lhxbzflectkuysaklvji**
3. Menu gauche → **⚙️ Settings** → **API**
4. Section **"Project API keys"** → Cherchez **`service_role`**
5. Cliquez sur **👁️ Reveal** → Copiez la clé (commence par `eyJ...`)

⚠️ **IMPORTANT** : Cette clé donne un accès administrateur complet à votre base de données. Ne la partagez jamais publiquement.

#### 2. DATABASE_URL

1. Même projet Supabase → **⚙️ Settings** → **Database**
2. Section **"Connection Pooling"** (Transaction mode)
3. Copiez la **Connection string** avec port **6543**
4. Format : `postgresql://postgres.lhxbzflectkuysaklvji:[PASSWORD]@aws-0-eu-west-3.pooler.supabase.com:6543/postgres`

**Note** : Le mot de passe contient des caractères spéciaux encodés en URL (`%2F`, `%25`, etc.)

#### 3. JWT_SECRET_KEY

Générez une clé aléatoire forte (64 caractères minimum) :

**Méthode 1 : Site web**
- Allez sur [https://randomkeygen.com](https://randomkeygen.com)
- Section **"Fort Knox Passwords"** → Copiez une clé

**Méthode 2 : Ligne de commande**
```bash
# Sur Linux/Mac/WSL
openssl rand -hex 32

# Sur Windows PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 64 | ForEach-Object {[char]$_})
```

---

## 🚀 Étape 1 : Créer le projet Railway

### 1.1 Connexion et création

1. Allez sur **[https://railway.app](https://railway.app)**
2. Cliquez sur **"Login"** → Connectez-vous avec GitHub
3. Cliquez sur **"New Project"** (bouton violet en haut à droite)
4. Sélectionnez **"Deploy from GitHub repo"**
5. Recherchez et sélectionnez : **`eliseotisegbo-sys/surCheck`**
6. Railway va détecter le repo et créer un service

### 1.2 Confirmation

Railway va afficher :
```
✓ Repository connected
✓ Service created: surCheck
⏳ Waiting for configuration...
```

**Ne vous inquiétez pas si le premier build échoue** - c'est normal, nous devons configurer le Root Directory.

---

## ⚙️ Étape 2 : Configurer le service (CRUCIAL)

### 2.1 Accéder aux paramètres

1. Dans Railway, cliquez sur le **service créé** (carte avec le nom du repo)
2. En haut à droite, cliquez sur **"Settings"** (⚙️)

### 2.2 Configurer le Root Directory

**C'est LA configuration la plus importante !**

1. Dans Settings, cherchez la section **"Root Directory"**
2. Par défaut, c'est **`/`** (racine) ❌
3. Cliquez sur **"Configure"** ou le champ de saisie
4. Tapez : **`apps/api`** ✅
5. Appuyez sur **Entrée** ou cliquez en dehors pour sauvegarder

**Pourquoi ?** Railway doit savoir où se trouve le Dockerfile. Sans cette configuration, il analyse la racine du monorepo et ne trouve pas l'application Python.

### 2.3 Vérifier le Builder

1. Toujours dans Settings, cherchez **"Builder"** ou **"Build Method"**
2. Doit être : **"Dockerfile"** ✅
3. Si c'est différent, sélectionnez **"Dockerfile"** dans la liste

### 2.4 Configuration du port (optionnel)

Railway détecte automatiquement le port 8000 depuis le Dockerfile, mais vous pouvez le vérifier :

1. Settings → Section **"Networking"** ou **"Port"**
2. Vérifiez : **Port 8000** ✅

---

## 🔐 Étape 3 : Ajouter les variables d'environnement

### 3.1 Accéder à l'éditeur de variables

1. Dans Railway, cliquez sur l'onglet **"Variables"** (en haut)
2. Cliquez sur **"RAW Editor"** (en haut à droite)

Le RAW Editor permet de coller toutes les variables en une seule fois.

### 3.2 Copier-coller les variables

**Copiez ce bloc complet et collez-le dans le RAW Editor :**

```env
ENVIRONMENT=production
VERSION=v1.0.0
API_PREFIX=/api/v1
CORS_ORIGINS=["https://sur-check.vercel.app","https://surcheck.bj"]
APP_URL=https://sur-check.vercel.app
SUPABASE_URL=https://lhxbzflectkuysaklvji.supabase.co
SUPABASE_ANON_KEY=sb_publishable_59E__jIIWr3HRG3XkV4Rcg_U0KZdYNH
SUPABASE_SERVICE_ROLE_KEY=VOTRE_CLE_SERVICE_ROLE_ICI
DATABASE_URL=postgresql://postgres.lhxbzflectkuysaklvji:ZP%2FdttG%25u4RUYZx@aws-0-eu-west-3.pooler.supabase.com:6543/postgres
JWT_SECRET_KEY=VOTRE_CLE_JWT_ALEATOIRE_ICI
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

### 3.3 Remplacer les secrets

**Modifiez ces 2 lignes avec vos vrais secrets :**

1. Remplacez `VOTRE_CLE_SERVICE_ROLE_ICI` par votre `SUPABASE_SERVICE_ROLE_KEY`
2. Remplacez `VOTRE_CLE_JWT_ALEATOIRE_ICI` par votre `JWT_SECRET_KEY` générée

### 3.4 Sauvegarder

1. Cliquez sur **"Save"** ou **"Update Variables"**
2. Railway va automatiquement redémarrer le service avec les nouvelles variables

---

## 🌐 Étape 4 : Générer le domaine public

### 4.1 Activer le domaine

1. Dans Railway, onglet **"Settings"**
2. Cherchez la section **"Networking"** ou **"Domains"**
3. Cliquez sur **"Generate Domain"**

Railway va créer une URL publique comme :
```
https://surcheck-production-xxxx.up.railway.app
```

### 4.2 Noter l'URL

**⚠️ IMPORTANT : NOTEZ CETTE URL !**

Vous en aurez besoin pour :
- Configurer Vercel (`INTERNAL_API_URL`)
- Configurer le webhook Chariow

**Exemple :**
```
https://surcheck-production-abc123.up.railway.app
```

---

## 📦 Étape 5 : Déploiement automatique

### 5.1 Lancement du build

Railway va automatiquement :
1. Cloner le repo GitHub
2. Détecter le Dockerfile dans `apps/api/`
3. Builder l'image Docker
4. Démarrer le conteneur sur le port 8000

### 5.2 Suivre le build

1. Onglet **"Deployments"** (en haut)
2. Vous verrez le build en cours avec les logs en temps réel

**Logs attendus :**
```
Cloning repository...
Building Docker image...
Step 1/10 : FROM python:3.12-slim
Step 2/10 : ENV PYTHONDONTWRITEBYTECODE=1
...
Successfully built image
Starting service...
✓ Service is running on port 8000
```

### 5.3 Vérifier le statut

Le déploiement doit afficher :
- **Status** : ✅ Active
- **Health** : ✅ Healthy (si healthcheck configuré)

**Temps de build estimé** : 3-5 minutes (première fois), 1-2 minutes (builds suivants)

---

## ✅ Étape 6 : Vérifier que l'API fonctionne

### 6.1 Test de santé (Health Check)

Ouvrez votre navigateur ou utilisez `curl` :

```bash
curl https://[VOTRE_URL_RAILWAY]/health
```

**Réponse attendue :**
```json
{
  "status": "healthy",
  "engine_version": "v1.0.0",
  "environment": "production"
}
```

### 6.2 Test des packs de crédits

```bash
curl https://[VOTRE_URL_RAILWAY]/api/v1/payment/packs
```

**Réponse attendue :**
```json
{
  "packs": [
    {
      "id": "pack_1",
      "credits": 1,
      "amount_fcfa": 600,
      "label": "Analyse unique",
      "unit_price": 600,
      "description": "1 analyse complète immédiate"
    },
    ...
  ]
}
```

### 6.3 Test de la documentation API (dev uniquement)

En production, Swagger est désactivé pour la sécurité.

Si vous voulez tester localement :
```bash
cd apps/api
python -m uvicorn src.main:app --reload
```

Puis ouvrez : http://localhost:8000/docs

---

## 🔄 Étape 7 : Configuration du webhook Chariow

### 7.1 Connexion à Chariow

1. Allez sur [https://app.chariow.com](https://app.chariow.com)
2. Connectez-vous avec votre compte
3. Menu gauche → **"Pulses"** (Webhooks)

### 7.2 Configurer le webhook existant

1. Trouvez le webhook SûrCheck (si déjà créé)
2. Cliquez dessus pour l'éditer
3. **URL du webhook** : Remplacez par votre URL Railway :

```
https://[VOTRE_URL_RAILWAY]/api/v1/payment/webhook
```

**Exemple complet :**
```
https://surcheck-production-abc123.up.railway.app/api/v1/payment/webhook
```

4. **Secret** : Doit être `whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz`
5. **Events** : Sélectionnez `checkout.completed`
6. Cliquez sur **"Save"** ou **"Update"**

### 7.3 Tester le webhook (optionnel)

Chariow permet de tester les webhooks :
1. Dans la configuration du webhook, cliquez sur **"Send test event"**
2. Vérifiez les logs Railway pour voir la requête reçue

---

## 🔐 Étape 8 : Mise à jour CORS sur Railway (après déploiement Vercel)

Une fois que Vercel vous donne l'URL finale (ex: `https://sur-check.vercel.app`), mettez à jour le CORS :

1. Railway → Variables
2. Modifiez `CORS_ORIGINS` :

```json
["https://sur-check.vercel.app","https://surcheck.bj"]
```

3. Sauvegardez → Railway redémarre automatiquement

---

## 📊 Monitoring et logs

### Voir les logs en temps réel

1. Railway → Onglet **"Deployments"**
2. Cliquez sur le déploiement actif
3. Les logs s'affichent en temps réel

### Logs utiles pour le débogage

**Recherchez ces messages :**
- ✅ `Application startup complete` → API démarrée
- ✅ `Uvicorn running on http://0.0.0.0:8000` → Serveur lancé
- ❌ `ModuleNotFoundError` → Dépendance manquante
- ❌ `Connection refused` → Problème de connexion DB

### Redémarrer le service

Si besoin de redémarrer manuellement :
1. Railway → Service
2. Menu **3 points (...)** → **"Restart"**

---

## 🐛 Dépannage

### Erreur : "Railpack could not determine how to build the app"

**Cause** : Root Directory non configuré

**Solution** :
1. Settings → Root Directory → `apps/api`
2. Redéployer

### Erreur : "Module not found: psycopg2"

**Cause** : Dépendances non installées

**Solution** : Vérifiez `apps/api/requirements.txt` contient `psycopg2-binary>=2.9.9`

### Erreur : "Connection to database failed"

**Cause** : `DATABASE_URL` incorrecte ou Supabase inaccessible

**Solution** :
1. Vérifiez `DATABASE_URL` dans les variables Railway
2. Testez la connexion depuis Supabase Dashboard → Database → Connection

### Erreur : "Port 8000 already in use"

**Cause** : Conflit de port (ne devrait pas arriver sur Railway)

**Solution** : Railway gère automatiquement les ports via la variable `$PORT`

### Le build est lent

**Normal** : Le premier build prend 3-5 minutes (installation des dépendances Python + tesseract-ocr)

**Builds suivants** : 1-2 minutes (cache Docker)

---

## 📈 Optimisations post-déploiement

### 1. Activer le cache Docker

Railway active automatiquement le cache Docker pour accélérer les builds.

### 2. Configurer les variables d'échelle

Railway Free Plan :
- 1 réplica
- 512 MB RAM
- Partagé CPU

Pour scaler :
1. Settings → **"Resources"**
2. Augmentez RAM/CPU si nécessaire (plans payants)

### 3. Configurer les health checks

Railway détecte automatiquement le healthcheck depuis le Dockerfile :
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

### 4. Monitoring des métriques

Railway Dashboard → Onglet **"Metrics"** :
- CPU usage
- Memory usage
- Network I/O
- Request count

---

## 🔒 Sécurité

### Secrets sensibles

**Ces variables ne doivent JAMAIS être commitées dans Git :**
- ✅ Configurées dans Railway Variables uniquement
- ❌ Jamais dans le code source

**Variables critiques :**
- `SUPABASE_SERVICE_ROLE_KEY`
- `JWT_SECRET_KEY`
- `DATABASE_URL` (contient le mot de passe)
- `CHARIOW_WEBHOOK_SECRET`

### HTTPS automatique

Railway fournit automatiquement :
- ✅ Certificat SSL gratuit
- ✅ HTTPS activé par défaut
- ✅ HTTP → HTTPS redirect

### Rate limiting

L'API inclut `slowapi` pour le rate limiting :
- 120 requêtes/minute par IP
- Désactivé en mode test

---

## ✅ Checklist finale

Avant de passer à Vercel, vérifiez :

- [ ] Build Railway réussi ✅
- [ ] Service en statut "Active" ✅
- [ ] Domaine public généré et noté ✅
- [ ] Test `/health` retourne 200 ✅
- [ ] Test `/api/v1/payment/packs` retourne les packs ✅
- [ ] Webhook Chariow configuré avec l'URL Railway ✅
- [ ] Variables d'environnement complètes ✅
- [ ] Logs Railway sans erreur ✅

---

## 🎯 Prochaine étape

Une fois Railway déployé avec succès, passez à **VERCEL_DEPLOYMENT.md** pour connecter le frontend au backend.

**URL Railway à utiliser dans Vercel :**
```
https://[VOTRE_URL_RAILWAY]
```

---

## 📞 Support Railway

**Documentation officielle :**
- [https://docs.railway.app](https://docs.railway.app)

**Support communautaire :**
- Discord Railway : [https://discord.gg/railway](https://discord.gg/railway)

**Problèmes techniques :**
- GitHub Issues : [https://github.com/railwayapp/railway/issues](https://github.com/railwayapp/railway/issues)

---

_Dernière mise à jour : 2025-01-09_
