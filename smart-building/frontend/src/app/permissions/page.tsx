"use client";

import { useEffect, useState } from "react";
import { useTenant } from "@/lib/TenantContext";
import { Users, Mail, X, CheckCircle2, Trash2, Cpu, Eye, Lock } from "lucide-react";
import { cn } from "@/lib/utils";

export default function PermissionsPage() {
    const { currentTenant, authFetch } = useTenant();
    const [users, setUsers] = useState<any[]>([]);

    // Modals
    const [isInviteModalOpen, setIsInviteModalOpen] = useState(false);

    // Form states
    const [newUser, setNewUser] = useState({ name: "", email: "", role: "CLIENT" });
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (currentTenant) {
            fetchData();
        }
    }, [currentTenant]);

    const fetchData = async () => {
        try {
            const res = await authFetch(`/api/users?organizationId=${currentTenant?.id}`);
            setUsers(await res.json());
        } catch (e) {
            console.error(e);
        }
    };

    const handleSaveUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await authFetch("/api/users", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: newUser.name,
                    email: newUser.email,
                    role: newUser.role,
                    organizationId: currentTenant?.id
                })
            });
            setIsInviteModalOpen(false);
            setNewUser({ name: "", email: "", role: "CLIENT" });
            fetchData();
        } catch (e) {
            console.error(e);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteUser = async (id: string, name: string) => {
        if (confirm(`Voulez-vous vraiment retirer l'accès à ${name} ?`)) {
            try {
                await authFetch(`/api/users/${id}`, { method: "DELETE" });
                fetchData();
            } catch (e) {
                console.error(e);
            }
        }
    };

    const filteredUsers = users.filter((u: any) => u.organization && u.organization.id === currentTenant?.id);

    return (
        <div className="p-8 max-w-7xl mx-auto space-y-8 min-h-screen bg-slate-50 dark:bg-[#0B1120]">
            <header className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-black text-slate-900 dark:text-white mb-2">Utilisateurs & Rôles</h1>
                    <p className="text-slate-500">Gérez les accès de vos collaborateurs à l'espace {currentTenant?.name}.</p>
                </div>
                <button onClick={() => setIsInviteModalOpen(true)} className="flex items-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary dark:bg-emerald-500/10 dark:text-emerald-400 dark:hover:bg-emerald-500/20 px-4 py-2 rounded-xl font-bold text-sm transition-colors border border-primary/20">
                    <Mail className="w-4 h-4" /> Inviter
                </button>
            </header>

            <div className="bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-3xl overflow-hidden shadow-xl shadow-slate-200/50 dark:shadow-none">
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 text-xs uppercase tracking-wider font-bold">
                            <tr>
                                <th className="px-6 py-4">Collaborateur</th>
                                <th className="px-6 py-4">Rôle</th>
                                <th className="px-6 py-4">Statut</th>
                                <th className="px-6 py-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-200 dark:divide-white/5">
                            {filteredUsers.map((usr: any) => (
                                <tr key={usr.id} className="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="font-bold text-slate-900 dark:text-white">{usr.name}</div>
                                        <div className="text-xs text-slate-500 opacity-70"><a href={`mailto:${usr.email}`} className="hover:text-primary">{usr.email}</a></div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className={cn(
                                            "px-2.5 py-1 font-bold rounded text-[10px] uppercase tracking-wider border",
                                            usr.role === "ENERGY_MANAGER" ? "bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-500/20" :
                                                usr.role === "TECHNICIAN" ? "bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-500/20" :
                                                    "bg-slate-50 dark:bg-white/5 text-slate-500 border-slate-200 dark:border-white/10"
                                        )}>
                                            {usr.role === "ENERGY_MANAGER" ? "Energy Manager" : usr.role === "TECHNICIAN" ? "Technicien" : "Lecteur Invité"}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4">
                                        <span className="flex items-center gap-1.5 text-emerald-500 font-bold text-xs"><CheckCircle2 className="w-3.5 h-3.5" /> Actif</span>
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button onClick={() => handleDeleteUser(usr.id, usr.name)} className="text-slate-400 hover:text-red-500 p-1.5 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors inline-block"><Trash2 className="w-4 h-4 mx-auto" /></button>
                                    </td>
                                </tr>
                            ))}
                            {filteredUsers.length === 0 && (
                                <tr>
                                    <td colSpan={4} className="px-6 py-12 text-center text-slate-500 font-medium">
                                        Aucun collaborateur trouvé pour ce domaine.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Invite Modal */}
            {isInviteModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
                    <div className="w-full max-w-2xl bg-white dark:bg-[#0B1120] rounded-3xl border border-slate-200 dark:border-white/10 p-8 shadow-2xl relative my-auto">
                        <button onClick={() => setIsInviteModalOpen(false)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors">
                            <X className="h-5 w-5" />
                        </button>

                        <div className="mb-8">
                            <h2 className="text-2xl font-black text-slate-900 dark:text-white flex items-center mb-2">
                                <Users className="w-6 h-6 mr-3 text-primary" />
                                Inviter un collaborateur
                            </h2>
                            <p className="text-sm text-slate-500 font-medium ml-9">
                                Ajoutez un membre à l'espace {currentTenant?.name} et définissez ses droits d'accès.
                            </p>
                        </div>

                        <form onSubmit={handleSaveUser} className="space-y-8">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2">Nom complet</label>
                                    <input required type="text" value={newUser.name} onChange={e => setNewUser({ ...newUser, name: e.target.value })} placeholder="ex: Jean Dupont" className="w-full bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 outline-none focus:border-primary text-slate-900 dark:text-white transition-all font-medium" />
                                </div>
                                <div>
                                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2">Email</label>
                                    <input required type="email" value={newUser.email} onChange={e => setNewUser({ ...newUser, email: e.target.value })} placeholder="jean@entreprise.com" className="w-full bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 outline-none focus:border-primary text-slate-900 dark:text-white transition-all font-medium" />
                                </div>
                            </div>

                            <div>
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4 border-b border-slate-100 dark:border-white/5 pb-2">
                                    Niveau d'Autorisation
                                </h3>

                                <div className="space-y-3">
                                    <label className={cn("flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all", newUser.role === "ENERGY_MANAGER" ? "border-orange-500 bg-orange-500/5" : "border-slate-100 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20")}>
                                        <input type="radio" name="role" value="ENERGY_MANAGER" checked={newUser.role === "ENERGY_MANAGER"} onChange={() => setNewUser({ ...newUser, role: "ENERGY_MANAGER" })} className="mt-1 mr-4 hidden" />
                                        <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 mr-4 shrink-0 transition-colors", newUser.role === "ENERGY_MANAGER" ? "border-orange-500" : "border-slate-300 dark:border-slate-600")}>
                                            {newUser.role === "ENERGY_MANAGER" && <div className="w-2.5 h-2.5 bg-orange-500 rounded-full" />}
                                        </div>
                                        <div>
                                            <span className={cn("text-base font-black flex items-center gap-2", newUser.role === "ENERGY_MANAGER" ? "text-orange-600" : "text-slate-700 dark:text-slate-300")}>
                                                <Lock className="w-4 h-4" /> Energy Manager
                                            </span>
                                            <span className="text-sm text-slate-500 mt-1 block">Accès total à la supervision, modification des consignes CVC, gestion des règles métiers et exports énergétiques avancés. Droit d'inviter d'autres techniciens.</span>
                                        </div>
                                    </label>

                                    <label className={cn("flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all", newUser.role === "TECHNICIAN" ? "border-blue-500 bg-blue-500/5" : "border-slate-100 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20")}>
                                        <input type="radio" name="role" value="TECHNICIAN" checked={newUser.role === "TECHNICIAN"} onChange={() => setNewUser({ ...newUser, role: "TECHNICIAN" })} className="mt-1 mr-4 hidden" />
                                        <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 mr-4 shrink-0 transition-colors", newUser.role === "TECHNICIAN" ? "border-blue-500" : "border-slate-300 dark:border-slate-600")}>
                                            {newUser.role === "TECHNICIAN" && <div className="w-2.5 h-2.5 bg-blue-500 rounded-full" />}
                                        </div>
                                        <div>
                                            <span className={cn("text-base font-black flex items-center gap-2", newUser.role === "TECHNICIAN" ? "text-blue-600" : "text-slate-700 dark:text-slate-300")}>
                                                <Cpu className="w-4 h-4" /> Technicien (Mainteneur)
                                            </span>
                                            <span className="text-sm text-slate-500 mt-1 block">Pilote le CVC et les équipements en temps réel, acquitte les alertes réseau/matériel. Ne peut pas modifier les scénarios AI ni inviter d'autres membres.</span>
                                        </div>
                                    </label>

                                    <label className={cn("flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all", newUser.role === "CLIENT" ? "border-slate-400 bg-slate-50 dark:bg-white/5" : "border-slate-100 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20")}>
                                        <input type="radio" name="role" value="CLIENT" checked={newUser.role === "CLIENT"} onChange={() => setNewUser({ ...newUser, role: "CLIENT" })} className="mt-1 mr-4 hidden" />
                                        <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 mr-4 shrink-0 transition-colors", newUser.role === "CLIENT" ? "border-slate-500" : "border-slate-300 dark:border-slate-600")}>
                                            {newUser.role === "CLIENT" && <div className="w-2.5 h-2.5 bg-slate-500 rounded-full" />}
                                        </div>
                                        <div>
                                            <span className={cn("text-base font-black flex items-center gap-2", newUser.role === "CLIENT" ? "text-slate-800 dark:text-white" : "text-slate-700 dark:text-slate-300")}>
                                                <Eye className="w-4 h-4" /> Lecteur (Read-Only)
                                            </span>
                                            <span className="text-sm text-slate-500 mt-1 block">Accès consultatif limité aux dashboards de KPI environnementaux et énergétiques. Aucune action autorisée (ni CVC, ni alertes).</span>
                                        </div>
                                    </label>
                                </div>
                            </div>

                            <button disabled={isLoading} type="submit" className="w-full bg-primary hover:bg-emerald-500 text-white font-black py-4 rounded-xl transition-all disabled:opacity-50 mt-4 shadow-lg shadow-primary/30 active:scale-[0.98]">
                                {isLoading ? "Création en cours..." : "Envoyer l'invitation"}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
