# Routeur Délégué (Message Broker) Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Implémenter le système de file d'attente asynchrone pour que l'Orchestrateur Node.js puisse déléguer les requêtes (ex: dev, finance) aux Workers ("Intérimaires IA") sans bloquer la requête HTTP.

**Architecture:** Pour rester frugal et cloud-native (Vercel/SaaS), l'utilisation d'une file en mémoire ou base Redis via un service managé comme Upstash ou Redis local est privilégiée. Pour ce plan initial, nous allons construire une abstraction (`broker.ts`) permettant facilement d'intervertir avec Redis/RabbitMQ plus tard, et utiliserons l'implémentation la plus simple (BullMQ sur Redis en local).

**Tech Stack:** Node.js, Express, BullMQ (le standard Redis), Redis server (facultatif localement on peut simuler ou mocker).

---

### Task 1: Installer les dépendances du Broker & Mocker les tests

**Files:**
- Create: `tests/broker.test.ts`
- Create: `src/services/broker.ts`

**Step 1: Write the failing test**

`tests/broker.test.ts`
```typescript
import { describe, it, expect, vi } from 'vitest';
import { enqueueTask } from '../src/services/broker';

describe('Message Broker', () => {
  it('should successfully add a task to the queue', async () => {
    // Mocker la fonction pour simuler le retour Redis
    const task = { type: 'dev', data: { prompt: 'Hello' } };
    const jobId = await enqueueTask('aina-tasks', task);
    
    expect(jobId).toBeDefined();
    expect(typeof jobId).toBe('string');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npx vitest run tests/broker.test.ts`
Expected: FAIL avec `enqueueTask is not defined` ou `Cannot find module '../src/services/broker'`

**Step 3: Write minimal implementation**

Afin d'avancer localement sans dockeriser Redis tout de suite, nous allons construire l'interface et une implémentation simulée en mémoire (ou mock direct) qui sera branchée à BullMQ plus tard.


`src/services/broker.ts`
```typescript
import { v4 as uuidv4 } from 'uuid';

// Simule un ajout à une Queue (Comme BullMQ mais en RAM pour l'instant local)
export const enqueueTask = async (queueName: string, payload: any): Promise<string> => {
  console.log(`[Broker] Task added to queue: ${queueName}`, payload);
  return uuidv4(); // Retourne un faux JobId
};
```

**Step 4: Run test to verify it passes**

Run: `npx vitest run tests/broker.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/broker.test.ts src/services/broker.ts
git commit -m "feat(broker): add basic task queue interface with in-memory simulation"
```

---

### Task 2: Créer la Route Générique d'Ingestion des Tâches (Délégation)

**Files:**
- Create: `tests/taskRouter.test.ts`
- Create: `src/routes/tasks.ts`
- Modify: `src/app.ts:8-12`

**Step 1: Write the failing test**

`tests/taskRouter.test.ts`
```typescript
import { describe, it, expect } from 'vitest';
import request from 'supertest';
import app from '../src/app';

describe('POST /api/tasks', () => {
  it('should accept a task and return a job id (202 Accepted)', async () => {
    const res = await request(app)
      .post('/api/tasks')
      .send({ agent: 'dev', context: 'Create a script' });
      
    expect(res.status).toBe(202); // 202 = Accepted for processing
    expect(res.body).toHaveProperty('jobId');
    expect(res.body).toHaveProperty('status', 'queued');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npx vitest run tests/taskRouter.test.ts`
Expected: FAIL (404 Not Found car la route n'existe pas)

**Step 3: Write minimal implementation**

`src/routes/tasks.ts`
```typescript
import { Router } from 'express';
import { enqueueTask } from '../services/broker';

const router = Router();

router.post('/', async (req, res) => {
  const { agent, context } = req.body;
  
  try {
    const jobId = await enqueueTask(`aina-agent-${agent}`, { context });
    res.status(202).json({ status: 'queued', jobId });
  } catch (err) {
    res.status(500).json({ error: 'Failed to queue task' });
  }
});

export default router;
```

Update `src/app.ts` pour inclure le routeur:
```typescript
import express from 'express';
import cors from 'cors';
import healthRouter from './routes/health';
import taskRouter from './routes/tasks';

const app = express();
app.use(cors());
app.use(express.json());

app.use('/health', healthRouter);
app.use('/api/tasks', taskRouter);

export default app;
```

**Step 4: Run test to verify it passes**

Run: `npx vitest run tests/taskRouter.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/taskRouter.test.ts src/routes/tasks.ts src/app.ts
git commit -m "feat(api): create generic asynchronous task delegation endpoint /api/tasks"
```
