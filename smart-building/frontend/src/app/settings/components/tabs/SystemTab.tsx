import { cn } from "@/lib/utils";
import { SettingsState } from "../types";

export function SystemTab({ state }: { state: SettingsState }) {
    const { currentTenant, maintenanceMode, setMaintenanceMode } = state;

    return (
        <div className="max-w-xl space-y-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white border-b border-slate-200 dark:border-white/10 pb-4">Paramètres Système</h2>

            <div className="space-y-4">
                <div className="flex flex-col">
                    <label className="text-sm font-medium text-slate-900 dark:text-white mb-1">Nom de l'Espace</label>
                    <input
                        type="text"
                        defaultValue={currentTenant?.name || "SmartBuild GTB"}
                        className="bg-slate-50 dark:bg-black/20 border border-slate-200 dark:border-white/10 rounded-lg px-4 py-2.5 text-slate-900 dark:text-white focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/50 transition-all text-sm font-medium"
                    />
                </div>

                <div className="flex flex-col">
                    <label className="text-sm font-medium text-slate-900 dark:text-white mb-1">Fuseau Horaire de Référence</label>
                    <select className="bg-slate-50 dark:bg-black/20 border border-slate-200 dark:border-white/10 rounded-lg px-4 py-2.5 text-slate-900 dark:text-white focus:outline-none focus:border-primary/50 text-sm font-medium">
                        <option value="Europe/Paris">Europe/Paris (CET/CEST)</option>
                        <option value="UTC">UTC Globale</option>
                    </select>
                    <p className="text-xs text-slate-500 mt-1">Sert de base de calcul pour la fermeture des bâtiments.</p>
                </div>

                <div className="flex items-center justify-between pt-4 border-t border-slate-200 dark:border-white/5 mt-6">
                    <div>
                        <h4 className="text-slate-900 dark:text-white font-bold flex items-center">
                            Mode Maintenance
                            {maintenanceMode && <span className="ml-2 px-2 py-0.5 bg-orange-500/10 text-orange-500 text-[10px] font-bold uppercase rounded-full border border-orange-500/20">Actif</span>}
                        </h4>
                        <p className="text-xs text-slate-500 dark:text-muted-foreground mt-1">Désactive l'accès aux utilisateurs standards et suspend les alertes sortantes.</p>
                    </div>
                    <div
                        onClick={() => setMaintenanceMode(!maintenanceMode)}
                        className={cn("w-12 h-6 rounded-full relative cursor-pointer transition-colors shadow-inner", maintenanceMode ? "bg-orange-500" : "bg-slate-300 dark:bg-slate-700")}>
                        <div className={cn("absolute top-1 w-4 h-4 rounded-full bg-white transition-transform", maintenanceMode ? "translate-x-7" : "translate-x-1")}></div>
                    </div>
                </div>
            </div>

            <div className="pt-8">
                <button className="bg-primary text-slate-900 dark:text-white px-6 py-2.5 rounded-xl text-sm font-bold shadow-lg shadow-primary/30 hover:shadow-primary/50 transition-all">
                    Sauvegarder les modifications
                </button>
            </div>
        </div>
    );
}
