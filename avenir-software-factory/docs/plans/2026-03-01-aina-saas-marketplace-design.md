# Aïna SaaS Marketplace : Plateforme d'Intérim IA (Agent-as-a-Service)

## 1. Vision et Proposition de Valeur
Le modèle économique de demain n'est plus la vente de licences logicielles mensuelles (SaaS classique), mais de **l'Intérim d'IA (Agent-as-a-Service)**. 
Les entreprises "embauchent" sur une Marketplace des compétences expertes sous forme d'Agents (Finance, RH, Dev, Cybersécurité, OCR) à la demande. Le client ne paie plus pour de la disponibilité logicielle, mais pour la **consommation du travail effectif** réalisé par l'expertise digitale.

---

## 2. Architecture "Serverless Frugale"

Pour maximiser la rentabilité avec un modèle asynchrone as-a-service, l'architecture s'affranchit des contraintes massives de serveurs "Always-On" via trois piliers :

- **L'Orchestrateur (Le Back-Office Central)**
  - Un serveur *Serverless* (Node.js/Bun via Vercel ou AWS Lambda) très léger. Il intercepte les requêtes (Push ou API) de l'Entreprise cliente, classe l'intention (via un LLM peu coûteux type Haiku) et dépose des messages dans un Bus Événementiel (RabbitMQ/NATS/Redis Queue). Ce composant ne coûte que s'il est utilisé.

- **Le Swarm d'Agents (Les Intérimaires)**
  - Ce sont des "Workers" indépendants qui écoutent la file d'attente et agissent selon leur expertise (ex: Kimi pour lire des rapports audités sur `docs`, DeepSeek pour de l'analyse RH structurée).
  - Ils scale-to-zero : ils dorment complètement la nuit, ce qui réduit la facture d'hébergement.

- **La Base de Données SaaS Multi-Tenants**
  - PostgreSQL avec **RLS (Row-Level Security)** : La clé absolue. L'historique d'un "tenant_id" est protégé physiquement et logiquement depuis le moteur SQL plutôt que depuis l'applicatif, éliminant tout risque de fuite de données inter-entreprises. Hébergement idéal chez Neon ou Supabase (approche Serverless native pour la BDD).

- **Stockage et Ingestion Vectorielle**
  - **S3 agnostique (Cloudflare R2 / MinIO local)** pour la conservation massive et sans frais sortants (Egress = 0).
  - **Recherche Semantic (pgvector)** : Plus besoin d'API chères comme Azure AI Search, PostgreSQL prend le relais pour toute l'analyse RAG via l'extension libre pgvector.

---

## 3. Sécurité Extrême (Forteresse Défensive)

C'est aujourd'hui la préoccupation première quant aux LLMs : le vol des données ou des exécutions malveillantes.

1. **Ingestion Cloud Connectors** : Connexion Oauth Microsoft/Google (Push/Pull) à l'espace de l'entreprise. Pas d'ouverture des bases de données internes du SI (moins d'appréhension DSI).
2. **Le Zero Trust Execute (Garantie de Quarantaine)** : Si les équipes de Dev ou Cyber Aïna doivent évaluer et compiler du code logiciel, ils opèrent dans une **MicroVM Firecracker ou Container Jetable (sandbox)** avec un time-out drastique et un espace réseau coupé. Fin de vie du code en 15 secondes.
3. **Anonymisation Optionnelle** : Avant l'appel vers un LMM public lointain (Deepseek/Kimi), un passage via le Scrubber de la Marketplace expurge les informations ultra-critiques (IBAN, numéros de sécurité sociale) ou fait basculer la requête sur un LLM *Souverain Open Weight* (Llama-3 sur machines locales).

---

## 4. Modèle Économique (Pricing et Recettes)

Deux formules pour une adoption de masse ultra-fluide :

- **La Formule Ticket (Jetons)**
  - *Le "Freelancing "* : L'entreprise charge 500$ de "Crédits Aïna". Analyse d'une PR par Neo (Cyber) = 0.5$ de crédits. L'analyse ne coûte que 0.02$ d'API à l'éditeur = **marge à plus de 95%**.
  - Favorise le mode "à la tâche" pour tester une compétence.

- **Le "CDI Digital" (Abonnement Mensuel)**
  - *Le "Full Time Equivalent" (FTE)* : Un Agent Assistant RH dédié, branché sur tous les PDFs Mutuelle/Congés de la PME, pour 199€/mois. Fournit l'interopérabilité H24 dans Slack/Teams avec un paramétrage dédié pour le "Tone of Voice" ou les règles de son patron d'entreprise.

---

## 5. Prochaines Étapes Techniques (Workflow d'Implémentation)

1. **Initialisation de l'Orchestrateur SaaS** : 
   - Modélisation du schéma PostgreSQL (RLS / Tenant / Utilisateurs)
   - Configuration du serveur Node.js / Express asynchrone et d'un routeur pour l'API.

2. **Interface Marketplace (Front-End)** : 
   - Catalogue des agents avec leurs fiches de postes (UX intuitive "Hire Me").
   - Dashboard de configuration des API Keys / Tokens Oauth client. 

3. **Modules Spécialisés d'Aïna (Skills As-A-Service)** : 
   - *Intégration DevFactory* (le mock créé précédemment branché au Broker SaaS)
   - *Intégration Finance* (Kimi/Excel Analysis)

4. **Tests Cybersécurité (Red Team vs Blue Team)** :
   - Penetration tests sur l'architecture Multi-Tenant RLS pour s'assurer que personne n'accède au PDF du magasin A depuis le rôle B.
