import { z } from 'zod';

export const CustomRoleSchema = z.object({
    name: z.string().min(2, "Le nom doit contenir au moins 2 caractères").max(50),
    description: z.string().max(255).optional(),
    permissions: z.array(z.string()).default([]),
    organizationId: z.string().uuid().optional(),
}).strict(); // Rejet des champs supplémentaires
