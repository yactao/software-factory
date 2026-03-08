import { z } from 'zod';

// Schema strict : rejette les clés supplémentaires pour éviter l'injection NoSQL/SQL depuis le payload
export const InviteUserSchema = z.object({
    name: z.string().min(2, "Le nom doit contenir au moins 2 caractères").max(50, "Le nom est trop long"),
    email: z.string().email("Adresse email invalide").trim(),
    role: z.enum(['SUPER_ADMIN', 'ADMIN_FONCTIONNEL', 'CLIENT']),
    password: z.string().min(6, "Mot de passe requis").optional(), // Peut être fourni par le Frontend ou auto-généré
    organizationId: z.string().uuid().optional(),
}).strict(); // <-- Empeche d'ajouter des champs comme { "isActive": true, "isAdmin": true, "<script>": "..." }
