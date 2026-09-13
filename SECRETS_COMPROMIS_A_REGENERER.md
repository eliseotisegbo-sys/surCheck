# SECRETS COMPROMIS À RÉGÉNÉRER IMMÉDIATEMENT

**Date d'identification** : 9 septembre 2026  
**Gravité** : CRITIQUE  
**Action requise** : Régénération AVANT toute mise en production

---

## 🚨 CONTEXTE

Les secrets suivants ont été **exposés en clair** dans des fichiers versionnés du dépôt Git :
- Valeurs par défaut dans `config.py`
- Documentation technique (`APIChariow.md`, `RAILWAY_DEPLOYMENT.md`)
- Fichier exemple `.env.example` (versions antérieures)

**Conséquence** : Ces secrets doivent être considérés comme **publics** et **compromis**, même si le dépôt est privé.

---

## 📋 LISTE DES SECRETS À RÉGÉNÉRER

### 1. CHARIOW_API_KEY
- **Valeur exposée** : `sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7`
- **Exposition** : `config.py` (valeur par défaut), `APIChariow.md`
- **Action** : 
  - ⚠️ **NOTE** : Chariow n'est plus utilisé dans le code (migration SasPay terminée)
  - Si compte Chariow toujours actif : révoquer la clé sur `app.chariow.com`
  - Sinon : ignorer (service non utilisé)

### 2. CHARIOW_WEBHOOK_SECRET
- **Valeur exposée** : `whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz`
- **Exposition** : `config.py` (valeur par défaut), `.env.example` (versions antérieures)
- **Action** : Même que ci-dessus (Chariow non utilisé)

### 3. JWT_SECRET_KEY
- **Valeur exposée** : `surcheck_jwt_secret_key_production_grade_super_secret_bj`
- **Exposition** : `config.py` (valeur par défaut), `.env` local
- **Impact** : ⚠️ **CRITIQUE** - Permet de forger des tokens d'authentification valides
- **Action** :
  1. Générer nouvelle clé : `openssl rand -hex 32` ou équivalent
  2. Mettre à jour `.env` local et variables Railway
  3. ⚠️ Tous les tokens existants seront invalidés (reconnexion utilisateurs requise)

### 4. PHONE_HASH_SALT
- **Valeur exposée** : `surcheck_bj_secure_salt_2026_antigravity_trust`
- **Exposition** : `config.py` (valeur par défaut), `.env` local
- **Impact** : Permet de recalculer les hashs de numéros de téléphone
- **Action** :
  1. Générer nouveau salt : `openssl rand -hex 32`
  2. Mettre à jour `.env` local et variables Railway
  3. ⚠️ Les hashs existants en base ne correspondront plus (migration nécessaire si base production active)

### 5. DATABASE_URL (mot de passe PostgreSQL)
- **Valeur exposée** : Mot de passe Supabase dans `.env` local
- **Exposition** : `.env` (risque si fichier partagé)
- **Impact** : Accès complet à la base de données
- **Action** :
  1. Sur Supabase Dashboard → Settings → Database → Reset database password
  2. Mettre à jour `DATABASE_URL` avec nouveau mot de passe
  3. Redéployer backend immédiatement

### 6. SUPABASE_SERVICE_ROLE_KEY
- **Valeur exposée** : Non présente dans `.env` actuel (commentée)
- **Statut** : ✅ Pas encore configurée = pas compromise
- **Action** : Ne JAMAIS la mettre en valeur par défaut dans `config.py`

---

## 🔧 PROCÉDURE DE RÉGÉNÉRATION

### Étape 1 : Générer les nouveaux secrets

```bash
# JWT_SECRET_KEY (32 bytes = 64 caractères hex)
openssl rand -hex 32

# PHONE_HASH_SALT (32 bytes)
openssl rand -hex 32
```

### Étape 2 : Mettre à jour `.env` local

Remplacer dans `c:\SûrCheck\.env` :
- `JWT_SECRET_KEY=<nouvelle_valeur_générée>`
- `PHONE_HASH_SALT=<nouvelle_valeur_générée>`
- `DATABASE_URL=<nouveau_mot_de_passe_supabase>`

### Étape 3 : Mettre à jour Railway

Sur Railway Dashboard → Variables :
- Mettre à jour `JWT_SECRET_KEY`
- Mettre à jour `PHONE_HASH_SALT`
- Mettre à jour `DATABASE_URL`
- Redéployer le service

### Étape 4 : Révoquer anciennes clés Chariow (optionnel)

Si compte Chariow actif :
1. Se connecter à `app.chariow.com`
2. Aller dans API Keys
3. Révoquer `sk_o0xs5yj1_...`
4. Supprimer le webhook configuré

---

## ✅ VÉRIFICATION POST-RÉGÉNÉRATION

- [ ] `.env` local contient uniquement les nouvelles valeurs
- [ ] `config.py` ne contient AUCUNE valeur par défaut sensible
- [ ] Railway variables mises à jour
- [ ] Backend redémarré sans erreur
- [ ] Authentification fonctionne (test login)
- [ ] Anciennes clés Chariow révoquées (si applicable)

---

## 🔒 PRÉVENTION FUTURE

1. **JAMAIS** de valeur par défaut sensible dans `config.py`
2. **TOUJOURS** vérifier `.gitignore` contient `.env`
3. **TOUJOURS** scanner les commits avant push : `git diff --cached`
4. **UTILISER** un gestionnaire de secrets (Railway, Doppler, AWS Secrets Manager)
5. **ROTATION** régulière des secrets (tous les 6 mois minimum)

---

## 📞 CONTACT EN CAS D'INCIDENT

Si une clé compromise a été utilisée malicieusement :
1. Révoquer immédiatement
2. Auditer les logs d'accès
3. Notifier les utilisateurs si données exposées
4. Documenter l'incident

---

**Document généré automatiquement le 9 septembre 2026**  
**À archiver après régénération complète**
