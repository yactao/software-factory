"use client";

import { useState, useEffect } from "react";
import { ShieldCheck, Zap, HardDrive, Users, CheckCircle2, AlertCircle, ArrowRight, Activity, Database, Cloud, Edit2, X, Save } from "lucide-react";
import { useTenant } from "@/lib/TenantContext";
import { cn } from "@/lib/utils";

export default function LicensePage() {
    const { currentTenant, authFetch } = useTenant();
    const [orgData, setOrgData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [editData, setEditData] = useState({ subscriptionPlan: "Enterprise", maxUsers: 5, maxDevices: 100, maxSites: 5 });
    const isAdmin = currentTenant?.role === "SUPER_ADMIN" || currentTenant?.role === "ENERGY_MANAGER";

    const fetchQuota = async () => {
        if (!currentTenant?.id) return;
        try {
            const res = await authFetch(`http://localhost:3001/api/organizations`);
            if (res.ok) {
                const data = await res.json();
                const org = data.find((o: any) => o.id === currentTenant.id);
                setOrgData(org);
                setEditData({
                    subscriptionPlan: org.subscriptionPlan || "Enterprise",
                    maxUsers: org.maxUsers || 5,
                    maxDevices: org.maxDevices || 100,
                    maxSites: org.maxSites || 5
                });
            }
        } catch (err) {
            console.error("Failed to fetch quotas", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchQuota();
    }, [currentTenant, authFetch]);

    const handleSaveQuotas = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await authFetch(`http://localhost:3001/api/organizations/${currentTenant?.id}`, {
                method: "PUT",
                body: JSON.stringify(editData)
            });
            if (res.ok) {
                setIsEditModalOpen(false);
                await fetchQuota();
            }
        } catch (err) {
            console.error("Failed to update quotas", err);
        }
    };
    if (loading) return <div className="p-8 text-center text-slate-500">Chargement de la licence...</div>;
    if (!orgData) return <div className="p-8 text-center text-rose-500">Données de l'organisation introuvables.</div>;

    // Calculs des pourcentages
    const usersPercent = Math.min(100, Math.round((orgData.usersCount / orgData.maxUsers) * 100)) || 0;
    const devicesPercent = Math.min(100, Math.round((orgData.devicesCount / orgData.maxDevices) * 100)) || 0;
    const sitesPercent = Math.min(100, Math.round((orgData.sitesCount / orgData.maxSites) * 100)) || 0;

    return (
        <div className="max-w-6xl mx-auto pt-8 pb-12">
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2 flex items-center">
                        <ShieldCheck className="h-8 w-8 text-primary mr-3" />
                        Licence & Quotas
                    </h1>
                    <p className="text-slate-500 dark:text-muted-foreground">Pilotez votre abonnement UBBEE Cloud et vérifiez les limites de votre plan actuel.</p>
                </div>
                <div className="text-right">
                    <p className="text-sm font-semibold text-slate-500 dark:text-muted-foreground uppercase tracking-widest mb-1">Organisation</p>
                    <p className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">{currentTenant?.name || "Global"}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Plan Details */}
                <div className="lg:col-span-1 space-y-6">
                    <div className="glass-card rounded-2xl p-8 border-t-4 border-t-primary shadow-xl bg-white dark:bg-slate-900/60 relative overflow-hidden">
                        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-[40px] pointer-events-none -translate-y-1/2 translate-x-1/3"></div>

                        <div className="flex items-center justify-between mb-6">
                            <span className="px-3 py-1 bg-primary/20 text-emerald-500 text-xs font-bold uppercase tracking-wider rounded-full">Plan Actuel</span>
                            <span className="flex items-center text-emerald-500 text-sm font-bold"><CheckCircle2 className="w-4 h-4 mr-1" /> Actif</span>
                        </div>

                        <h2 className="text-4xl font-extrabold text-slate-900 dark:text-white mb-2">{orgData.subscriptionPlan || "Enterprise"}</h2>
                        <p className="text-slate-500 dark:text-muted-foreground text-sm mb-6">Idéal pour la gestion de parcs immobiliers distribués avec IA et Analytics avancés.</p>

                        <div className="text-3xl font-bold text-slate-900 dark:text-white mb-6">
                            {orgData.subscriptionPlan === "Enterprise" ? "Sur mesure" : orgData.subscriptionPlan === "Pro" ? "499 CHF" : "99 CHF"} <span className="text-sm text-slate-500 dark:text-muted-foreground font-normal">{orgData.subscriptionPlan !== "Enterprise" && "/ mois"}</span>
                        </div>

                        {isAdmin && (
                            <button
                                onClick={() => setIsEditModalOpen(true)}
                                className="w-full py-3 bg-slate-900 hover:bg-slate-800 dark:bg-white dark:hover:bg-slate-200 text-white dark:text-slate-900 rounded-xl font-bold transition-colors mb-4 flex items-center justify-center"
                            >
                                <Edit2 className="w-4 h-4 mr-2" /> Modifier l'abonnement
                            </button>
                        )}
                        <button
                            onClick={isAdmin ? () => setIsEditModalOpen(true) : undefined}
                            className={cn(
                                "w-full py-3 bg-transparent hover:bg-slate-100 dark:hover:bg-white/5 text-slate-600 dark:text-slate-300 rounded-xl font-semibold transition-colors flex items-center justify-center",
                                isAdmin ? "" : "opacity-50 cursor-not-allowed"
                            )}>
                            Voir les offres <ArrowRight className="w-4 h-4 ml-2" />
                        </button>
                    </div>
                </div>

                {/* Quotas & Features */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="glass-card rounded-2xl p-8 bg-white dark:bg-slate-900/60 border border-slate-200 dark:border-white/10">
                        <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-6">Consommation du Quota</h3>

                        <div className="space-y-8">
                            {/* Quota: Users */}
                            <div>
                                <div className="flex justify-between items-end mb-2">
                                    <div className="flex items-center">
                                        <Users className="w-5 h-5 text-slate-400 dark:text-slate-500 mr-2" />
                                        <span className="font-semibold text-slate-700 dark:text-slate-300">Utilisateurs Enregistrés</span>
                                    </div>
                                    <span className="text-sm font-bold text-slate-900 dark:text-white">{orgData.usersCount} / {orgData.maxUsers}</span>
                                </div>
                                <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5">
                                    <div className={`h-2.5 rounded-full ${usersPercent > 90 ? 'bg-rose-500' : 'bg-cyan-500'}`} style={{ width: `${usersPercent}%` }}></div>
                                </div>
                            </div>

                            {/* Quota: Devices */}
                            <div>
                                <div className="flex justify-between items-end mb-2">
                                    <div className="flex items-center">
                                        <Database className="w-5 h-5 text-slate-400 dark:text-slate-500 mr-2" />
                                        <span className="font-semibold text-slate-700 dark:text-slate-300">Capteurs & Passerelles IoT</span>
                                    </div>
                                    <span className="text-sm font-bold text-slate-900 dark:text-white">{orgData.devicesCount || 0} / {orgData.maxDevices}</span>
                                </div>
                                <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5">
                                    <div className={`h-2.5 rounded-full ${devicesPercent > 90 ? 'bg-rose-500' : 'bg-primary'}`} style={{ width: `${devicesPercent}%` }}></div>
                                </div>
                            </div>

                            {/* Quota: Sites */}
                            <div>
                                <div className="flex justify-between items-end mb-2">
                                    <div className="flex items-center">
                                        <Activity className="w-5 h-5 text-slate-400 dark:text-slate-500 mr-2" />
                                        <span className="font-semibold text-slate-700 dark:text-slate-300">Bâtiments & Sites Connectés</span>
                                    </div>
                                    <span className="text-sm font-bold text-slate-900 dark:text-white">{orgData.sitesCount} / {orgData.maxSites}</span>
                                </div>
                                <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5">
                                    <div className={`h-2.5 rounded-full ${sitesPercent > 90 ? 'bg-rose-500' : 'bg-orange-400'}`} style={{ width: `${sitesPercent}%` }}></div>
                                </div>
                            </div>

                            {/* Quota: Cloud Storage */}
                            <div>
                                <div className="flex justify-between items-end mb-2">
                                    <div className="flex items-center">
                                        <HardDrive className="w-5 h-5 text-slate-400 dark:text-slate-500 mr-2" />
                                        <span className="font-semibold text-slate-700 dark:text-slate-300">Historique de Stockage (Cold Data)</span>
                                    </div>
                                    <span className="text-sm font-bold text-slate-900 dark:text-white">35 GB / 100 GB</span>
                                </div>
                                <div className="w-full bg-slate-200 dark:bg-slate-800 rounded-full h-2.5">
                                    <div className="bg-purple-500 h-2.5 rounded-full" style={{ width: '35%' }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Infrastructure & Billing Info (3 aligned blocks) */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8">
                {/* Block 1: Mise à jour */}
                <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900 border border-slate-200 dark:border-white/5 relative overflow-hidden group">
                    <AlertCircle className="absolute -right-4 -bottom-4 w-24 h-24 text-slate-300 dark:text-white/5 group-hover:scale-110 transition-transform duration-500" />
                    <h4 className="font-bold text-lg text-slate-900 dark:text-white mb-1 relative z-10">Prochaine Facture</h4>
                    <p className="text-slate-500 dark:text-muted-foreground text-sm relative z-10">01 Mars 2026</p>
                    <p className="text-xs font-mono text-slate-400 mt-4 relative z-10 text-orange-500/80">Renouvellement Automatique</p>
                </div>

                {/* Block 2: Region Cloud */}
                <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900 border border-slate-200 dark:border-white/5 relative overflow-hidden group">
                    <Cloud className="absolute -right-4 -bottom-4 w-24 h-24 text-slate-300 dark:text-white/5 group-hover:scale-110 transition-transform duration-500" />
                    <h4 className="font-bold text-lg text-slate-900 dark:text-white mb-1 relative z-10">Région Cloud</h4>
                    <p className="text-slate-500 dark:text-muted-foreground text-sm relative z-10">eu-west-3 (Paris)</p>
                    <p className="text-xs font-mono text-slate-400 mt-4 relative z-10">Conforme RGPD</p>
                </div>

                {/* Block 3: Support */}
                <div className="p-6 rounded-2xl bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-800 dark:to-slate-900 border border-slate-200 dark:border-white/5 relative overflow-hidden group">
                    <Zap className="absolute -right-4 -bottom-4 w-24 h-24 text-slate-300 dark:text-white/5 group-hover:scale-110 transition-transform duration-500" />
                    <h4 className="font-bold text-lg text-slate-900 dark:text-white mb-1 relative z-10">Support Technique</h4>
                    <p className="text-slate-500 dark:text-muted-foreground text-sm relative z-10">Priorité SLA 99.9%</p>
                    <p className="text-xs font-mono text-slate-400 mt-4 relative z-10">Garantie d'intervention 2H</p>
                </div>
            </div>

            {/* Modal: Edit Quotas */}
            {isEditModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                        <button onClick={() => setIsEditModalOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white">
                            <X className="h-5 w-5" />
                        </button>
                        <h2 className="text-xl font-bold mb-6 text-slate-900 dark:text-white flex items-center">
                            <Edit2 className="h-5 w-5 mr-2 text-primary" />
                            Modifier l'Abonnement
                        </h2>
                        <form onSubmit={handleSaveQuotas} className="space-y-4">
                            <div className="bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-200 dark:border-white/10 space-y-4">
                                <div>
                                    <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Plan d'Abonnement</label>
                                    <select
                                        value={editData.subscriptionPlan}
                                        onChange={e => setEditData({ ...editData, subscriptionPlan: e.target.value })}
                                        className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                    >
                                        <option value="Starter">Starter - 99 CHF/mo</option>
                                        <option value="Pro">Pro - 499 CHF/mo</option>
                                        <option value="Enterprise">Enterprise - Sur mesure</option>
                                    </select>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Max Utilisateurs</label>
                                        <input
                                            type="number"
                                            value={editData.maxUsers}
                                            onChange={e => setEditData({ ...editData, maxUsers: parseInt(e.target.value) || 0 })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Max Sites</label>
                                        <input
                                            type="number"
                                            value={editData.maxSites}
                                            onChange={e => setEditData({ ...editData, maxSites: parseInt(e.target.value) || 0 })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Max Équipements IoT</label>
                                    <input
                                        type="number"
                                        value={editData.maxDevices}
                                        onChange={e => setEditData({ ...editData, maxDevices: parseInt(e.target.value) || 0 })}
                                        className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                    />
                                </div>
                            </div>

                            <button type="submit" className="w-full py-3 mt-4 bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)] flex items-center justify-center">
                                <Save className="w-5 h-5 mr-2" /> Appliquer les quotas
                            </button>
                            <button type="button" onClick={() => setIsEditModalOpen(false)} className="w-full py-3 mt-2 bg-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-white font-bold rounded-xl transition-all">
                                Annuler
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
