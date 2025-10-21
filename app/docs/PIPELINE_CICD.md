# PIPELINE_CICD

> Déploiement **GitHub Actions → Azure App Service** en **OIDC** (sans secrets). Ce guide couvre : prérequis Azure, App Registration, RBAC, fédération OIDC et workflow GitHub.

---

## 0) Prérequis

- **Repo GitHub** : `ITSynchronic/aina-backend`
- **Azure App Service** existant (ex: `rg: rg-aina` / `app: app-aina-backend`)
- **Droits Azure** pour créer une App Registration et ajouter RBAC sur la **Web App** (scope le plus restrictif)

---

## 1) App Registration (Microsoft Entra ID)

1. **Azure Portal** → *Microsoft Entra ID* → *App registrations* → *New registration*  
   - Name: `gha-aina-backend-deploy`
   - Single tenant (recommandé)
   - Redirect URI: vide (pas utile ici)
2. Note **Application (client) ID** et **Directory (tenant) ID**

### Federated Credentials

Dans la même App Reg → *Certificates & secrets* → *Federated credentials* → **Add credential** :
- **Issuer**: GitHub Actions
- **Organization**: `ITSynchronic`
- **Repository**: `aina-backend`
- **Entity type**: `Repository`
- **Subject** (branche `main`):  
  `repo:ITSynchronic/aina-backend:ref:refs/heads/main`
- **Name**: `github-actions-main`

> Ajoute un 2e credential pour `dev`/`prod` si tu utilises des **Environments** GitHub (subject de type `environment:prod`).

---

## 2) RBAC (assignation de rôle)

Sur la **Web App** (scope le plus restrictif) :
- *Access control (IAM)* → *Add* → *Add role assignment*  
  - **Role**: `Contributor` (ou `Website Contributor`)  
  - **Assign access to**: User, group, or service principal  
  - **Member**: l’**App Registration** créée (`gha-aina-backend-deploy`)

> Si le bouton est grisé, demande à un **Owner** du RG/WebApp d’effectuer l’assignation.

---

## 3) Variables d’environnement Azure

Dans l’**App Service** → *Configuration* → *Application settings* :  
Ajoute toutes les variables requises (Search, AOAI, Storage, Auth…).  
Ne mets **aucun secret** dans GitHub (OIDC évite les clés).

---

## 4) Workflow GitHub Actions (OIDC)

Crée `.github/workflows/deploy.yml` dans le repo :

```yaml
name: Deploy AINA Backend (OIDC)

on:
  push:
    branches: [ "main" ]
  workflow_dispatch:

permissions:
  id-token: write   # OIDC
  contents: read

env:
  AZURE_WEBAPP_NAME: "app-rag-its-new2"      # <- Nom de ta Web App
  AZURE_RESOURCE_GROUP: "rg-rag-itsynchronic"            # (optionnel)
  PYTHON_VERSION: "3.11"

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ env.PYTHON_VERSION }}

      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          # Optionnel : tests unitaires
          # pytest -q

      # Connexion Azure via OIDC
      - name: Azure Login (OIDC)
        uses: azure/login@v2
        with:
          client-id: ${{ secrets.AZURE_CLIENT_ID }}   # App Registration client id
          tenant-id: ${{ secrets.AZURE_TENANT_ID }}   # Directory (tenant) id
          subscription-id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}

      # Déploiement vers App Service
      - name: 'Deploy to Azure WebApp'
        uses: azure/webapps-deploy@v3
        with:
          app-name: ${{ env.AZURE_WEBAPP_NAME }}
          package: .
          # par défaut, détecte Python et fait le bon runtime

      - name: Post-Deployment ping
        run: |
          echo "Deployment completed"
```

### Secrets GitHub à créer (Settings → Secrets and variables → Actions → New Repository Secret)
- `AZURE_CLIENT_ID` : **Application (client) ID** de l’App Registration
- `AZURE_TENANT_ID` : **Directory (tenant) ID**
- `AZURE_SUBSCRIPTION_ID` : ton **Subscription ID** Azure

> Aucune clé/publish profile nécessaire (OIDC).

---

## 5) Patterns multi-env (optionnel)

- Plusieurs **federated credentials** (ex: `github-actions-dev`, `github-actions-prod`)  
- Plusieurs **workflows** ou **jobs** conditionnels par branche/tag
- **Environments** GitHub (`dev`, `prod`) + **Approvals**

---

## 6) Rollback

- Utiliser **Run History** de GitHub Actions pour ré-exécuter un build précédent.
- Azure App Service garde des **deployments** (si activé via *Deployment Center*).

---

## 7) Diagnostics

- Logs GitHub Actions (étape par étape).
- **App Service → Log stream** pour vérifier `uvicorn`.
- Vérifier CORS et variables d’environnement (Configuration).

---

## 8) Checklist CI/CD

- [ ] App Registration créée + Federated credentials (repo main)
- [ ] RBAC **Contributor** (ou **Website Contributor**) sur **Web App**
- [ ] Secrets GitHub : `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`
- [ ] Variables App Service ajoutées (Search/AOAI/Storage/Auth)
- [ ] Workflow `deploy.yml` dans `main`

**Fin.**
