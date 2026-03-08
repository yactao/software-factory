import { Mail } from "lucide-react";
import { cn } from "@/lib/utils";
import { SettingsState } from "../types";

export function NotificationsTab({ state }: { state: SettingsState }) {
    const { emailAlerts, setEmailAlerts, smsAlerts, setSmsAlerts } = state;

    return (
        <div className="max-w-xl space-y-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white border-b border-slate-200 dark:border-white/10 pb-4 flex items-center">
                Préférences d'Alertes
            </h2>
            <p className="text-sm text-slate-500 dark:text-muted-foreground">
                Choisissez comment le système doit vous contacter lorsqu'une règle domotique lève une alerte.
            </p>

            <div className="space-y-4 pt-4">
                <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/10">
                    <div>
                        <h4 className="text-slate-900 dark:text-white font-bold flex items-center"><Mail className="w-4 h-4 mr-2" /> Rapport d'Incident Quotidien (Email)</h4>
                        <p className="text-xs text-slate-500 dark:text-muted-foreground mt-1">Résumé des alertes non-traitées envoyé à 8h00.</p>
                    </div>
                    <div
                        className={cn("w-11 h-6 rounded-full relative cursor-pointer transition-colors shadow-inner", emailAlerts ? "bg-primary" : "bg-slate-300 dark:bg-slate-700")}
                        onClick={() => setEmailAlerts(!emailAlerts)}
                    >
                        <div className={cn("absolute top-1 w-4 h-4 rounded-full bg-white transition-transform", emailAlerts ? "translate-x-6" : "translate-x-1")}></div>
                    </div>
                </div>

                <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-white/5 rounded-xl border border-slate-100 dark:border-white/10">
                    <div>
                        <h4 className="text-slate-900 dark:text-white font-bold flex items-center">Alertes Temps Réel SMS (Critique uniquement)</h4>
                        <p className="text-xs text-slate-500 dark:text-muted-foreground mt-1">Notification immédiate pour interventions d'urgence.</p>
                    </div>
                    <div
                        className={cn("w-11 h-6 rounded-full relative cursor-pointer transition-colors shadow-inner", smsAlerts ? "bg-primary" : "bg-slate-300 dark:bg-slate-700")}
                        onClick={() => setSmsAlerts(!smsAlerts)}
                    >
                        <div className={cn("absolute top-1 w-4 h-4 rounded-full bg-white transition-transform", smsAlerts ? "translate-x-6" : "translate-x-1")}></div>
                    </div>
                </div>
            </div>
        </div>
    );
}
