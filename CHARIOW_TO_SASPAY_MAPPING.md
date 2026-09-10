# MAPPING DÉTAILLÉ CHARIOW → SASPAY

**Date** : 2026-09-09  
**Objectif** : Guide technique complet de transformation des appels API

---

## 🔄 1. CRÉATION CHECKOUT (Initiation de paiement)

### Chariow `/v1/checkout`
```python
# Requête Chariow actuelle
payload = {
    "product_id": "prd_060n1o9q",  # Pack défini dans dashboard
    "email": "client@example.com",
    "first_name": "Awa",
    "last_name": "Sossou",
    "phone": {
        "number": "97505050",  # Sans indicatif pays
        "country_code": "BJ"
    },
    "custom_metadata": {
        "surcheck_user_id": "user_123",
        "credit_pack": "pack_10",
        "credits": "10",
        "internal_order_ref": "uuid-123"
    },
    "redirect_url": "https://sur-check.vercel.app/paiement/success?order_ref=uuid-123"
}

# Réponse Chariow
{
    "message": "Checkout créé",
    "data": {
        "step": "payment",  # ou "completed", "already_purchased", "error"
        "sale_id": "sal_abc123",
        "payment": {
            "checkout_url": "https://checkout.chariow.com/xyz"
        }
    }
}
```

### SasPay `/v1/payments/softpay/`
```python
# Transformation pour SasPay
payload = {
    "amount": "2500.00",  # ⚠️ NOUVEAU : montant explicite (depuis PACKS serveur)
    "currency": "XOF",    # ⚠️ NOUVEAU : toujours XOF pour Bénin
    "country": "BJ",      # Extrait de phone.country_code
    "network": "mtn_bj",  # ⚠️ NOUVEAU : détecter depuis numéro (97xxx = MTN, 66xxx = Moov)
    "description": "Pack 10 analyses SûrCheck AI",  # ⚠️ NOUVEAU : description lisible
    "customer": {         # ⚠️ RESTRUCTURÉ : tous les champs client dans un objet
        "email": "client@example.com",
        "first_name": "Awa",
        "last_name": "Sossou",
        "phone": "+22997505050"  # ⚠️ FORMAT COMPLET avec indicatif
    },
    "metadata": {         # Renommé de custom_metadata
        "surcheck_user_id": "user_123",
        "credit_pack": "pack_10",
        "credits": "10",
        "internal_order_ref": "uuid-123",
        "redirect_url": "https://sur-check.vercel.app/paiement/success?order_ref=uuid-123"  # Stocké dans metadata
    }
}

# Headers SasPay
headers = {
    "Authorization": "Bearer sk_test_xxx",
    "Content-Type": "application/json",
    "Idempotency-Key": "uuid-123"  # ⚠️ NOUVEAU : UUID unique par tentative (évite doublons)
}

# Réponse SasPay
{
    "message": "Payment pushed successfully",
    "id": "b1f2c3d4-uuid",  # ID du paiement
    "status": "PENDING",
    "checkout_url": ""  # Vide pour MTN/Moov push direct, non-vide pour Wave/Orange/Djamo
}
```

### Algorithme de détection réseau
```python
def detect_network(phone: str, country_code: str) -> str:
    """Détecte le réseau Mobile Money depuis le numéro de téléphone."""
    # Nettoyer le numéro
    digits = re.sub(r'[^\d]', '', phone)
    
    if country_code == "BJ":
        # Bénin
        if digits.startswith("229"):
            digits = digits[3:]  # Retirer indicatif pays
        
        # Préfixes MTN Bénin: 40-49, 50-59, 60-69, 90-99
        first_two = digits[:2]
        if first_two in ["40", "41", "42", "43", "44", "45", "46", "47", "48", "49",
                          "50", "51", "52", "53", "54", "55", "56", "57", "58", "59",
                          "60", "61", "62", "63", "64", "65", "66", "67", "68", "69",
                          "90", "91", "92", "93", "94", "95", "96", "97", "98", "99"]:
            return "mtn_bj"
        
        # Préfixes Moov Bénin: 01, 02, 03, 80-89
        if first_two in ["01", "02", "03",
                          "80", "81", "82", "83", "84", "85", "86", "87", "88", "89"]:
            return "moov_bj"
        
        # Par défaut MTN (plus courant)
        return "mtn_bj"
    
    elif country_code == "TG":
        # Togo (TODO: à documenter)
        return "mtn_tg"  # Placeholder
    
    # Autres pays...
    return f"mtn_{country_code.lower()}"  # Fallback
```

---

## 📥 2. VÉRIFICATION STATUT PAIEMENT

### Chariow `/v1/sales/{sale_id}`
```python
# Requête
GET https://api.chariow.com/v1/sales/sal_abc123
Authorization: Bearer sk_xxx

# Réponse
{
    "data": {
        "id": "sal_abc123",
        "status": "successful",
        "pricing": {
            "price": {
                "value": 2500,
                "currency": "XOF"
            }
        },
        "customer": {...},
        "custom_metadata": {...}
    }
}
```

### SasPay `/v1/payments/{id}/verify/`
```python
# Requête
GET https://api.saspay.me/api/v1/payments/b1f2c3d4-uuid/verify/
Authorization: Bearer sk_test_xxx

# Réponse
{
    "message": "Payment transaction fetched successfully",
    "id": "b1f2c3d4-uuid",
    "status": "SUCCESS",  # ⚠️ Majuscules vs minuscules Chariow
    "net_amount": "2500.00",  # ⚠️ String avec décimales
    "currency": "XOF"
}
```

### Mapping des statuts
```python
STATUS_MAPPING = {
    # Chariow → SasPay
    "successful": "SUCCESS",
    "pending": "PENDING",
    "failed": "FAILED",
    "abandoned": "CANCELLED",  # Présumé
    
    # SasPay → Unifié (pour WebhookEvent)
    "SUCCESS": "successful",
    "PENDING": "pending",
    "FAILED": "failed",
    "CANCELLED": "abandoned",
}
```

---

## 🔔 3. WEBHOOKS (Événements de paiement)

### Chariow Pulse
```python
# Headers reçus
{
    "x-chariow-signature": "sha256=abc123...",
    "x-pulse-delivery-id": "delivery_xyz",
    "content-type": "application/json"
}

# Body
{
    "event": "successful.sale",  # Format point.notation
    "id": "pulse_delivery_id",
    "data": {
        "id": "sal_abc123",
        "product_id": "prd_060n1o9q",
        "status": "successful",
        "pricing": {
            "price": {
                "value": 2500,
                "currency": "XOF"
            }
        },
        "customer": {
            "email": "client@example.com"
        },
        "custom_metadata": {
            "surcheck_user_id": "user_123",
            "credit_pack": "pack_10",
            "credits": "10"
        }
    }
}

# Vérification signature
expected_sig = hmac.new(
    webhook_secret.encode(),
    raw_body,
    hashlib.sha256
).hexdigest()
```

### SasPay Webhook (présumé)
```python
# Headers reçus (à documenter en sandbox)
{
    "x-saspay-signature": "???",  # ⚠️ À confirmer
    "x-webhook-id": "webhook_xyz",  # ⚠️ Présumé
    "content-type": "application/json"
}

# Body (format présumé)
{
    "event": "payment.succeeded",  # ⚠️ Format présumé
    "id": "webhook_xyz",
    "data": {
        "id": "b1f2c3d4-uuid",
        "status": "SUCCESS",
        "amount": "2500.00",
        "currency": "XOF",
        "network": "mtn_bj",
        "customer": {
            "email": "client@example.com",
            "phone": "+22997505050"
        },
        "metadata": {  # ⚠️ Renommé de custom_metadata
            "surcheck_user_id": "user_123",
            "credit_pack": "pack_10",
            "credits": "10"
        }
    }
}

# Vérification signature (à documenter)
# Possibilités:
# 1. HMAC-SHA256 comme Chariow
# 2. JWT signé
# 3. Autre mécanisme
```

### Mapping événements
```python
EVENT_MAPPING = {
    # Chariow → SasPay (présumé)
    "successful.sale": "payment.succeeded",
    "failed.sale": "payment.failed",
    "abandoned.sale": "payment.cancelled",
    "refunded.sale": "payment.refunded",
    
    # Événements SasPay additionnels possibles
    "payment.pending": "payment.pending",
}
```

---

## 🔧 4. TRANSFORMATIONS CODE

### Fonction create_checkout()
```python
# AVANT (Chariow)
async def create_checkout_chariow(pack, user, phone_number, country_code):
    payload = {
        "product_id": pack["product_id"],  # ID Chariow dashboard
        "email": user["email"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "phone": {
            "number": phone_number.replace("+", "").replace("229", ""),
            "country_code": country_code
        },
        "custom_metadata": {...},
        "redirect_url": redirect_url
    }
    
    response = await httpx.post(
        f"{CHARIOW_BASE_URL}/checkout",
        headers={"Authorization": f"Bearer {CHARIOW_API_KEY}"},
        json=payload
    )
    
    return {
        "step": response["data"]["step"],
        "checkout_url": response["data"]["payment"]["checkout_url"],
        "sale_id": response["data"]["sale_id"]
    }

# APRÈS (SasPay)
async def create_checkout_saspay(pack, user, phone_number, country_code):
    # ⚠️ Nouveau: Détecter réseau
    network = detect_network(phone_number, country_code)
    
    # ⚠️ Nouveau: Générer idempotency key
    idempotency_key = str(uuid.uuid4())
    
    payload = {
        "amount": f"{pack['amount_fcfa']}.00",  # ⚠️ Montant explicite
        "currency": "XOF",
        "country": country_code,
        "network": network,  # ⚠️ Requis
        "description": pack["label"],  # ⚠️ Nouveau
        "customer": {  # ⚠️ Restructuré
            "email": user["email"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "phone": f"+229{phone_number}"  # ⚠️ Format complet
        },
        "metadata": {  # ⚠️ Renommé
            "surcheck_user_id": user["id"],
            "credit_pack": pack["id"],
            "credits": str(pack["credits"]),
            "redirect_url": redirect_url  # ⚠️ Stocké en metadata
        }
    }
    
    response = await httpx.post(
        f"{SASPAY_BASE_URL}/payments/softpay/",
        headers={
            "Authorization": f"Bearer {SASPAY_API_KEY}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key  # ⚠️ Nouveau header
        },
        json=payload
    )
    
    # ⚠️ Déduire step depuis checkout_url
    checkout_url = response.get("checkout_url", "")
    step = "redirect" if checkout_url else "payment"
    
    return {
        "step": step,
        "checkout_url": checkout_url,
        "sale_id": response["id"]  # ⚠️ Chemin différent
    }
```

### Fonction verify_webhook_signature()
```python
# AVANT (Chariow)
def verify_webhook_chariow(raw_body: bytes, signature_header: str) -> bool:
    actual_sig = signature_header.replace("sha256=", "")
    expected_sig = hmac.new(
        CHARIOW_WEBHOOK_SECRET.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, actual_sig)

# APRÈS (SasPay) - À documenter en sandbox
def verify_webhook_saspay(raw_body: bytes, signature_header: str) -> bool:
    # TODO: Documenter le mécanisme réel après tests
    # Possibilités:
    # 1. HMAC-SHA256 identique à Chariow
    # 2. JWT avec clé publique
    # 3. Autre mécanisme
    
    if not SASPAY_WEBHOOK_SECRET:
        logger.warning("SASPAY_WEBHOOK_SECRET non configuré")
        return True  # Mode dev
    
    # Implémentation temporaire (à valider)
    actual_sig = signature_header
    expected_sig = hmac.new(
        SASPAY_WEBHOOK_SECRET.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, actual_sig)
```

### Fonction parse_webhook()
```python
# AVANT (Chariow)
def parse_webhook_chariow(raw_body: bytes, headers: dict) -> WebhookEvent:
    payload = json.loads(raw_body)
    data = payload.get("data", {})
    custom_metadata = data.get("custom_metadata", {})
    
    return WebhookEvent(
        event_name=payload["event"],  # "successful.sale"
        delivery_id=headers.get("x-pulse-delivery-id"),
        sale_id=data["id"],
        user_id=custom_metadata.get("surcheck_user_id"),
        pack_id=custom_metadata.get("credit_pack"),
        credits=int(custom_metadata.get("credits", 0)),
        amount=int(data["pricing"]["price"]["value"]),
        status="successful" if "successful" in payload["event"] else "unknown"
    )

# APRÈS (SasPay)
def parse_webhook_saspay(raw_body: bytes, headers: dict) -> WebhookEvent:
    payload = json.loads(raw_body)
    data = payload.get("data", {})
    metadata = data.get("metadata", {})  # ⚠️ Renommé
    
    # ⚠️ Mapper événement
    event_name = payload.get("event", "unknown")
    if event_name == "payment.succeeded":
        normalized_event = "successful.sale"
    elif event_name == "payment.failed":
        normalized_event = "failed.sale"
    elif event_name == "payment.cancelled":
        normalized_event = "abandoned.sale"
    else:
        normalized_event = event_name
    
    return WebhookEvent(
        event_name=normalized_event,  # Normalisé au format Chariow
        delivery_id=headers.get("x-webhook-id"),  # ⚠️ Header différent
        sale_id=data["id"],
        user_id=metadata.get("surcheck_user_id"),
        pack_id=metadata.get("credit_pack"),
        credits=int(metadata.get("credits", 0)),
        amount=int(float(data.get("amount", "0"))),  # ⚠️ String → float → int
        status="successful" if data.get("status") == "SUCCESS" else "unknown"
    )
```

---

## 📊 5. TABLEAU RÉCAPITULATIF DES CHANGEMENTS

| Aspect | Chariow | SasPay | Action requise |
|--------|---------|--------|----------------|
| **URL base** | `api.chariow.com/v1` | `api.saspay.me/api/v1` | Modifier config |
| **Endpoint checkout** | `/checkout` | `/payments/softpay/` | Modifier URL |
| **Endpoint verify** | `/sales/{id}` | `/payments/{id}/verify/` | Modifier URL |
| **Montant** | Implicite (product_id) | Explicite (amount) | Ajouter champ |
| **Réseau** | Auto-détecté | Requis (network) | Ajouter logique |
| **Description** | Optionnel | Requis | Ajouter champ |
| **Customer** | Champs séparés | Objet `customer` | Restructurer |
| **Téléphone** | Sans indicatif | Avec indicatif (+229) | Transformer |
| **Metadata** | `custom_metadata` | `metadata` | Renommer |
| **Redirect URL** | Champ dédié | Dans metadata | Déplacer |
| **Idempotence** | Automatique | Header requis | Ajouter header |
| **Réponse checkout** | `data.step` | Déduire de `checkout_url` | Adapter logique |
| **Statuts** | Minuscules | MAJUSCULES | Mapper |
| **Événements** | `successful.sale` | `payment.succeeded` | Mapper |
| **Signature webhook** | `x-chariow-signature` | `x-saspay-signature` (?) | Documenter |
| **Delivery ID** | `x-pulse-delivery-id` | `x-webhook-id` (?) | Documenter |

---

## ✅ COMPATIBILITÉ GARANTIE

L'interface `PaymentProvider` garantit que :
1. **Aucun changement** dans `payment.py` (router)
2. **Aucun changement** dans `credit_service.py`
3. **Aucun changement** dans la base de données
4. **Aucun changement** dans le frontend

Seul le fichier `saspay_provider.py` contient les transformations.

---

## 🚨 RISQUES IDENTIFIÉS

1. **Webhooks non documentés** → Tests sandbox obligatoires
2. **Détection réseau** → Préfixes à valider par pays
3. **checkout_url comportement** → Frontend doit gérer redirection
4. **Montants décimaux** → Conversion string/float/int à sécuriser

---

**Status** : Mapping complet - Prêt pour implémentation
