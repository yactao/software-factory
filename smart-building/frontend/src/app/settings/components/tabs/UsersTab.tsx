import { Mail, Shield, Plus, Trash2, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { SettingsState } from "../types";

export function UsersTab({ state }: { state: SettingsState }) {
    const {
        usersList, rolesList, setRolesList,
        setIsInviteModalOpen, setIsProfileModalOpen, handleDeleteUser
    } = state;

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center border-b border-slate-200 dark:border-white/10 pb-4">
                <div>
                    <h2 className="text-xl font-bold text-slate-900 dark:text-white">Gestion des Accès (Globaux)</h2>
                    <p className="text-sm text-slate-500">Collaborateurs ayant accès au tableau de bord.</p>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                    <button onClick={() => setIsInviteModalOpen(true)} className="flex items-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary dark:bg-emerald-500/10 dark:text-emerald-400 dark:hover:bg-emerald-500/20 px-4 py-2 rounded-xl font-bold text-sm transition-colors border border-primary/20">
                        <Mail className="w-4 h-4" /> Inviter un Utilisateur
                    </button>
                </div>
            </div>

            <div className="border border-slate-200 dark:border-white/5 rounded-xl overflow-hidden bg-slate-50/50 dark:bg-black/20">
                <table className="w-full text-sm text-left text-slate-500 dark:text-slate-400">
                    <thead className="text-xs text-slate-700 uppercase bg-slate-100 dark:bg-black/40 dark:text-slate-300">
                        <tr>
                            <th className="px-4 py-3 font-bold">Utilisateur</th>
                            <th className="px-4 py-3 font-bold">Rôle</th>
                            <th className="px-4 py-3 font-bold">Statut</th>
                            <th className="px-4 py-3 text-right font-bold">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {usersList.map((usr: { id: string, name: string, email: string, role: string, isDefault?: boolean, status?: string, lastActive?: string }) => (
                            <tr key={usr.id} className="border-b border-slate-200 dark:border-white/5 hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                                <td className="px-4 py-3">
                                    <div className="font-bold text-slate-900 dark:text-white">{usr.name}</div>
                                    <div className="text-xs opacity-70"><a href={`mailto:${usr.email}`} className="hover:text-primary">{usr.email}</a></div>
                                </td>
                                <td className="px-4 py-3">
                                    <span className={cn(
                                        "px-2 py-1 font-bold rounded text-[10px] uppercase tracking-wider",
                                        usr.role === "SUPER_ADMIN" ? "bg-purple-500/10 text-purple-600" :
                                            usr.role === "ADMIN_FONCTIONNEL" ? "bg-orange-500/10 text-orange-600" :
                                                "bg-emerald-500/10 text-emerald-600"
                                    )}>
                                        {usr.role}
                                    </span>
                                </td>
                                <td className="px-4 py-3"><span className="flex items-center gap-1.5 text-emerald-500 font-medium text-xs"><CheckCircle2 className="w-3.5 h-3.5" /> Actif</span></td>
                                <td className="px-4 py-3 text-right">
                                    <button onClick={() => handleDeleteUser(usr.id, usr.name)} className="text-slate-400 hover:text-red-500 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"><Trash2 className="w-4 h-4 ml-auto" /></button>
                                </td>
                            </tr>
                        ))}
                        {usersList.length === 0 && (
                            <tr>
                                <td colSpan={4} className="px-4 py-8 text-center text-slate-500 italic">Aucun utilisateur trouvé.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {/* ROLES TABLE */}
            <div className="pt-8 border-t border-slate-200 dark:border-white/10 mt-8">
                <div className="flex justify-between items-center mb-4">
                    <div>
                        <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center">
                            Profils d'Administration (Rôles)
                        </h3>
                        <p className="text-xs text-slate-500">Liste des rôles sur-mesure pour vos équipes globales.</p>
                    </div>
                    <button onClick={() => setIsProfileModalOpen(true)} className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 dark:bg-white/5 dark:text-slate-300 dark:hover:bg-white/10 px-3 py-1.5 rounded-lg font-bold text-xs transition-colors border border-slate-200 dark:border-white/5">
                        <Plus className="w-4 h-4" /> Créer un Profil
                    </button>
                </div>
                <div className="space-y-3">
                    {rolesList.map((role: { id: number, name: string, description: string }) => (
                        <div key={role.id} className="flex justify-between items-center p-4 bg-slate-50 dark:bg-white/5 border border-slate-200 dark:border-white/10 shadow-sm rounded-xl hover:border-indigo-500/30 transition-colors">
                            <div className="flex items-center gap-3">
                                <div className="bg-indigo-500/10 p-2 rounded-lg">
                                    <Shield className="w-5 h-5 text-indigo-500" />
                                </div>
                                <div>
                                    <div className="font-bold text-slate-900 dark:text-white text-sm">{role.name}</div>
                                    <div className="text-xs text-slate-500 mt-0.5">{role.description}</div>
                                </div>
                            </div>
                            <div className="text-right">
                                <button onClick={() => setRolesList(rolesList.filter((r: { id: number }) => r.id !== role.id))} className="text-slate-400 hover:text-red-500 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors">
                                    <Trash2 className="w-4 h-4 ml-auto" />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
