# Aïna SaaS Marketplace Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use executing-plans to implement this plan task-by-task.

**Goal:** Initialize the base Serverless backend for the Aïna SaaS Marketplace with the Express orchestrator and PostgreSQL (Neon/Supabase) schema migrations using Prisma.

**Architecture:** Node.js/Express lightweight orchestrator. Prisma ORM to connect to the PostgreSQL multi-tenant database. Row-Level Security (RLS) is configured purely at the DB level, but Prisma handles migration schemas for User, Tenant, and ChatEvent.

**Tech Stack:** Node.js, Express, Prisma ORM, PostgreSQL.

---

### Task 1: Initialize Node.js Backend & Install Dependencies

**Files:**
- Create: `package.json`
- Create: `.env.example`

**Step 1: Initialize project & install basic dependencies**

Run: `npm init -y` inside `c:\Users\taouf\Documents\antigravity lab\avenir-software-factory\aina-saas-orchestrator` (directory needs to be created first).
Actually, let's just initialize the base in `aina-saas-orchestrator` folder.

```bash
mkdir aina-saas-orchestrator
cd aina-saas-orchestrator
npm init -y
npm install express cors dotenv uuid
npm install -D typescript @types/node @types/express @types/cors ts-node nodemon vitest
npx tsc --init
```

**Step 2: Setup basic TypeScript configuration**

In `tsconfig.json`, set:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "CommonJS",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true
  }
}
```

**Step 3: Commit**

```bash
cd aina-saas-orchestrator
git init
git add package.json tsconfig.json package-lock.json
git commit -m "chore: initialize aina saas backend project with typescript"
```

---

### Task 2: Setup Express Orchestrator Entrypoint

**Files:**
- Create: `src/server.ts`
- Create: `src/routes/health.ts`
- Create: `tests/health.test.ts`

**Step 1: Write the failing test for health endpoint**

`tests/health.test.ts`
```typescript
import { describe, it, expect } from 'vitest';
import request from 'supertest';
import app from '../src/app'; // We will separate app from server

describe('GET /health', () => {
  it('should return 200 OK and status', async () => {
    const res = await request(app).get('/health');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('status', 'ok');
  });
});
```

**Step 2: Run test to verify it fails**

Run: `npx vitest run tests/health.test.ts`
Expected: FAIL (app is not defined)

**Step 3: Write minimal implementation**

`src/app.ts`
```typescript
import express from 'express';
import cors from 'cors';
import healthRouter from './routes/health';

const app = express();
app.use(cors());
app.use(express.json());

app.use('/health', healthRouter);

export default app;
```

`src/routes/health.ts`
```typescript
import { Router } from 'express';

const router = Router();

router.get('/', (req, res) => {
  res.json({ status: 'ok', time: Date.now() / 1000 });
});

export default router;
```

`src/server.ts`
```typescript
import app from './app';
import dotenv from 'dotenv';

dotenv.config();

const PORT = process.env.PORT || 4000;

app.listen(PORT, () => {
  console.log(`[Aïna SaaS Orchestrator] 🚀 Server running on port ${PORT}`);
});
```

**Step 4: Run test to verify it passes**

Run: `npm install -D supertest @types/supertest`
Run: `npx vitest run tests/health.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/ tests/
git commit -m "feat(api): add express orchestrator with /health endpoint"
```

---

### Task 3: Initialize Prisma and Database Schema

**Files:**
- Create: `prisma/schema.prisma`
- Create: `.env`

**Step 1: Initialize Prisma**

Run: `npx prisma init`
Expected: Creates `prisma/schema.prisma` and `.env`

**Step 2: Define the Multi-Tenant Schema**

Modify `prisma/schema.prisma`:
```prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model Tenant {
  id        String   @id @default(uuid())
  name      String
  createdAt DateTime @default(now())
  users     User[]
  chats     ChatEvent[]
}

model User {
  id        String   @id @default(uuid())
  email     String   @unique
  role      String   @default("user")
  tenantId  String
  tenant    Tenant   @relation(fields: [tenantId], references: [id])
  chats     ChatEvent[]
}

model ChatEvent {
  id             String   @id @default(uuid())
  conversationId String
  tenantId       String
  userId         String
  role           String   // 'user', 'assistant', 'system'
  route          String   // 'dev', 'finance', 'rag'
  message        String
  meta           Json?
  createdAt      DateTime @default(now())

  tenant         Tenant   @relation(fields: [tenantId], references: [id])
  user           User     @relation(fields: [userId], references: [id])
}
```

**Step 3: Dry-run validate the schema**

Run: `npx prisma validate`
Expected: `Environment variables loaded from .env... Prisma schema loaded... Prisma schema is valid.`

*(Note: We don't apply migration yet until the client provides their Neon/Supabase DB string in the real `.env`, but the schema is locked in source control).*

**Step 4: Commit**

```bash
git add prisma/schema.prisma .gitignore
git commit -m "feat(db): initialize prisma with multi-tenant schema (RLS ready)"
```
