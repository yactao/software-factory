import { useState } from "react";
import { Mail, X, AlertCircle } from "lucide-react";
import { z } from "zod";
import { SettingsState } from "../types";

// User Invitation Schema using Zod
const inviteSchema = z.object({
    name: z.string().min(2, "Le nom doit contenir au moins 2 caractères"),
    email: z.string().email("Adresse email invalide"),
    role: z.string().min(1, "Veuillez sélectionner un rôle")
});

export function InviteUserModal({ state }: { state: SettingsState }) {
    const { isInviteModalOpen, setIsInviteModalOpen, rolesList, handleInviteUser } = state;

    const [formData, setFormData] = useState({ name: "", email: "", role: "CLIENT" });
    const [errors, setErrors] = useState<Record<string, string>>({});
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [apiError, setApiError] = useState<string | null>(null);

    if (!isInviteModalOpen) return null;

    const onSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setErrors({});
        setApiError(null);

        // Validation with Zod
        const result = inviteSchema.safeParse(formData);

        if (!result.success) {
            const newErrors: Record<string, string> = {};
            result.error.issues.forEach((err: z.ZodIssue) => {
                if (err.path[0]) newErrors[err.path[0] as string] = err.message;
            });
            setErrors(newErrors);
            return;
        }

        setIsSubmitting(true);

        handleInviteUser(
            formData,
            () => { // onSuccess
                setIsSubmitting(false);
                setIsInviteModalOpen(false);
                setFormData({ name: "", email: "", role: "CLIENT" });
            },
            (err) => { // onError
                setIsSubmitting(false);
                setApiError(err);
            }
        );
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                <button onClick={() => setIsInviteModalOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"><X className="h-5 w-5" /></button>
                <h2 className="text-xl font-bold mb-2 text-slate-900 dark:text-white flex items-center"><Mail className="w-5 h-5 mr-2 text-primary" /> Inviter un Utilisateur (Global)</h2>
                <p className="text-xs text-slate-500 mb-6">Cet utilisateur aura des accès transversaux (sans assignation de client spécifique).</p>

                {apiError && (
                    <div className="mb-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start gap-2 text-red-600 dark:text-red-400 text-sm">
                        <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                        <p>{apiError}</p>
                    </div>
                )}

                <form onSubmit={onSubmit} className="space-y-5">
                    <div>
                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Nom Complet</label>
                        <input type="text" value={formData.name} onChange={e => setFormData({ ...formData, name: e.target.value })} className={`w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border ${errors.name ? 'border-red-500' : 'border-slate-200 dark:border-white/10'} rounded-lg text-slate-900 dark:text-white focus:border-primary outline-none transition-all placeholder-slate-400`} placeholder="ex: Admin UBBEE" />
                        {errors.name && <p className="text-red-500 text-xs mt-1">{errors.name}</p>}
                    </div>

                    <div>
                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Adresse Email</label>
                        <input type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} className={`w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border ${errors.email ? 'border-red-500' : 'border-slate-200 dark:border-white/10'} rounded-lg text-slate-900 dark:text-white focus:border-primary outline-none transition-all placeholder-slate-400`} placeholder="admin@ubbee.fr" />
                        {errors.email && <p className="text-red-500 text-xs mt-1">{errors.email}</p>}
                    </div>

                    <div className="bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-200 dark:border-white/10">
                        <label className="text-sm font-bold text-slate-900 dark:text-white mb-3 block">Délégation de Droits & Rôle</label>
                        <div className="space-y-3">
                            {rolesList.map((role: { id: number, name: string, description: string }) => (
                                <label key={role.id} className="flex items-start cursor-pointer group">
                                    <input type="radio" name="role" value={role.name.toUpperCase().replace(/ /g, "_")} checked={formData.role === role.name.toUpperCase().replace(/ /g, "_")} onChange={e => setFormData({ ...formData, role: e.target.value })} className="mt-1 mr-3 text-indigo-500 focus:ring-indigo-500" />
                                    <div>
                                        <span className="text-sm font-bold text-slate-900 dark:text-white block group-hover:text-indigo-500 transition-colors">{role.name}</span>
                                        <span className="text-xs text-slate-500">{role.description}</span>
                                    </div>
                                </label>
                            ))}
                        </div>
                        {errors.role && <p className="text-red-500 text-xs mt-2">{errors.role}</p>}
                    </div>

                    <button type="submit" disabled={isSubmitting} className="w-full py-3 mt-6 bg-primary hover:bg-emerald-400 disabled:opacity-50 text-white font-bold rounded-xl transition-all shadow-lg shadow-primary/30 flex justify-center items-center">
                        {isSubmitting ? "Création en cours..." : "Envoyer l'invitation globale"}
                    </button>
                </form>
            </div>
        </div>
    );
}
