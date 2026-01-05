# Documentation du Code - API RAG

Cette documentation détaille le fonctionnement interne de l'API RAG (Retrieval Augmented Generation) et toutes les fonctions utilisées.

## Vue d'ensemble

L'API RAG permet de rechercher et synthétiser des réponses à partir de documents d'audit stockés dans Azure AI Search. Elle utilise plusieurs agents et services pour classer les questions, rechercher des documents, et générer des réponses contextuelles.

## Architecture du flux

### 1. Point d'entrée : `rag()` dans `app/routers/rag.py`

La fonction principale `rag()` orchestre tout le processus :

```python
@router.post("/api/rag")
def rag(req: RAGRequest, claims: Dict[str, Any] = Depends(_auth_dependency))
```

**Paramètres** :
- `req` : Objet `RAGRequest` contenant la question, les filtres, `top_k`, et `conversation_id`
- `claims` : Claims JWT de l'utilisateur authentifié

**Flux d'exécution** :

1. **Enregistrement du message utilisateur** via `_save_chat_event()`
2. **Détection du smalltalk** via regex `SMALLTALK_RE`
3. **Classification de la portée** via `decide_scope_with_kimi()`
4. **Traitement selon la portée** :
   - `global` : Utilise `answer_global_with_kimi()`
   - `single_store` ou `fallback` : Flux RAG standard
5. **RAG standard** :
   - Récupération de l'historique via `_get_last_qna_pairs()`
   - Raffinement de la requête via `_compose_search_query_from_history()`
   - Recherche dans Azure Search via `_search_docs()`
   - Construction des contextes
   - Synthèse via `_synthesize_with_citations()`
   - Extraction d'images via `_gather_images_for_store()`

## Fonctions principales

### Classification de la portée

#### `decide_scope_with_kimi(question: str) -> Tuple[ScopeType, str]`

**Localisation** : `app/services/agents_classif.py`

**Description** : Détermine si la question concerne un magasin spécifique, tous les magasins, ou est ambiguë.

**Paramètres** :
- `question` : La question de l'utilisateur

**Retour** : Tuple contenant :
- `scope` : "single_store", "global", ou "fallback"
- `reason` : Raison de la classification

**Fonctionnement** :
1. Construit un prompt système pour le classifieur Kimi
2. Appelle `kimi_chat_completion()` avec température 0.0 pour une réponse déterministe
3. Parse le JSON de réponse de manière robuste (gestion des erreurs)
4. Valide que le scope est dans les valeurs autorisées

**Utilisation** :
```python
scope, scope_reason = decide_scope_with_kimi(question)
```

### Agent d'analyse globale

#### `answer_global_with_kimi(question: str) -> Tuple[str, bool]`

**Localisation** : `app/services/agent_global_audit.py`

**Description** : Analyse le PDF global contenant toutes les fiches d'audit.

**Paramètres** :
- `question` : La question de l'utilisateur

**Retour** : Tuple contenant :
- `answer` : Texte de la réponse
- `uses_context` : Toujours `True` (utilise le contexte du PDF)

**Fonctionnement** :
1. Télécharge le PDF global depuis Azure Blob via `download_global_audit_pdf_to_temp()`
2. Upload le PDF vers Kimi avec `purpose="file-extract"`
3. Récupère le texte extrait via `client.files.content(file_id=file_id).text`
4. Construit un prompt système avec le texte complet du document
5. Appelle `client.chat.completions.create()` avec le modèle `KIMI_MODEL_GLOBAL`
6. Gère les réponses string ou liste de blocs

**Utilisation** :
```python
answer_text, uses_context = answer_global_with_kimi(question)
```

### Recherche dans Azure Search

#### `_search_docs(question: str, filters: Optional[Dict[str, Any]], k: int = RETRIEVAL_K) -> Dict[str, Any]`

**Localisation** : `app/services/search_azure.py`

**Description** : Effectue une recherche dans l'index Azure AI Search.

**Paramètres** :
- `question` : Requête de recherche
- `filters` : Filtres OData optionnels
- `k` : Nombre de résultats à retourner (défaut : `RETRIEVAL_K`)

**Retour** : Dictionnaire JSON contenant les résultats de recherche avec :
- `value` : Liste des documents trouvés
- `@search.answers` : Réponses extractives (si disponibles)
- `@search.captions` : Captions extractives (si disponibles)

**Fonctionnement** :
1. Vérifie la configuration via `_require_search_config()`
2. Construit l'URL de l'API Azure Search
3. **Requête 1 (Simple)** : Mode BM25 sans configuration sémantique
   - Utilise `queryType: "simple"`
   - Sélectionne les champs pertinents
   - Applique les filtres OData via `_build_odata_filter()`
4. **Requête 2 (Sémantique)** : Si `RAG_ALLOW_SEMANTIC=1` et configuration présente
   - Utilise `queryType: "semantic"`
   - Active les captions extractives
   - Utilise le reranker pour améliorer la pertinence
5. Gestion des erreurs avec repli sur requête simple si échec

**Champs retournés** :
- `id`, `entity_type`, `file_name`, `content`
- `magasin_name`, `magasin_code`, `pdf_blob_url`
- `image_blob_container`, `image_blob_urls`
- `@search.score`, `@search.rerankerScore`

**Utilisation** :
```python
search_json = _search_docs(effective_question, req.filters, k=RETRIEVAL_K)
hits = search_json.get("value", []) or []
answers = search_json.get("@search.answers", []) or []
```

### Raffinement de requête

#### `_compose_search_query_from_history(question: str, chat_history_pairs: list[dict]) -> tuple[str, dict]`

**Localisation** : `app/utils/query_refiner.py`

**Description** : Complète la question avec le contexte de l'historique de conversation.

**Paramètres** :
- `question` : Question actuelle
- `chat_history_pairs` : Liste des derniers couples question/réponse

**Retour** : Tuple contenant :
- `query_effective` : Requête complétée pour Azure Search
- `meta` : Métadonnées avec `used_history` et `reason`

**Fonctionnement** :
1. Si pas d'historique, retourne la question telle quelle
2. Construit un bloc d'historique avec les 3 derniers échanges
3. Configure un modèle Gemini avec instruction système pour compléter les questions elliptiques
4. Appelle `model.generate_content()` avec réponse JSON
5. Parse le JSON et extrait la requête raffinée
6. Gestion des erreurs avec fallback sur la question originale

**Utilisation** :
```python
effective_question, refine_meta = _compose_search_query_from_history(question, history_pairs)
```

### Synthèse avec citations

#### `_synthesize_with_citations(question: str, contexts: List[Dict[str, Any]], chat_history_pairs: List[Dict[str, str]]) -> Tuple[str, bool, List[int]]`

**Localisation** : `app/services/gemini_rag.py`

**Description** : Synthétise une réponse à partir des contextes trouvés.

**Paramètres** :
- `question` : Question de l'utilisateur
- `contexts` : Liste de contextes (documents) numérotés 1..N
- `chat_history_pairs` : Historique de conversation

**Retour** : Tuple contenant :
- `answer_text` : Texte de la réponse synthétisée
- `uses_context` : Booléen indiquant si le contexte a été utilisé
- `used_sources_indices` : Liste d'indices 1-based des sources utilisées

**Fonctionnement** :
1. Construit un bloc SOURCES numérotées avec titre et snippet
2. Construit un bloc HISTORIQUE avec les 3 derniers échanges
3. Crée un prompt système pour Kimi avec instructions strictes
4. Appelle `kimi_chat_completion()` avec le modèle `KIMI_MODEL_SINGLE`
5. Parse le JSON de réponse de manière robuste (extraction du bloc JSON si nécessaire)
6. Extrait `answer`, `uses_context`, et `used_sources`
7. Valide que les indices de sources sont dans la plage valide

**Format de réponse attendu** :
```json
{
  "answer": "texte de la réponse",
  "uses_context": true,
  "used_sources": [1, 2, 3]
}
```

**Utilisation** :
```python
answer_text, uses_context, used_list = _synthesize_with_citations(
    question=question,
    contexts=contexts,
    chat_history_pairs=history_pairs,
)
```

### Extraction et traitement des snippets

#### `_extract_title(d: Dict[str, Any]) -> Optional[str]`

**Localisation** : `app/utils/snippets.py`

**Description** : Extrait un titre lisible depuis les métadonnées d'un document.

**Fonctionnement** :
- Si `entity_type == "cv"` : Retourne `cv_person_name` ou `file_name`
- Si `entity_type == "audit_pdf"` : Retourne `magasin_name` ou `file_name`
- Sinon : Retourne `file_name`

#### `_extract_path(d: Dict[str, Any]) -> Optional[str]`

**Localisation** : `app/utils/snippets.py`

**Description** : Extrait l'URL du blob depuis les métadonnées.

**Fonctionnement** :
- Si `entity_type == "audit_pdf"` : Retourne `pdf_blob_url`
- Si `entity_type == "cv"` : Retourne `cv_blob_url`
- Sinon : Retourne `None`

#### `_prefer_answer_or_focused_snippet(question: str, d: dict) -> str`

**Localisation** : `app/utils/snippets.py`

**Description** : Sélectionne le meilleur snippet pour un document.

**Fonctionnement** :
1. Privilégie `@search.captions` si disponible
2. Sinon, utilise un windowing focalisé sur les termes de la question
3. Appelle `_best_window()` pour trouver la fenêtre la mieux scorée
4. Fallback sur les 1200 premiers caractères du contenu

#### `_best_window(text: str, terms: list[str], window: int = 1400, step: int = 350) -> str`

**Localisation** : `app/utils/snippets.py`

**Description** : Trouve la fenêtre de texte la plus pertinente.

**Fonctionnement** :
1. Normalise le texte en minuscules
2. Glisse une fenêtre de taille `window` avec un pas de `step`
3. Score chaque fenêtre avec `_score_text_span()`
4. Retourne la fenêtre avec le meilleur score

#### `_score_text_span(txt_norm: str, terms: list[str]) -> int`

**Localisation** : `app/utils/snippets.py`

**Description** : Calcule un score de pertinence pour un segment de texte.

**Fonctionnement** :
1. Compte les occurrences de chaque terme
2. Bonus de proximité si plusieurs termes apparaissent dans 120 caractères
3. Retourne le score total

### Extraction d'images pour magasin

#### `_extract_store_hints(question: str) -> Tuple[Optional[str], Optional[str]]`

**Localisation** : `app/routers/rag.py`

**Description** : Extrait des indices de magasin (nom et code) depuis la question.

**Retour** : Tuple contenant :
- `name_hint` : Nom du magasin (normalisé)
- `code_hint` : Code du magasin (2-6 chiffres)

**Fonctionnement** :
1. Normalise la question avec `_norm()`
2. Recherche un code magasin avec regex `STORE_CODE_RE`
3. Extrait un nom en retirant les mots vides et les codes
4. Retourne `None` si le nom fait moins de 3 caractères

#### `_gather_images_for_store(hits: List[Dict[str, Any]], name_hint: Optional[str], code_hint: Optional[str], limit: int) -> List[str]`

**Localisation** : `app/routers/rag.py`

**Description** : Rassemble les URLs d'images avec SAS valides pour un magasin.

**Paramètres** :
- `hits` : Résultats de recherche Azure
- `name_hint` : Nom du magasin
- `code_hint` : Code du magasin
- `limit` : Nombre maximum d'images

**Retour** : Liste d'URLs SAS valides

**Fonctionnement** :
1. Filtre les hits avec `_doc_matches_store()`
2. **Cas 1** : Si `image_blob_urls` est présent dans l'index
   - Extrait le chemin du blob via `_extract_blob_path_from_url()`
   - Régénère un SAS frais via `_make_sas_url()`
3. **Cas 2** : Si `image_blob_urls` est vide
   - Devine les noms d'images via `_guess_images_from_file_pattern()`
   - Teste l'existence des blobs
   - Génère les SAS correspondants
4. Déduplique et limite à `limit`

#### `_guess_images_from_file_pattern(d: Dict[str, Any], container: str, limit: int) -> List[str]`

**Localisation** : `app/routers/rag.py`

**Description** : Devine les noms d'images à partir du pattern du nom de fichier.

**Fonctionnement** :
1. Extrait le nom de base sans extension
2. Parse les parties séparées par `_`
3. Construit un préfixe avec le numéro de fiche et le reste
4. Teste les candidats `{prefix}_photo_{i}.{ext}` pour i=1..max_photos
5. Vérifie l'existence via `_blob_exists()`
6. Génère les SAS via `_make_sas_url()`

### Construction des documents utilisés

#### `_make_used_doc_from_context(c: Dict[str, Any]) -> Dict[str, Any]`

**Localisation** : `app/utils/snippets.py`

**Description** : Construit un objet document utilisé depuis un contexte.

**Retour** : Dictionnaire avec :
- `id` : ID du document
- `title` : Titre du document
- `path` : Chemin/URL du document
- `score` : Score de recherche
- `reranker` : Score du reranker

### Vérification de pertinence

#### `_is_in_scope(hits: List[Dict[str, Any]]) -> bool`

**Localisation** : `app/utils/snippets.py`

**Description** : Vérifie si les résultats sont suffisamment pertinents.

**Fonctionnement** :
1. Prend le premier hit
2. Si `@search.rerankerScore` existe : Vérifie qu'il est >= `RERANKER_MIN` (0.8)
3. Sinon, si `@search.score` existe : Vérifie qu'il est >= `BM25_MIN` (0.5)
4. Sinon : Retourne `True` par défaut

## Gestion de l'historique

### `_save_chat_event(claims, conversation_id, role, route, message, meta)`

**Localisation** : `app/services/history_helpers.py`

**Description** : Enregistre un événement de conversation dans Azure Table Storage.

**Paramètres** :
- `claims` : Claims JWT
- `conversation_id` : ID de conversation (généré si None)
- `role` : "user", "assistant", ou "meta"
- `route` : Route API ("rag", "trading", etc.)
- `message` : Contenu du message
- `meta` : Métadonnées JSON

### `_get_last_qna_pairs(claims, conversation_id, route, max_pairs) -> List[Dict[str, str]]`

**Localisation** : `app/services/history_helpers.py`

**Description** : Récupère les derniers couples question/réponse.

**Retour** : Liste de dictionnaires avec clés "user" et "assistant"

## Configuration

Les constantes importantes sont définies dans `app/core/config.py` :

- `RETRIEVAL_K` : Nombre de documents à récupérer (défaut : 8)
- `TOPN_MAX` : Nombre maximum de documents à utiliser pour la synthèse
- `KIMI_MODEL_SINGLE` : Modèle Kimi pour synthèse single store
- `KIMI_MODEL_GLOBAL` : Modèle Kimi pour analyse globale
- `RERANKER_MIN` : Score minimum du reranker
- `BM25_MIN` : Score minimum BM25

## Gestion des erreurs

L'API gère plusieurs types d'erreurs :

1. **Question vide** : HTTPException 400
2. **Erreur de recherche** : HTTPException 502 (service unreachable) ou code d'erreur Azure
3. **Erreur de synthèse** : Message d'erreur dans la réponse
4. **Pas de résultats pertinents** : Message informatif retourné

## Optimisations

1. **Cache de requêtes** : L'historique permet d'éviter les recherches redondantes
2. **Raffinement de requête** : Améliore la précision des recherches
3. **Windowing focalisé** : Réduit la taille du contexte envoyé au LLM
4. **Limitation des résultats** : `TOPN_MAX` limite le nombre de contextes traités
5. **Déduplication d'images** : Évite les doublons dans les résultats

