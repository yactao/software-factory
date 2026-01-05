# Documentation du Code - API Web Search

Cette documentation détaille le fonctionnement interne de l'API Web Search et toutes les fonctions utilisées pour effectuer des recherches web avec grounding via Gemini.

## Vue d'ensemble

L'API Web Search permet d'effectuer des recherches sur le web en utilisant Gemini avec grounding. Le grounding permet de citer les sources utilisées et d'améliorer la fiabilité des réponses.

## Architecture du flux

### 1. Point d'entrée : `search_web()` dans `app/routers/websearch.py`

La fonction principale `search_web()` orchestre le processus :

```python
@router.post("/api/search", response_model=WebSearchOut)
def search_web(body: WebSearchIn, claims: dict = Depends(_auth_dependency))
```

**Paramètres** :
- `body` : Objet `WebSearchIn` contenant :
  - `question` : Question de l'utilisateur (requis)
  - `context` : Contexte optionnel
  - `force_grounding` : Force l'activation/désactivation du grounding (optionnel)
  - `legacy_15` : Utilise l'ancienne version des outils (optionnel, défaut: False)
  - `conversation_id` : ID de conversation (optionnel)
- `claims` : Claims JWT de l'utilisateur authentifié

**Flux d'exécution** :

1. **Validation** : Vérifie que la question n'est pas vide
2. **Enregistrement utilisateur** : Sauvegarde le message via `_save_chat_event()`
3. **Configuration grounding** : Détermine si le grounding doit être activé
4. **Construction outils** : Construit les outils de recherche web si nécessaire
5. **Appel Gemini** : Appelle le modèle Gemini avec la question et le contexte
6. **Extraction citations** : Extrait les citations des sources utilisées
7. **Enregistrement réponse** : Sauvegarde la réponse avec métadonnées
8. **Retour** : Retourne la réponse avec citations et statut de grounding

## Fonctions principales

### Configuration du grounding

#### `_build_web_tools(legacy_15: bool) -> List[gtypes.Tool]`

**Localisation** : `app/services/gemini_web.py`

**Description** : Construit les outils de recherche web pour Gemini.

**Paramètres** :
- `legacy_15` : Si `True`, utilise l'ancienne version des outils (v1.5), sinon utilise la version native 2.0+

**Retour** : Liste d'outils Gemini

**Fonctionnement** :

**Cas legacy_15 = True** :
```python
retrieval_tool = gtypes.Tool(
    google_search_retrieval=gtypes.GoogleSearchRetrieval(
        dynamic_retrieval_config=gtypes.DynamicRetrievalConfig(
            mode=gtypes.DynamicRetrievalConfigMode.MODE_DYNAMIC,
            dynamic_threshold=0.7,
        )
    )
)
return [retrieval_tool]
```

**Cas legacy_15 = False** (défaut) :
```python
return [gtypes.Tool(google_search=gtypes.GoogleSearch())]
```

**Différences** :
- **Legacy v1.5** : Utilise `GoogleSearchRetrieval` avec configuration dynamique et seuil de 0.7
- **Native 2.0+** : Utilise `GoogleSearch` natif, plus simple et intégré

**Utilisation** :
```python
use_grounding = body.force_grounding if body.force_grounding is not None else USE_GROUNDING
config = None
if use_grounding:
    tools = _build_web_tools(legacy_15=bool(body.legacy_15))
    config = gtypes.GenerateContentConfig(tools=tools)
```

### Client Gemini Web

#### `get_web_client() -> genai_web.Client`

**Localisation** : `app/services/gemini_web.py`

**Description** : Retourne le client Gemini Web configuré.

**Fonctionnement** :
```python
_gemini_web_client = genai_web.Client(api_key=GEMINI_API_KEY)

def get_web_client():
    return _gemini_web_client
```

**Configuration** :
- Utilise `GEMINI_API_KEY` depuis la configuration
- Client global initialisé une seule fois

### Appel à Gemini

#### `client.models.generate_content(model, contents, config)`

**Localisation** : Utilisation directe de l'API Gemini

**Description** : Appelle le modèle Gemini pour générer une réponse.

**Paramètres** :
- `model` : `GEMINI_MODEL_WEB` (défini dans config, ex: "gemini-2.0-flash-exp")
- `contents` : Liste de contenus avec rôle et texte
- `config` : Configuration optionnelle avec outils si grounding activé

**Construction du contenu** :
```python
system = (
    "Tu es un assistant qui répond avec des faits exacts. "
    "Si le grounding est activé, cite uniquement les sources renvoyées. "
    "Structure la réponse en paragraphes courts."
)
contents = [gtypes.Content(
    role="user",
    parts=[gtypes.Part(text=f"{system}\n\nQuestion: {question}\nContexte: {body.context or 'N/A'}")]
)]
```

**Gestion d'erreurs** :
```python
try:
    resp = client.models.generate_content(model=GEMINI_MODEL_WEB, contents=contents, config=config)
except Exception as e:
    err_txt = f"Erreur Gemini: {e}"
    payload_err = WebSearchOut(
        answer=err_txt,
        citations=[],
        model=GEMINI_MODEL_WEB,
        grounded=False,
        conversation_id=conv_id
    )
    _save_chat_event(claims, conv_id, role="assistant", route="search", message=err_txt, meta=payload_err.dict())
    raise HTTPException(502, err_txt)
```

### Extraction des citations

#### `_extract_web_citations(resp) -> List[WebCitation]`

**Localisation** : `app/services/gemini_web.py`

**Description** : Extrait les citations des sources utilisées depuis la réponse Gemini.

**Paramètres** :
- `resp` : Réponse de Gemini (`GenerateContentResponse`)

**Retour** : Liste d'objets `WebCitation` avec `title` et `url`

**Fonctionnement** :

1. **Accès aux métadonnées de grounding** :
```python
cand = resp.candidates[0]
gm = getattr(cand, "grounding_metadata", None)
```

2. **Vérification des chunks de grounding** :
```python
if not gm or not gm.grounding_chunks:
    return cites
```

3. **Extraction des URLs** :
```python
seen = set()
for ch in gm.grounding_chunks:
    web = getattr(ch, "web", None)
    if not web:
        continue
    uri = getattr(web, "uri", None)
    title = getattr(web, "title", None)
    if uri and uri not in seen:
        cites.append(WebCitation(title=title, url=uri))
        seen.add(uri)
```

**Déduplication** : Utilise un `set` pour éviter les doublons d'URLs

**Gestion d'erreurs** : Retourne une liste vide en cas d'exception

**Utilisation** :
```python
text = getattr(resp, "text", "") or ""
citations = _extract_web_citations(resp)
grounded = len(citations) > 0
```

### Détermination du statut de grounding

```python
grounded = len(citations) > 0
if use_grounding and not grounded:
    text = f"{text}\n\n[Note] Aucune source explicite renvoyée par le grounding."
```

**Logique** :
- `grounded = True` si au moins une citation a été extraite
- Si grounding activé mais aucune citation : Ajoute une note dans le texte

## Gestion de l'historique

### `_save_chat_event(claims, conversation_id, role, route, message, meta)`

**Localisation** : `app/services/history_helpers.py`

**Description** : Enregistre un événement de conversation.

**Utilisation dans Web Search** :

**Message utilisateur** :
```python
conv_id = _save_chat_event(
    claims,
    conversation_id=body.conversation_id,
    role="user",
    route="search",
    message=question if not body.context else f"{question}\n\n[CTX]\n{body.context}",
    meta={
        "type": "search_user",
        "force_grounding": body.force_grounding,
        "legacy_15": body.legacy_15
    }
)
```

**Message assistant** :
```python
_save_chat_event(
    claims,
    conv_id,
    role="assistant",
    route="search",
    message=payload.answer,
    meta=payload.dict()
)
```

## Configuration

Les constantes importantes sont définies dans `app/core/config.py` :

- `USE_GROUNDING` : Activation par défaut du grounding (booléen)
- `GEMINI_MODEL_WEB` : Modèle Gemini utilisé (ex: "gemini-2.0-flash-exp")
- `GEMINI_API_KEY` : Clé API Gemini

## Modèles de données

### `WebSearchIn`

**Localisation** : `app/models/schemas.py`

**Structure** :
```python
class WebSearchIn(BaseModel):
    question: str
    context: Optional[str] = None
    force_grounding: Optional[bool] = None
    legacy_15: Optional[bool] = False
    conversation_id: Optional[str] = None
```

### `WebSearchOut`

**Localisation** : `app/models/schemas.py`

**Structure** :
```python
class WebSearchOut(BaseModel):
    answer: str
    citations: List[WebCitation]
    model: str
    grounded: bool
    conversation_id: Optional[str] = None
```

### `WebCitation`

**Localisation** : `app/models/schemas.py`

**Structure** :
```python
class WebCitation(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None
```

## Gestion des erreurs

1. **Question vide** : `HTTPException 400` avec message "Le champ 'question' est requis et ne doit pas être vide."
2. **Erreur Gemini** : `HTTPException 502` avec détails de l'erreur
   - La réponse d'erreur est enregistrée dans l'historique avant de lever l'exception

## Logique de grounding

### Détermination de l'activation

```python
use_grounding = body.force_grounding if body.force_grounding is not None else USE_GROUNDING
```

**Priorité** :
1. Si `force_grounding` est fourni : Utilise cette valeur
2. Sinon : Utilise `USE_GROUNDING` depuis la configuration

### Construction de la configuration

```python
config = None
if use_grounding:
    tools = _build_web_tools(legacy_15=bool(body.legacy_15))
    config = gtypes.GenerateContentConfig(tools=tools)
```

**Si grounding activé** :
- Construit les outils de recherche web
- Crée une configuration avec ces outils
- Passe la configuration à l'appel Gemini

**Si grounding désactivé** :
- `config = None`
- Gemini n'utilise pas d'outils de recherche
- Les citations seront vides

## Format de réponse

La réponse finale suit le modèle `WebSearchOut` :

```python
payload = WebSearchOut(
    answer=text.strip(),
    citations=citations,
    model=GEMINI_MODEL_WEB,
    grounded=grounded,
    conversation_id=conv_id
)
```

**Exemple de réponse** :
```json
{
  "answer": "Réponse générée par Gemini...",
  "citations": [
    {
      "title": "Titre de la source",
      "url": "https://example.com/article"
    }
  ],
  "model": "gemini-2.0-flash-exp",
  "grounded": true,
  "conversation_id": "conv_123"
}
```

## Différences entre versions d'outils

### Version Legacy (v1.5)

- Utilise `GoogleSearchRetrieval` avec configuration dynamique
- Seuil de confiance : 0.7
- Mode : `MODE_DYNAMIC`
- Plus de contrôle sur le comportement de récupération

### Version Native (2.0+)

- Utilise `GoogleSearch` natif
- Configuration simplifiée
- Intégration directe avec les modèles Gemini 2.0+
- Performance améliorée

## Bonnes pratiques

1. **Gestion du contexte** : Le contexte optionnel est inclus dans le message utilisateur
2. **Enregistrement complet** : Toutes les métadonnées sont enregistrées (force_grounding, legacy_15)
3. **Note informative** : Si grounding activé mais aucune citation, une note est ajoutée
4. **Déduplication** : Les citations sont dédupliquées par URL
5. **Gestion d'erreurs robuste** : Les erreurs sont enregistrées avant d'être propagées

## Optimisations

1. **Client global** : Le client Gemini est initialisé une seule fois
2. **Configuration conditionnelle** : Les outils ne sont construits que si nécessaire
3. **Extraction efficace** : Utilisation de `getattr()` pour accès sécurisé aux attributs
4. **Déduplication** : Utilisation d'un `set` pour éviter les doublons

