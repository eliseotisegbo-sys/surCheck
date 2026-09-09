# ▲ Guide de déploiement Vercel - Frontend Next.js SûrCheck AI

Ce guide vous accompagne étape par étape pour déployer et configurer le frontend Next.js sur Vercel.

---

## 📋 Prérequis

### ✅ Avant de commencer, assurez-vous d'avoir :

- [x] Un compte GitHub avec le repo `eliseotisegbo-sys/surCheck`
- [x] Un compte Vercel (gratuit) → [vercel.com](https://vercel.com)
- [x] Le fichier `.gitignore` corrigé (fichiers `lib/` versionnés)
- [x] Les fichiers `apps/web/src/lib/*.ts` pushés sur GitHub
- [ ] L'URL Railway du backend (optionnel pour démarrer)

### 📦 Structure du projet

```
surCheck/
├── apps/
│   ├── web/           ← Frontend Next.js (à déployer sur Vercel)
│   │   ├── src/
│   │   │   ├── app/   ← Pages Next.js App Router
│   │   │   └── lib/   ← Modules (auth, api, engine, supabase)
│   │   ├── package.json
│   │   ├── next.config.ts
│   │   └── vercel.json
│   └── api/           ← Backend FastAPI (déjà sur Railway)
└── .gitignore         ← Corrigé pour ne pas ignorer lib/
```

---

## 🚀 Étape 1 : Importer le projet sur Vercel

### 1.1 Connexion à Vercel

1. Allez sur **[https://vercel.com](https://vercel.com)**
2. Cliquez sur **"Sign Up"** ou **"Log In"**
3. Sélectionnez **"Continue with GitHub"**
4. Autorisez Vercel à accéder à vos repos GitHub

### 1.2 Créer un nouveau projet

1. Une fois connecté, cliquez sur **"Add New..."** → **"Project"** (en haut à droite)
2. Section **"Import Git Repository"**
3. Recherchez : **`eliseotisegbo-sys/surCheck`**
4. Cliquez sur **"Import"** à côté du repo

### 1.3 Configuration initiale du projet

Vercel va afficher l'écran de configuration. **NE CLIQUEZ PAS ENCORE SUR "DEPLOY"** !

Nous devons d'abord configurer :
- Le Root Directory
- Les variables d'environnement
- Les paramètres de build

---

## ⚙️ Étape 2 : Configurer le projet (CRUCIAL)

### 2.1 Nom du projet

En haut de l'écran de configuration :

1. **Project Name** : `sur-check` (ou le nom que vous préférez)
2. Ce nom déterminera l'URL : `https://sur-check.vercel.app`

### 2.2 Framework Preset

Vercel détecte automatiquement Next.js, mais vérifiez :

1. Section **"Framework Preset"**
2. Doit afficher : **Next.js** ✅
3. Si différent, sélectionnez **Next.js** dans la liste

### 2.3 Root Directory (LE PLUS IMPORTANT)

**C'est LA configuration critique qui résout l'erreur 404 !**

1. Cherchez la section **"Root Directory"**
2. Par défaut, c'est **`./`** (racine) ❌
3. Cliquez sur **"Edit"** à côté
4. Dans la liste des dossiers, sélectionnez : **`apps/web`** ✅
5. Validez

**Pourquoi ?** Vercel doit savoir où se trouve l'application Next.js dans le monorepo. Sans cette configuration, il cherche à la racine et ne trouve pas `package.json`, d'où l'erreur 404.

### 2.4 Build & Development Settings

Vérifiez ces paramètres (normalement détectés automatiquement) :

| Paramètre | Valeur | Modification |
|-----------|--------|--------------|
| **Build Command** | `next build --webpack` ou laisser vide | ✅ OK |
| **Output Directory** | `.next` ou laisser vide | ✅ OK |
| **Install Command** | `npm install` ou laisser vide | ✅ OK |
| **Development Command** | `next dev --webpack` ou laisser vide | ✅ OK |

**Note** : Vous pouvez laisser tous ces champs vides, Vercel utilisera les commandes du `package.json`.

---

## 🔐 Étape 3 : Ajouter les variables d'environnement

### 3.1 Accéder à la section Environment Variables

Sur l'écran de configuration du projet (avant le premier déploiement) :

1. Cherchez la section **"Environment Variables"**
2. Vous verrez un formulaire pour ajouter des variables une par une

### 3.2 Ajouter les 5 variables essentielles

**Variable 1 : INTERNAL_API_URL**

- **Key** : `INTERNAL_API_URL`
- **Value** : `https://votre-url-railway.up.railway.app` (remplacez par votre URL Railway)
- **Environments** : Cochez **Production**, **Preview**, **Development**
- Cliquez sur **"Add"**

⚠️ **Si vous n'avez pas encore déployé Railway** :
- Mettez temporairement : `http://localhost:8000`
- Vous pourrez la changer plus tard

**Variable 2 : NEXT_PUBLIC_API_URL**

- **Key** : `NEXT_PUBLIC_API_URL`
- **Value** : `/api/v1`
- **Environments** : Cochez **Production**, **Preview**, **Development**
- Cliquez sur **"Add"**

**Variable 3 : NEXT_PUBLIC_APP_NAME**

- **Key** : `NEXT_PUBLIC_APP_NAME`
- **Value** : `SûrCheck AI`
- **Environments** : Cochez **Production**, **Preview**, **Development**
- Cliquez sur **"Add"**

**Variable 4 : NEXT_PUBLIC_SUPABASE_URL**

- **Key** : `NEXT_PUBLIC_SUPABASE_URL`
- **Value** : `https://lhxbzflectkuysaklvji.supabase.co`
- **Environments** : Cochez **Production**, **Preview**, **Development**
- Cliquez sur **"Add"**

**Variable 5 : NEXT_PUBLIC_SUPABASE_ANON_KEY**

- **Key** : `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- **Value** : `sb_publishable_59E__jIIWr3HRG3XkV4Rcg_U0KZdYNH`
- **Environments** : Cochez **Production**, **Preview**, **Development**
- Cliquez sur **"Add"**

### 3.3 Vérification des variables

Vous devriez maintenant voir **5 variables** dans la liste :

```
✓ INTERNAL_API_URL
✓ NEXT_PUBLIC_API_URL
✓ NEXT_PUBLIC_APP_NAME
✓ NEXT_PUBLIC_SUPABASE_URL
✓ NEXT_PUBLIC_SUPABASE_ANON_KEY
```

---

## 🚀 Étape 4 : Premier déploiement

### 4.1 Lancer le déploiement

1. Vérifiez une dernière fois :
   - ✅ Root Directory : `apps/web`
   - ✅ Framework : Next.js
   - ✅ 5 variables d'environnement ajoutées
2. Cliquez sur **"Deploy"** (bouton bleu en bas)

### 4.2 Suivre le build en temps réel

Vercel va afficher les logs en temps réel :

```
Cloning repository...
✓ Cloned repository in 1.2s

Installing dependencies...
✓ Installed dependencies in 14s

Building application...
✓ Compiled successfully

Deploying...
✓ Deployment ready
```

**Temps estimé** : 2-4 minutes pour le premier déploiement

### 4.3 Erreurs possibles et solutions

#### Erreur : "Module not found: '@/lib/auth'"

**Cause** : Les fichiers `src/lib/*.ts` ne sont pas sur GitHub

**Solution** :
1. Vérifiez que `.gitignore` a été corrigé (ne doit pas ignorer `lib/`)
2. Commitez et pushez les fichiers `lib/` :
   ```bash
   git add apps/web/src/lib/
   git commit -m "fix: Add lib files for Vercel build"
   git push origin main
   ```
3. Vercel redéploiera automatiquement

#### Erreur : "Invalid rewrite found"

**Cause** : `INTERNAL_API_URL` est mal configurée ou manquante

**Solution** :
1. Vercel Dashboard → Votre projet → Settings → Environment Variables
2. Vérifiez `INTERNAL_API_URL` est bien définie
3. Si Railway n'est pas encore déployé, mettez : `http://localhost:8000`
4. Redéployez : Deployments → Menu ⋯ → Redeploy

#### Erreur : "Build failed" (autre)

**Solution** :
1. Lisez les logs complets sur Vercel
2. Vérifiez que `package.json` et `next.config.ts` sont corrects
3. Testez le build localement :
   ```bash
   cd apps/web
   npm install
   npm run build
   ```

---

## ✅ Étape 5 : Vérifier le déploiement

### 5.1 URL du déploiement

Une fois le build terminé, Vercel affiche :

```
✓ Deployment ready
🎉 https://sur-check.vercel.app
```

### 5.2 Tester l'application

1. Cliquez sur l'URL ou ouvrez : `https://sur-check.vercel.app`
2. Vous devriez voir la page d'accueil SûrCheck AI ✅
3. **Testez une analyse** :
   - Collez un message test dans le formulaire
   - Cliquez sur "Analyser ce contenu"
   - Vous devriez voir un résultat (moteur local embarqué)

### 5.3 Vérifications de base

**Page d'accueil :**
- ✅ Le logo et le titre s'affichent
- ✅ Le formulaire d'analyse est présent
- ✅ Les onglets (Message, URL, Capture) fonctionnent

**Analyse de contenu :**
- ✅ L'analyse fonctionne (moteur local)
- ✅ Le score de risque s'affiche
- ✅ Les signaux sont listés

**Authentification (si backend Railway connecté) :**
- ✅ Lien "Connexion" visible
- ⏳ Page `/compte` accessible

---

## 🔄 Étape 6 : Connecter au backend Railway (après déploiement Railway)

### 6.1 Récupérer l'URL Railway

Si vous avez déjà déployé le backend sur Railway :

1. Allez sur Railway Dashboard → Votre service
2. Copiez l'URL publique (ex: `https://surcheck-production-xxx.up.railway.app`)

### 6.2 Mettre à jour INTERNAL_API_URL

1. Vercel Dashboard → Votre projet → **Settings**
2. Menu gauche → **Environment Variables**
3. Trouvez `INTERNAL_API_URL`
4. Cliquez sur **Edit** (icône crayon)
5. Remplacez par votre URL Railway : `https://surcheck-production-xxx.up.railway.app`
6. Cliquez sur **Save**

### 6.3 Redéployer

1. Allez dans l'onglet **Deployments**
2. Dernier déploiement → Menu **⋯** (3 points) → **Redeploy**
3. **Décochez** "Use existing Build Cache"
4. Cliquez sur **Redeploy**

Vercel va reconstruire l'application avec la nouvelle URL backend.

### 6.4 Mettre à jour CORS sur Railway

N'oubliez pas de mettre à jour le CORS sur Railway :

1. Railway → Variables → `CORS_ORIGINS`
2. Remplacez par :
   ```json
   ["https://sur-check.vercel.app","https://surcheck.bj"]
   ```
3. Railway redémarre automatiquement

---

## 🎨 Étape 7 : Configuration du domaine personnalisé (optionnel)

### 7.1 Ajouter un domaine

Si vous avez un domaine personnalisé (ex: `surcheck.bj`) :

1. Vercel Dashboard → Votre projet → **Settings**
2. Menu gauche → **Domains**
3. Cliquez sur **"Add"**
4. Entrez votre domaine : `surcheck.bj`
5. Cliquez sur **"Add"**

### 7.2 Configurer les DNS

Vercel va vous donner des enregistrements DNS à ajouter :

**Pour un domaine racine (surcheck.bj) :**
```
Type: A
Name: @
Value: 76.76.21.21
```

**Pour un sous-domaine (www.surcheck.bj) :**
```
Type: CNAME
Name: www
Value: cname.vercel-dns.com
```

### 7.3 Vérification

1. Ajoutez ces enregistrements chez votre registrar (ex: Namecheap, OVH, etc.)
2. Attendez la propagation DNS (jusqu'à 48h, souvent 1-2h)
3. Vercel vérifie automatiquement et active le domaine
4. Certificat SSL automatique activé ✅

---

## 📊 Monitoring et analytics

### 7.1 Vercel Analytics (gratuit)

1. Vercel Dashboard → Votre projet → **Analytics**
2. Activez **"Enable Web Analytics"**
3. Vous verrez :
   - Nombre de visiteurs
   - Pages les plus visitées
   - Temps de chargement
   - Core Web Vitals

### 7.2 Logs en temps réel

1. Onglet **"Deployments"**
2. Cliquez sur un déploiement
3. Section **"Runtime Logs"**
4. Voir les requêtes et erreurs en temps réel

### 7.3 Performance monitoring

Vercel affiche automatiquement :
- ✅ Lighthouse Score
- ✅ Time to First Byte (TTFB)
- ✅ First Contentful Paint (FCP)
- ✅ Largest Contentful Paint (LCP)

---

## 🔄 Déploiements automatiques

### 8.1 Git Push → Auto-deploy

Vercel est configuré pour déployer automatiquement :

- ✅ Push sur `main` → Déploiement en **Production**
- ✅ Push sur autre branche → Déploiement en **Preview**
- ✅ Pull Request → URL de preview unique

### 8.2 Preview Deployments

Pour chaque PR GitHub, Vercel crée une URL unique :
```
https://sur-check-git-feature-xxx.vercel.app
```

Vous pouvez tester les changements avant de merger.

### 8.3 Rollback

Si un déploiement cause un problème :

1. Vercel Dashboard → **Deployments**
2. Trouvez le déploiement précédent qui fonctionnait
3. Menu **⋯** → **"Promote to Production"**

Le rollback est instantané ✅

---

## 🔐 Sécurité et best practices

### 9.1 Variables d'environnement sensibles

**Règles importantes :**

- ✅ Les variables `NEXT_PUBLIC_*` sont exposées au navigateur (publiques)
- ❌ Ne JAMAIS mettre de secrets dans `NEXT_PUBLIC_*`
- ✅ Les variables sans `NEXT_PUBLIC_` restent côté serveur (privées)

**Variables publiques (OK pour le navigateur) :**
- `NEXT_PUBLIC_API_URL` ✅
- `NEXT_PUBLIC_SUPABASE_URL` ✅
- `NEXT_PUBLIC_SUPABASE_ANON_KEY` ✅ (clé anonyme uniquement)

**Variables privées (serveur uniquement) :**
- `INTERNAL_API_URL` ✅ (utilisée par le rewrite Next.js)

### 9.2 Headers de sécurité

Le `next.config.ts` configure automatiquement :

```typescript
headers: [
  {
    key: "X-Frame-Options",
    value: "DENY",
  },
  {
    key: "X-Content-Type-Options",
    value: "nosniff",
  },
  {
    key: "Referrer-Policy",
    value: "strict-origin-when-cross-origin",
  },
  {
    key: "Strict-Transport-Security",
    value: "max-age=63072000; includeSubDomains; preload",
  },
]
```

### 9.3 Protection DDoS

Vercel inclut automatiquement :
- ✅ Protection DDoS
- ✅ Rate limiting intelligent
- ✅ CDN global (cache automatique)

---

## 🐛 Dépannage

### Problème : Erreur 404 NOT_FOUND

**Cause** : Le build a échoué ou Root Directory incorrect

**Solution** :
1. Vérifiez Root Directory = `apps/web`
2. Vérifiez que les fichiers `lib/` sont sur GitHub
3. Redéployez sans cache

### Problème : "Module not found"

**Cause** : Fichiers manquants sur GitHub (`.gitignore` trop restrictif)

**Solution** :
1. Vérifiez `.gitignore` (ne doit pas ignorer `lib/`)
2. Commitez et pushez les fichiers manquants
3. Vercel redéploie automatiquement

### Problème : L'API ne répond pas

**Cause** : Backend Railway non connecté ou CORS incorrect

**Solution** :
1. Vérifiez que Railway est déployé et actif
2. Vérifiez `INTERNAL_API_URL` sur Vercel
3. Vérifiez `CORS_ORIGINS` sur Railway inclut l'URL Vercel
4. Testez le backend : `curl https://votre-url-railway/health`

### Problème : Les variables d'environnement ne sont pas prises en compte

**Cause** : Cache de build ou variables ajoutées après le déploiement

**Solution** :
1. Deployments → Redeploy **sans cache**
2. Vérifiez que les variables sont bien dans **tous** les environnements (Production, Preview, Development)

### Problème : Build trop lent

**Cause** : Dépendances lourdes ou build complexe

**Optimisations** :
1. Activez le cache Vercel (par défaut)
2. Utilisez `output: 'standalone'` dans `next.config.ts` (déjà configuré si présent)
3. Vérifiez que `node_modules/.cache` est dans `.gitignore`

---

## 📈 Optimisations de performance

### 10.1 Activer le cache automatique

Vercel cache automatiquement :
- ✅ Pages statiques
- ✅ API Routes avec `revalidate`
- ✅ Images optimisées

### 10.2 Image Optimization

Next.js optimise automatiquement les images :

```jsx
import Image from 'next/image'

<Image
  src="/icon.svg"
  alt="SûrCheck"
  width={32}
  height={32}
/>
```

Vercel génère automatiquement :
- WebP/AVIF selon le navigateur
- Tailles responsives
- Lazy loading

### 10.3 Edge Functions (optionnel)

Pour les API Routes ultra-rapides, utilisez Edge Runtime :

```typescript
export const runtime = 'edge'
```

Déployé sur le CDN Vercel (latence < 50ms mondiale).

---

## ✅ Checklist finale

Avant de considérer le déploiement terminé :

- [ ] Build Vercel réussi ✅
- [ ] Application accessible sur l'URL Vercel ✅
- [ ] Page d'accueil s'affiche correctement ✅
- [ ] Analyse de texte fonctionne (moteur local) ✅
- [ ] Variables d'environnement configurées (5 minimum) ✅
- [ ] `INTERNAL_API_URL` pointe vers Railway (si déployé) ✅
- [ ] CORS configuré sur Railway avec l'URL Vercel ✅
- [ ] Authentification fonctionne (si backend connecté) ✅
- [ ] Aucune erreur 404 sur les routes principales ✅
- [ ] SSL/HTTPS actif automatiquement ✅

---

## 🎯 Récapitulatif des URLs

### URLs de production

| Service | URL | Usage |
|---------|-----|-------|
| **Frontend** | https://sur-check.vercel.app | Application publique |
| **Backend** | https://surcheck-production-xxx.up.railway.app | API FastAPI |
| **Database** | https://lhxbzflectkuysaklvji.supabase.co | Supabase PostgreSQL |
| **Dashboard Vercel** | https://vercel.com/dashboard | Gestion frontend |
| **Dashboard Railway** | https://railway.app/dashboard | Gestion backend |
| **Dashboard Supabase** | https://supabase.com/dashboard | Gestion DB |

---

## 🔜 Prochaines étapes

Une fois le frontend déployé avec succès :

1. ✅ Tester l'application en production
2. ✅ Vérifier les analyses fonctionnent
3. 🔜 Connecter au backend Railway (si pas encore fait)
4. 🔜 Tester l'authentification complète
5. 🔜 Tester l'achat de crédits Chariow
6. 🔜 Configurer un domaine personnalisé (optionnel)
7. 🔜 Activer les analytics Vercel

---

## 📞 Support Vercel

**Documentation officielle :**
- [https://vercel.com/docs](https://vercel.com/docs)

**Support communauté :**
- Discord Vercel : [https://vercel.com/discord](https://vercel.com/discord)

**Problèmes Next.js :**
- GitHub Next.js : [https://github.com/vercel/next.js/discussions](https://github.com/vercel/next.js/discussions)

**Contact support :**
- Dashboard → Help → Contact Support (plans Pro/Enterprise)

---

_Dernière mise à jour : 2025-01-09_
