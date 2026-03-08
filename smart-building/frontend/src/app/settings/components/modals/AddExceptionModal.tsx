import { X } from "lucide-react";
import { SettingsState } from "../types";

export function AddExceptionModal({ state }: { state: SettingsState }) {
    const { isAddExceptionModalOpen, setIsAddExceptionModalOpen, newException, setNewException, handleAddException } = state;

    if (!isAddExceptionModalOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                <button onClick={() => setIsAddExceptionModalOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"><X className="h-5 w-5" /></button>
                <h2 className="text-xl font-bold mb-2 text-slate-900 dark:text-white flex items-center">Ajouter une Exception</h2>
                <p className="text-xs text-slate-500 mb-6">Définissez une ouverture exceptionnelle ou un jour de fermeture (férié).</p>

                <form onSubmit={handleAddException} className="space-y-4">
                    <div>
                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Intitulé</label>
                        <input type="text" required value={newException.name} onChange={e => setNewException({ ...newException, name: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:border-primary outline-none transition-all placeholder-slate-400" placeholder="ex: 14 Juillet, Ouverture Black Friday" />
                    </div>

                    <div>
                        <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Date</label>
                        <input type="date" required value={newException.date} onChange={e => setNewException({ ...newException, date: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:border-primary outline-none transition-all" />
                    </div>

                    <div className="bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-200 dark:border-white/10">
                        <label className="text-sm font-bold text-slate-900 dark:text-white mb-3 block">Type d'exception</label>
                        <div className="space-y-3">
                            <label className="flex items-start cursor-pointer group">
                                <input type="radio" name="extype" value="closed" checked={newException.type === 'closed'} onChange={e => setNewException({ ...newException, type: e.target.value })} className="mt-1 mr-3 text-red-500 focus:ring-red-500" />
                                <div>
                                    <span className="text-sm font-bold text-red-600 dark:text-red-400 block transition-colors">Fermé (Jour férié / Chômé)</span>
                                    <span className="text-xs text-slate-500">Le bâtiment passe en mode ÉCO pour la journée entière.</span>
                                </div>
                            </label>
                            <label className="flex items-start cursor-pointer group">
                                <input type="radio" name="extype" value="open" checked={newException.type === 'open'} onChange={e => setNewException({ ...newException, type: e.target.value })} className="mt-1 mr-3 text-blue-500 focus:ring-blue-500" />
                                <div>
                                    <span className="text-sm font-bold text-blue-600 dark:text-blue-400 block transition-colors">Ouverture exceptionnelle</span>
                                    <span className="text-xs text-slate-500">Le bâtiment sera chauffé/ventilé même si c'est normalement fermé.</span>
                                </div>
                            </label>
                        </div>
                    </div>

                    {newException.type === 'open' && (
                        <div className="flex items-center gap-4">
                            <div className="flex-1">
                                <label className="text-[10px] text-slate-500 uppercase font-bold">Ouverture</label>
                                <input type="time" required value={newException.startTime} onChange={e => setNewException({ ...newException, startTime: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-sm font-bold text-slate-900 dark:text-white" />
                            </div>
                            <div className="flex-1">
                                <label className="text-[10px] text-slate-500 uppercase font-bold">Fermeture</label>
                                <input type="time" required value={newException.endTime} onChange={e => setNewException({ ...newException, endTime: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-sm font-bold text-slate-900 dark:text-white" />
                            </div>
                        </div>
                    )}

                    <button type="submit" className="w-full py-3 mt-6 bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white font-bold rounded-xl transition-all flex justify-center items-center shadow-lg shadow-primary/30">
                        Enregistrer la date
                    </button>
                </form>
            </div>
        </div>
    );
}
