import { Key, Webhook } from "lucide-react";

export function IntegrationsTab() {
    return (
        <div className="max-w-2xl space-y-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white border-b border-slate-200 dark:border-white/10 pb-4">API & Webhooks B2B</h2>
            <p className="text-sm text-slate-500">Connectez vos propres systèmes internes (ERP, Jira, ServiceNow) pour réagir aux évènements de la GMAO.</p>

            <div className="space-y-6 pt-4">
                <div className="glass-card bg-slate-50/50 dark:bg-white/5 p-5 rounded-xl border border-slate-200 dark:border-white/10 relative overflow-hidden">
                    <div className="absolute top-0 right-0 w-24 h-24 bg-primary/10 rounded-full blur-[30px] -mr-8 -mt-8 pointer-events-none"></div>
                    <h3 className="font-bold text-slate-900 dark:text-white flex items-center mb-1">
                        <Key className="w-4 h-4 mr-2 text-primary" />
                        Clé d'API (Read-Only)
                    </h3>
                    <p className="text-xs text-slate-500 mb-4">Utilisée pour aspirer la data brute depuis vos scripts (PowerBI, Python).</p>

                    <div className="flex gap-2">
                        <code className="flex-1 bg-white dark:bg-black/50 border border-slate-200 dark:border-white/10 py-2 px-3 rounded-lg text-xs font-mono text-slate-600 dark:text-slate-300 overflow-hidden text-ellipsis">sk_live_9f8d7c6b5a4...</code>
                        <button className="bg-slate-200 dark:bg-white/10 text-slate-900 dark:text-white text-xs font-bold px-4 rounded-lg hover:bg-slate-300 dark:hover:bg-white/20 transition-colors">Copier</button>
                        <button className="bg-primary/20 text-primary border border-primary/30 text-xs font-bold px-4 rounded-lg hover:bg-primary hover:text-white transition-colors">Renouveler la clé</button>
                    </div>
                </div>

                <div className="glass-card bg-slate-50/50 dark:bg-white/5 p-5 rounded-xl border border-slate-200 dark:border-white/10 relative overflow-hidden">
                    <div className="flex justify-between items-start mb-4">
                        <div>
                            <h3 className="font-bold text-slate-900 dark:text-white flex items-center mb-1">
                                <Webhook className="w-4 h-4 mr-2 text-primary" />
                                Webhooks "Création d'Alerte"
                            </h3>
                            <p className="text-xs text-slate-500">POST Request envoyé lors d'un défaut matériel critique (CVC hors ligne).</p>
                        </div>
                        <div className="w-11 h-6 bg-primary rounded-full relative cursor-pointer shadow-inner">
                            <div className="absolute right-1 top-1 w-4 h-4 rounded-full bg-white transition-transform"></div>
                        </div>
                    </div>

                    <div className="flex flex-col gap-2">
                        <label className="text-[10px] uppercase font-bold text-slate-500">URL du point d'entrée (Payload JSON)</label>
                        <input
                            type="url"
                            defaultValue="https://api.votre-erp.com/webhooks/smartbuild/alerts"
                            className="bg-white dark:bg-black/50 border border-slate-200 dark:border-white/10 py-2 px-3 rounded-lg text-sm font-mono text-slate-900 dark:text-white focus:outline-none focus:border-primary/50"
                        />
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-200 dark:border-white/5 flex gap-2">
                        <button className="text-xs bg-slate-200 dark:bg-white/10 text-slate-600 dark:text-slate-300 px-3 py-1.5 rounded font-bold">Voir un exemple de Payload</button>
                        <button className="text-xs bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 px-3 py-1.5 rounded font-bold">Tester la requête (Ping)</button>
                    </div>
                </div>
            </div>
        </div>
    );
}
