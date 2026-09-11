# ⚠️ ACTION REQUISE : Vérification synchronisation moteur frontend/backend

**Date :** 2026-09-09  
**Priorité :** 🟡 HAUTE  
**Durée estimée :** 1 heure

---

## 📋 CONTEXTE

Le fichier `apps/web/src/lib/engine.ts` contient une **implémentation locale partielle** du moteur d'analyse, utilisée comme **fallback résilience** en cas d'erreur API backend.

### Utilisation actuelle

```typescript
// apps/web/src/lib/api.ts (ligne 38-41)
try {
  const res = await fetch(endpoint, ...);
  return data; // Résultat backend
} catch (err) {
  console.warn("Backend non joignable, fallback local");
  return analyzeContentLocally(content, type); // ← MOTEUR LOCAL
}
```

**Cas d'usage légitime :**
- ✅ Connexion mobile lente/instable
- ✅ Latence backend élevée
- ✅ Downtime temporaire Railway

**Risque identifié :**
- ⚠️ Règles backend (21 règles) != Règles frontend (10 règles visible)
- ⚠️ Logique fuzzy matching backend absente frontend
- ⚠️ Négation/obfuscation backend absentes frontend
- ⚠️ Scoring co-occurrence backend absent frontend

---

## 🔍 ANALYSE DIVERGENCES

### Backend (`apps/api/src/engine/rules.py`)

**21 règles complètes :**
1. MONEY_REQUEST (Demande argent préalable)
2. OTP_PIN_REQUEST (Code secret/OTP)
3. URGENCY (Pression temporelle)
4. UNREAL_GAIN (Promesse gain irréaliste)
5. THREATENING (Menaces/intimidation)
6. IDENTITY_THEFT_BANK (Usurpation banque)
7. IDENTITY_THEFT_OPERATOR (Usurpation opérateur)
8. CRYPTO_INVESTMENT (Investissement crypto)
9. ROMANCE_SCAM (Arnaque sentimentale)
10. FAKE_LOTTERY (Faux tirage/loterie)
11. FAKE_JOB_OFFER (Fausse offre emploi)
12. SUSPICIOUS_LINK (Lien raccourci suspect)
13. FAKE_PARCEL (Colis bloqué/douane)
14. FAKE_TRANSFER (Transfert erroné)
15. FAKE_VISA_IMMIGRATION (Visa/immigration frauduleux)
16. FAKE_CHARITY (Fausse charité/don)
17. MEDICAL_URGENCY (Urgence médicale fabricée)
18. **✅ NOUVEAU** FAKE_TECH_SUPPORT (Support technique frauduleux)
19. **✅ NOUVEAU** FAKE_DELIVERY_CUSTOMS (Colis/douane avancé)
20. **✅ NOUVEAU** ROMANCE_IMPERSONATION (Usurpation proche)
21. **✅ NOUVEAU** FAKE_REFUND (Faux remboursement)

**+ Fonctionnalités avancées :**
- ✅ Fuzzy matching (rapidfuzz, 40 termes, seuil 85%)
- ✅ Gestion négation (18 marqueurs + 9 récit)
- ✅ Normalisation obfuscation
- ✅ Co-occurrence signaux (+10 à +25)
- ✅ ML classification (TF-IDF + 300+ exemples)

### Frontend (`apps/web/src/lib/engine.ts`)

**10 règles visibles (lecture partielle) :**
1. RULE_OTP_PIN (Code secret)
2. RULE_MONEY_REQ (Frais préalables)
3. RULE_URGENCY (Pression temporelle)
4. RULE_UNREAL_GAIN (Promesse gain)
5. RULE_SUSPICIOUS_LINK (Lien raccourci)
6. RULE_USURPATION_MOMO (Usurpation opérateur)
7. RULE_FALSE_TRANSFER (Faux transfert)
8. RULE_PARCEL_CUSTOMS (Colis/douane)
9. RULE_CRYPTO_INVESTMENT (Crypto)
10. *(fichier tronqué, peut en contenir plus)*

**Fonctionnalités absentes :**
- ❌ Fuzzy matching
- ❌ Gestion négation
- ❌ Normalisation obfuscation
- ❌ Co-occurrence
- ❌ ML classification

---

## ⚖️ DÉCISION : CONSERVER OU SUPPRIMER ?

### Option A : **CONSERVER et synchroniser** (Recommandé ✅)

**Avantages :**
- ✅ Résilience mobile (UX améliorée en cas de latence)
- ✅ Analyse instantanée hors-ligne
- ✅ Fonctionnalité différenciante

**Inconvénients :**
- ⚠️ Maintenance double (risque divergence)
- ⚠️ Résultats légèrement différents backend/frontend
- ⚠️ Taille bundle frontend augmentée (~50 KB)

**Actions requises :**
1. Lire fichier `engine.ts` complet (actuellement tronqué)
2. Comparer les 21 règles backend vs frontend
3. Synchroniser règles manquantes
4. Ajouter disclaimer dans UI : "Analyse hors-ligne simplifiée"
5. Documenter stratégie fallback dans `README.md`

### Option B : **SUPPRIMER et forcer backend** (Simplicité)

**Avantages :**
- ✅ Une seule source de vérité (cohérence garantie)
- ✅ Maintenance simplifiée
- ✅ Bundle frontend allégé

**Inconvénients :**
- ❌ Erreur utilisateur si backend indisponible
- ❌ UX dégradée en cas de latence mobile
- ❌ Perte fonctionnalité résilience

**Actions requises :**
1. Supprimer `apps/web/src/lib/engine.ts`
2. Modifier `apps/web/src/lib/api.ts` :
   ```typescript
   } catch (err) {
     throw new Error(
       "Service temporairement indisponible. Veuillez réessayer."
     );
   }
   ```
3. Ajouter gestion erreur UI avec message utilisateur

---

## 🎯 RECOMMANDATION

### **Option A : CONSERVER et synchroniser** ✅

**Justification :**

1. **Contexte africain :** Connexions mobiles instables fréquentes (2G/3G)
2. **UX critique :** Analyse instantanée = promesse produit
3. **Risque divergence maîtrisable :** Tests E2E peuvent valider cohérence

**Stratégie de synchronisation :**

#### Phase 1 : Audit complet (30 min)

```bash
# Lire fichier engine.ts complet
cat apps/web/src/lib/engine.ts | wc -l  # Nombre lignes total

# Comparer règles
# Backend : apps/api/src/engine/rules.py (21 règles)
# Frontend : apps/web/src/lib/engine.ts (? règles)
```

#### Phase 2 : Synchronisation règles (1h)

**Actions :**
1. Ajouter 4 nouvelles règles backend dans frontend :
   - `RULE_FAKE_TECH_SUPPORT`
   - `RULE_FAKE_DELIVERY_CUSTOMS` (si différente de `RULE_PARCEL_CUSTOMS`)
   - `RULE_ROMANCE_IMPERSONATION`
   - `RULE_FAKE_REFUND`

2. Harmoniser noms règles :
   - Backend : `MONEY_REQUEST`
   - Frontend : `RULE_MONEY_REQ`
   - → Décision : Garder préfixe `RULE_` frontend pour clarté

3. Synchroniser poids :
   - Backend : Poids 15-50
   - Frontend : Vérifier cohérence

#### Phase 3 : Documentation disclaimer (15 min)

**Ajouter dans UI frontend :**

```typescript
// apps/web/src/app/page.tsx (afficher si fallback utilisé)
{isFallbackUsed && (
  <div className="bg-yellow-50 border border-yellow-200 p-3 rounded mb-4">
    <p className="text-sm text-yellow-800">
      ⚠️ <strong>Mode hors-ligne :</strong> Analyse simplifiée effectuée localement.
      Pour une évaluation complète, veuillez réessayer avec une connexion stable.
    </p>
  </div>
)}
```

**Ajouter dans `engine.ts` :**

```typescript
/**
 * IMPORTANT : Ce moteur local est une VERSION SIMPLIFIÉE du backend.
 * Il sert de fallback en cas d'erreur réseau pour maintenir l'UX.
 * 
 * Limitations vs backend complet :
 * - Pas de fuzzy matching (tolère moins les fautes frappe)
 * - Pas de gestion négation (risque faux positifs sur prévention)
 * - Pas de ML classification (catégorie moins précise)
 * - Pas de réputation communauté (signalements non consultés)
 * 
 * Synchronisation : Dernière mise à jour 2026-09-09
 */
```

#### Phase 4 : Tests validation (30 min)

**Tests à ajouter :**

```typescript
// apps/web/src/lib/__tests__/engine.test.ts

describe("Fallback local engine", () => {
  it("détecte règles critiques identiques au backend", () => {
    const criticalRules = [
      "OTP_PIN",
      "MONEY_REQ",
      "URGENCY",
      "UNREAL_GAIN",
      "SUSPICIOUS_LINK",
    ];
    
    criticalRules.forEach((rule) => {
      const local = analyzeContentLocally(`Test ${rule}`, "text");
      expect(local.signals.some(s => s.code.includes(rule))).toBe(true);
    });
  });

  it("retourne score cohérent ±10 points backend", async () => {
    const testContent = "Envoyez votre code secret pour gagner 1 million FCFA urgent";
    
    // Analyse locale
    const local = analyzeContentLocally(testContent, "text");
    
    // Analyse backend (mock)
    const backend = await checkContent(testContent, "text");
    
    // Tolérance ±10 points (local moins précis)
    expect(Math.abs(local.risk_score - backend.risk_score)).toBeLessThan(10);
  });
});
```

---

## ✅ CHECKLIST ACTIONS

### Priorité 🟡 HAUTE (Semaine 1)

- [ ] **1. Audit complet `engine.ts`**
  - [ ] Lire fichier complet (actuellement tronqué à 100 lignes)
  - [ ] Compter nombre total règles frontend
  - [ ] Lister règles manquantes vs backend

- [ ] **2. Synchronisation règles**
  - [ ] Ajouter 4 nouvelles règles backend dans frontend
  - [ ] Vérifier cohérence poids
  - [ ] Tester localement règles ajoutées

- [ ] **3. Documentation disclaimer**
  - [ ] Ajouter commentaire limitations dans `engine.ts`
  - [ ] Ajouter bandeau UI "Mode hors-ligne" si fallback
  - [ ] Documenter stratégie dans `README.md`

- [ ] **4. Tests validation**
  - [ ] Tests règles critiques identiques
  - [ ] Tests cohérence score ±10 points
  - [ ] Tests fallback automatique si API down

### Priorité 🟢 MOYENNE (Semaine 2)

- [ ] **5. Monitoring fallback**
  - [ ] Logger utilisation fallback (analytics)
  - [ ] Mesurer fréquence API errors
  - [ ] Dashboard taux fallback vs backend

- [ ] **6. Optimisation bundle**
  - [ ] Lazy-load `engine.ts` (import dynamique)
  - [ ] Minifier règles (réduire taille)
  - [ ] Vérifier impact bundle size (<50 KB)

---

## 📊 CRITÈRES DE VALIDATION

**Synchronisation réussie si :**

1. ✅ **Cohérence règles critiques** : 100% (5/5 règles testées identiques)
2. ✅ **Cohérence score** : ±10 points maximum backend/frontend
3. ✅ **Documentation claire** : Limitations expliquées dans code + UI
4. ✅ **Tests passent** : Tests validation règles + score passent
5. ✅ **Bundle size** : +50 KB maximum (impact acceptable mobile)

**Seuils d'alerte :**

- 🔴 Score diverge >20 points → Revoir logique scoring frontend
- 🟡 Fallback utilisé >30% → Investiguer stabilité backend
- 🟢 Fallback utilisé <10% → Bon équilibre résilience/cohérence

---

## 🎯 DÉCISION FINALE

**Recommandation :** ✅ **CONSERVER engine.ts comme fallback + SYNCHRONISER règles**

**Justification :**
- Fonctionnalité résilience = valeur ajoutée forte contexte africain
- Risque divergence maîtrisable avec tests E2E
- Documentation claire évite confusion utilisateurs

**Actions immédiates :**
1. Lire `engine.ts` complet
2. Synchroniser 4 règles manquantes
3. Ajouter disclaimer UI

**Durée totale :** 1 heure (Priorité HAUTE)

---

**Document créé le :** 2026-09-09  
**Auditeur :** Antigravity AI Agent  
**Lié à :** SURCHECK_RELIABILITY_PHASE_AUDIT.md (section 6.3 Limitations)
