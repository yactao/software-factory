import { X, Shield } from "lucide-react";
import { useState } from "react";
import { SettingsState } from "../types";

export function RoleProfileModal({ state }: { state: SettingsState }) {
    const { isProfileModalOpen, setIsProfileModalOpen, newRoleName, setNewRoleName, handleCreateRole } = state;

    // State to track selected permissions
    const [permissions, setPermissions] = useState<string[]>([]);

    const togglePermission = (perm: string) => {
        setPermissions(prev =>
            prev.includes(perm) ? prev.filter(p => p !== perm) : [...prev, perm]
        );
    };

    if (!isProfileModalOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
            <div className="w-full max-w-3xl bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-8 shadow-2xl relative my-auto">
                <button onClick={() => setIsProfileModalOpen(false)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors">
                    <X className="h-5 w-5" />
                </button>

                <div className="mb-8">
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center mb-2">
                        <Shield className="w-6 h-6 mr-3 text-indigo-500" />
                        Profil d'Administration UBBEE
                    </h2>
                    <p className="text-sm text-slate-500 dark:text-muted-foreground ml-9">
                        Sélectionnez les droits de ce profil sur l'ensemble de la plateforme (Multi-Clients).
                    </p>
                </div>

                <div className="space-y-8">
                    {/* Intitulé */}
                    <div>
                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300 mb-2 block">
                            Intitulé du profil administratif
                        </label>
                        <input
                            type="text"
                            value={newRoleName}
                            onChange={e => setNewRoleName(e.target.value)}
                            placeholder="ex: Analyste Technique, Équipe Logistique, Support N1..."
                            className="w-full p-3 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none transition-all placeholder-slate-300"
                        />
                    </div>

                    {/* Matrice */}
                    <div>
                        <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-6 border-b border-slate-100 dark:border-white/5 pb-2">
                            Matrice Globale (Opérateur)
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-10">
                            {/* Group 1 */}
                            <div>
                                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-4">Gestion des Comptes B2B</h4>
                                <div className="space-y-3">
                                    <label className="flex items-start cursor-pointer group">
                                        <input type="checkbox" checked={permissions.includes("view:orgs")} onChange={() => togglePermission("view:orgs")} className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500 mt-0.5 mr-3 shrink-0" />
                                        <span className="text-sm text-slate-600 dark:text-slate-400">
                                            Lecture des fiches Clients <span className="font-mono text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded ml-1">( view:orgs )</span>
                                        </span>
                                    </label>
                                    <label className="flex items-start cursor-pointer group">
                                        <input type="checkbox" checked={permissions.includes("edit:orgs")} onChange={() => togglePermission("edit:orgs")} className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500 mt-0.5 mr-3 shrink-0" />
                                        <span className="text-sm text-slate-600 dark:text-slate-400">
                                            Création / Édition de Clients <span className="font-mono text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded ml-1">( edit:orgs )</span>
                                        </span>
                                    </label>
                                    <div className="pl-7 pt-1">
                                        <span className="text-sm text-blue-300 dark:text-blue-500/50 block">
                                            Suppression de la donnée Client (Réservé au Fondateur)
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Group 2 */}
                            <div>
                                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-4">Inventaire Matériel (Gateways)</h4>
                                <div className="space-y-3">
                                    <label className="flex items-start cursor-pointer group">
                                        <input type="checkbox" checked={permissions.includes("view:fleet")} onChange={() => togglePermission("view:fleet")} className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500 mt-0.5 mr-3 shrink-0" />
                                        <span className="text-sm text-slate-600 dark:text-slate-400">
                                            Consulter le stock Global <span className="font-mono text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded ml-1">( view:fleet )</span>
                                        </span>
                                    </label>
                                    <label className="flex items-start cursor-pointer group">
                                        <input type="checkbox" checked={permissions.includes("edit:fleet")} onChange={() => togglePermission("edit:fleet")} className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500 mt-0.5 mr-3 shrink-0" />
                                        <span className="text-sm text-slate-600 dark:text-slate-400 block leading-relaxed">
                                            Provisionner un U-BOT (MAC Address)<br />
                                            <span className="font-mono text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">( edit:fleet )</span>
                                        </span>
                                    </label>
                                </div>
                            </div>

                            {/* Group 3 */}
                            <div>
                                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-4">Support Technique & Réseau</h4>
                                <div className="space-y-3">
                                    <label className="flex items-start cursor-pointer group">
                                        <input type="checkbox" checked={permissions.includes("view:network")} onChange={() => togglePermission("view:network")} className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500 mt-0.5 mr-3 shrink-0" />
                                        <span className="text-sm text-slate-600 dark:text-slate-400">
                                            Lecture des Logs (MQTT Live) <span className="font-mono text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded ml-1">( view:network )</span>
                                        </span>
                                    </label>
                                    <label className="flex items-start cursor-pointer group">
                                        <input type="checkbox" checked={permissions.includes("edit:network")} onChange={() => togglePermission("edit:network")} className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500 mt-0.5 mr-3 shrink-0" />
                                        <span className="text-sm text-slate-600 dark:text-slate-400">
                                            Assigner/Dépanner un Capteur <span className="font-mono text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded ml-1">( edit:network )</span>
                                        </span>
                                    </label>
                                </div>
                            </div>

                            {/* Group 4 */}
                            <div>
                                <h4 className="text-sm font-bold text-slate-800 dark:text-slate-200 mb-4">Système & Intégrations</h4>
                                <div className="space-y-3">
                                    <label className="flex items-start cursor-pointer group">
                                        <input type="checkbox" checked={permissions.includes("edit:system")} onChange={() => togglePermission("edit:system")} className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500 mt-0.5 mr-3 shrink-0" />
                                        <span className="text-sm text-slate-600 dark:text-slate-400">
                                            Configurer Webhooks & API <span className="font-mono text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded ml-1">( edit:system )</span>
                                        </span>
                                    </label>
                                    <label className="flex items-start cursor-pointer group">
                                        <input type="checkbox" checked={permissions.includes("edit:theme")} onChange={() => togglePermission("edit:theme")} className="w-4 h-4 rounded border-slate-300 text-indigo-500 focus:ring-indigo-500 mt-0.5 mr-3 shrink-0" />
                                        <span className="text-sm text-slate-600 dark:text-slate-400 block leading-relaxed">
                                            Changer l'apparence (Marque Blanche)<br />
                                            <span className="font-mono text-[10px] text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">( edit:theme )</span>
                                        </span>
                                    </label>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Footer Buttons */}
                    <div className="flex justify-end items-center gap-6 pt-6">
                        <button onClick={() => setIsProfileModalOpen(false)} className="text-sm font-bold text-slate-500 hover:text-slate-700 dark:hover:text-white transition-colors">
                            Annuler
                        </button>
                        <button onClick={() => {
                            if (newRoleName) {
                                handleCreateRole?.(newRoleName, permissions);
                            } else {
                                alert("Veuillez saisir un intitulé pour ce rôle.");
                            }
                        }} className="bg-[#818CF8] hover:bg-indigo-500 text-white font-bold py-3 px-8 rounded-xl transition-all shadow-lg shadow-indigo-500/30">
                            Enregistrer le Profil UBBEE
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
