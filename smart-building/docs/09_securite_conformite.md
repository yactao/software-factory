# 9. Sécurité & Conformité de la Plateforme (RGPD)

La sécurité, la confidentialité des données et la conformité légale sont des piliers de l'architecture SaaS d'UBBEE. Ce document liste les mesures techniques et organisationnelles mises en place pour assurer la protection du système et des données (Security by Design).

---

## 🔒 1. Mesures de Sécurité Applicative

### Authentification & Accès (IAM)
- **Authentification forte :** Implémentation de jetons **JWT (JSON Web Tokens)** pour les sessions utilisateur, signés cryptographiquement. Aucune session de longue durée n'est stockée en clair côté client.
- **Mots de passe protégés :** Les mots de passe utilisateurs sont systématiquement hachés et salés (*salted hash* via bcrypt) avant insertion en base de données. Il est mathématiquement impossible de les retrouver en clair en cas de fuite de la base.
- **Rôle et Isolation (Multi-Tenancy) :** La plateforme intègre un strict RBAC (*Role-Based Access Control*). Un Energy Manager de l'Organisation 'A' ne peut techniquement pas requêter les données, l'annuaire ou les sites de l'Organisation 'B' via l'API, car le backend filtre systématiquement l'accès par le `Tenant ID` sécurisé du JWT injecté.

### Tolérance aux Vulnérabilités Web
- **Injections SQL (CWE-89) :** L'utilisation stricte de l'ORM (TypeORM) empêche l'injection SQL classique, l'ORM échappant lui-même les paramètres de requête.
- **Failles XSS (CWE-79) :** Le frontend développé en React échappe nativement le contenu textuel rendu dans le DOM.
- **Contrôle du trafic API :** Les requêtes entrantes sont soumises à la vérification globale des Headers d'authentification avant de rentrer dans la couche métier. 

---

## 📡 2. Sécurité Réseaux et Infrastructures

- **Chiffrement des Flux (En Transit) :** Dans l'environnement de production standardisé, toutes les connexions entre le navigateur client et les serveurs UBBEE (Frontend HTML, API REST, WebSockets temps réel) se font exclusivement via le protocole chiffré **HTTPS (TLS 1.2/1.3)**.
- **Chiffrement IoT :** Les concentrateurs et capteurs transmettent leurs trames vers la plateforme en utilisant les couches sécurisées (ex: MQTT over TLS, Webhooks M2M authentifiés).
- **Surface d'attaque minimale :** Le serveur d'hébergement s'appuie sur une politique de "Zero Trust" (voir `05_hebergement_et_reseau.md`). Seuls les ports 80/443 (HTTP/s) et 22 (SSH sur clé asymétrique uniquement) sont accessibles depuis l'extérieur. Le pare-feu système (UFW) bloque toute autre tentative.

---

## ⚖️ 3. Conformité RGPD & Données à caractère personnel

La plateforme **UBBEE** a été pensée pour minimiser l'impact sur la vie privée : sa fonction principale est de mesurer l'activité technique des bâtiments, et non de surveiller des individus.

### La minimisation des données (Data Minimization)
- Aucun traceur ni cookie de ciblage publicitaire n'est injecté. Seul un identifiant de session technique (Strictement nécessaire) est exploité.
- Les seules données à Caractère Personnel (PII) conservées en base concernent les administrateurs et collaborateurs enregistrés de la plateforme (Prénom, Nom, Courriel professionnel, Rôle, Mot de passe haché).
- **Aucune donnée personnelle de grand public ou de "visiteurs" du bâtiment n'est collectée.**

### L'anonymisation des données de comptage (IoT)
- Les caméras thermiques, les capteurs de CO2 ou les détecteurs infrarouges (PIR) remonteront via UBBEE des **états binaires ou agglomérés** (ex: *Présence active dans la salle A* ou *Pourcentage d'occupation*). 
- UBBEE refuse par définition technique la captation et l'ingestion d'images, de données biométriques ou d'enregistrements vocaux dans son modèle spatial interne. 

### Exercice des droits
- En accord avec le Chapitre 3 du RGPD européen, tout utilisateur, via son compte, peut :
  - Procéder à la modification de ses données.
  - Demander la désactivation ou la suppression définitive de son compte et des traces nominatives qui y sont associées ("Droit à l'oubli"). 

---

## 🚨 4. Maintien en Condition de Sécurité (Sécurité du Copilote IA)

L'intégration de modèles d'Intelligence Artificielle de type LLM (Large Language Models) dans la GTB fait l'objet d'un "sandboxing" (voir document `07_copilot_ia.md`) :
- **Human-in-the-Middle (HIM) :** L'IA ne possède aucun accès direct aux relais de puissance ou aux déclencheurs CVC de vos bâtiments. Chaque action demandée par le Copilote déclenche un composant visuel de confirmation (Carte d'autorisation), exigeant une action physique et intentionnelle d'un opérateur humain (Energy Manager) authentifié. 
- Les requêtes générées vers les serveurs LLM extérieurs ne transmettent jamais l'identité nominative du requérant ni d'informations confidentielles du client, mais uniquement le contexte technique immédiat de la salle (Température, Nom matériel, ID Anonymisé).

---

## 🛡️ 5. Audits et Tests d'Intrusion (Wargames)

Afin d'éprouver la résilience de notre code et de notre architecture, nous organisons périodiquement des exercices de type "Red Team vs Blue Team". Ces simulations d'attaque permettent de traquer les failles architecturales profondes (injections avancées, dénis de service, fuites mémoire) avant le déploiement public.

Pour plus de détails, vous pouvez consulter le **[Rapport du premier Audit de Sécurité Interne (Mars 2026)](./11_rapport_audit_securite.md)**, qui détaille les méthodes offensives employées et les correctifs déployés avec succès.
