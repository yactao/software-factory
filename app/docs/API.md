# API

> Spécification des endpoints principaux. Toutes les routes (sauf `/health`) exigent un **JWT Bearer** Microsoft Entra ID avec le scope **`REQUIRED_SCOPE`** (ex: `ragapi`).

---

## Authentification

- **Header** : `Authorization: Bearer <access_token>`
- **Vérifications** côté backend :
  - Signature (JWKS),
  - `iss = https://login.microsoftonline.com/{TENANT_ID}/v2.0`,
  - `aud` = `SCOPE_URI` (ou App ID URI configuré),
  - `scp` contient `REQUIRED_SCOPE` (ex: `ragapi`).

---

## 1) Santé

### `GET /health`

Réponse 200 :
```json
{ "name": "AINA Backend", "status": "ok", "time": "2025-10-19T10:00:00Z" }
```

---

## 2) RAG Documents

### `POST /api/rag`

**Body**
```json
{
  "question": "Quel est le processus d'onboarding ?",
  "conversation_id": "conv-rag",
  "filters": { "index_name": "idx-rag-chunks" },
  "top_k": 4
}
```

**Réponse 200**
```json
{
  "answer": "…",
  "uses_context": true,
  "used_docs": [
    { "id": "doc123", "title": "Guide Onboarding", "path": "blob://…", "score": 4.2, "reranker": 12.1 }
  ],
  "citations": [],
  "conversation_id": "conv-rag"
}
```

**Codes**
- `200` OK
- `400` Requête invalide
- `401` Non authentifié
- `403` Scope manquant
- `500` Erreur interne / dépendance

---

## 3) Trading / Finance (exemples)

### `POST /api/trading`
Body/format proche de `/api/rag`, adapté au domaine trading.

### `POST /api/finance`
Idem, pour requêtes Finance (si activé).

---

## 4) Historique de chat

### `GET /api/chat/history?conversation_id={id}`

**Réponse 200**
```json
{
  "conversation_id": "conv-rag",
  "events": [
    { "role": "user", "route": "rag", "message": "Bonjour", "meta": {} },
    { "role": "assistant", "route": "rag", "message": "Salut !", "meta": {} }
  ]
}
```

### `GET /api/chat/list/{route}`

Liste des conversations d’une route (par user).
**Réponse 200**
```json
{
  "conversations": [
    {
      "conversation_id": "conv-rag",
      "title": "📄 Première question…",
      "last_activity_utc": "2025-10-19T09:58:12Z",
      "last_route": "rag"
    }
  ],
  "count": 1
}
```

### `DELETE /api/chat/delete/{conversation_id}`

Supprime toutes les entrées d’une conversation.

**Réponse 200**
```json
{ "deleted": 7 }
```

### `DELETE /api/chat/delete-all/{route}`

Purge toutes les conversations de la **route** pour l’utilisateur courant.

**Réponse 200**
```json
{ "deleted_conversations": 3 }
```

---

## 5) SAS / Blobs (si exposé)

### `GET /api/sas?path=...`

Retourne une SAS éphémère pour lecture d’un document source.

**Réponse 200**
```json
{ "url": "https://…?sv=…" }
```

---

## 6) Erreurs & format

**Erreur typique**
```json
{
  "detail": "Token invalide: Audience doesn't match"
}
```

**Codes**
- `400` payload invalide
- `401` non authentifié
- `403` non autorisé (scope manquant)
- `404` ressource absente
- `409` conflit
- `422` validation FastAPI
- `500` erreur interne

---

## 7) En-têtes & CORS

- `Access-Control-Allow-Origin`: valeurs de `FRONT_ORIGIN`
- `Access-Control-Allow-Credentials: true`
- Prévol: `OPTIONS` géré par middleware.

---

## 8) Versioning & Compat

- Préfixes `/api/*`.
- Changement majeur → nouveau endpoint ou champ.
- Retour JSON stable; nouveaux champs ajoutés de manière additive.

**Fin.**
