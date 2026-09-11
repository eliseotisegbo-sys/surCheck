# 🚨 AUDIT SÉCURITÉ — SECRETS EXPOSÉS

**Date :** 2026-09-09  
**Phase :** SûrCheck Reliability Phase  
**Priorité :** 🔴 CRITIQUE

---

## ⚠️ RÉSUMÉ EXÉCUTIF

**7 secrets de production exposés** dans le dépôt Git versionné :

1. ❌ **Mot de passe DB** : `Ge5ZNjlSDRT9cw1t` (`.env.example` — NETTOYÉ)
2. ❌ **JWT_SECRET_KEY** : `8a027971-87c1-4053-ada5-d15f7517a455` (`.env.example` — NETTOYÉ)
3. ❌ **SUPABASE_SERVICE_ROLE_KEY** : `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` (`.env.example` — NETTOYÉ)
4. ❌ **Chariow API Key** : `sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7` (5 fichiers)
5. ❌ **Chariow Webhook Secret** : `whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz` (4 fichiers)

### 🛡️ STATUT ACTUEL

| Secret | Exposition | Action | Statut |
|--------|-----------|---------|--------|
| Mot de passe DB | `.env.example` ligne 283 | Nettoyé | ✅ CORRIGÉ |
| JWT_SECRET_KEY | `.env.example` ligne 284 | Nettoyé | ✅ CORRIGÉ |
| SUPABASE_SERVICE_ROLE_KEY | `.env.example` ligne 285 | Nettoyé | ✅ CORRIGÉ |
| Chariow API Key | 5 fichiers (voir détail) | À nettoyer | ⏸️ EN COURS |
| Chariow Webhook Secret | 4 fichiers (voir détail) | À nettoyer | ⏸️ EN COURS |

---

## 📋 DÉTAIL DES EXPOSITIONS

### 1. ✅ `.env.example` (NETTOYÉ)

**Fichier :** `c:\SûrCheck\.env.example`  
**Lignes :** 283-285 (SUPPRIMÉES)

**Secrets exposés :**
```bash
# AVANT (EXPOSÉ) :
mot_de_passe= Ge5ZNjlSDRT9cw1t
JWT_SECRET_KEY= 8a027971-87c1-4053-ada5-d15f7517a455 
SUPABASE_SERVICE_ROLE_KEY= eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# APRÈS (NETTOYÉ) :
# ====================================================================
# FIN DU FICHIER .env.example
# ====================================================================
```

**Impact :** Ces 3 secrets étaient versionnés dans Git → **compromis**.

---

### 2. ⏸️ `APIChariow.md` (À NETTOYER)

**Fichier :** `c:\SûrCheck\APIChariow.md`  
**Ligne :** 1

**Secret exposé :**
```markdown
Voici la clé api a utilisé: sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7
```

**Action requise :**
```markdown
# REMPLACER LIGNE 1 PAR :
# Documentation API Chariow — SûrCheck AI
> ⚠️ Clé API à configurer dans Railway → Variables → CHARIOW_API_KEY
```

---

### 3. ⏸️ `apps/api/src/config.py` (À CORRIGER)

**Fichier :** `c:\SûrCheck\apps\api\src\config.py`  
**Ligne :** 58-60

**Secret exposé :**
```python
CHARIOW_API_KEY: str = os.getenv(
    "CHARIOW_API_KEY", "sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7"
)
```

**Problème :** Si `CHARIOW_API_KEY` n'est pas dans l'environnement, le code utilise silencieusement cette clé exposée.

**Action requise :**
```python
# REMPLACER PAR :
CHARIOW_API_KEY: str = os.getenv("CHARIOW_API_KEY", "")
```

**⚠️ IMPORTANT :** La validation "clé manquante" doit être faite au démarrage de l'application ou lors de la première utilisation.

---

### 4. ⏸️ `DEPLOYMENT.md` (À NETTOYER)

**Fichier :** `c:\SûrCheck\DEPLOYMENT.md`  
**Lignes :** 55-58

**Secrets exposés :**
```bash
CHARIOW_API_KEY=sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7
CHARIOW_WEBHOOK_SECRET=whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz
```

**Action requise :**
```bash
# REMPLACER PAR :
CHARIOW_API_KEY=<<VOTRE_CLE_CHARIOW_API>>
CHARIOW_WEBHOOK_SECRET=<<VOTRE_SECRET_WEBHOOK_CHARIOW>>
```

---

### 5. ⏸️ `RAILWAY_DEPLOYMENT.md` (À NETTOYER)

**Fichier :** `c:\SûrCheck\RAILWAY_DEPLOYMENT.md`  
**Lignes :** 143-146, 314

**Secrets exposés :**
```bash
# Ligne 143-146 :
CHARIOW_API_KEY=sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7
CHARIOW_WEBHOOK_SECRET=whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz

# Ligne 314 :
4. **Secret** : Doit être `whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz`
```

**Action requise :**
```bash
# Lignes 143-146 REMPLACER PAR :
CHARIOW_API_KEY=<<VOTRE_CLE_CHARIOW_API>>
CHARIOW_WEBHOOK_SECRET=<<VOTRE_SECRET_WEBHOOK_CHARIOW>>

# Ligne 314 REMPLACER PAR :
4. **Secret** : Copier depuis app.chariow.com → Pulses → Votre webhook → Secret
```

---

### 6. ⏸️ `MIGRATION_SASPAY.md` (À NETTOYER)

**Fichier :** `c:\SûrCheck\MIGRATION_SASPAY.md`  
**Lignes :** 120-123, 301-304

**Secrets exposés :**
```bash
# Ligne 120-123 :
CHARIOW_API_KEY=sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7
CHARIOW_WEBHOOK_SECRET=whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz

# Ligne 301-304 (doublon) :
CHARIOW_API_KEY=sk_o0xs5yj1_6ed3b1413ce916e7835c6d884b6548f7
CHARIOW_WEBHOOK_SECRET=whsec_GmbUMyji4cdf07Hv1pRGlBOUquHiZ4ibfAXW38xz
```

**Action requise :**
```bash
# REMPLACER TOUTES OCCURRENCES PAR :
CHARIOW_API_KEY=<<VOTRE_CLE_CHARIOW_API>>
CHARIOW_WEBHOOK_SECRET=<<VOTRE_SECRET_WEBHOOK_CHARIOW>>
```

---

## 🔐 ANALYSE D'IMPACT

### Secrets compromis (doivent être régénérés)

| Secret | Impact si compromis | Régénération |
|--------|-------------------|--------------|
| **Mot de passe DB** | ❌ Accès lecture/écriture complet DB Supabase | Supabase Dashboard → Settings → Database → Reset password |
| **JWT_SECRET_KEY** | ❌ Forger tokens authentification, usurpation identité | Générer nouvelle clé → Invalidera toutes sessions actives |
| **SUPABASE_SERVICE_ROLE_KEY** | ❌ Accès admin complet DB (bypass RLS) | **NOTE :** Semble être la clé `anon` (pas service_role) → Vérifier sur Supabase |
| **Chariow API Key** | ❌ Créer paiements frauduleux, accéder données clients | app.chariow.com → Settings → API Keys → Révoquer + Créer nouvelle |
| **Chariow Webhook Secret** | ⚠️ Forger notifications paiement (crédits gratuits) | app.chariow.com → Pulses → Webhook → Régénérer secret |

### Évaluation de la clé Supabase exposée

**Clé exposée :**
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxoeGJ6ZmxlY3RrdXlzYWtsdmppIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg3NzM2OTUsImV4cCI6MjEwNDM0OTY5NX0.M1R-TigPppjEC-1PUSFNnj_DQwOvspBu-bdI463jsUM
```

**Décodage du JWT :**
```json
{
  "iss": "supabase",
  "ref": "lhxbzflectkuysaklvji",
  "role": "anon",
  "iat": 1788773695,
  "exp": 2104349695
}
```

🟡 **CONSTAT :** C'est la clé **`anon`** (publique), pas la `service_role` !

**Impact :**
- ✅ Moins critique : clé `anon` est exposable côté client
- ⚠️ Problème nommage : variable nommée `SUPABASE_SERVICE_ROLE_KEY` mais contient clé `anon`
- ❌ Confusion dans le code : risque d'utiliser clé `anon` là où `service_role` est attendue

**Action requise :**
1. Vérifier que `.env` production contient la **vraie** clé `service_role`
2. Corriger `.env.example` : renommer variable ou clarifier qu'il s'agit d'un placeholder

---

## 📦 VÉRIFICATION HISTORIQUE GIT

### Commits analysés

```bash
git log --all --oneline | Select-String "\.env"
# Résultat : Aucun commit ne mentionne .env
```

✅ **Fichier `.env` n'a jamais été commité** (protégé par `.gitignore`).

### Recherche secrets dans l'historique

```bash
git log --all -p -S "Ge5ZNjlSDRT9cw1t"
# Résultat : Aucune trace du mot de passe DB dans l'historique
```

✅ **Les secrets dans `.env.example` semblent avoir été ajoutés récemment** (derniers commits mentionnent "clés masquées").

**Conclusion :**
- Les secrets dans `.env.example` sont présents dans le commit actuel
- Pas de trace dans l'historique ancien
- **Action :** Nettoyer commit actuel + pousser correction

---

## ✅ ACTIONS CORRECTIVES (Ordre de priorité)

### Phase 1 : Nettoyage immédiat des fichiers (EN COURS)

- [x] ✅ `.env.example` — Nettoyé (3 secrets supprimés)
- [ ] ⏸️ `APIChariow.md` — Supprimer ligne 1
- [ ] ⏸️ `config.py` — Remplacer valeur par défaut par `""`
- [ ] ⏸️ `DEPLOYMENT.md` — Remplacer par placeholders
- [ ] ⏸️ `RAILWAY_DEPLOYMENT.md` — Remplacer par placeholders (2 endroits)
- [ ] ⏸️ `MIGRATION_SASPAY.md` — Remplacer par placeholders (2 endroits)

### Phase 2 : Régénération secrets (ACTIONS MANUELLES REQUISES)

**🔴 À FAIRE MANUELLEMENT PAR L'UTILISATEUR :**

1. **Supabase Dashboard**
   - [ ] Régénérer mot de passe DB : Settings → Database → Reset password
   - [ ] Vérifier clé `service_role` : Settings → API → service_role (Reveal)
   - [ ] Mettre à jour `.env` production avec nouveau mot de passe

2. **Générer nouveau JWT_SECRET_KEY**
   ```bash
   # Linux/Mac :
   openssl rand -hex 32
   
   # PowerShell :
   -join ((48..57) + (65..70) | Get-Random -Count 64 | ForEach-Object {[char]$_})
   
   # Ou : https://randomkeygen.com (Fort Knox Passwords)
   ```
   - [ ] Copier nouvelle clé dans `.env` production
   - [ ] Mettre à jour variable Railway `JWT_SECRET_KEY`
   - ⚠️ **ATTENTION :** Invalide toutes les sessions utilisateur actives

3. **Chariow Dashboard**
   - [ ] Révoquer clé : app.chariow.com → Settings → API Keys → Révoquer `sk_o0xs5yj1_...`
   - [ ] Créer nouvelle clé : Settings → API Keys → Create API Key
   - [ ] Mettre à jour `.env` production + Railway variable `CHARIOW_API_KEY`
   - [ ] Régénérer webhook secret : Pulses → Webhook → Regenerate Secret
   - [ ] Mettre à jour Railway variable `CHARIOW_WEBHOOK_SECRET`

### Phase 3 : Validation post-correction

- [ ] Commit + push corrections fichiers documentation
- [ ] Vérifier Railway variables à jour
- [ ] Tester authentification (nouveau JWT)
- [ ] Tester paiement Chariow (nouvelle clé API)
- [ ] Tester webhook Chariow (nouveau secret)
- [ ] Vérifier logs Railway (pas d'erreurs auth)

---

## 🛡️ RECOMMANDATIONS FUTURES

### 1. Validation secrets au démarrage

**Ajouter dans `main.py` :**
```python
@app.on_event("startup")
async def validate_secrets():
    """Valide que tous les secrets critiques sont configurés."""
    required_secrets = [
        "JWT_SECRET_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
        "CHARIOW_API_KEY",
    ]
    
    missing = []
    for secret in required_secrets:
        value = getattr(settings, secret, "")
        if not value or value == "":
            missing.append(secret)
    
    if missing:
        raise RuntimeError(
            f"🚨 SECRETS MANQUANTS : {', '.join(missing)}. "
            "Configurez ces variables dans Railway → Variables."
        )
```

### 2. Pre-commit hook détection secrets

**Créer `.git/hooks/pre-commit` :**
```bash
#!/bin/bash
# Détecte secrets avant commit

PATTERNS=(
    "sk_[a-z0-9_]{8,}"          # Clés API (Chariow, SasPay)
    "whsec_[a-zA-Z0-9]{40,}"    # Webhook secrets
    "eyJ[a-zA-Z0-9_-]{20,}"     # JWT tokens
    "[0-9a-f]{64}"              # Clés hexadécimales 64 chars
)

for pattern in "${PATTERNS[@]}"; do
    if git diff --cached | grep -E "$pattern"; then
        echo "🚨 ALERTE : Secret potentiel détecté !"
        echo "Pattern : $pattern"
        exit 1
    fi
done
```

### 3. Scanner automatique GitHub

**GitHub Actions workflow :**
```yaml
name: Secret Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD
```

### 4. Documentation sécurité

**Créer `SECURITY.md` :**
```markdown
# Politique de sécurité

## Variables d'environnement sensibles

Les secrets suivants ne doivent JAMAIS être commités :
- JWT_SECRET_KEY
- SUPABASE_SERVICE_ROLE_KEY
- CHARIOW_API_KEY
- CHARIOW_WEBHOOK_SECRET
- SASPAY_API_KEY
- SASPAY_WEBHOOK_SECRET
- Mot de passe DB

## Signalement vulnérabilité

Contact : [email sécurité]
```

---

## 📊 RÉSUMÉ STATUT

| Catégorie | Total | Traité | Restant |
|-----------|-------|--------|---------|
| **Fichiers avec secrets** | 6 | 1 | 5 |
| **Secrets uniques exposés** | 5 | 3 | 2 |
| **Actions manuelles** | 3 | 0 | 3 |

**Progression globale :** 🟡 20% (1/5 fichiers nettoyés)

---

**Dernière mise à jour :** 2026-09-09 (Session Reliability Phase)
