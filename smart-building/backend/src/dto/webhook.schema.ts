import { z } from 'zod';

export const IotWebhookSchema = z.object({
    deviceType: z.string().min(2).max(50),
    externalId: z.string().min(2).max(100),
    payload: z.record(z.string(), z.any()), // Can be more specific depending on payload structure
}).strict(); // <-- Rejette tout champ non documenté pour la sécurité du webhook
