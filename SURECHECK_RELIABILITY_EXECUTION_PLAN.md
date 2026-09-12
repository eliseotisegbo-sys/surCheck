# SûrCheck — Reliability Phase

## Document de travail pour Antigravity

Ce document constitue le prompt d’exécution destiné à Antigravity pour auditer, fiabiliser et préparer la mise en production du projet SûrCheck existant, sans repartir de zéro et en excluant volontairement l’OCR de cette phase.

> **Règle directrice : ne pas chercher à impressionner. Chercher à prouver.**

MISSION — PRODUIRE LE DOCUMENT D’EXÉCUTION DE LA SÛRCheck RELIABILITY PHASE

Tu travailles sur le dépôt existant **SûrCheck**.

Ta mission dans cette étape n’est PAS de réécrire le projet, ni de commencer immédiatement toutes les modifications.

Ta mission est d’abord de produire un **document technique d’exécution extrêmement précis, concret et directement exploitable**, permettant ensuite de réaliser les corrections et améliorations nécessaires sur le projet existant.

Le document doit être suffisamment détaillé pour qu’un développeur puisse suivre les étapes une par une sans devoir réinterpréter les besoins.

---

# 1. CONTEXTE DU PROJET

SûrCheck est un service privé d’aide à la vérification de contenus et transactions potentiellement frauduleux.

Promesse principale :

> « Envoie-moi le message avant d’envoyer ton argent. »

Le projet possède déjà un socle technique important.

Ne repars surtout PAS de zéro.

Le dépôt possède notamment déjà :

- FastAPI ;
- moteur de normalisation ;
- extraction ;
- règles ;
- scoring ;
- fuzzy matching ;
- OCR ;
- réputation ;
- classification ;
- authentification ;
- crédits ;
- paiements ;
- signalements ;
- administration ;
- Supabase/PostgreSQL ;
- intégration Chariow ;
- intégration prévue de SASPAS ;
- Docker ;
- déploiement ;
- tests.

Le moteur est déjà organisé autour de plusieurs composants.

L’architecture existante doit être préservée autant que possible.

---

# 2. RÈGLE ABSOLUE : INSPECTER AVANT DE MODIFIER

Avant de proposer la moindre modification, inspecte réellement le dépôt.

Tu dois examiner :

1. l’arborescence complète ;
2. le backend ;
3. le frontend ;
4. les modèles de données ;
5. les migrations ;
6. les services ;
7. les routes API ;
8. l’authentification ;
9. le système de crédits ;
10. le système de paiement ;
11. l’intégration Chariow ;
12. l’intégration SASPAS déjà présente ;
13. les fichiers de configuration ;
14. les variables d’environnement ;
15. les tests ;
16. les documents techniques existants ;
17. l’audit déjà présent dans le dépôt ;
18. les fichiers de pricing ;
19. les informations de contact/support ;
20. les règles de scoring ;
21. les éventuelles duplications frontend/backend.

Tu dois identifier ce qui existe réellement dans le code et ce qui n’existe que dans la documentation.

Ne suppose jamais qu’une fonctionnalité décrite dans un document fonctionne réellement.

Ne considère pas un test vert comme une preuve suffisante qu’une fonctionnalité réelle fonctionne.

---

# 3. OBJECTIF GÉNÉRAL DE CETTE PHASE

Le nom de cette phase est :

## SÛRCHECK RELIABILITY PHASE

Objectif :

> Faire en sorte que chaque promesse visible dans SûrCheck corresponde réellement à une fonctionnalité exécutée, testée, traçable et vérifiable.

Il faut transformer le projet :

DE :

> projet SaaS techniquement avancé et bien documenté

VERS :

> produit réellement fiable, cohérent, explicable, sécurisé et crédible.

---

# 4. OCR : NE PAS LE TRAITER MAINTENANT

IMPORTANT :

## NE PAS CORRIGER L’OCR DANS CETTE PHASE.

L’OCR est connu comme un problème du projet, mais il doit être volontairement exclu de cette phase.

Ne pas :

- modifier le pipeline OCR ;
- refaire l’upload d’image ;
- refaire l’extraction OCR ;
- ajouter un nouveau moteur OCR ;
- corriger les traitements d’image ;
- ajouter des tests OCR.

Le document doit simplement mentionner :

> OCR volontairement reporté à une phase ultérieure.

Aucun autre travail ne doit être bloqué par cette fonctionnalité.

---

# 5. PRIORITÉ N°1 — SÉCURITÉ ET SECRETS

Le dépôt contient ou a contenu des secrets sensibles.

Traite ce sujet comme PRIORITÉ CRITIQUE.

Le document doit définir précisément :

### 5.1 Identification

Lister tous les endroits où des secrets peuvent apparaître :

- `.env`
- `.env.example`
- documentation
- configuration
- fichiers Python
- fichiers frontend
- scripts
- Git history
- logs éventuels
- exemples de configuration
- CI/CD

Identifier notamment les catégories suivantes :

- clés API ;
- JWT secret ;
- Supabase service role ;
- mots de passe DB ;
- clés de paiement ;
- secrets webhook ;
- autres credentials.

### 5.2 Règle

Aucun secret réel ne doit être présent dans :

- Git ;
- frontend ;
- documentation publique ;
- fichiers exemples.

Les secrets doivent uniquement être injectés par l’environnement.

### 5.3 IMPORTANT

Toutes les clés nécessaires au fonctionnement sont déjà disponibles dans :
