# Documentation du Code - API Aïna Finance

Cette documentation détaille le fonctionnement interne de l'API Aïna Finance et toutes les fonctions utilisées pour analyser les fichiers Excel financiers.

## Vue d'ensemble

L'API Aïna Finance permet d'analyser des fichiers Excel financiers en utilisant l'agent Kimi. Elle extrait des données, génère des graphiques, et fournit des explications textuelles basées sur les données réelles du fichier.

## Architecture du flux

### 1. Point d'entrée : `finance()` dans `app/routers/aina_finance.py`

La fonction principale `finance()` orchestre le processus :

```python
@router.post("/api/aina/finance")
def finance(req: FinanceRequest, claims: Dict[str, Any] = Depends(_auth_dependency))
```

**Paramètres** :
- `req` : Objet `FinanceRequest` contenant `question` et `conversation_id`
- `claims` : Claims JWT de l'utilisateur authentifié

**Flux d'exécution** :

1. **Validation** : Vérifie que la question n'est pas vide
2. **Enregistrement utilisateur** : Sauvegarde le message via `_save_chat_event()`
3. **Récupération historique** : Obtient les 3 derniers couples Q/A via `_get_last_qna_pairs()`
4. **Appel agent** : Appelle `answer_finance_with_kimi()` pour l'analyse
5. **Enregistrement réponse** : Sauvegarde la réponse avec métadonnées complètes
6. **Retour** : Retourne `answer`, `chart`, `rows`, et `conversation_id`

## Fonction principale : Analyse avec Kimi

### `answer_finance_with_kimi(question: str, history_pairs: List[Dict[str, str]]) -> Tuple[str, Dict[str, Any], List[Dict[str, Any]]]`

**Localisation** : `app/services/agent_finance.py`

**Description** : Analyse le fichier Excel finance avec l'agent Kimi et retourne une réponse textuelle, un graphique, et les lignes utilisées.

**Paramètres** :
- `question` : Question de l'utilisateur
- `history_pairs` : Historique des derniers échanges (format [{"user": "...", "assistant": "..."}])

**Retour** : Tuple contenant :
- `answer` : Texte explicatif en français
- `chart` : Configuration du graphique (type, titre, axes, séries)
- `excerpt_rows` : Liste des lignes exactes utilisées (anti-hallucination)

**Flux détaillé** :

#### Étape 1 : Téléchargement du fichier Excel

```python
xlsx_path = download_finance_excel_to_temp()
```

**Fonction** : `download_finance_excel_to_temp()` dans `app/services/blob_finance_excel.py`

**Description** : Télécharge le fichier Excel depuis Azure Blob Storage vers un fichier temporaire local.

**Retour** : Chemin du fichier temporaire

**Gestion d'erreurs** : Lève `HTTPException 500` si le téléchargement échoue

#### Étape 2 : Chargement et préparation des données

```python
df = pd.read_excel(xlsx_path)
df = df.dropna(how="all").reset_index(drop=True)
```

**Opérations** :
- Charge le fichier Excel avec pandas
- Supprime les lignes entièrement vides
- Réinitialise l'index

**Limitation** : Seules les 300 premières lignes sont envoyées au LLM (`MAX_ROWS_FOR_LLM = 300`)

#### Étape 3 : Conversion en JSON

```python
records = df_llm.to_dict(orient="records")
data_json = json.dumps(records, ensure_ascii=False)
```

**Format** : Liste de dictionnaires où chaque dictionnaire représente une ligne avec les colonnes comme clés.

**Sérialisation** : Utilise `_serialize_value()` pour gérer :
- Dates : Conversion en format ISO
- NaN : Conversion en `None`
- Types NumPy : Conversion en types Python natifs

#### Étape 4 : Extraction des informations de colonnes

```python
columns_info: List[Dict[str, Any]] = []
for col in df_llm.columns:
    col_type = str(df_llm[col].dtype)
    columns_info.append({"name": col, "dtype": col_type})
columns_json = json.dumps(columns_info, ensure_ascii=False)
```

**Objectif** : Fournir au LLM le schéma des colonnes (nom et type) pour une meilleure compréhension.

#### Étape 5 : Construction de l'historique

```python
hist_lines: List[str] = []
for pair in history_pairs[-3:]:
    u = (pair.get("user") or "").strip()
    a = (pair.get("assistant") or "").strip()
    if u:
        hist_lines.append(f"U: {u}")
    if a:
        hist_lines.append(f"A: {a}")
history_text = "\n".join(hist_lines) if hist_lines else "aucun historique pertinent."
```

**Format** : Texte simple avec préfixes "U:" et "A:" pour user et assistant.

**Limitation** : Seuls les 3 derniers échanges sont conservés.

#### Étape 6 : Construction de l'index de validation (anti-hallucination)

```python
def _canonical_row(d: Dict[str, Any]) -> str:
    normalized: Dict[str, Any] = {}
    for c in df_llm.columns:
        normalized[c] = _serialize_value(d.get(c))
    return json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

llm_rows_map: Dict[str, Dict[str, Any]] = {}
for r in records:
    canon = _canonical_row(r)
    if canon not in llm_rows_map:
        full_norm = {c: _serialize_value(r.get(c)) for c in df_llm.columns}
        llm_rows_map[canon] = full_norm
```

**Objectif** : Créer un index permettant de valider que les lignes renvoyées par le LLM existent réellement dans les données.

**Mécanisme** :
- Chaque ligne est sérialisée de manière canonique (clés triées, valeurs normalisées)
- L'index mappe la représentation canonique vers la ligne normalisée complète

#### Étape 7 : Construction du prompt système

Le prompt système contient :

1. **Rôle** : Expert data analyst et finance
2. **Règles importantes** :
   - Répondre strictement à partir des données
   - Ne pas inventer d'informations
   - Permettre calculs simples (somme, moyenne, max, min, classement, comparaison)
   - Montants en euros
   - Inclure certaines colonnes dans les extraits si présentes
3. **Format de sortie** : JSON strict avec schéma défini
4. **Instructions spéciales** : Ne pas renvoyer d'indices de lignes, mais les lignes complètes

**Schéma JSON attendu** :
```json
{
  "answer": "texte en français",
  "uses_context": true,
  "chart": {
    "type": "bar" | "horizontal_bar" | "line" | "pie" | "bubble" | "none",
    "title": "Titre",
    "x_label": "Axe X",
    "y_label": "Axe Y",
    "series": [{
      "label": "Série",
      "points": [{"x": "catégorie", "y": nombre}]
    }]
  },
  "table_excerpt": {
    "columns": ["col1", "col2", ...],
    "rows": [{"col1": "val1", "col2": 123, ...}, ...]
  }
}
```

#### Étape 8 : Construction du prompt utilisateur

Le prompt utilisateur contient :

1. **Contexte conversation** : Historique formaté
2. **Question utilisateur** : Question actuelle
3. **Schéma des colonnes** : JSON avec nom et type
4. **Données de la table** : JSON avec toutes les lignes
5. **Instructions** : Copier exactement les objets-lignes existants

#### Étape 9 : Appel à Kimi

```python
client = get_kimi_client()
completion = client.chat.completions.create(
    model=KIMI_MODEL_SINGLE,
    messages=messages,
    temperature=0.2,
    max_tokens=2500,
)
```

**Configuration** :
- Modèle : `KIMI_MODEL_SINGLE` (défini dans config)
- Température : 0.2 (faible pour plus de cohérence)
- Max tokens : 2500

#### Étape 10 : Parsing de la réponse

**Gestion du contenu** :
- Si `msg.content` est une string : Utilisation directe
- Si `msg.content` est une liste : Extraction des parties texte

**Parsing JSON robuste** :
1. Tentative directe : `json.loads(raw_text)`
2. Extraction du bloc JSON : Recherche de `{` et `}`
3. En cas d'échec : Lève `HTTPException 500`

#### Étape 11 : Extraction et normalisation des résultats

**Answer** :
```python
answer = (obj.get("answer") or "").strip() or "Réponse vide."
```

**Chart** :
```python
chart = obj.get("chart") or {
    "type": "none",
    "title": "",
    "x_label": "",
    "y_label": "",
    "series": [],
}
chart = _normalize_chart_axes(chart)
```

**Normalisation des axes** : Voir fonction `_normalize_chart_axes()`

**Rows** :
```python
table_excerpt = obj.get("table_excerpt") or {}
raw_columns = table_excerpt.get("columns") or []
raw_rows = table_excerpt.get("rows") or []

# Validation des colonnes
if isinstance(raw_columns, list) and raw_columns:
    cols: List[str] = [c for c in raw_columns if c in df_llm.columns]
    for c in df_llm.columns:
        if c not in cols:
            cols.append(c)
else:
    cols = list(df_llm.columns)

# Validation des rows (anti-hallucination)
excerpt_rows: List[Dict[str, Any]] = []
if isinstance(raw_rows, list) and raw_rows:
    for rr in raw_rows:
        if not isinstance(rr, dict):
            continue
        canon = _canonical_row(rr)
        matched = llm_rows_map.get(canon)
        if matched:
            excerpt_rows.append({c: matched.get(c) for c in cols})
```

**Mécanisme anti-hallucination** :
- Chaque row renvoyée est canonisée
- Recherche dans `llm_rows_map` pour vérifier l'existence
- Si trouvée, ajout à `excerpt_rows` avec toutes les colonnes
- Si non trouvée, ignorée (pas de fallback)

## Fonctions utilitaires

### `_normalize_chart_axes(chart: Dict[str, Any]) -> Dict[str, Any]`

**Localisation** : `app/services/agent_finance.py`

**Description** : Normalise les axes des graphiques pour s'assurer que X contient les catégories (texte) et Y les valeurs (nombres).

**Fonctionnement** :
1. Vérifie le type de graphique (`bar`, `horizontal_bar`, `line`, `bubble`)
2. Pour chaque série, examine les points
3. Si X est majoritairement numérique et Y majoritairement texte : Inverse X et Y
4. Retourne le graphique normalisé

**Exemple** :
- Avant : `{"x": 1000, "y": "Magasin A"}`
- Après : `{"x": "Magasin A", "y": 1000}`

### `_serialize_value(v: Any) -> Any`

**Localisation** : `app/services/agent_finance.py` (fonction interne)

**Description** : Sérialise une valeur de manière stable pour la comparaison.

**Fonctionnement** :
- Dates (`pd.Timestamp`, `datetime`, `date`) : Conversion en ISO format
- NaN : Conversion en `None`
- Types NumPy : Conversion en types Python natifs via `.item()`
- Autres : Retour tel quel

### `_canonical_row(d: Dict[str, Any]) -> str`

**Localisation** : `app/services/agent_finance.py` (fonction interne)

**Description** : Crée une représentation canonique d'une ligne pour la comparaison.

**Fonctionnement** :
1. Normalise toutes les valeurs avec `_serialize_value()`
2. Trie les clés pour stabilité
3. Sérialise en JSON compact (sans espaces)

## Gestion de l'historique

### `_save_chat_event(claims, conversation_id, role, route, message, meta)`

**Localisation** : `app/services/history_helpers.py`

**Description** : Enregistre un événement de conversation.

**Utilisation dans Aïna Finance** :
- Route : `"finance"`
- Meta : Contient le payload complet (answer, chart, rows)

### `_get_last_qna_pairs(claims, conversation_id, route, max_pairs) -> List[Dict[str, str]]`

**Localisation** : `app/services/history_helpers.py`

**Description** : Récupère les derniers couples question/réponse.

**Utilisation** :
- Route : `"finance"`
- Max pairs : 3
- Format retour : `[{"user": "...", "assistant": "..."}]`

## Configuration

Les constantes importantes sont définies dans `app/core/config.py` :

- `KIMI_MODEL_SINGLE` : Modèle Kimi utilisé pour l'analyse
- `MAX_ROWS_FOR_LLM` : Limite de lignes envoyées au LLM (300)

## Gestion des erreurs

1. **Question vide** : `HTTPException 400` avec message "Question vide."
2. **Erreur téléchargement Excel** : `HTTPException 500` avec détails
3. **Erreur lecture Excel** : `HTTPException 500` avec détails
4. **Excel vide** : `HTTPException 500` avec message "Le fichier Excel finance est vide."
5. **Erreur Kimi** : `HTTPException 500` avec détails de l'erreur
6. **Réponse non JSON** : `HTTPException 500` avec extrait de la réponse

## Optimisations et bonnes pratiques

1. **Limitation des données** : Seulement 300 lignes envoyées au LLM pour limiter les coûts
2. **Anti-hallucination** : Validation stricte des rows renvoyées
3. **Sérialisation stable** : Garantit la reproductibilité des comparaisons
4. **Normalisation des graphiques** : Assure la cohérence des axes
5. **Gestion des types** : Conversion appropriée des dates et NaN
6. **Historique limité** : Seulement 3 derniers échanges pour le contexte

## Format de réponse

La réponse finale contient :

```python
{
    "answer": "Explication textuelle...",
    "chart": {
        "type": "bar",
        "title": "Titre du graphique",
        "x_label": "Axe X",
        "y_label": "Axe Y",
        "series": [{
            "label": "Série 1",
            "points": [
                {"x": "Catégorie 1", "y": 100},
                {"x": "Catégorie 2", "y": 200}
            ]
        }]
    },
    "rows": [
        {"colonne1": "valeur1", "colonne2": 123, ...},
        ...
    ],
    "conversation_id": "conv_123"
}
```

