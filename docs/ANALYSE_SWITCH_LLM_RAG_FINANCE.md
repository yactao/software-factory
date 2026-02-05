# Analyse : passage à GPT (OpenAI) pour RAG et Aïna Finance tout en gardant Kimi

## Réponse courte

**Oui, c’est possible** de proposer GPT (OpenAI ou Azure OpenAI) pour les APIs RAG et Aïna Finance, et de garder Kimi (et d’autres) en choisissant par configuration/env quel fournisseur et quel modèle utiliser pour chaque API.  
Cela demandera **un peu de code** : une couche d’abstraction (client + modèle choisis selon la config) et, pour le RAG « global », un cas spécifique quand le fournisseur est OpenAI.

---

## 1. Ce que font aujourd’hui RAG et Aïna Finance

### 1.1 API RAG (`/api/rag`)

Le RAG utilise **trois** appels LLM, tous via le client Kimi (SDK OpenAI avec `base_url` Moonshot) :

| Étape | Service / fonction | Rôle | Type d’appel |
|-------|--------------------|------|--------------|
| 1 | `agents_classif.decide_scope_with_kimi` | Classifier la question (single_store / global / fallback) | `kimi_chat_completion` → `client.chat.completions.create` |
| 2a | `agent_global_audit.answer_global_with_kimi` | Réponse sur le PDF global (toutes fiches) | **Upload PDF** `client.files.create` + **extraction** `client.files.content(...).text` + `client.chat.completions.create` |
| 2b | `gemini_rag._synthesize_with_citations` | Synthèse à partir des chunks (fiche unique) | `kimi_chat_completion` → `client.chat.completions.create` |

- **Config utilisée** : `KIMI_MODEL_SINGLE`, `KIMI_MODEL_GLOBAL`, `MOONSHOT_API_KEY`, client avec `base_url="https://api.moonshot.ai/v1"`.

### 1.2 API Aïna Finance (`/api/aina/finance`)

Un seul type d’appel :

| Étape | Service / fonction | Rôle | Type d’appel |
|-------|--------------------|------|--------------|
| 1 | `agent_finance.answer_finance_with_kimi` | Analyse Excel (données en JSON dans le prompt) | `get_kimi_client()` puis `client.chat.completions.create` |

- Pas d’upload de fichier vers le LLM : l’Excel est lu en local, converti en JSON, et passé dans le prompt.
- **Config** : `KIMI_MODEL_SINGLE`, `MOONSHOT_API_KEY`, même client Kimi.

---

## 2. Compatibilité avec OpenAI / GPT

### 2.1 Client Kimi = API compatible OpenAI

Dans `app/services/kimi_client.py` :

- Utilisation du SDK **`openai.OpenAI`** avec `base_url="https://api.moonshot.ai/v1"`.
- Les appels sont **uniquement** :
  - `client.chat.completions.create(model=..., messages=..., temperature=..., max_tokens=...)`
  - et dans le RAG global : `client.files.create` + `client.files.content(...).text`.

Donc tout ce qui est **chat completions** (classification, synthèse RAG fiche, Aïna Finance) est **directement compatible** avec :
- OpenAI (openai.com) : même SDK, autre `api_key` et pas de `base_url` (ou `base_url` par défaut).
- Azure OpenAI : SDK `AzureOpenAI`, même interface `chat.completions.create` et même format `messages`.

Conclusion : **pour RAG (classification + synthèse fiche) et Aïna Finance, utiliser GPT à la place de Kimi est possible sans changer la logique métier**, à condition de :
- choisir le **bon client** (Kimi vs OpenAI vs Azure OpenAI),
- et le **bon nom de modèle**,
- selon la config (env).

### 2.2 Cas particulier : RAG global (PDF)

Dans `agent_global_audit.answer_global_with_kimi` :

- **Kimi** : `client.files.create(file=..., purpose="file-extract")` puis `client.files.content(file_id).text` pour extraire le texte du PDF.
- **OpenAI / Azure OpenAI** : il n’existe pas la même API « file-extract » que Moonshot. Pour faire la même chose avec GPT il faudrait soit :
  - **Option A** : extraire le texte du PDF côté backend (PyPDF2, pdf2image + OCR, ou autre), puis envoyer ce texte dans un simple `chat.completions.create` (comme aujourd’hui avec le texte déjà extrait). Pas d’upload de fichier vers OpenAI.
  - **Option B** : utiliser l’API Assistants d’OpenAI avec upload de fichier (autre forme d’API, plus de changements).

Donc **pour le RAG global, le passage à GPT est possible**, mais il faut **adapter le code** quand le fournisseur est OpenAI (par ex. brancher une extraction PDF locale puis le même flux de chat qu’aujourd’hui).

---

## 3. Ce qu’il faut pour tout piloter par env/config

### 3.1 Sans toucher à la logique métier

L’idée est de ne pas changer les prompts ni le parsing, seulement **qui** fait l’appel et **avec quel modèle**.

- **RAG (classification + synthèse fiche)** et **Aïna Finance** : il suffit que chaque service reçoive un **client** et un **nom de modèle** (string). Ce client peut être :
  - Kimi : `OpenAI(api_key=MOONSHOT_API_KEY, base_url="https://api.moonshot.ai/v1")`
  - OpenAI : `OpenAI(api_key=OPENAI_API_KEY)` 
  - Azure OpenAI : `AzureOpenAI(azure_endpoint=..., api_key=..., api_version=...)`
- Les appels restent : `client.chat.completions.create(model=..., messages=..., ...)`. Donc **oui, on peut tout faire avec GPT et garder Kimi**, en choisissant par config le client et le modèle.

### 3.2 Variables d’environnement / config envisageables

Exemples (à adapter à ton naming) :

- **Par API / usage**  
  - `RAG_LLM_PROVIDER` = `kimi` | `openai` | `azure_openai`  
  - `RAG_MODEL_SINGLE` = modèle pour synthèse fiche (ex. `kimi-k2-turbo-preview` ou `gpt-4o`)  
  - `RAG_MODEL_GLOBAL` = modèle pour RAG global  
  - `RAG_GLOBAL_PDF_EXTRACT` = `kimi` | `local` (si `local` : extraction PDF côté backend puis GPT)  
  - `FINANCE_LLM_PROVIDER` = `kimi` | `openai` | `azure_openai`  
  - `FINANCE_MODEL` = modèle pour Aïna Finance  

- **Clés / endpoints** (déjà partiellement présents)  
  - Kimi : `MOONSHOT_API_KEY`  
  - OpenAI : `OPENAI_API_KEY`  
  - Azure OpenAI : `AZURE_OAI_ENDPOINT`, `AZURE_OAI_KEY`, `AZURE_OAI_DEPLOYMENT` (ou équivalent par usage)

Ainsi tu peux garder les anciens modèles Kimi et en configurer d’autres (GPT) par API, sans changer la logique des prompts ni du parsing.

### 3.3 Changements de code minimaux nécessaires

- **Config**  
  - Lire ces nouvelles variables dans `app/core/config.py` (ou équivalent) et exposer des constantes / helpers du type « client + modèle pour RAG single », « pour RAG global », « pour Finance ».

- **Couche d’abstraction**  
  - Une petite couche (un module ou des fonctions) qui, selon `RAG_LLM_PROVIDER` / `FINANCE_LLM_PROVIDER`, retourne le bon client et le bon nom de modèle.  
  - Les services existants (`agents_classif`, `gemini_rag`, `agent_finance`, etc.) ne prennent plus `get_kimi_client()` et `KIMI_MODEL_*` en dur, mais **client + modèle** fournis par cette couche.  
  - Aucun changement de structure de messages ni de traitement des réponses.

- **RAG global**  
  - Si `RAG_LLM_PROVIDER` = OpenAI (ou Azure) et que tu veux garder le même comportement qu’avec Kimi :  
    - Quand le provider est OpenAI, utiliser une extraction PDF **locale** (pas d’upload vers Kimi), puis le même flux que maintenant : un seul `chat.completions.create` avec le texte du document dans le prompt.  
  - Donc **un peu de code** spécifique « si provider = OpenAI alors extraire le PDF ici, sinon garder l’upload + file-extract Kimi ».

Résumé : **aucun changement dans la logique métier des APIs RAG et Aïna Finance** ; seuls la config, la construction du client et du nom de modèle, et le cas particulier du PDF global pour OpenAI, doivent être ajoutés/adaptés.

---

## 4. Synthèse

| Question | Réponse |
|----------|--------|
| Est-ce que c’est possible de passer à GPT (OpenAI) pour RAG et Aïna Finance tout en gardant le code qui marche ? | **Oui.** |
| Est-ce qu’on peut garder Kimi (et autres) et choisir par env/config quel modèle utiliser pour chaque API ? | **Oui.** En centralisant le choix du client et du modèle dans la config et une petite couche d’abstraction. |
| Est-ce faisable sans toucher du tout au code ? | **Non.** Il faut au minimum : config/env pour le provider et les modèles, et une abstraction « client + modèle » utilisée par les services. Pour le RAG global avec GPT, il faut en plus un chemin d’extraction PDF côté backend. |

En résumé : **oui, tu peux tout faire avec GPT via OpenAI en gardant Kimi et les autres, et tout configurer par env/config par API** ; il faut uniquement ajouter la config, une couche qui choisit le bon client et le bon modèle, et gérer le cas du PDF global quand le provider est OpenAI.
