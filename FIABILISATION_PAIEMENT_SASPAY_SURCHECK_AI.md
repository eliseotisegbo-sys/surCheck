# MISSION ANTIGRAVITY — FIABILISATION DE SÛRCHECK AI (PHASE PAIEMENT & CONFIANCE)
## Périmètre : sécurité, paiement réel via SasPay, honnêteté des résultats, sources uniques de vérité
## Hors périmètre explicite : OCR (traité dans une mission séparée ultérieure)

**Contexte** : un audit externe indépendant a évalué SûrCheck AI et conclut que le produit a un bon socle technique (architecture modulaire, moteur hybride, abstraction de paiement déjà en place) mais n'est pas encore fiable pour une publication publique. Cette mission demande à Antigravity de **fiabiliser l'existant**, pas d'ajouter des fonctionnalités. Ne réécris rien qui fonctionne déjà correctement ; corrige, sécurise, explique, unifie.

**Règle non négociable pour toute cette mission** : toute clé API, tout secret (SasPay, Chariow, Supabase, JWT) est lu **exclusivement** depuis les variables d'environnement du fichier `.env` (via `settings` dans `config.py`, comme c'est déjà fait pour Chariow/Supabase). Aucune clé ne doit jamais apparaître en dur dans un fichier versionné, un commit, une documentation ou une réponse d'API. Le fichier `.env` réel ne doit jamais être committé ; seul `.env.example` (sans valeurs réelles) est versionné.

Respecte en tout temps `REGLES_ANTIGRAVITY_SURCHECK_AI.md` (vocabulaire non accusatoire, sobriété visuelle, architecture adaptée au marché béninois).

---

# 0. ORDRE D'EXÉCUTION OBLIGATOIRE

Ne pas paralléliser. Chaque priorité dépend de la précédente pour être testée en confiance.

1. Sécurité des secrets (section 1)
2. Correction des bugs bloquants indépendants de l'OCR (section 2)
3. Intégration paiement SasPay + correction du parcours de paiement (section 3)
4. Sources uniques de vérité — prix, contacts, versions (section 4)
5. Honnêteté des résultats — confiance, "indéterminé" (section 5)
6. Explicabilité du score — signal / preuve / décision (section 6)
7. Réputation communautaire réelle (section 7)
8. Suppression de la duplication moteur frontend/backend (section 8)
9. Pages de confiance et retrait des mentions "certifié" / "République du Bénin" (section 9)
10. Tests de bout en bout (section 10)

---

# 1. SÉCURITÉ DES SECRETS (PRIORITÉ ABSOLUE)

1. Considérer comme **compromis** et à régénérer immédiatement : `CHARIOW_API_KEY`, `CHARIOW_WEBHOOK_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`, `JWT_SECRET_KEY`, le mot de passe `DATABASE_URL`. Ces valeurs ont circulé en clair dans des fichiers du dépôt (`config.py` en valeurs par défaut, `APIChariow.md`, `.env.example`, `RAILWAY_DEPLOYMENT.md`).
2. Retirer **toutes** les valeurs par défaut sensibles codées en dur dans `config.py` (ex: `CHARIOW_API_KEY: str = os.getenv("CHARIOW_API_KEY", "sk_o0xs5yj1_...")`). Le fallback par défaut d'un secret ne doit jamais être une vraie valeur, uniquement une chaîne vide `""` ou lever une erreur explicite au démarrage si absent en production.
3. Nettoyer `APIChariow.md` et tout fichier `.md` du dépôt contenant une clé réelle : remplacer par une référence à `.env` uniquement.
4. Nettoyer l'historique Git (`git filter-repo` ou équivalent) une fois les secrets régénérés, pour qu'ils ne restent pas consultables dans un ancien commit.
5. Ajouter une vérification de démarrage dans `main.py` : si `ENVIRONMENT == "production"` et qu'une variable critique (`JWT_SECRET_KEY`, `CHARIOW_WEBHOOK_SECRET`, `SASPAY_WEBHOOK_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`) est vide ou égale à une valeur de développement connue, l'application refuse de démarrer et logue une erreur claire plutôt que de tourner silencieusement avec une sécurité dégradée.

---

# 2. CORRECTION DES BUGS BLOQUANTS INDÉPENDANTS DE L'OCR

Ces bugs empêchent le moteur de fonctionner correctement en production, indépendamment de toute image :

## 2.1 `RiskLevel` non importé dans `analyze.py`

Dans `apps/api/src/routers/analyze.py`, la fonction `_enrich_with_reputation` utilise `RiskLevel.ELEVE` alors que `RiskLevel` n'est jamais importé (seuls `ContentType` et `AnalysisFeedbackRequest` le sont depuis `..schemas`). Ceci provoque un `NameError` dès qu'un numéro ou une URL signalés sont détectés dans un message. Corriger l'import :

```python
from ..schemas import (
    AnalyzeTextRequest,
    AnalyzeUrlRequest,
    AnalysisResult,
    ContentType,
    RiskLevel,
    AnalysisFeedbackRequest,
)
```

## 2.2 `datetime` non importé dans `supabase_db.py`

Dans `apps/api/src/services/supabase_db.py`, la méthode `moderate_report` appelle `datetime.now().isoformat()` sans jamais importer `datetime`. Ajouter en tête de fichier :

```python
from datetime import datetime
```

Sans ce correctif, toute modération de signalement plante silencieusement côté serveur.

## 2.3 Métadonnées non tranchables dans `chariow_provider.py`

Dans `create_checkout()` (`apps/api/src/services/chariow_provider.py`), la ligne :

```python
"custom_metadata": {k: str(v)[:255] for k, v in custom_metadata.items()[:10]},
```

lève un `TypeError` car `dict.items()` retourne un objet `dict_items` non indexable en Python. Corriger en :

```python
"custom_metadata": {k: str(v)[:255] for k, v in list(custom_metadata.items())[:10]},
```

Appliquer la même correction si le même motif est répliqué dans le futur provider SasPay (section 3).

## 2.4 Validation de ces correctifs

Ajouter dans `apps/api/tests/test_api.py` ou `test_engine.py` un test qui déclenche réellement le chemin `_enrich_with_reputation` avec un numéro signalé simulé (mock de `check_phone_reputation` retournant un compte > 0), pour prouver que le `NameError` ne se reproduit pas. Ajouter un test unitaire direct sur la construction de `custom_metadata` avec plus de 10 clés pour vérifier qu'aucune exception n'est levée.

---

# 3. PAIEMENT RÉEL — INTÉGRATION SASPAY

## 3.1 Pourquoi SasPay en complément/alternative à Chariow

SasPay (`https://saspay.me`, documentation `https://docs.saspay.me`) est un agrégateur de paiement Mobile Money / carte pour l'Afrique de l'Ouest et du Centre, avec une API REST unique, un support explicite du XOF, des webhooks signés HMAC-SHA256, et une gestion d'idempotence native. L'architecture actuelle (`PaymentProvider` abstrait dans `payment_provider.py`, avec `ChariowPaymentProvider` comme implémentation) est **exactement** ce qu'il faut pour ajouter SasPay sans rien casser : créer `SaspayPaymentProvider` qui implémente la même interface abstraite (`create_checkout`, `verify_webhook_signature`, `parse_webhook`, `get_sale`), et choisir le provider actif via une variable d'environnement (`PAYMENT_PROVIDER=saspay` ou `chariow`), sans jamais modifier `credit_service.py` ni les tables PostgreSQL.

## 3.2 Étapes préalables (à faire une seule fois, hors code, avant l'implémentation)

Ces étapes ne se font PAS par clé API (elle n'existe pas encore) mais par jeton de session (JWT obtenu par login classique email/mot de passe), exactement comme le tableau de bord `app.saspay.me` :

1. **Créer le compte utilisateur** : `POST https://api.saspay.me/api/v1/users/` avec `full_name`, `email`, `country` (UUID de pays, récupéré via `GET /countries/`), `password`. Endpoint public, aucune authentification requise.
2. **Vérifier l'email** : `POST /api/v1/auth/verify-email/` avec le code reçu par email.
3. **Se connecter** : `POST /api/v1/auth/login/` renvoie `{"tokens": {"access": "...", "refresh": "..."}}`. Ce jeton `access` sert de `Authorization: Bearer <access>` pour les étapes suivantes **uniquement** — ce n'est jamais la clé API finale.
4. **Créer le marchand** (la "boutique") : `POST /api/v1/merchants/` avec `name`, `website_url`, `category`. Démarre avec `kyc_status: "NONE"` et `is_active: false`.
5. **Soumettre le dossier KYC** : `POST /api/v1/merchant-kyc/` (infos entreprise : `company_name`, `rccm_number`, `ifu_number`), puis uploader chaque pièce via `POST /api/v1/merchant-kyc/upload/` (multipart, 10 Mo max, renvoie une `url`), puis attacher chaque URL au dossier via `POST /api/v1/merchant-kyc/{id}/documents/` avec `document_type` (`ID_CARD`, `PASSPORT`, `SELFIE`, `BUSINESS_REGISTRATION`, `FISCAL`, `OTHER`).
6. **Attendre la validation manuelle** par un administrateur SasPay (email de notification, `kyc_status` passe à `"VERIFIED"`).
7. **Créer la clé API** une fois validé : `POST /api/v1/merchant-api-keys/` avec `{"name": "Backend production", "environment": "SANDBOX", "scope": "PAYIN"}`. Commencer en `SANDBOX` (préfixe `sk_test_`) pour tous les tests, ne passer en `LIVE` (préfixe `sk_live_`) qu'après validation complète du parcours en section 3.5. Le champ `secret` (clé complète) n'est renvoyé **qu'une seule fois** dans cette réponse : le copier immédiatement dans le gestionnaire de secrets/`.env`, il n'est plus jamais récupérable ensuite.
8. **Limiter le scope** : une clé destinée uniquement à encaisser (le cas de SûrCheck aujourd'hui, pas de retrait/payout prévu) doit avoir `scope: "PAYIN"`, jamais `"BOTH"` par défaut, pour réduire la surface d'attaque si la clé fuit un jour.

Toute la gestion du compte marchand, du KYC et des clés API elles-mêmes reste **exclusivement** accessible depuis `app.saspay.me` (jeton de session) — jamais par clé API, pas même en lecture. Ne pas tenter d'automatiser cette partie dans le backend SûrCheck : elle est hors du périmètre applicatif normal.

## 3.3 Variables `.env` à ajouter (aucune valeur réelle dans ce document ni dans le code)

Ajouter dans `.env.example` (sans valeurs) et documenter dans `config.py` exactement comme les variables Chariow existantes :

```env
PAYMENT_PROVIDER=saspay              # ou "chariow" — bascule le provider actif sans changer le code
SASPAY_API_KEY=                      # sk_test_... en développement, sk_live_... en production
SASPAY_BASE_URL=https://api.saspay.me/api/v1
SASPAY_WEBHOOK_SECRET=               # signing_secret du webhook, récupéré UNE SEULE FOIS depuis app.saspay.me
SASPAY_DEFAULT_COUNTRY=BJ
SASPAY_DEFAULT_CURRENCY=XOF
```

Dans `config.py`, ajouter ces champs à `Settings` sur le modèle exact des champs `CHARIOW_*` déjà présents, avec des valeurs par défaut **vides** (jamais de vraie clé en dur, voir section 1.2).

## 3.4 Création de `SaspayPaymentProvider`

Créer `apps/api/src/services/saspay_provider.py`, implémentant `PaymentProvider` (déjà défini dans `payment_provider.py`, à ne pas modifier) :

```python
"""Implémentation du fournisseur SasPay pour SûrCheck AI.
Conforme à la documentation officielle https://docs.saspay.me/
Gère la création de session de checkout hébergé, la validation HMAC-SHA256
des webhooks et la réconciliation.
"""

import hashlib
import hmac
import json
import logging
import time
from typing import Optional, Dict, Any

import httpx

from ..config import settings
from .payment_provider import PaymentProvider, CheckoutSession, WebhookEvent

logger = logging.getLogger("surcheck.saspay")

WEBHOOK_TOLERANCE_SECONDS = 300


class SaspayPaymentProvider(PaymentProvider):
    """Fournisseur de paiement SasPay (checkout hébergé)."""

    def __init__(self):
        self.api_key = settings.SASPAY_API_KEY
        self.base_url = settings.SASPAY_BASE_URL.rstrip("/")
        self.webhook_secret = settings.SASPAY_WEBHOOK_SECRET

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def create_checkout(
        self,
        product_id: str,  # non utilisé par SasPay (pas de product_id, montant direct) — conservé pour compatibilité d'interface
        email: str,
        first_name: str,
        last_name: str,
        phone_number: str,
        country_code: str,
        custom_metadata: Dict[str, str],
        redirect_url: Optional[str] = None,
    ) -> CheckoutSession:
        """Crée une session de checkout hébergé SasPay.

        NOTE IMPORTANTE : contrairement à Chariow, l'endpoint de checkout SasPay
        ne supporte PAS le header Idempotency-Key. Un double appel réseau crée
        deux sessions distinctes — sans conséquence financière tant qu'aucune
        des deux n'est payée, mais éviter les doubles soumissions côté frontend.
        """
        amount_str = custom_metadata.get("amount_fcfa", "0")
        payload: Dict[str, Any] = {
            "amount": amount_str,
            "currency": settings.SASPAY_DEFAULT_CURRENCY,
            "description": custom_metadata.get("description", "Analyse SûrCheck AI"),
            "country": country_code.upper() or settings.SASPAY_DEFAULT_COUNTRY,
            "customer_email": email.strip().lower(),
            "customer_name": f"{first_name.strip()} {last_name.strip()}".strip() or "Client SûrCheck",
            "customer_phone": phone_number.strip(),
            "metadata": {k: str(v)[:255] for k, v in list(custom_metadata.items())[:10]},
        }
        if redirect_url:
            payload["return_url"] = redirect_url

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    f"{self.base_url}/checkout-sessions/",
                    headers=self._headers(),
                    json=payload,
                )

            data = res.json() if res.content else {}

            if res.status_code != 201:
                logger.error(f"Erreur API SasPay ({res.status_code}): {res.text}")
                error_msg = data.get("message") or f"Erreur SasPay HTTP {res.status_code}"
                return CheckoutSession(step="error", message=error_msg, raw_response=data)

            return CheckoutSession(
                step="payment",
                checkout_url=data.get("checkout_url"),
                sale_id=data.get("id"),
                message=None,
                raw_response=data,
            )

        except Exception as e:
            logger.error(f"Exception lors de l'appel checkout SasPay: {e}")
            return CheckoutSession(
                step="error",
                message="Impossible de contacter le serveur de paiement SasPay.",
                raw_response={"error": str(e)},
            )

    def verify_webhook_signature(self, raw_body: bytes, signature_header: str) -> bool:
        """Valide la signature HMAC-SHA256 du webhook SasPay.
        La vérification de l'âge du timestamp est faite séparément dans parse_webhook
        via l'en-tête X-Webhook-Timestamp, transmis par le routeur (voir section 3.6).
        """
        if not self.webhook_secret:
            logger.warning("SASPAY_WEBHOOK_SECRET non configuré — validation désactivée (mode dev)")
            return True
        if not signature_header:
            return False
        # La comparaison réelle nécessite timestamp + body, voir verify_webhook_full()
        return True  # signature complète vérifiée dans verify_webhook_full()

    def verify_webhook_full(self, raw_body: bytes, signature: str, timestamp: str) -> bool:
        """Vérification complète recommandée par SasPay : âge + signature HMAC."""
        if not self.webhook_secret:
            return True
        try:
            if abs(int(time.time()) - int(timestamp)) > WEBHOOK_TOLERANCE_SECONDS:
                logger.warning("Webhook SasPay rejeté : horodatage hors tolérance (5 min)")
                return False
        except (ValueError, TypeError):
            return False

        signed = f"{timestamp}.".encode() + raw_body
        expected = hmac.new(self.webhook_secret.encode(), signed, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    def parse_webhook(self, raw_body: bytes, headers: Dict[str, str]) -> WebhookEvent:
        """Parse l'enveloppe SasPay {event, data} et la normalise."""
        try:
            payload = json.loads(raw_body)
        except Exception:
            payload = {}

        event_name = payload.get("event", "unknown")
        data = payload.get("data", {})

        status_map = {
            "transaction.success": "successful",
            "transaction.failed": "failed",
            "transaction.cancelled": "abandoned",
        }
        normalized_status = status_map.get(event_name, "unknown")

        metadata = data.get("metadata", {})

        return WebhookEvent(
            event_name=event_name,
            delivery_id=data.get("id", ""),
            sale_id=data.get("reference", data.get("id", "")),
            transaction_id=metadata.get("internal_order_ref"),
            product_id=None,
            user_id=metadata.get("surcheck_user_id"),
            pack_id=metadata.get("credit_pack"),
            credits=int(metadata.get("credits", 0)) if str(metadata.get("credits", "")).isdigit() else 0,
            amount=int(float(data.get("net_amount", data.get("amount", 0)))),
            currency=data.get("currency", "XOF"),
            status=normalized_status,
            customer_email=None,
            raw_payload=payload,
        )

    async def get_sale(self, sale_id: str) -> Dict[str, Any]:
        """Récupère le détail d'une transaction pour réconciliation."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{self.base_url}/transactions/{sale_id}/",
                    headers=self._headers(),
                )
            if res.status_code == 200:
                return res.json()
            return {"error": f"HTTP {res.status_code}", "detail": res.text}
        except Exception as e:
            return {"error": str(e)}


saspay_provider = SaspayPaymentProvider()
```

Points à respecter strictement, tirés de la documentation officielle SasPay :

- **`amount` n'est pas ce que le client paie réellement.** Selon `fee_charge_mode` (`ADD_ON` ou `DEDUCTED`), le montant réellement débité (`charged`) et le montant net reçu par SûrCheck (`net_amount`) diffèrent de `amount`. Utiliser `net_amount` pour créditer les comptes, jamais `amount` seul.
- **`msisdn` est vide pour les transactions antérieures au 17 août 2026** dans l'historique SasPay — non pertinent pour un nouveau compte, mais à garder en tête si une réconciliation historique est un jour nécessaire.
- **Le `signing_secret` du webhook n'est jamais consultable après coup** : il n'apparaît qu'à la création du webhook (ou lors d'une rotation), exclusivement depuis le tableau de bord `app.saspay.me`. Le copier immédiatement dans `.env`.
- **La création, modification, suppression d'un webhook se fait uniquement depuis le tableau de bord**, jamais par clé API. Créer le webhook manuellement sur `app.saspay.me` pointant vers `https://<url-railway>/api/v1/payment/webhook/saspay`, avec les abonnements `transaction.success`, `transaction.failed`, `transaction.cancelled`.

## 3.5 Sélection dynamique du provider actif

Dans `apps/api/src/routers/payment.py`, remplacer l'import direct de `chariow_provider` par une résolution dynamique basée sur `settings.PAYMENT_PROVIDER` :

```python
from ..services.chariow_provider import chariow_provider
from ..services.saspay_provider import saspay_provider

def get_active_payment_provider():
    if settings.PAYMENT_PROVIDER == "saspay":
        return saspay_provider
    return chariow_provider

active_provider = get_active_payment_provider()
```

Utiliser `active_provider` partout où `chariow_provider` était appelé directement dans `create_checkout_session` et `handle_chariow_pulse`. Renommer si besoin la route webhook générique `/payment/webhook` en conservant une route dédiée par prestataire (`/payment/webhook/chariow` et `/payment/webhook/saspay`) pour permettre de faire tourner les deux prestataires en parallèle pendant la phase de bascule, sans jamais mélanger leurs vérifications de signature respectives.

## 3.6 Vérification de signature du webhook SasPay dans le routeur

Adapter `handle_chariow_pulse` (ou créer `handle_saspay_webhook`) pour utiliser la vérification complète à deux facteurs (âge + signature) exigée par SasPay :

```python
@router.post("/webhook/saspay")
async def handle_saspay_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("x-webhook-signature", "")
    timestamp = request.headers.get("x-webhook-timestamp", "")

    if not saspay_provider.verify_webhook_full(raw_body, signature, timestamp):
        logger.warning("Webhook SasPay rejeté : signature ou horodatage invalide")
        raise HTTPException(status_code=401, detail="Signature de webhook invalide.")

    event = saspay_provider.parse_webhook(raw_body, dict(request.headers))
    # ... même logique de traitement idempotent que pour Chariow (credit_service.add_credits_idempotent) ...
```

Réutiliser **sans duplication** la logique déjà existante de `credit_service.add_credits_idempotent` — elle est déjà agnostique du prestataire (elle prend `sale_id`, `credits`, `amount_fcfa`, `pack_code`, `raw_event_id`, `raw_payload`), donc aucune modification n'y est nécessaire.

## 3.7 Idempotence côté paiement direct (softpay, optionnel à ce stade)

Si un mode de paiement push direct (softpay, sans page hébergée) est envisagé plus tard pour certains réseaux, l'endpoint `POST /payments/softpay/` de SasPay supporte un header `Idempotency-Key` optionnel mais fortement recommandé : générer un UUID par intention de paiement (pas par tentative), le réutiliser pour tout retry de cette même intention, en changer pour toute nouvelle intention. Ceci n'est pas requis pour la V1 de cette mission (le checkout hébergé suffit et ne le supporte de toute façon pas), mais documenter ce point dans le code pour une itération future.

## 3.8 Tests de paiement réels à ajouter (`test_saspay_payment.py`)

Sur le modèle exact de `test_chariow_credits.py` déjà existant :

1. Test de vérification de signature HMAC valide/invalide/expirée (>5 min).
2. Test de parsing de l'enveloppe `{event, data}` pour `transaction.success`, `transaction.failed`, `transaction.cancelled`.
3. Test que `net_amount` (et non `amount`) est bien utilisé pour créditer le compte.
4. Test de bascule de provider (`PAYMENT_PROVIDER=saspay` vs `chariow`) sans changer le comportement de `credit_service`.
5. Test end-to-end en environnement `SANDBOX` réel (pas seulement mocké) : checkout créé → webhook de test reçu (`webhook.test`) → vérifier que la route répond `200` sans planter, avant de brancher un vrai paiement sandbox.

---

# 4. SOURCES UNIQUES DE VÉRITÉ

## 4.1 Prix

Créer `apps/api/src/pricing.py` (backend, source de vérité unique) exportant les 4 packs déjà définis dans `PACKS` (`payment.py`) sans changement de valeurs pour l'instant — mais s'assurer qu'aucun autre fichier (documentation, frontend, seeds) n'affiche un prix différent. Le frontend (`fetchPacks()` dans `api.ts`) doit **toujours** afficher les valeurs retournées par `GET /payment/packs`, jamais son fallback local codé en dur (actuellement présent dans `api.ts` en cas d'échec réseau) sans le signaler clairement à l'utilisateur comme non confirmé serveur.

## 4.2 Contacts opérateurs (numéros d'urgence)

Créer `apps/web/src/lib/operator-contacts.ts` :

```ts
export const OPERATOR_CONTACTS = {
  mtn_bj: { name: "MTN Bénin", number: "111", description: "Opposition et blocage compte" },
  moov_bj: { name: "Moov Money Bénin", number: "100", description: "Assistance et litige transfert" },
  ocrc: { name: "Police / OCRC Cotonou", number: "21 30 08 62", description: "Office Central de Répression de la Cybercriminalité" },
} as const;
```

Remplacer **toutes** les occurrences en dur de "111", "100", "123" dans `scorer.py`, `page.tsx`, `guide_reflexe_surcheck.html` par une référence à cette source unique (créer l'équivalent Python si nécessaire côté backend pour les recommandations générées par `scorer.py`). Vérifier manuellement chaque numéro auprès des opérateurs avant publication — ne pas se fier au contenu déjà présent dans le dépôt, incohérent d'un fichier à l'autre.

## 4.3 Versioning du moteur

Étendre `AnalysisResult.engine_version` (déjà présent) pour qu'il encode distinctement : version du moteur de règles, version du corpus ML, version de la base de réputation. Format proposé : `"rules:2026.09.1|ml:0.4|reputation:2026.09"`. Stocker ces trois valeurs séparément dans `analysis_features` ou dans une nouvelle colonne JSON `engine_versions` sur `analyses`, pour pouvoir répondre précisément à "pourquoi ce résultat a changé".

---

# 5. HONNÊTETÉ DES RÉSULTATS — NIVEAU DE CONFIANCE ET "INDÉTERMINÉ"

1. Le champ `confidence_level` existe déjà (`elevee`, `moyenne`, `incertain`) dans `AnalysisResult` et `scorer.py`. L'exposer clairement dans l'interface (`page.tsx`) à côté du niveau de risque, pas seulement en interne.
2. Ajouter un niveau de risque supplémentaire `RiskLevel.INDETERMINE` pour les cas où le texte est trop court, trop ambigu, ou où aucune source externe n'a pu être consultée (URL non vérifiable, réputation non disponible). Ne jamais forcer un score de risque ferme quand les données sont insuffisantes.
3. Ne jamais afficher un verdict positif ferme ("ce lien est sûr") sur une vérification qui n'a pas pu être effectuée. Si `check_url_reputation` échoue ou ne retourne aucune donnée, l'analyse doit le dire explicitement ("Nous n'avons pas pu vérifier suffisamment cette adresse.") plutôt que de laisser le score par défaut suggérer une sécurité non prouvée.

---

# 6. EXPLICABILITÉ DU SCORE — SIGNAL / PREUVE / DÉCISION

Chaque signal détecté (`DetectedSignal`, déjà bien structuré avec `code`, `title`, `category`, `weight`, `evidence`, `advice`) doit être affiché dans l'interface avec cette séparation à trois niveaux, déjà présente dans le schéma mais pas encore assez visible côté UI :

```
Signal détecté        → title
Preuve                → evidence (extrait exact ayant déclenché le signal)
Pourquoi cela compte   → advice reformulé en explication, pas juste en conseil d'action
Décision recommandée   → recommendations (déjà présent, section distincte)
```

Ne jamais fusionner "signal détecté" et "verdict" dans la même phrase. Le score final (déjà calculé dans `scorer.py`) doit rester présenté comme une **synthèse** de ces signaux, jamais comme la donnée d'entrée de l'explication.

---

# 7. RÉPUTATION COMMUNAUTAIRE RÉELLE

Le schéma de données (`reported_numbers`, `reported_urls`, `reputation_events`) le permet déjà. Modifier `_enrich_with_reputation` (`analyze.py`) et le format retourné par `check_phone_reputation`/`check_url_reputation` (`supabase_db.py`) pour renvoyer, en plus du compte total, une **ventilation par catégorie** (ex: "3 signalements liés à une demande d'argent, 2 liés à une fausse livraison") plutôt qu'un chiffre brut. Cela nécessite d'agréger `category` depuis la table `reports` liée au `target_hash`, pas seulement le compteur de `reported_numbers`/`reported_urls`.

---

# 8. SUPPRESSION DE LA DUPLICATION FRONTEND/BACKEND DU MOTEUR

`engine.ts` (frontend) et `rules.py`/`scorer.py` (backend) contiennent une logique de scoring dupliquée avec un risque de divergence. Conserver `engine.ts` uniquement comme **indicateur d'indisponibilité honnête**, jamais comme équivalent silencieux du backend : si l'appel à `checkContent` échoue, l'interface doit afficher clairement "Analyse temporairement indisponible, réessayez dans un instant" plutôt que de basculer silencieusement vers `analyzeContentLocally` en présentant le résultat comme équivalent à une analyse serveur complète. Le fallback local peut rester disponible mais doit être visuellement et textuellement distingué (ex: bandeau "Estimation hors ligne, non confirmée par nos serveurs").

---

# 9. PAGES DE CONFIANCE ET RETRAIT DES MENTIONS INAPPROPRIÉES

1. Supprimer de `guide_reflexe_surcheck.html` toute mise en forme évoquant un document administratif officiel ("SûrCheck AI — République du Bénin", tricolore institutionnel, "Guide Réflexe Citoyen", "Réf. SC-BJ/2026-PUB"). Remplacer par un positionnement explicite : *"SûrCheck AI est un service privé d'aide à la vérification de contenus et transactions potentiellement frauduleux. Non affilié à une administration publique."*
2. Retirer "Attestation certifiée", "Document officiel opposable", "Certifié Bénin" de `page.tsx` (section analyse débloquée). Remplacer par "Rapport SûrCheck" ou "Rapport d'analyse".
3. Créer/publier les pages manquantes signalées par l'audit : `/cgu`, `/confidentialite`, `/comment-ca-marche`, `/sources`, `/limites` (le contenu CGU/Confidentialité a déjà été rédigé précédemment — vérifier qu'il est bien publié et lié depuis le footer, pas seulement rédigé en `.md` non déployé).

---

# 10. TESTS DE BOUT EN BOUT (APRÈS LES SECTIONS 1 À 9)

Ajouter des tests de scénario complet (pas seulement unitaires) couvrant, sans jamais toucher à l'OCR :

1. Analyse texte non connectée → résultat affiché sans blocage de compte.
2. Achat de pack via SasPay sandbox → webhook reçu → crédits ajoutés → solde correct.
3. Webhook SasPay reçu deux fois (même `id`) → un seul crédit de compte, pas de doublon.
4. Paiement annulé (`transaction.cancelled`) → aucun crédit ajouté.
5. Numéro signalé → réputation ventilée par catégorie affichée dans le résultat.
6. URL non vérifiable → résultat "Indéterminé", jamais un verdict positif ferme.
7. Backend d'analyse indisponible → message honnête affiché côté frontend, pas de faux résultat local présenté comme équivalent.
8. Double clic sur "Débloquer avec 1 crédit" → une seule consommation de crédit (déjà testé côté `credit_service`, à revérifier après les changements de provider).

---

# RAPPEL FINAL

Ne pas commencer par le design ni par de nouvelles fonctionnalités. L'objectif de cette mission unique est que chaque promesse déjà visible dans l'application (score, réputation, paiement, confiance) corresponde à quelque chose de réellement exécuté, vérifiable et testé. L'OCR reste explicitement hors périmètre : ne pas toucher à `ocr.py`, `analyze_image`, ni au champ `file: bytes` de l'endpoint image dans cette mission.
