import { Palette } from "lucide-react";
import { cn } from "@/lib/utils";
import { SettingsState } from "../types";

export function AppearanceTab({ state }: { state: SettingsState }) {
    const { themeColor, setThemeColor } = state;

    return (
        <div className="max-w-xl space-y-6">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white border-b border-slate-200 dark:border-white/10 pb-4">Identité Visuelle (Marque Blanche)</h2>
            <p className="text-sm text-slate-500">Personnalisez le rendu visuel de la plateforme pour qu'elle corresponde à votre charte graphique.</p>

            <div className="space-y-8 pt-4">
                <div>
                    <label className="text-sm font-bold text-slate-900 dark:text-white mb-3 block">Couleur Primaire (Thème)</label>
                    <div className="flex gap-4">
                        {[
                            { id: 'emerald', color: 'bg-emerald-500' },
                            { id: 'blue', color: 'bg-blue-500' },
                            { id: 'purple', color: 'bg-purple-500' },
                            { id: 'orange', color: 'bg-orange-500' },
                        ].map(theme => (
                            <button
                                key={theme.id}
                                onClick={() => setThemeColor(theme.id)}
                                className={cn("w-12 h-12 rounded-full ring-offset-2 dark:ring-offset-slate-900 transition-all", theme.color, themeColor === theme.id ? "ring-2 ring-primary scale-110 shadow-lg" : "scale-100 opacity-50 hover:opacity-100")}
                            />
                        ))}
                    </div>
                </div>

                <div className="flex flex-col">
                    <label className="text-sm font-bold text-slate-900 dark:text-white mb-3">Logo de l'Entreprise</label>
                    <div className="border-2 border-dashed border-slate-200 dark:border-white/10 rounded-xl p-8 flex flex-col items-center justify-center bg-slate-50/50 dark:bg-black/20 hover:bg-slate-50 dark:hover:bg-black/40 transition-colors cursor-pointer group">
                        <Palette className="w-8 h-8 text-slate-400 group-hover:text-primary transition-colors mb-3" />
                        <p className="text-sm font-medium text-slate-600 dark:text-slate-300">Cliquez ou glissez une image (PNG/SVG, 400x100px max)</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
