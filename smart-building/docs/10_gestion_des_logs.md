# 10. Gestion des Logs & Traçabilité (Audit)

Ce document décrit la stratégie de traçabilité implémentée sur la plateforme UBBEE. Les logs sont séparés en 3 piliers distincts afin d'assurer à la fois la sécurité, le débogage technique, et la conformité RGPD.

---

## 1. 🛡️ Logs d'Audit Métier (Base de données)
L'historique des actions humaines.

Afin de pouvoir répondre à la question *"Qui a fait ça ?"* (surtout dans le cadre de modifications critiques sur les bâtiments), nous avons créé une entité dédiée en base de données : `AuditLog`.

**Caractéristiques :**
- L'entité enregistre l'utilisateur (relation PII), l'action (ex: `UPDATE_ZONE`), la cible (ex: `Bureau Principal`) et un payload technique de détails.
- Séparé par `organizationId` pour respecter le modèle Multi-Tenant.
- **Stockage à long terme** : Ces logs s'accumulent au fil des ans et pourront être restitués aux administrateurs Finaux via le Frontend dans une future interface d'export CSV / Historique de sécurité.

## 2. 🖥️ Logs API & Serveur (Winston - Rotation)
La "boîte noire" de l'infrastructure de développement.

Plutôt que d'inonder la console PM2 avec les `console.log` basiques de NestJS, l'API globale a été branchée sur le standard industriel **Winston**.

**Emplacements et Stratégie :**
- Générés dans le dossier `/logs` du backend (`/opt/gravity-lab/smart-building/backend/logs` sur le VPS).
- **Format** : JSON (pour une ingestion facile par ELK, Datadog ou Filebeat à l'avenir).
- **Rotation Automatique (`winston-daily-rotate-file`)** : 
  - Fichier scindé par jour (ex: `api-combined-2026-03-08.log`).
  - **Auto-purge** : Les fichiers âgés de plus de 14 jours ou dépassant 20Mo sont compressés (.gz) puis supprimés dynamiquement. Cela empêche l'API de saturer le disque dur du serveur VPS (Frugalité et stabilité).

## 3. 📡 Logs IoT (Traffic Machine-to-Machine)
Pour ne pas inonder les logs serveurs traditionnels avec les centaines de trames MQTT illisibles remontées par M2M, un Logger spécifique nommé `iotLoggerInfo` a été créé.

**Emplacement :** `/logs/iot-traffic-%DATE%.log`.
**Usage :** 
Ce fichier enregistre en exclusivité les "Payloads Bruts" reçus par MQTT avant leur formatage. C'est l'outil indispensable pour les techniciens sur le terrain qui doivent valider : *"Le capteur a-t-il bien envoyé sa trame LoraWan ?"*, sans être gênés par les requêtes HTTP de l'interface admin.

---

### Mettre en Œuvre (Rappel technique pour les développeurs)
Pour utiliser le logger IoT dans un service NestJS sans dépendance globale d'injection, l'import fonctionne ainsi :
```typescript
import { iotLoggerInfo } from '../logger/logger.config';
iotLoggerInfo.info('Trame brute reçue du broker', { payload, topic });
```
