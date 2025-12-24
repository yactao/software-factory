# Documentation du Code - API Vision

Cette documentation détaille le fonctionnement interne de l'API Vision et toutes les fonctions utilisées pour analyser des images de plans avec détection d'objets et calcul de surfaces/périmètres.

## Vue d'ensemble

L'API Vision permet d'analyser des images de plans architecturaux en utilisant Azure Custom Vision pour la détection d'objets, puis calcule des surfaces et périmètres selon une échelle fournie. Elle peut également générer des images annotées.

## Architecture du flux

### 1. Point d'entrée : `analyze_plan()` dans `app/routers/vision.py`

La fonction principale `analyze_plan()` orchestre tout le processus :

```python
@router.post("/api/vision", response_model=AnalyzeResponse)
async def analyze_plan(
    file: Optional[UploadFile] = File(None),
    prompt: str = Form(...),
    m_per_pixel: Optional[float] = Form(0.02),
    ratio: Optional[str] = Form("1/100"),
    return_image: bool = Form(True),
    conversation_id: Optional[str] = Form(None),
    claims: dict = Depends(_auth_dependency),
)
```

**Paramètres** :
- `file` : Fichier image optionnel (png, jpg, jpeg, pdf)
- `prompt` : Instruction utilisateur (requis)
- `m_per_pixel` : Échelle en mètres par pixel (défaut: 0.02)
- `ratio` : Échelle sous forme de ratio (défaut: "1/100")
- `return_image` : Si vrai, renvoie une image annotée
- `conversation_id` : ID de conversation optionnel
- `claims` : Claims JWT de l'utilisateur authentifié

**Flux d'exécution** :

1. **Enregistrement utilisateur** : Sauvegarde le message via `_save_chat_event()`
2. **Récupération/upload fichier** : Gère l'upload ou la réutilisation d'un fichier existant
3. **Calcul échelle** : Parse l'échelle via `_parse_scale()`
4. **Analyse intention** : Détermine l'intention via `llm_client.analyze_request()`
5. **Détection objets** : Détecte les objets via `vision_client.detect_objects()`
6. **Calcul surfaces/périmètres** : Calcule selon l'intention
7. **Génération image annotée** : Si demandé, via `_annotate_image()`
8. **Stockage Blob** : Stocke les fichiers dans Azure Blob Storage
9. **Retour** : Retourne les résultats avec URLs SAS

## Fonctions principales

### Gestion des fichiers

#### `_pdf_to_image(file_bytes: bytes) -> Image.Image`

**Localisation** : `app/services/vision_helpers.py`

**Description** : Convertit un PDF en image PIL.

**Fonctionnement** :
1. Utilise `pdf2image.convert_from_bytes()` pour convertir le PDF
2. Prend la première page
3. Convertit en RGB

**Gestion d'erreurs** :
- Lève `HTTPException 500` si `pdf2image` ou `poppler` manquent
- Lève `HTTPException 400` si le PDF est vide

**Utilisation** :
```python
if name.endswith(".pdf"):
    pil_img = _pdf_to_image(content)
```

### Calcul de l'échelle

#### `_parse_scale(m_per_pixel: Optional[float], ratio_str: Optional[str]) -> float`

**Localisation** : `app/services/vision_helpers.py`

**Description** : Parse l'échelle depuis `m_per_pixel` ou `ratio`.

**Paramètres** :
- `m_per_pixel` : Échelle directe en mètres par pixel
- `ratio_str` : Échelle sous forme "1/n" (ex: "1/100")

**Retour** : Échelle en mètres par pixel (float)

**Fonctionnement** :
1. Si `m_per_pixel` fourni : Retourne directement
2. Si `ratio_str` fourni : Parse "1/n" et retourne `1.0 / float(n)`
3. Sinon : Utilise la variable d'environnement `PIXEL_TO_METER_RATIO` (défaut: 0.02)

**Gestion d'erreurs** :
- Lève `HTTPException 400` si le format de ratio est invalide

**Utilisation** :
```python
scale_ratio = _parse_scale(m_per_pixel, ratio)
```

### Analyse de l'intention

#### `llm_client.analyze_request(prompt: str) -> Dict[str, Any]`

**Localisation** : `app/utils/llm_interface.py` (méthode de `LLMInterface`)

**Description** : Analyse la requête utilisateur pour déterminer l'intention et la cible.

**Retour** : Dictionnaire avec :
- `intent` : Type de demande parmi ["surface", "detection_objets", "perimetre", "analyse_globale"]
- `target` : Pièce ou objet concerné (optionnel)

**Fonctionnement** :
1. Appelle Azure OpenAI avec un prompt système spécialisé
2. Le modèle retourne un JSON avec `intent` et `target`
3. Parse le JSON et normalise le `target` (liste -> premier élément, dict -> nom)
4. Fallback sur "analyse_globale" en cas d'erreur

**Prompt système** :
```
"Tu es un assistant d'analyse de plans architecturaux multilangue.
Ta tâche est de comprendre l'intention de l'utilisateur et la traduire en anglais
et d'extraire deux informations :
1. intent : le type de demande parmi [surface, detection_objets, perimetre, analyse_globale].
2. target : la pièce ou l'objet concerné s'il est mentionné."
```

**Utilisation** :
```python
intent_data = llm_client.analyze_request(prompt)
intent = intent_data.get("intent", "analyse_globale")
target = _normalize_target(intent_data.get("target"))
```

#### `_normalize_target(target) -> Optional[str]`

**Localisation** : `app/services/vision_helpers.py`

**Description** : Normalise la cible extraite par le LLM.

**Fonctionnement** :
- Si liste : Retourne le premier élément
- Si dict : Extrait `name` ou `tag_name`
- Si string : Retourne tel quel
- Sinon : Retourne `None`

### Détection d'objets

#### `vision_client.detect_objects(image_path: str) -> List[Dict[str, Any]]`

**Localisation** : `app/utils/vision_analysis.py` (méthode de `VisionAnalyzer`)

**Description** : Détecte les objets dans une image via Azure Custom Vision.

**Paramètres** :
- `image_path` : Chemin vers l'image locale

**Retour** : Liste de dictionnaires avec :
- `tag_name` : Nom de l'objet détecté
- `probability` : Probabilité de détection (0.0-1.0)
- `bounding_box` : Boîte englobante avec `left`, `top`, `width`, `height` (normalisées 0-1)

**Fonctionnement** :
1. Ouvre l'image en mode binaire
2. Appelle `client.detect_image()` avec `project_id` et `published_name`
3. Filtre les prédictions avec `probability >= min_confidence`
4. Formate les résultats avec bounding boxes normalisées

**Configuration** :
- `endpoint` : Endpoint Azure Custom Vision
- `prediction_key` : Clé de prédiction
- `project_id` : ID du projet
- `model_name` : Nom du modèle publié
- `min_confidence` : Seuil minimum de confiance (défaut: 0.6)

**Utilisation** :
```python
with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
    pil_img.save(tmp.name, format="JPEG")
    tmp_path = tmp.name
try:
    detections = vision_client.detect_objects(tmp_path)
finally:
    os.remove(tmp_path)
```

### Calcul de surfaces et périmètres

#### `calculate_surface(bbox, img_width: float, img_height: float, scale_ratio: float) -> float`

**Localisation** : `app/utils/geometry_utils.py`

**Description** : Calcule la surface d'un objet détecté en m².

**Paramètres** :
- `bbox` : Bounding box avec `w` et `h` (normalisées 0-1)
- `img_width` : Largeur de l'image en pixels
- `img_height` : Hauteur de l'image en pixels
- `scale_ratio` : Échelle en mètres par pixel

**Retour** : Surface en m² (float)

**Formule** :
```python
w = bbox["w"] * img_width * scale_ratio
h = bbox["h"] * img_height * scale_ratio
return w * h
```

#### `calculate_perimeter(bbox, img_width: float, img_height: float, scale_ratio: float) -> float`

**Localisation** : `app/utils/geometry_utils.py`

**Description** : Calcule le périmètre d'un objet détecté en mètres.

**Formule** :
```python
w = bbox["w"] * img_width * scale_ratio
h = bbox["h"] * img_height * scale_ratio
return 2.0 * (w + h)
```

#### `adapt_bbox(bbox: dict) -> dict`

**Localisation** : `app/utils/geometry_utils.py`

**Description** : Adapte le format de bounding box pour uniformité.

**Fonctionnement** :
- Azure Custom Vision peut utiliser `width`/`height` ou `w`/`h`
- Normalise vers `w` et `h` (float, normalisées 0-1)
- Gère les erreurs de conversion avec fallback sur 0.0

**Utilisation** :
```python
bbox = adapt_bbox(d["bounding_box"])
surfaces[tag] = calculate_surface(bbox, W, H, scale_ratio)
perimeters[tag] = calculate_perimeter(bbox, W, H, scale_ratio)
```

#### `analyze_global(surfaces: dict, perimeters: dict) -> Tuple[float, float]`

**Localisation** : `app/utils/geometry_utils.py`

**Description** : Calcule les totaux globaux de surface et périmètre.

**Retour** : Tuple `(total_surface, total_perimeter)`

**Fonctionnement** :
```python
total_surface = float(sum(float(v) for v in surfaces.values()))
total_perimeter = float(sum(float(v) for v in perimeters.values()))
```

**Gestion d'erreurs** :
- Lève `HTTPException 500` si les valeurs ne sont pas numériques

### Génération de réponse textuelle

#### `generate_response(intent, detections, surfaces, perimeters, ...) -> str`

**Localisation** : `app/utils/response_generator.py`

**Description** : Génère une réponse textuelle selon l'intention.

**Paramètres** :
- `intent` : Type d'intention
- `detections` : Liste des détections
- `surfaces` : Dictionnaire des surfaces
- `perimeters` : Dictionnaire des périmètres
- `target` : Cible optionnelle

**Fonctionnement selon l'intention** :

**intent == "surface"** :
- Si `target` spécifié : Retourne la surface de cette pièce
- Sinon, si une seule pièce : Retourne sa surface
- Sinon : Message d'erreur

**intent == "perimetre"** :
- Même logique que surface mais pour périmètre

**intent == "detection_objets"** :
- Compte les objets par tag
- Retourne la liste des objets détectés avec compteurs

**intent == "analyse_globale"** :
- Liste toutes les pièces avec surface et périmètre
- Format structuré avec totaux

**Utilisation** :
```python
try:
    response_text = generate_response(intent, detections, f_surfaces, f_perimeters) or response_text
except Exception:
    pass
```

### Annotation d'image

#### `_annotate_image(pil_img: Image.Image, detections: list) -> Image.Image`

**Localisation** : `app/services/vision_helpers.py`

**Description** : Dessine les bounding boxes et labels sur l'image.

**Paramètres** :
- `pil_img` : Image PIL à annoter
- `detections` : Liste des détections avec bounding boxes

**Retour** : Image PIL annotée

**Fonctionnement** :
1. Crée un objet `ImageDraw` sur l'image
2. Charge la police par défaut (fallback si échec)
3. Pour chaque détection :
   - Convertit les coordonnées normalisées en pixels
   - Dessine un rectangle rouge avec `draw.rectangle()`
   - Ajoute un label avec tag et probabilité
4. Retourne l'image annotée

**Utilisation** :
```python
if return_image:
    annotated = _annotate_image(pil_img.copy(), detections)
    annotated_blob_path = put_jpeg(pk, conv_id, "annotated.jpg", annotated)
```

### Stockage Blob

#### `put_temp(pk: str, conv_id: str, filename: str, content: bytes) -> str`

**Localisation** : `app/services/blob_vision.py`

**Description** : Stocke un fichier binaire dans Azure Blob Storage.

**Retour** : Chemin du blob stocké

#### `put_jpeg(pk: str, conv_id: str, filename: str, pil_img: Image.Image) -> str`

**Localisation** : `app/services/blob_vision.py`

**Description** : Stocke une image PIL en JPEG dans Azure Blob Storage.

**Retour** : Chemin du blob stocké

#### `sas_url(path: str, minutes: int) -> str`

**Localisation** : `app/services/blob_vision.py`

**Description** : Génère une URL SAS temporaire pour accéder à un blob.

**Paramètres** :
- `path` : Chemin du blob
- `minutes` : Durée de validité en minutes

**Retour** : URL SAS complète

## Gestion des fichiers

### Upload nouveau fichier

```python
if file is not None:
    content = await file.read()
    name = (file.filename or "upload").lower()
    
    if name.endswith(".pdf"):
        pil_img = _pdf_to_image(content)
        vision_file_path = put_jpeg(pk, conv_id, "source.jpg", pil_img)
    else:
        vision_file_path = put_temp(pk, conv_id, name, content)
        pil_img = Image.open(io.BytesIO(content)).convert("RGB")
```

### Réutilisation fichier existant

```python
else:
    vision_file_path = get_last_vision_file_path(claims, conv_id)
    if not vision_file_path:
        raise HTTPException(400, "Aucun fichier image attaché à cette conversation.")
    
    from azure.storage.blob import BlobClient
    cont = _container()
    bc = cont.get_blob_client(vision_file_path)
    data = bc.download_blob().readall()
    
    if name.endswith(".pdf"):
        pil_img = _pdf_to_image(data)
    else:
        pil_img = Image.open(io.BytesIO(data)).convert("RGB")
```

## Traitement selon l'intention

### Filtrage par cible

```python
if target and isinstance(target, str):
    f_surfaces = {k: v for k, v in surfaces.items() if k.lower() == target.lower()}
    f_perimeters = {k: v for k, v in perimeters.items() if k.lower() == target.lower()}
else:
    f_surfaces, f_perimeters = surfaces, perimeters
```

### Génération de réponse selon intention

```python
if intent == "surface":
    response_text = "\n".join([f"{k} : {float(v):.2f} m²" for k, v in f_surfaces.items()]) or "Aucune surface trouvée."
elif intent == "perimetre":
    response_text = "\n".join([f"{k} : {float(v):.2f} m" for k, v in f_perimeters.items()]) or "Aucun périmètre trouvé."
elif intent == "detection_objets":
    counts = {}
    for d in detections:
        counts[d["tag_name"]] = counts.get(d["tag_name"], 0) + 1
    response_text = "Objets détectés:\n" + "\n".join([f"{k} : {v}" for k, v in counts.items()])
else:
    total_surface, total_perimeter = analyze_global(f_surfaces, f_perimeters)
    response_text = f"Surface totale : {total_surface:.2f} m²\nPérimètre total : {total_perimeter:.2f} m"
```

## Configuration

Les constantes importantes sont définies dans `app/core/config.py` :

- `AZURE_OAI_ENDPOINT` : Endpoint Azure OpenAI
- `AZURE_OAI_KEY` : Clé API Azure OpenAI
- `AZURE_OAI_DEPLOYMENT` : Nom du déploiement
- `CV_ENDPOINT` : Endpoint Azure Custom Vision
- `CV_PRED_KEY` : Clé de prédiction Custom Vision
- `CV_PROJECT_ID` : ID du projet Custom Vision
- `CV_PUBLISHED_NAME` : Nom du modèle publié
- `CV_MIN_CONFIDENCE` : Seuil minimum de confiance

## Gestion des erreurs

1. **Fichier vide** : `HTTPException 400` avec message "Fichier vide."
2. **Image invalide** : `HTTPException 400` avec détails de l'erreur
3. **Aucun fichier attaché** : `HTTPException 400` si réutilisation sans fichier
4. **Format échelle invalide** : `HTTPException 400` si ratio mal formaté
5. **Erreur calcul** : `HTTPException 500` si surfaces/périmètres non numériques

## Format de réponse

La réponse suit le modèle `AnalyzeResponse` :

```python
{
    "intent": "analyse_globale",
    "target": "rayon_fraicheur",
    "surfaces": {"rayon_fraicheur": 25.5, "caisse": 10.2},
    "perimeters": {"rayon_fraicheur": 20.0, "caisse": 12.0},
    "response_text": "Surface totale : 35.7 m²\nPérimètre total : 32.0 m",
    "detections": [
        {
            "tag_name": "rayon_fraicheur",
            "probability": 0.95,
            "bounding_box": {"left": 0.1, "top": 0.2, "width": 0.3, "height": 0.4}
        }
    ],
    "annotated_image_b64": null,
    "meta": {
        "scale_ratio_m_per_px": 0.02,
        "image_size": {"width": 1920, "height": 1080},
        "return_image": true,
        "vision_file_path": "pk/conv/source.jpg",
        "vision_annotated_blob_path": "pk/conv/annotated.jpg"
    },
    "conversation_id": "conv_123",
    "vision_file_sas": "https://...",
    "vision_annotated_sas": "https://..."
}
```

## Optimisations

1. **Réutilisation fichiers** : Permet de réutiliser un fichier uploadé précédemment
2. **Traitement asynchrone** : Utilise `async/await` pour les opérations I/O
3. **Fichiers temporaires** : Nettoyage automatique après détection
4. **Stockage Blob** : Évite d'envoyer des images en base64
5. **URLs SAS** : Accès sécurisé et temporaire aux fichiers

