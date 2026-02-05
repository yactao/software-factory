# Configuration LLM pour RAG et Aïna Finance

Vous pouvez choisir le fournisseur LLM (Kimi, OpenAI, Azure OpenAI) par API via les variables d'environnement.

## Variables d'environnement

### Choix du fournisseur

| Variable | Valeurs | Défaut | Description |
|----------|---------|--------|-------------|
| `RAG_LLM_PROVIDER` | `kimi` \| `openai` \| `azure_openai` | `kimi` | Fournisseur pour toutes les étapes RAG (classification, synthèse fiche, RAG global). |
| `FINANCE_LLM_PROVIDER` | `kimi` \| `openai` \| `azure_openai` | `kimi` | Fournisseur pour l'API Aïna Finance. |

### Modèles (utilisés si provider = openai ou azure_openai)

| Variable | Défaut | Description |
|----------|--------|-------------|
| `RAG_MODEL_SINGLE` | `KIMI_MODEL_SINGLE` | Modèle pour la synthèse RAG (fiche unique). |
| `RAG_MODEL_GLOBAL` | `KIMI_MODEL_GLOBAL` | Modèle pour le RAG global (PDF complet). |
| `RAG_MODEL_CLASSIF` | `RAG_MODEL_SINGLE` | Modèle pour la classification de portée (single_store / global). |
| `FINANCE_MODEL` | `KIMI_MODEL_SINGLE` | Modèle pour Aïna Finance. |

### OpenAI (platform)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Clé API OpenAI (requise si `RAG_LLM_PROVIDER` ou `FINANCE_LLM_PROVIDER` = `openai`). |

### Azure OpenAI

| Variable | Description |
|----------|-------------|
| `AZURE_OAI_ENDPOINT` | Endpoint Azure OpenAI. |
| `AZURE_OAI_KEY` | Clé API Azure OpenAI. |
| `AZURE_OAI_DEPLOYMENT` | Nom du déploiement (fallback pour tous les usages). |
| `RAG_AZURE_DEPLOYMENT` | Déploiement pour RAG (single + classif). |
| `RAG_GLOBAL_AZURE_DEPLOYMENT` | Déploiement pour RAG global. |
| `FINANCE_AZURE_DEPLOYMENT` | Déploiement pour Aïna Finance. |

### Kimi (inchangé)

| Variable | Description |
|----------|-------------|
| `MOONSHOT_API_KEY` | Clé API Moonshot (Kimi). |
| `KIMI_MODEL_SINGLE` | Modèle Kimi pour RAG single / classif. |
| `KIMI_MODEL_GLOBAL` | Modèle Kimi pour RAG global. |

## Comportement RAG global selon le fournisseur

- **Kimi** : le PDF est envoyé à l’API (upload + extraction de texte côté Kimi), puis le texte est utilisé dans le prompt.
- **OpenAI** : le PDF est envoyé à l’API (upload avec `purpose=user_data`), puis le `file_id` est passé dans le message user. Si l’upload échoue, extraction locale du texte (pypdf) et envoi du texte dans le prompt.
- **Azure OpenAI** : pas d’upload de PDF côté API ; extraction locale du texte (pypdf) puis envoi du texte dans le prompt.

## Exemple : tout en OpenAI

```env
RAG_LLM_PROVIDER=openai
FINANCE_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
RAG_MODEL_SINGLE=gpt-4o
RAG_MODEL_GLOBAL=gpt-4o
RAG_MODEL_CLASSIF=gpt-4o
FINANCE_MODEL=gpt-4o
```

## Exemple : RAG en Azure, Finance en Kimi

```env
RAG_LLM_PROVIDER=azure_openai
FINANCE_LLM_PROVIDER=kimi
AZURE_OAI_ENDPOINT=https://....openai.azure.com/
AZURE_OAI_KEY=...
RAG_AZURE_DEPLOYMENT=deploy-rag
RAG_GLOBAL_AZURE_DEPLOYMENT=deploy-rag-global
MOONSHOT_API_KEY=...
```

## Dépendance

Pour le fallback d’extraction de texte PDF (Azure ou en cas d’échec d’upload OpenAI), le projet utilise **pypdf** (`pip install pypdf`).
