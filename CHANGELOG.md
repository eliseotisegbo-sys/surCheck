# Changelog - SûrCheck AI

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/).

---

## [1.0.0] - 2025-01-09

### 🎯 Déploiement Production

#### Infrastructure déployée
- **Frontend** : Vercel → https://sur-check.vercel.app
- **Backend** : Railway (à déployer) → https://surcheck-production.up.railway.app
- **Base de données** : Supabase PostgreSQL (projet: lhxbzflectkuysaklvji)
- **Paiements** : Chariow API (webhook configuré)

---

### 🔴 Problème résolu : Erreur 404 Vercel (Build Failed)

#### Diagnostic
- **Erreur initiale** : `404: NOT_FOUND` sur https://sur-check.vercel.app
- **Erreur build** : `Module not found: Can't resolve '@/lib/auth'`
- **Cause racine** : Le fichier `.gitignore` à la racine ignorait TOUS les dossiers `lib/`, y compris `apps/web/src/lib/` contenant les modules TypeScript essentiels
- **Impact** : Les fichiers `auth.ts`, `api.ts`, `engine.ts`, `supabase.ts` n'étaient pas versionnés sur GitHub, donc absents lors du build Vercel

#### Solution appliquée

##### 1. Correction du `.gitignore` (racine du projet)

**Avant :**
```gitignore
lib/          # ❌ Ignorait TOUS les dossiers lib/
lib64/
```

**Après :**
```gitignore
# Python virtual environments only (NOT TypeScript/Node lib folders)
**/lib/python*/
**/lib64/python*/
venv/lib/
env/lib/
ENV/lib/
```

**Raison** : Cibler uniquement les environnements virtuels Python, pas les dossiers `lib/` de Node.js/TypeScript

##### 2. Fichiers ajoutés au versionnement Git
- ✅ `apps/web/src/lib/auth.ts` - Module d'authentification Supabase + JWT
- ✅ `apps/web/src/lib/api.ts` - Client API FastAPI avec fallback local
- ✅ `apps/web/src/lib/engine.ts` - Moteur d'analyse local embarqué (7 règles)
- ✅ `apps/web/src/lib/supabase.ts` - Client Supabase pour authentification

##### 3. Variables d'environnement Vercel configurées

| Variable | Valeur | Environnement | Usage |
|----------|--------|---------------|-------|
| `INTERNAL_API_URL` | `https://surcheck-production.up.railway.app` | Production | Rewrite Next.js vers backend |
| `NEXT_PUBLIC_API_URL` | `/api/v1` | Tous | Base URL API côté client |
| `NEXT_PUBLIC_APP_NAME` | `SûrCheck AI` | Tous | Nom de l'application |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://lhxbzflectkuysaklvji.supabase.co` | Tous | Connexion Supabase |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `sb_publishable_59E__jIIWr3HRG3XkV4Rcg...` | Tous | Clé publique Supabase |

##### 4. Configuration Vercel
- **Root Directory** : `apps/web` ✅
- **Framework Preset** : Next.js 16.3.4 ✅
- **Build Command** : `next build --webpack` ✅
- **Node Version** : 20.x ✅

---

### 📋 Résultat attendu

#### Après ces modifications
- ✅ Build Vercel réussi
- ✅ Application accessible sur https://sur-check.vercel.app
- ✅ Analyses fonctionnelles avec moteur local embarqué
- ✅ Interface complète (analyse texte/SMS/URL/capture d'écran)
- ⏳ Authentification et crédits (nécessite backend Railway)

#### Fonctionnalités opérationnelles en mode autonome
- ✅ Analyse de texte/SMS (moteur local 7 règles)
- ✅ Détection de signaux de risque
- ✅ Scoring de risque (0-100)
- ✅ Recommandations ciblées
- ✅ Historique local (localStorage)
- ✅ Interface responsive mobile-first

#### Fonctionnalités nécessitant le backend Railway
- ⏳ Authentification utilisateurs (register/login)
- ⏳ Système de crédits et quota
- ⏳ Paiement Chariow (packs de crédits)
- ⏳ Déblocage d'analyses complètes
- ⏳ Historique persistant en base de données

---

### 🚀 Commandes Git exécutées

```bash
# 1. Modification du .gitignore
git add .gitignore

# 2. Ajout des fichiers lib/ précédemment ignorés
git add apps/web/src/lib/

# 3. Ajout du CHANGELOG et guides de déploiement
git add CHANGELOG.md
git add RAILWAY_DEPLOYMENT.md
git add VERCEL_DEPLOYMENT.md

# 4. Mise à jour du .env.example avec commentaires explicatifs
git add .env.example

# 5. Commit descriptif des modifications
git commit -m "fix(vercel): Correction .gitignore et ajout des modules lib/ manquants

- Correction .gitignore pour ignorer uniquement les lib/ Python
- Ajout de auth.ts, api.ts, engine.ts, supabase.ts au versionnement
- Résout l'erreur 'Module not found' lors du build Vercel
- Ajout de la documentation complète de déploiement
- Fixes #404-NOT_FOUND"

# 6. Push vers GitHub (déclenche auto-deploy Vercel)
git push origin main
```

---

## 📚 Documentation créée

### Fichiers ajoutés
1. **CHANGELOG.md** - Ce fichier, historique des modifications
2. **RAILWAY_DEPLOYMENT.md** - Guide détaillé déploiement backend Railway
3. **VERCEL_DEPLOYMENT.md** - Guide détaillé configuration Vercel
4. **.env.example** mis à jour - Variables d'environnement avec commentaires explicatifs

---

## 🔜 Prochaines étapes

### Phase 1 : Validation frontend (MAINTENANT)
1. ✅ Corriger .gitignore
2. ✅ Pusher les fichiers lib/ sur GitHub
3. ⏳ Attendre le redéploiement automatique Vercel (2-3 min)
4. ⏳ Vérifier que https://sur-check.vercel.app fonctionne
5. ⏳ Tester une analyse de texte avec le moteur local

### Phase 2 : Déploiement backend (APRÈS VALIDATION FRONTEND)
1. 🔜 Déployer le backend sur Railway (voir RAILWAY_DEPLOYMENT.md)
2. 🔜 Récupérer l'URL Railway générée
3. 🔜 Mettre à jour `INTERNAL_API_URL` sur Vercel
4. 🔜 Redéployer Vercel pour connecter au backend
5. 🔜 Configurer le webhook Chariow avec l'URL Railway

### Phase 3 : Tests de validation (APRÈS DÉPLOIEMENT BACKEND)
1. 🔜 Test santé API : `GET /health`
2. 🔜 Test inscription/connexion
3. 🔜 Test analyse avec compte connecté
4. 🔜 Test packs de crédits
5. 🔜 Test paiement Chariow (sandbox)

---

## 📖 Notes techniques

### Pourquoi le .gitignore ignorait lib/ ?

Le template `.gitignore` Python standard inclut `lib/` et `lib64/` pour ignorer les environnements virtuels Python (venv, virtualenv). Dans un monorepo multi-langages (Python + Node.js/TypeScript), cette règle trop large ignore aussi les dossiers `src/lib/` contenant du code TypeScript légitime.

### Solution appliquée

Utiliser des patterns plus spécifiques :
- `**/lib/python*/` → Cible uniquement les sous-dossiers Python des venvs
- `venv/lib/` → Environnements virtuels à la racine
- `apps/api/.venv/lib/` → Environnements virtuels du backend

Ces patterns n'affectent pas `apps/web/src/lib/` qui contient du TypeScript.

### Architecture du moteur d'analyse

Le moteur embarqué (`engine.ts`) permet un **fonctionnement résilient** :
1. Tentative d'appel au backend FastAPI
2. En cas d'échec réseau → Fallback automatique vers le moteur local
3. L'utilisateur ne voit aucune erreur, analyse instantanée
4. 7 règles de détection : OTP, demande d'argent, urgence, gain irréaliste, liens suspects, usurpation opérateur, fausse transaction

### Leçon apprise

**Dans un monorepo multi-langages, toujours vérifier que les règles `.gitignore` ne s'appliquent pas trop largement.**

Pattern à éviter : `lib/` (trop large)  
Pattern recommandé : `**/lib/python*/` (spécifique)

---

## 🐛 Débogage

### Si le build Vercel échoue encore

**Vérifier :**
1. Les fichiers `apps/web/src/lib/*.ts` sont bien présents sur GitHub
2. La variable `INTERNAL_API_URL` est bien définie sur Vercel
3. Le Root Directory est `apps/web` (pas `/`)
4. Les variables d'environnement `NEXT_PUBLIC_*` sont définies

**Logs à surveiller :**
```
Module not found → Fichiers lib/ manquants
Invalid rewrite found → INTERNAL_API_URL mal configuré
Build failed → Vérifier les logs complets sur Vercel
```

### Si l'application affiche encore 404

**Vérifier :**
1. Le déploiement est en statut **Ready** (pas Failed)
2. L'URL Vercel est correcte : `https://sur-check.vercel.app`
3. Pas de cache DNS : Tester en navigation privée
4. Vercel Deployments → Le dernier build est bien actif

---

## 📞 Support

**En cas de problème :**
1. Consulter RAILWAY_DEPLOYMENT.md pour le backend
2. Consulter VERCEL_DEPLOYMENT.md pour le frontend
3. Vérifier les logs Vercel : Deployments → Build logs
4. Vérifier les logs Railway : Service → Deployments

**Variables d'environnement sensibles :**
- `SUPABASE_SERVICE_ROLE_KEY` → Ne JAMAIS committer
- `JWT_SECRET_KEY` → Générer une clé aléatoire forte
- `DATABASE_URL` → Contient le mot de passe DB

Ces variables doivent être configurées uniquement dans les interfaces Railway/Vercel, jamais dans le code.

---

_Dernière mise à jour : 2025-01-09_
