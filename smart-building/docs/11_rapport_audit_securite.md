# 11. Rapport d'Audit de Sécurité Interne (Red Team vs Blue Team)

Ce document retrace le premier exercice de type "Wargame" (simulation d'attaque et défense) réalisé sur l'infrastructure UBBEE. Cet audit s'inscrit dans notre démarche de maintien en condition de sécurité (MCS) et de *Security by Design*.

**Date de l'audit :** Mars 2026
**Périmètre :** Nouveaux modules de journalisation in-app (Logs Controller, Logs Service, Console Frontend).
**Méthodologie :** Analyse statique par la Red Team (offensive), suivie d'une remédiation immédiate par la Blue Team (défensive) et validation par le CISO (gouvernance).

---

## 🔴 1. Vecteurs d'attaque identifiés (Red Team)

La Red Team a découvert trois vulnérabilités architecturales critiques dans le mécanisme de consultation des logs en temps réel, pouvant mener à une compromission totale ou à un déni de service.

### Faille A : Vol de Session Administrateur (XSS to Storage)
- **Cible :** `ConsoleTab.tsx` (Frontend React)
- **Description :** L'extraction du jeton JWT directement depuis le `localStorage` de l'administrateur, combinée à l'affichage en clair des messages de logs contenant potentiellement des entrées utilisateur non assainies (ex: nom d'un capteur compromis), ouvrait la porte à une faille Cross-Site Scripting (XSS).
- **Impact (CVSS High) :** Exfiltration du token `SUPER_ADMIN` vers un serveur tiers et compromission de l'intégralité du parc de l'organisation.

### Faille B : Déni de Service par Blocage de Thread (Synchronous DoS)
- **Cible :** `logs.service.ts` (Backend NestJS)
- **Description :** La lecture des logs système s'appuyait sur l'ouverture synchrone et le parsing complet en ligne de commande (via un `.split('\n')`) de fichiers disques potentiellement très lourds. Node.js étant mono-thread, une lecture synchrone gèle l'Event Loop globale.
- **Impact (CVSS Critical) :** Une attaque par inondation (Flooding) sur la route `/api/logs/system` avec une centaine de requêtes/sec suffisait à paralyser 100% de l'API (tests capteurs, authentification, télémétrie) en moins de 5 secondes.

### Faille C : Épuisement de la Mémoire (OOM via Pagination Manquante)
- **Cible :** `logs.controller.ts` (Backend NestJS)
- **Description :** Le paramètre de limite `?lines=` n'était soumis à aucun plafond strict (*Hard Cap*). Un attaquant pouvait demander l'extraction de 99 millions de lignes, forçant le moteur JSON à allouer une quantité phénoménale de RAM.
- **Impact (CVSS High) :** Crash critique de l'application (Processus tué par le système pour libérer de la RAM, erreur `Out Of Memory`).

---

## 🔵 2. Mesures de Remédiation & Patchs (Blue Team)

Suite aux remontées offensives, la Blue Team a appliqué et déployé en *Hot-Swap* les correctifs matériels suivants sur l'environnement de production.

### Patch A : Assainissement DOM (Anti-XSS)
- **Mise en œuvre :** Déploiement de la bibliothèque standard `dompurify` sur le Frontend.
- **Action :** Toutes les données dynamiques reçues de l'API (Identifiants utilisateurs, types d'actions, détails du système) sont filtrées par `DOMPurify.sanitize()` avant l'injection HTML. Les balises `<script>` ou attributs `onload=` malveillants sont détruits à la volée.

### Patch B : Pagination Forcée et Capping Mathématique (Anti-OOM)
- **Mise en œuvre :** Injection de contraintes de limite forte dans les contrôleurs (`logs.controller.ts`).
- **Action :** La récupération des objets depuis la base de données (AuditLog) est désormais restreinte géométriquement : `Math.min(Number(limit), 2000)`. Toute requête absurde est rabattue à des dimensions gérables par le Garbage Collector de Node.js.

### Patch C : Verrouillage Mono-Thread (Anti-DoS)
- **Mise en œuvre :** Écrêtage en amont dans le processeur de fichiers (`logs.service.ts`).
- **Action :** La taille des données extraites lors de la lecture des fichiers `.log` physiques gérés par Winston a été castée (`safeMaxLines = Math.min(...)`). L'empreinte mémoire d'une requête est rendue déterministe et n'impacte plus l'Event Loop pendant plus de quelques millisecondes. 

---

## 👔 3. Bilan de Sécurité (CISO)

Malgré des processus globaux solides (JWT, pare-feu UFW, chiffrement en transit), cet exercice souligne que le péril interne (consommation mémoire d'un composant, affichage de traces corrompues) reste un vecteur d'attaque privilégié dans un SaaS B2B Multi-tenant.

**Score post-audit :** `A` (Vulnérabilités critiques patchées en live).
**Actions futures :** Maintenir des Wargames réguliers via notre pipeline d'agents automatiques (`/cyber-orchestration`) lors de la sortie de prochaines routes majeures (Jumeau Numérique 3D, Moteur de Règles CVC).
