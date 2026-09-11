# Documentation API Chariow — SûrCheck AI

> ⚠️ **Configuration requise :** Clé API à configurer dans Railway → Variables → `CHARIOW_API_KEY`

> ## Documentation Index
> Fetch the complete documentation index at: https://chariow.dev/llms.txt
> Use this file to discover all available pages before exploring further.

# Démarrage rapide

> Commencez à utiliser l'API Chariow en quelques minutes

Ce guide vous accompagne dans vos premiers pas avec l'API Chariow.

## Prérequis

* Un compte Chariow ([créer un compte](https://app.chariow.com/register))
* Une clé API (créée dans les paramètres de votre tableau de bord)

## Étape 1 : Créer une clé API

<Steps>
  <Step title="Connexion au tableau de bord">
    Allez sur [app.chariow.com](https://app.chariow.com) et connectez-vous.
  </Step>

  <Step title="Accéder aux paramètres">
    Cliquez sur **Paramètres** dans la barre latérale.
  </Step>

  <Step title="Ouvrir les clés API">
    Sélectionnez **Clés API** dans le menu des paramètres.
  </Step>

  <Step title="Créer une nouvelle clé">
    Cliquez sur **Créer une clé API**, donnez-lui un nom descriptif et copiez la clé générée.
  </Step>
</Steps>

<Warning>
  Copiez votre clé API immédiatement après sa création. Pour des raisons de sécurité, la clé complète n'est affichée qu'une seule fois.
</Warning>

## Étape 2 : Tester votre clé API

Faites votre première requête pour récupérer les informations de votre boutique :

<CodeGroup>
  ```bash cURL theme={null}
  curl -X GET "https://api.chariow.com/v1/store" \
    -H "Authorization: Bearer VOTRE_CLE_API"
  ```

  ```javascript JavaScript theme={null}
  const response = await fetch('https://api.chariow.com/v1/store', {
    headers: {
      'Authorization': 'Bearer VOTRE_CLE_API'
    }
  });

  const data = await response.json();
  console.log(data);
  ```

  ```python Python theme={null}
  import requests

  headers = {
      'Authorization': 'Bearer VOTRE_CLE_API'
  }

  response = requests.get('https://api.chariow.com/v1/store', headers=headers)
  print(response.json())
  ```

  ```php PHP theme={null}
  $ch = curl_init('https://api.chariow.com/v1/store');
  curl_setopt($ch, CURLOPT_HTTPHEADER, [
      'Authorization: Bearer VOTRE_CLE_API'
  ]);
  curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

  $response = curl_exec($ch);
  echo $response;
  ```
</CodeGroup>

## Étape 3 : Lister vos produits

Récupérez tous vos produits publiés :

```bash theme={null}
curl -X GET "https://api.chariow.com/v1/products" \
  -H "Authorization: Bearer VOTRE_CLE_API"
```

**Réponse :**

```json theme={null}
{
  "message": "success",
  "data": {
    "products": [
      {
        "id": "prd_abc123",
        "name": "Cours Premium",
        "slug": "cours-premium",
        "type": "course",
        "status": "published",
        "pricing": {
          "type": "one_time",
          "price": {
            "value": 49,
            "formatted": "49,00 €",
            "short": "49",
            "currency": "EUR"
          }
        }
      }
    ],
    "pagination": {
      "next_cursor": null,
      "prev_cursor": null,
      "has_more": false
    }
  },
  "errors": []
}
```

## Étape 4 : Initier un paiement

Créez une session de paiement pour un produit :

```bash theme={null}
curl -X POST "https://api.chariow.com/v1/checkout" \
  -H "Authorization: Bearer VOTRE_CLE_API" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "prd_abc123",
    "email": "client@exemple.com",
    "first_name": "Jean",
    "last_name": "Dupont",
    "phone": {
      "number": "612345678",
      "country_code": "FR"
    }
  }'
```

## Prochaines étapes

<CardGroup cols={2}>
  <Card title="Authentification" icon="lock" href="/fr/introduction/authentication">
    En savoir plus sur la sécurité API
  </Card>

  <Card title="Produits" icon="box" href="/fr/guides/products">
    Gérer vos produits via l'API
  </Card>

  <Card title="Paiement" icon="shopping-cart" href="/fr/guides/checkout">
    Intégrer le processus de paiement
  </Card>

  <Card title="Référence API" icon="code" href="/api-reference/introduction">
    Explorer tous les endpoints
  </Card>
</CardGroup>
