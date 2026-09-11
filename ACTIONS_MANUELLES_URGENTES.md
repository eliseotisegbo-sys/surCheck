# 🚨 ACTIONS MANUELLES URGENTES — RÉGÉNÉRATION SECRETS

**Date :** 2026-09-09  
**Priorité :** 🔴 CRITIQUE — À FAIRE IMMÉDIATEMENT

---

## ⚠️ CONTEXTE

**7 secrets de production** ont été exposés dans le dépôt Git versionné et doivent être **régénérés immédiatement**.

Les fichiers contenant les secrets ont été **nettoyés**, mais les secrets compromis restent **valides** jusqu'à leur régénération.

---

## 📋 CHECKLIST — 3 ACTIONS OBLIGATOIRES

### ✅ Action 1 : Régénérer secrets Supabase

**Temps estimé :** 5 minutes  
**Impact :** Redémarrage base de données (< 1 minute de downtime)

#### Étapes :

1. **Connexion Supabase Dashboard**
   - Allez sur : https://supabase.com/dashboard
   - Connectez-vous à votre compte
   - Sélectionnez le projet `lhxbzflectkuysaklvji`

2. **Régénérer le mot de passe DB**
   - Cliquez sur **Settings** (⚙️ en bas à gauche)
   - Allez dans **Database**
   - Section **"Database Password"**
   - Cliquez sur **"Reset Database Password"**
   - ⚠️ **ATTENTION :** Copiez le nouveau mot de passe IMMÉDIATEMENT (affiché une seule fois)
   - Sauvegardez-le temporairement dans un fichier local sécurisé

3. **Vérifier la clé service_role**
   - Toujours dans **Settings**
   - Allez dans **API**
   - Section **"Project API keys"**
   - Cliquez sur **"Reveal"** à côté de `service_role`
   - ⚠️ **IMPORTANT :** Vérifiez que ce n'est PAS la même que la clé `anon`
   - Copiez la clé `service_role` (commence par `eyJ...`)
   - Sauvegardez-la temporairement

4. **Mettre à jour `.env` local (si développement local)**
   ```bash
   # Ouvrir .env avec un éditeur
   # Remplacer les lignes suivantes :
   
   DATABASE_URL=postgresql://postgres.lhxbzflectkuysaklvji:<<NOUVEAU_MOT_DE_PASSE>>@aws-0-eu-west-3.pooler.supabase.com:6543/postgres
   SUPABASE_SERVICE_ROLE_KEY=<<NOUVELLE_CLE_SERVICE_ROLE>>
   ```

5. **Mettre à jour Railway**
   - Allez sur : https://railway.app
   - Sélectionnez votre projet SûrCheck
   - Cliquez sur le service **API**
   - Onglet **Variables**
   - Modifiez :
     - `DATABASE_URL` → Nouvelle connection string avec nouveau mot de passe
     - `SUPABASE_SERVICE_ROLE_KEY` → Nouvelle clé service_role
   - Cliquez sur **"Deploy"** (redémarrage automatique)

---

### ✅ Action 2 : Régénérer JWT_SECRET_KEY

**Temps estimé :** 3 minutes  
**Impact :** ⚠️ **Invalide toutes les sessions utilisateur actives** (ils devront se reconnecter)

#### Étapes :

1. **Générer nouvelle clé JWT (64 caractères minimum)**

   **Option A — PowerShell (Windows) :**
   ```powershell
   -join ((48..57) + (65..70) | Get-Random -Count 64 | ForEach-Object {[char]$_})
   ```

   **Option B — Linux/Mac :**
   ```bash
   openssl rand -hex 32
   ```

   **Option C — Site web :**
   - Allez sur : https://randomkeygen.com
   - Section **"Fort Knox Passwords"**
   - Copiez une clé (512-bit WPA Key recommandée)

2. **Sauvegarder temporairement**
   - Copiez la nouvelle clé dans un fichier local sécurisé
   - Exemple : `2f8e7a1b9c4d6f3e8a5b2c7d9e1f4a6b3c8d5e2f7a9b4c6d8e1f3a5b7c9d2e4f6`

3. **Mettre à jour `.env` local**
   ```bash
   JWT_SECRET_KEY=<<VOTRE_NOUVELLE_CLE_JWT_64_CHARS>>
   ```

4. **Mettre à jour Railway**
   - Railway Dashboard → Service API → Variables
   - Modifier `JWT_SECRET_KEY` → Nouvelle clé générée
   - Cliquer sur **"Deploy"**

5. **⚠️ Prévoir communication utilisateurs**
   ```
   Message suggéré :
   "Suite à une mise à jour de sécurité, vous devez vous reconnecter à votre compte SûrCheck."
   ```

---

### ✅ Action 3 : Régénérer secrets Chariow

**Temps estimé :** 5 minutes  
**Impact :** Paiements temporairement bloqués pendant la mise à jour (~2 minutes)

#### Étapes :

1. **Connexion Chariow Dashboard**
   - Allez sur : https://app.chariow.com
   - Connectez-vous à votre compte
   - Vérifiez que vous êtes sur le bon compte (celui avec les produits SûrCheck)

2. **Révoquer ancienne clé API**
   - Cliquez sur **Settings** (⚙️)
   - Allez dans **API Keys**
   - Trouvez la clé commençant par `sk_o0xs5yj1_...`
   - Cliquez sur **"Revoke"** ou **"Delete"**
   - ⚠️ **ATTENTION :** Les paiements seront bloqués après cette étape jusqu'à configuration nouvelle clé

3. **Créer nouvelle clé API**
   - Toujours dans **API Keys**
   - Cliquez sur **"Create API Key"** ou **"New Key"**
   - Nom suggéré : `SûrCheck Production 2026-09`
   - Copiez la nouvelle clé IMMÉDIATEMENT (format : `sk_xxxxxxxx_xxxxxxxxx...`)
   - Sauvegardez-la temporairement

4. **Régénérer webhook secret**
   - Dans le menu Chariow, allez dans **Pulses** ou **Webhooks**
   - Trouvez le webhook pour SûrCheck (URL contient votre domaine Railway)
   - Cliquez sur **"Edit"** ou **"Manage"**
   - Cliquez sur **"Regenerate Secret"** ou **"Rotate Secret"**
   - Copiez le nouveau secret (format : `whsec_xxxxxxxxxxxxxxxx...`)
   - Sauvegardez-le temporairement

5. **Mettre à jour `.env` local**
   ```bash
   CHARIOW_API_KEY=<<NOUVELLE_CLE_API_CHARIOW>>
   CHARIOW_WEBHOOK_SECRET=<<NOUVEAU_SECRET_WEBHOOK_CHARIOW>>
   ```

6. **Mettre à jour Railway**
   - Railway Dashboard → Service API → Variables
   - Modifier :
     - `CHARIOW_API_KEY` → Nouvelle clé API
     - `CHARIOW_WEBHOOK_SECRET` → Nouveau secret webhook
   - Cliquer sur **"Deploy"**

7. **Tester un paiement**
   - Attendre que Railway ait redéployé (2-3 minutes)
   - Aller sur le frontend SûrCheck
   - Tenter d'acheter le pack 1 crédit (600 FCFA)
   - Vérifier que la page Chariow s'ouvre correctement
   - **NE PAS FINALISER** le paiement si en mode production (ou utiliser un petit montant test)

---

## 🧪 VALIDATION POST-RÉGÉNÉRATION

### Checklist de tests :

- [ ] **Backend démarre sans erreur**
  ```bash
  # Vérifier logs Railway :
  # Pas d'erreur "SECRETS MANQUANTS"
  # Pas d'erreur Supabase connection
  ```

- [ ] **Authentification fonctionne**
  ```bash
  # Test :
  # 1. Créer nouveau compte sur frontend
  # 2. Se connecter
  # 3. Vérifier token dans localStorage
  ```

- [ ] **Base de données accessible**
  ```bash
  # Test :
  # 1. Vérifier page compte (affiche infos utilisateur)
  # 2. Vérifier historique analyses (si vous en avez)
  ```

- [ ] **Paiement Chariow fonctionne**
  ```bash
  # Test :
  # 1. Cliquer sur "Acheter 1 crédit"
  # 2. Vérifier redirection vers Chariow
  # 3. Page Chariow affiche le bon montant (600 FCFA)
  # 4. (Optionnel) Finaliser paiement test
  ```

- [ ] **Webhook Chariow fonctionne**
  ```bash
  # Test (si paiement finalisé) :
  # 1. Attendre confirmation paiement Chariow
  # 2. Vérifier que crédits apparaissent dans compte
  # 3. Vérifier logs Railway : "Webhook Chariow reçu"
  ```

---

## 📊 RÉSUMÉ TEMPS & IMPACT

| Action | Durée | Downtime | Utilisateurs impactés |
|--------|-------|----------|----------------------|
| Supabase secrets | 5 min | ~1 min | ❌ Aucun (si fait rapidement) |
| JWT_SECRET_KEY | 3 min | ❌ Aucun | ✅ Tous (doivent se reconnecter) |
| Chariow secrets | 5 min | ~2 min | ⚠️ Paiements uniquement |
| **TOTAL** | **13 min** | **~3 min** | **Sessions + Paiements** |

---

## ⚠️ NOTES IMPORTANTES

### 1. Ordre recommandé

Faites les actions **dans l'ordre** pour minimiser l'impact :

1. **Supabase d'abord** (impact minimal si rapide)
2. **JWT ensuite** (invalide sessions mais app reste fonctionnelle)
3. **Chariow en dernier** (bloque paiements temporairement)

### 2. Communication utilisateurs

**Si vous avez des utilisateurs actifs :**

```
AVANT la régénération :
"⚠️ Maintenance de sécurité prévue dans 10 minutes. 
Durée estimée : 5 minutes. Les paiements seront temporairement indisponibles."

APRÈS la régénération :
"✅ Maintenance terminée. Si vous rencontrez des problèmes de connexion, 
veuillez vous reconnecter."
```

### 3. Sauvegarde secrets

**Après régénération :**

1. **NE PAS** commiter secrets dans Git
2. **Sauvegarder** dans un gestionnaire de mots de passe (1Password, Bitwarden, etc.)
3. **Documenter** où sont les secrets :
   ```
   - Production Railway : Variables du service API
   - Développement local : .env (jamais versionné)
   - Backup sécurisé : [votre gestionnaire de mots de passe]
   ```

### 4. Surveillance post-régénération

**Surveiller pendant 24h :**

- Logs Railway → Pas d'erreurs auth/paiement
- Chariow Dashboard → Transactions passent correctement
- Supabase Dashboard → Queries exécutées normalement

---

## 🆘 EN CAS DE PROBLÈME

### Backend ne démarre plus

**Symptôme :** Logs Railway : `"RuntimeError: SECRETS MANQUANTS"`

**Cause :** Variable Railway mal configurée

**Solution :**
1. Vérifier Railway → Variables → Format exact
2. Vérifier pas d'espaces avant/après les clés
3. Vérifier que `DATABASE_URL` contient bien le mot de passe encodé URL

### Utilisateurs ne peuvent pas se connecter

**Symptôme :** Erreur "Token invalide" ou "Session expirée"

**Cause :** Ancien token en cache après changement JWT_SECRET_KEY

**Solution :**
1. Demander aux utilisateurs de vider cache navigateur
2. Ou de se reconnecter (supprime ancien token)

### Paiements Chariow échouent

**Symptôme :** Erreur "API key invalid" ou redirection échoue

**Cause :** Nouvelle clé API mal copiée

**Solution :**
1. Vérifier Railway → Variables → `CHARIOW_API_KEY`
2. Pas d'espaces, format exact : `sk_xxxxxxxx_...`
3. Si doute, régénérer nouvelle clé sur Chariow

### Webhook Chariow ne fonctionne pas

**Symptôme :** Paiement réussi sur Chariow mais crédits pas ajoutés

**Cause :** Webhook secret incorrect

**Solution :**
1. Vérifier Railway → Variables → `CHARIOW_WEBHOOK_SECRET`
2. Vérifier Chariow Dashboard → Pulses → Secret correspond
3. Si doute, régénérer + reconfigurer

---

## ✅ CONFIRMATION FINALE

**Avant de marquer comme terminé, vérifier :**

- [ ] ✅ Tous les secrets régénérés et testés
- [ ] ✅ Variables Railway mises à jour
- [ ] ✅ Tests validation passés
- [ ] ✅ Secrets sauvegardés en lieu sûr
- [ ] ✅ Documentation `.env.example` à jour (sans secrets)
- [ ] ✅ Commit + push corrections fichiers documentation
- [ ] ✅ Surveillance 24h planifiée

---

**Dernière mise à jour :** 2026-09-09  
**Document lié :** AUDIT_SECURITE_SECRETS.md
