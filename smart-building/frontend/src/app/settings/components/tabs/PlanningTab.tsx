import { Plus } from "lucide-react";
import { SettingsState } from "../types";

export function PlanningTab({ state }: { state: SettingsState }) {
    const { exceptionsList, setIsAddExceptionModalOpen } = state;

    return (
        <div className="max-w-2xl space-y-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white border-b border-slate-200 dark:border-white/10 pb-4">Horaires d'Ouverture du Bâtiment</h2>
            <p className="text-sm text-slate-500">Ces plages horaires permettent de basculer tous les équipements CVC (Chauffage, Ventilation, Climatisation) et éclairages en mode "Éco" automatiquement hors des heures d'ouverture.</p>

            <div className="space-y-4 pt-4">
                {["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi"].map(day => (
                    <div key={day} className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-slate-50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/5">
                        <span className="font-bold text-slate-900 dark:text-white mb-2 sm:mb-0 w-32">{day}</span>
                        <div className="flex items-center gap-4">
                            <div className="flex flex-col">
                                <span className="text-[10px] text-slate-500 mb-1 uppercase font-bold">Ouverture</span>
                                <input type="time" defaultValue="08:00" className="bg-white dark:bg-black/30 border border-slate-200 dark:border-white/10 rounded px-3 py-1.5 text-sm font-bold w-28 text-slate-900 dark:text-white" />
                            </div>
                            <span className="text-slate-400 mt-4">-</span>
                            <div className="flex flex-col">
                                <span className="text-[10px] text-slate-500 mb-1 uppercase font-bold">Fermeture</span>
                                <input type="time" defaultValue="19:00" className="bg-white dark:bg-black/30 border border-slate-200 dark:border-white/10 rounded px-3 py-1.5 text-sm font-bold w-28 text-slate-900 dark:text-white" />
                            </div>
                        </div>
                    </div>
                ))}

                <div className="flex items-center justify-between p-4 bg-orange-500/10 border border-orange-500/20 rounded-xl">
                    <span className="font-bold text-orange-600 dark:text-orange-400">Samedi & Dimanche</span>
                    <span className="font-bold text-orange-600/70 dark:text-orange-400/70 text-sm">Mode ÉCO Continu H24</span>
                </div>
            </div>

            <div className="pt-8 border-t border-slate-200 dark:border-white/10">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="font-bold text-lg text-slate-900 dark:text-white flex items-center">
                        Exceptions & Jours Fériés
                    </h3>
                    <button onClick={() => setIsAddExceptionModalOpen(true)} className="flex items-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary dark:bg-emerald-500/10 dark:text-emerald-400 dark:hover:bg-emerald-500/20 px-3 py-1.5 rounded-lg font-bold text-xs transition-colors border border-primary/20">
                        <Plus className="w-4 h-4" /> Ajouter une Exception
                    </button>
                </div>

                <div className="space-y-3">
                    {exceptionsList.map((exc: { id?: number | string, type: string, date: string, name: string, startTime?: string, endTime?: string }) => (
                        <div key={exc.id} className={`flex justify-between items-center p-4 ${exc.type === 'closed' ? 'bg-red-500/5 border-red-500/20' : 'bg-blue-500/5 border-blue-500/20'} border shadow-sm rounded-xl`}>
                            <div>
                                <div className={`font-bold ${exc.type === 'closed' ? 'text-red-600 dark:text-red-400' : 'text-blue-600 dark:text-blue-400'} text-sm`}>{new Date(exc.date).toLocaleDateString('fr-FR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</div>
                                <div className={`text-xs ${exc.type === 'closed' ? 'text-red-600/70 dark:text-red-400/70' : 'text-blue-600/70 dark:text-blue-400/70'} mt-0.5`}>{exc.name}</div>
                            </div>
                            {exc.type === 'closed' ? (
                                <span className="font-bold text-red-600 dark:text-red-400 text-xs px-3 py-1 bg-red-500/10 rounded-lg border border-red-500/20">Fermeture Totale / H24 ÉCO</span>
                            ) : (
                                <div className="flex items-center gap-2">
                                    <span className={`font-mono text-xs font-bold text-blue-600 dark:text-blue-400 bg-white dark:bg-black/30 px-2 py-1 border border-blue-500/20 rounded-md`}>{exc.startTime}</span>
                                    <span className="text-blue-400">-</span>
                                    <span className={`font-mono text-xs font-bold text-blue-600 dark:text-blue-400 bg-white dark:bg-black/30 px-2 py-1 border border-blue-500/20 rounded-md`}>{exc.endTime}</span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
