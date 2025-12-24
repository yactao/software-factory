# Documentation des Routes API - AINA Backend

Cette documentation décrit toutes les routes API disponibles dans l'application AINA Backend, leurs fonctionnalités, paramètres et réponses.

## Table des matières

1. [Health](#health)
2. [Authentification](#authentification)
3. [SAS (Shared Access Signature)](#sas)
4. [Chat](#chat)
5. [RAG (Retrieval Augmented Generation)](#rag)
6. [Trading](#trading)
7. [Aïna Finance](#aina-finance)
8. [Web Search](#web-search)
9. [Vision](#vision)
10. [Vision SAS](#vision-sas)
11. [Vision Cleanup](#vision-cleanup)
12. [Vision Attach](#vision-attach)
13. [Vision Plaque](#vision-plaque)
14. [Vet Doc](#vet-doc)
15. [Vet Finance](#vet-finance)

---

## Health

### GET `/health`

Endpoint de vérification de santé de l'application.

**Authentification** : Non requise

**Réponse** :
```json
{
  "status": "ok",
  "time": 1234567890.123
}
```

**Description** : Retourne le statut de l'application et un timestamp Unix. Utilisé pour les vérifications de santé et les probes de monitoring.

---

## Authentification

### GET `/auth/debug`

Endpoint de débogage pour vérifier les informations du token JWT.

**Authentification** : Requise (JWT)

**Réponse** :
```json
{
  "message": "Token valid",
  "user": {
    "sub": "user_id",
    "name": "Nom Utilisateur",
    "preferred_username": "username"
  },
  "tenant": {
    "tid": "tenant_id"
  },
  "token": {
    "iss": "issuer",
    "aud": "audience",
    "scp": "scope",
    "roles": ["role1", "role2"],
    "iat": 1234567890,
    "exp": 1234567890
  }
}
```

**Description** : Retourne les claims du token JWT décodé, permettant de vérifier l'identité de l'utilisateur et les permissions associées.

### GET `/secure`

Endpoint sécurisé de test.

**Authentification** : Requise (JWT)

**Réponse** :
```json
{
  "message": "Accès autorisé",
  "user": { ... }
}
```

**Description** : Route de test pour vérifier que l'authentification fonctionne correctement.

---

## SAS

### GET `/api/sas`

Génère une URL SAS (Shared Access Signature) pour accéder à un blob Azure Storage.

**Authentification** : Requise (JWT)

**Paramètres de requête** :
- `path` (string, requis) : Chemin du fichier dans le blob storage
- `ttl` (int, optionnel, défaut: 60) : Durée de validité en minutes (1-60)

**Réponse** :
```json
{
  "url": "https://account.blob.core.windows.net/container/file.pdf?sv=...",
  "container": "container_name",
  "blob": "file.pdf",
  "expires_in_minutes": 60
}
```

**Erreurs** :
- `400` : Paramètre path invalide (fichier requis, pas de dossier)
- `404` : Blob introuvable dans les containers recherchés
- `500` : Credentials de storage manquants

**Description** : 
- Recherche le fichier dans plusieurs containers (CONTAINER, vet-docs, CONTAINER_TRADING)
- Tente automatiquement les variantes PDF/DOCX si nécessaire
- Génère une URL SAS temporaire pour accéder au fichier

---

## Chat

### GET `/api/chat/history`

Récupère l'historique d'une conversation.

**Authentification** : Requise (JWT)

**Paramètres de requête** :
- `conversation_id` (string, requis) : Identifiant de la conversation

**Réponse** :
```json
{
  "conversation_id": "conv_123",
  "messages": [
    {
      "role": "user",
      "route": "rag",
      "message": "Question utilisateur",
      "timestamp_utc": "2024-01-01T00:00:00Z",
      "meta": {}
    }
  ],
  "count": 10
}
```

**Description** : Retourne tous les messages d'une conversation spécifique, triés chronologiquement.

### GET `/api/chat/list/{route_name}`

Liste toutes les conversations pour une route donnée.

**Authentification** : Requise (JWT)

**Paramètres de chemin** :
- `route_name` (string) : Nom de la route (rag, trading, finance, etc.)

**Réponse** :
```json
{
  "conversations": [
    {
      "conversation_id": "conv_123",
      "title": "Titre de la conversation",
      "last_activity_utc": "2024-01-01T00:00:00Z",
      "last_route": "rag"
    }
  ],
  "count": 5
}
```

**Description** : Retourne la liste des conversations pour une route spécifique, avec titre et dernière activité.

### POST `/api/chat/rename`

Renomme une conversation.

**Authentification** : Requise (JWT)

**Corps de la requête** :
```json
{
  "conversation_id": "conv_123",
  "title": "Nouveau titre"
}
```

**Réponse** :
```json
{
  "ok": true,
  "conversation_id": "conv_123",
  "title": "Nouveau titre"
}
```

**Description** : Enregistre un titre personnalisé pour une conversation.

### DELETE `/api/chat/clear`

Supprime tous les messages d'une conversation.

**Authentification** : Requise (JWT)

**Paramètres de requête** :
- `conversation_id` (string, requis) : Identifiant de la conversation

**Réponse** :
```json
{
  "deleted": true,
  "conversation_id": "conv_123"
}
```

**Description** : Supprime définitivement tous les messages d'une conversation spécifique.

### DELETE `/api/chat/clear-all/{route_name}`

Supprime toutes les conversations d'une route.

**Authentification** : Requise (JWT)

**Paramètres de chemin** :
- `route_name` (string) : Nom de la route

**Paramètres de requête** :
- `purge_entire_conversation` (bool, défaut: true) : Si true, supprime toute la conversation (toutes routes). Si false, supprime uniquement les messages de la route ciblée.

**Réponse** :
```json
{
  "route": "rag",
  "conversations_affected": 5,
  "entities_deleted": 50,
  "purge_entire_conversation": true
}
```

**Description** : Supprime toutes les conversations associées à une route. Permet de choisir entre suppression complète ou partielle.

---

## RAG

### POST `/api/rag`

Endpoint principal de RAG (Retrieval Augmented Generation) pour la recherche dans les documents d'audit.

**Authentification** : Requise (JWT)

**Corps de la requête** :
```json
{
  "question": "Quelle est la surface du magasin 42 ?",
  "filters": {},
  "top_k": 8,
  "conversation_id": "conv_123"
}
```

**Réponse** :
```json
{
  "answer": "Réponse générée par l'IA...",
  "citations": [],
  "used_docs": [
    {
      "id": "doc_123",
      "title": "Document titre",
      "path": "path/to/doc.pdf",
      "score": 0.95
    }
  ],
  "conversation_id": "conv_123",
  "images": ["url1", "url2"],
  "model": "Aïna Instant"
}
```

**Fonctionnement** :
1. Enregistre le message utilisateur dans l'historique
2. Détecte le type de question (smalltalk, single_store, global, fallback) via un agent de classification
3. Pour les questions globales : utilise un agent d'analyse globale du PDF d'audit
4. Pour les questions spécifiques : 
   - Récupère l'historique de conversation
   - Raffine la requête avec l'historique
   - Recherche dans l'index Azure AI Search
   - Construit des contextes à partir des résultats
   - Synthétise une réponse avec citations via Gemini/Kimi
   - Extrait des images associées au magasin si mentionné
5. Enregistre la réponse dans l'historique

**Modèles utilisés** :
- "Aïna Deep Search" : pour les analyses globales
- "Aïna Instant" : pour les recherches de fiches magasin

**Fonctionnalités spéciales** :
- Détection automatique de codes magasin et noms dans la question
- Extraction d'images associées aux magasins
- Raffinement de requête basé sur l'historique
- Gestion du smalltalk avec réponse générique

---

## Trading

### POST `/api/trading`

Endpoint RAG spécialisé pour les documents Trading.

**Authentification** : Requise (JWT)

**Corps de la requête** :
```json
{
  "question": "Quelles sont les tendances du marché ?",
  "filters": {},
  "top_k": 8,
  "conversation_id": "conv_123"
}
```

**Réponse** :
```json
{
  "answer": "Réponse synthétisée...",
  "citations": [],
  "used_docs": [
    {
      "id": "doc_123",
      "title": "Document Trading",
      "path": "path/to/doc.pdf",
      "score": 0.92
    }
  ],
  "conversation_id": "conv_123"
}
```

**Fonctionnement** :
1. Enregistre le message utilisateur
2. Gère le smalltalk avec réponse générique
3. Récupère un historique condensé de la conversation (format U:/A:)
4. Recherche dans l'index Trading (captions + contenu)
5. Construit des contextes avec captions et début du contenu
6. Synthétise une réponse via modèle trading (sans citations inline)
7. Retourne answer + used_docs (pas de citations inline)

**Caractéristiques** :
- Utilise un index Azure Search dédié aux documents Trading
- Injecte l'historique de conversation pour la continuité
- Réponses sans références inline dans le texte

---

## Aïna Finance

### POST `/api/aina/finance`

Endpoint principal Aïna Finance utilisant l'agent Kimi pour analyser les fichiers Excel financiers.

**Authentification** : Requise (JWT)

**Corps de la requête** :
```json
{
  "question": "Quel est le chiffre d'affaires total ?",
  "conversation_id": "conv_123"
}
```

**Réponse** :
```json
{
  "answer": "Explication textuelle...",
  "chart": {
    "type": "bar",
    "data": { ... },
    "options": { ... }
  },
  "rows": [
    {
      "colonne": "CA",
      "valeur": 100000
    }
  ],
  "conversation_id": "conv_123"
}
```

**Fonctionnement** :
1. Enregistre le message utilisateur
2. Récupère l'historique des 3 derniers couples Q/A
3. Appelle l'agent finance (Kimi) qui analyse l'Excel finance
4. Retourne :
   - `answer` : texte explicatif
   - `chart` : configuration du graphique pour visualisation
   - `rows` : extrait de lignes/colonnes utilisées pour affichage tabulaire
   - `conversation_id` : identifiant de la conversation

**Caractéristiques** :
- Utilise l'agent Kimi pour l'analyse intelligente des données Excel
- Génère automatiquement des graphiques
- Extrait les données pertinentes pour affichage

---

## Web Search

### POST `/api/search`

Endpoint de recherche web avec grounding via Gemini.

**Authentification** : Requise (JWT)

**Corps de la requête** :
```json
{
  "question": "Qu'est-ce que l'intelligence artificielle ?",
  "context": "Contexte optionnel",
  "force_grounding": true,
  "legacy_15": false,
  "conversation_id": "conv_123"
}
```

**Réponse** :
```json
{
  "answer": "Réponse générée...",
  "citations": [
    {
      "title": "Titre de la source",
      "url": "https://example.com"
    }
  ],
  "model": "gemini-2.0-flash-exp",
  "grounded": true,
  "conversation_id": "conv_123"
}
```

**Fonctionnement** :
1. Enregistre la question utilisateur avec contexte optionnel
2. Configure le grounding selon `force_grounding` ou `USE_GROUNDING`
3. Appelle Gemini avec outils de recherche web
4. Extrait les citations des sources utilisées
5. Retourne la réponse avec citations si grounding activé

**Paramètres** :
- `force_grounding` : Force l'activation/désactivation du grounding (override la config)
- `legacy_15` : Utilise l'ancienne version des outils de recherche (v1.5)

---

## Vision

### POST `/api/vision`

Analyse d'images de plans avec détection d'objets et calcul de surfaces/périmètres.

**Authentification** : Requise (JWT)

**Paramètres de formulaire** :
- `file` (file, optionnel) : Image du plan (png, jpg, jpeg, pdf)
- `prompt` (string, requis) : Instruction utilisateur
- `m_per_pixel` (float, défaut: 0.02) : Échelle en mètres par pixel
- `ratio` (string, défaut: "1/100") : Échelle sous forme de ratio (ex: "1/100")
- `return_image` (bool, défaut: true) : Si vrai, renvoie une image annotée
- `conversation_id` (string, optionnel) : ID de conversation

**Réponse** :
```json
{
  "intent": "analyse_globale",
  "target": "rayon_fraicheur",
  "surfaces": {
    "rayon_fraicheur": 25.5,
    "caisse": 10.2
  },
  "perimeters": {
    "rayon_fraicheur": 20.0,
    "caisse": 12.0
  },
  "response_text": "Surface totale : 35.7 m²\nPérimètre total : 32.0 m",
  "detections": [
    {
      "tag_name": "rayon_fraicheur",
      "probability": 0.95,
      "bounding_box": { "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4 }
    }
  ],
  "annotated_image_b64": null,
  "meta": {
    "scale_ratio_m_per_px": 0.02,
    "image_size": { "width": 1920, "height": 1080 },
    "return_image": true,
    "vision_file_path": "pk/conv/source.jpg",
    "vision_annotated_blob_path": "pk/conv/annotated.jpg"
  },
  "conversation_id": "conv_123",
  "vision_file_sas": "https://...",
  "vision_annotated_sas": "https://..."
}
```

**Fonctionnement** :
1. Récupère ou upload le fichier image
2. Analyse l'intention via LLM (surface, périmètre, détection, analyse globale)
3. Détecte les objets via Azure Custom Vision
4. Calcule surfaces et périmètres selon l'échelle fournie
5. Génère une image annotée si demandé
6. Stocke les fichiers dans Blob Storage
7. Retourne les résultats avec URLs SAS

**Intents possibles** :
- `surface` : Calcule uniquement les surfaces
- `perimetre` : Calcule uniquement les périmètres
- `detection_objets` : Compte les objets détectés
- `analyse_globale` : Surface et périmètre totaux

---

## Vision SAS

### GET `/api/vision/sas`

Génère une URL SAS pour un fichier vision stocké dans Blob Storage.

**Authentification** : Requise (JWT)

**Paramètres de requête** :
- `path` (string, requis) : Chemin du fichier (ex: pk/conv/file.jpg)

**Réponse** :
```json
{
  "url": "https://account.blob.core.windows.net/container/pk/conv/file.jpg?sv=..."
}
```

**Description** : Génère une URL SAS valide 180 minutes pour accéder à un fichier vision.

---

## Vision Cleanup

### DELETE `/api/vision/cleanup`

Supprime tous les fichiers vision associés à une conversation.

**Authentification** : Requise (JWT)

**Paramètres de requête** :
- `conversation_id` (string, requis) : ID de la conversation

**Réponse** :
```json
{
  "deleted": 5
}
```

**Description** : Nettoie tous les fichiers blob associés à une conversation vision (images source, annotées, etc.).

---

## Vision Attach

### POST `/api/vision/attach`

Attache un fichier image à une conversation pour utilisation ultérieure.

**Authentification** : Requise (JWT)

**Paramètres de formulaire** :
- `file` (file, requis) : Fichier image à attacher
- `conversation_id` (string, optionnel) : ID de conversation

**Réponse** :
```json
{
  "conversation_id": "conv_123",
  "vision_file_path": "pk/conv/file.jpg",
  "vision_file_sas": "https://..."
}
```

**Description** : 
- Upload un fichier dans Blob Storage
- L'associe à une conversation
- Permet de réutiliser ce fichier dans les appels `/api/vision` suivants sans re-upload

---

## Vision Plaque

### POST `/api/vision/plaque`

Analyse d'une plaque signalétique avec OCR et GPT.

**Authentification** : Requise (JWT)

**Paramètres de formulaire** :
- `file` (file, requis) : Image de la plaque (jpg, png, heic, pdf)
- `prompt` (string, requis) : Instruction utilisateur
- `conversation_id` (string, optionnel) : ID de conversation

**Réponse** :
```json
{
  "conversation_id": "conv_123",
  "response_text": "Analyse de la plaque...",
  "vision_plaque_file_path": "pk/conv/plaque.jpg",
  "vision_plaque_file_sas": "https://..."
}
```

**Fonctionnement** :
1. Sauvegarde l'image dans Blob Storage
2. Appelle l'agent plaques (OCR + GPT) pour analyser le contenu
3. Retourne l'analyse textuelle et l'URL SAS de l'image

**Description** : Utilise un agent spécialisé pour extraire et analyser les informations des plaques signalétiques.

---

## Vet Doc

### POST `/api/vet-doc`

RAG dédié aux documents vétérinaires (procédures, diagnostics, RH, RGPD).

**Authentification** : Requise (JWT)

**Corps de la requête** :
```json
{
  "question": "Quelle est la procédure pour une intervention chirurgicale ?",
  "filters": {},
  "top_k": 8,
  "conversation_id": "conv_123"
}
```

**Réponse** :
```json
{
  "answer": "Réponse basée sur les documents vétérinaires...",
  "citations": [],
  "used_docs": [
    {
      "id": "doc_123",
      "title": "Procédure chirurgicale",
      "path": "path/to/doc.pdf",
      "score": 0.92
    }
  ],
  "conversation_id": "conv_123",
  "images": [],
  "model": "Aïna Vet"
}
```

**Fonctionnement** :
1. Enregistre le message utilisateur (route: 'vet_doc')
2. Gère le smalltalk
3. Récupère l'historique Q/A
4. Raffine la requête avec l'historique
5. Recherche dans l'index vétérinaire (vet-knowledge-index)
6. Synthétise une réponse via Kimi spécialisé vétérinaire
7. Retourne la réponse avec documents utilisés

**Caractéristiques** :
- Index dédié aux documents vétérinaires
- Pas de logique magasin/images
- Réponses structurées pour procédures médicales, diagnostics, RH, RGPD

---

## Vet Finance

### POST `/api/vet/finance`

Endpoint Vet Finance utilisant l'agent Kimi pour analyser les fichiers Excel financiers vétérinaires.

**Authentification** : Requise (JWT)

**Corps de la requête** :
```json
{
  "question": "Quel est le revenu mensuel ?",
  "conversation_id": "conv_123"
}
```

**Réponse** :
```json
{
  "answer": "Explication financière...",
  "chart": {
    "type": "line",
    "data": { ... },
    "options": { ... }
  },
  "rows": [
    {
      "colonne": "Revenu",
      "valeur": 50000
    }
  ],
  "conversation_id": "conv_123"
}
```

**Fonctionnement** :
1. Enregistre le message utilisateur (route: 'vet_finance')
2. Récupère l'historique des 3 derniers couples Q/A
3. Appelle l'agent vet finance (Kimi) qui analyse le fichier Excel tri feuilles
4. Retourne answer, chart, rows et conversation_id

**Description** : Similaire à Aïna Finance mais spécialisé pour les données financières vétérinaires avec tri par feuilles Excel.

---

## Notes générales

### Authentification

Toutes les routes (sauf `/health`) nécessitent une authentification JWT. Le token doit être fourni dans le header `Authorization: Bearer <token>`.

### Gestion des conversations

La plupart des endpoints supportent un paramètre `conversation_id` optionnel. Si non fourni, un nouvel ID est généré automatiquement. L'historique est conservé dans Azure Table Storage.

### Format des réponses

Les réponses suivent généralement ce format :
- `answer` ou `response_text` : Texte de la réponse
- `conversation_id` : ID de la conversation
- `used_docs` : Documents utilisés pour générer la réponse
- `citations` : Citations inline (si applicable)
- `meta` : Métadonnées supplémentaires

### Gestion des erreurs

Les erreurs suivent le format HTTP standard :
- `400` : Requête invalide
- `401` : Non authentifié
- `403` : Non autorisé
- `404` : Ressource introuvable
- `500` : Erreur serveur
- `502` : Erreur service externe

### Stockage

Les fichiers sont stockés dans Azure Blob Storage avec des URLs SAS temporaires pour l'accès. Les conversations sont stockées dans Azure Table Storage.

