# DIAGNOSTIC : Erreur "Inscription impossible. Réessayez."

**Date** : 9 septembre 2026  
**Problème** : L'inscription utilisateur échoue avec un message générique

---

## 🔍 CAUSES POSSIBLES

### 1. Base de données Supabase inaccessible

**Symptômes** :
- Message : "Inscription impossible. Réessayez."
- Timeout ou erreur réseau

**Vérification** :
```bash
# Tester la connexion Supabase
curl -H "apikey: sb_publishable_59E__jIIWr3HRG3XkV4Rcg_U0KZdYNH" \
     https://lhxbzflectkuysaklvji.supabase.co/rest/v1/users?limit=1
```

**Solutions** :
- Vérifier que `SUPABASE_URL` et `SUPABASE_ANON_KEY` sont corrects dans `.env`
- Vérifier connexion internet
- Vérifier que le projet Supabase est actif sur `supabase.com`

---

### 2. Table `users` manquante ou schéma incorrect

**Symptômes** :
- Erreur HTTP 404 ou 400 lors de l'insertion
- Message "relation users does not exist"

**Vérification** :
```sql
-- Dans Supabase SQL Editor
SELECT * FROM users LIMIT 1;
```

**Solution** :
Créer/vérifier la table :
```sql
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'user',
    free_analyses_quota INTEGER DEFAULT 5,
    paid_credits_balance INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

### 3. Politiques RLS (Row Level Security) trop strictes

**Symptômes** :
- L'API reçoit 403 Forbidden
- Logs Supabase montrent "policy violation"

**Vérification** :
```sql
-- Dans Supabase SQL Editor
SELECT * FROM pg_policies WHERE tablename = 'users';
```

**Solution temporaire** (dev uniquement) :
```sql
-- DÉSACTIVER RLS temporairement pour tester
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
```

**Solution production** :
```sql
-- Permettre INSERT anonyme (inscription)
CREATE POLICY "Allow anonymous registration"
ON users FOR INSERT
WITH CHECK (true);

-- Permettre SELECT pour utilisateur authentifié
CREATE POLICY "Users can view own data"
ON users FOR SELECT
USING (auth.uid()::text = id::text);
```

---

### 4. JWT_SECRET_KEY vide ou invalide

**Symptômes** :
- Token généré mais invalide
- Erreur "Token invalide" après inscription

**Vérification** :
```bash
# Vérifier que JWT_SECRET_KEY n'est pas vide
grep JWT_SECRET_KEY .env
```

**Solution** :
Régénérer une clé forte :
```bash
# Linux/Mac
openssl rand -hex 32

# Windows PowerShell
[System.Convert]::ToBase64String((1..32 | ForEach-Object {Get-Random -Maximum 256}))
```

Mettre à jour `.env` :
```env
JWT_SECRET_KEY="<nouvelle_clé_générée>"
```

---

### 5. CORS bloqué (frontend)

**Symptômes** :
- Erreur dans console navigateur : "CORS policy"
- Requête n'atteint jamais le backend

**Vérification** :
Ouvrir console navigateur (F12) et regarder l'onglet Network

**Solution** :
Vérifier `config.py` :
```python
CORS_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Ajouter votre domaine frontend
]
```

---

### 6. Validation frontend échoue avant envoi

**Symptômes** :
- Message "Inscription impossible" sans appel API
- Champs formulaire invalides

**Vérification** :
- Email au bon format (ex: `user@example.com`)
- Mot de passe >= 6 caractères
- Nom >= 2 caractères

---

## 🛠️ PROCÉDURE DE DIAGNOSTIC

### Étape 1 : Vérifier logs backend

```bash
# Démarrer le backend en mode debug
cd apps/api
uvicorn src.main:app --reload --log-level debug
```

Chercher dans les logs :
- `Erreur vérification email existant`
- `Erreur création utilisateur Supabase`
- `Fallback mémoire activé`

### Étape 2 : Tester l'API directement

```bash
# Test inscription via curl
curl -X POST http://localhost:8001/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "password123"
  }'
```

**Réponse attendue** :
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "user_name": "Test User",
  "user_email": "test@example.com",
  "free_quota": 5,
  "paid_credits": 0
}
```

**Erreur possible** :
```json
{
  "detail": "Service d'inscription temporairement indisponible..."
}
```

### Étape 3 : Vérifier mode fallback

Si l'inscription échoue mais vous obtenez un token, le **mode fallback mémoire** est actif.

**Implications** :
- ✅ Vous pouvez vous inscrire et utiliser l'app
- ⚠️ Les comptes ne persistent pas (perdus au redémarrage)
- 🔴 Supabase n'est pas connecté

**Logs à chercher** :
```
Fallback mémoire activé pour inscription de test@example.com
```

---

## ✅ SOLUTIONS RAPIDES

### Solution 1 : Mode développement local (sans Supabase)

Si Supabase pose problème, utilisez le mode mémoire :

1. Les inscriptions fonctionnent en mémoire
2. Les comptes persistent pendant la session
3. Parfait pour développement/tests

**Aucune action requise**, le code gère déjà ce fallback.

### Solution 2 : Activer Supabase

1. **Vérifier connexion** :
   ```bash
   curl https://lhxbzflectkuysaklvji.supabase.co/rest/v1/
   ```

2. **Créer table users** (voir section 2 ci-dessus)

3. **Désactiver RLS temporairement** (dev uniquement)

4. **Redémarrer backend** :
   ```bash
   uvicorn src.main:app --reload
   ```

### Solution 3 : Message d'erreur détaillé

J'ai ajouté une gestion d'erreur améliorée dans `auth.py`.  
Redémarrez le backend et réessayez l'inscription.

Le message sera plus précis :
- "Service d'inscription temporairement indisponible" → Problème Supabase
- "Cette adresse email est déjà associée à un compte" → Email existe
- Token retourné → Inscription réussie (vérifier mode utilisé dans logs)

---

## 📊 CHECKLIST DE VÉRIFICATION

- [ ] Backend démarré sans erreur
- [ ] `.env` contient `SUPABASE_URL` et `SUPABASE_ANON_KEY`
- [ ] `.env` contient `JWT_SECRET_KEY` non vide
- [ ] Table `users` existe dans Supabase
- [ ] RLS désactivé (dev) ou politiques configurées (prod)
- [ ] Frontend peut joindre `http://localhost:8001`
- [ ] CORS autorise l'origine frontend
- [ ] Logs backend montrent la tentative d'inscription

---

## 🆘 SUPPORT

Si le problème persiste après ces vérifications :

1. **Copier les logs backend complets** (dernière tentative d'inscription)
2. **Copier l'erreur console navigateur** (F12 → Console → copier erreur)
3. **Vérifier Supabase Dashboard** → Logs → chercher erreurs récentes

**Fallback garanti** : Même si Supabase échoue, l'inscription fonctionne en mémoire locale.
