"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Building2, Search, Plus, Filter, MapPin, Building, Activity, Upload } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTenant } from "@/lib/TenantContext";

// Types
interface Site {
    id: string;
    name: string;
    type?: string;
    address: string;
    postalCode?: string;
    city: string;
    status: string;
    zonesCount?: number;
    statusColor?: "green" | "orange" | "red";
    organization?: { name: string };
}

export default function SitesListPage() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const filterParam = searchParams.get('filter');
    const { authFetch, currentTenant } = useTenant();
    const [sites, setSites] = useState<Site[]>([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState("");
    const [isUploading, setIsUploading] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Modal state
    const [isAddSiteOpen, setIsAddSiteOpen] = useState(false);
    const [newSite, setNewSite] = useState({ name: "", type: "Bureaux", address: "", postalCode: "", city: "", country: "France" });

    const isAdmin = currentTenant?.role === "ENERGY_MANAGER" || currentTenant?.role === "SUPER_ADMIN";

    const fetchSites = async () => {
        setLoading(true);
        try {
            const res = await authFetch("http://localhost:3001/api/sites");
            if (res.ok) {
                const data = await res.json();
                const processedSites = data.map((d: any) => ({
                    ...d,
                    zonesCount: d.zones ? d.zones.length : 0
                }));
                setSites(processedSites);
            }
        } catch (err) {
            console.error("Failed to fetch sites", err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateSite = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await authFetch("http://localhost:3001/api/sites", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(newSite)
            });
            if (res.ok) {
                setIsAddSiteOpen(false);
                setNewSite({ name: "", type: "Bureaux", address: "", postalCode: "", city: "", country: "France" });
                fetchSites();
            } else {
                alert("Erreur lors de la création du site.");
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        try {
            const text = await file.text();
            const lines = text.split('\n').map(l => l.trim()).filter(Boolean);

            // Expected CSV format: name,address,postalCode,city,type
            let successCount = 0;
            // Skip header if first line contains 'nom' or 'name'
            const startIndex = lines[0].toLowerCase().includes('nom') || lines[0].toLowerCase().includes('name') ? 1 : 0;

            for (let i = startIndex; i < lines.length; i++) {
                // Split by comma or semicolon
                const separator = lines[i].includes(';') ? ';' : ',';
                const row = lines[i].split(separator);
                if (row.length >= 4) {
                    const siteData = {
                        name: row[0].trim(),
                        address: row[1].trim(),
                        postalCode: row[2].trim(),
                        city: row[3].trim(),
                        type: row[4]?.trim() || 'Bureaux',
                        country: row[5]?.trim() || 'France',
                        status: 'active'
                    };

                    const res = await authFetch("http://localhost:3001/api/sites", {
                        method: 'POST',
                        body: JSON.stringify(siteData),
                        headers: { 'Content-Type': 'application/json' }
                    });

                    if (res.ok) successCount++;
                }
            }
            alert(`✅ Import terminé : ${successCount} sites créés avec succès !`);
            fetchSites();
        } catch (err) {
            console.error("Erreur lors de l'import :", err);
            alert("❌ Une erreur est survenue lors de l'import CSV.");
        } finally {
            setIsUploading(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    useEffect(() => {
        fetchSites();
    }, [authFetch, currentTenant?.id]);

    const filteredSites = sites.filter(site => {
        const matchName = (site.name || "").toLowerCase().includes(search.toLowerCase());
        const matchCity = (site.city || "").toLowerCase().includes(search.toLowerCase());
        const matchesSearch = matchName || matchCity;

        if (filterParam === 'out_of_target') {
            return matchesSearch && (site.statusColor === 'red' || site.statusColor === 'orange');
        }
        return matchesSearch;
    });

    const getStatusUI = (color: "green" | "orange" | "red" = "green") => {
        switch (color) {
            case 'red': return { text: "Hors Objectif (Critique)", classes: "text-red-500 dark:text-red-400", bg: "bg-red-500" };
            case 'orange': return { text: "Surveillance Requise", classes: "text-orange-500 dark:text-orange-400", bg: "bg-orange-500" };
            case 'green':
            default: return { text: "Optimal", classes: "text-emerald-500 dark:text-emerald-400", bg: "bg-emerald-500" };
        }
    };

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto pb-12 pt-4">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-slate-200 dark:border-white/5 pb-6">
                <div>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-white/60 bg-clip-text text-transparent mb-2 flex items-center">
                        <Building2 className="h-8 w-8 text-primary mr-3" />
                        Annuaire des Sites (Parc)
                    </h1>
                    <p className="text-slate-500 dark:text-muted-foreground font-medium">Consultez et recherchez parmi tous les bâtiments de votre infrastructure.</p>
                </div>

                {isAdmin && (
                    <div className="flex items-center gap-3">
                        {currentTenant?.id === '11111111-1111-1111-1111-111111111111' ? (
                            <div className="text-xs font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-white/5 px-4 py-2.5 rounded-xl border border-dashed border-slate-300 dark:border-white/20">
                                Pour créer un site, veuillez d'abord sélectionner un client spécifique.
                            </div>
                        ) : (
                            <>
                                <label className={`bg-slate-800 hover:bg-slate-700 text-white px-5 py-2.5 rounded-xl text-sm font-bold flex items-center transition-all cursor-pointer shadow-[0_0_15px_rgba(30,41,59,0.2)] hover:shadow-[0_0_20px_rgba(30,41,59,0.4)] ${isUploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                                    <Upload className="w-5 h-5 mr-2" />
                                    {isUploading ? "Importation..." : "Importer (CSV)"}
                                    <input
                                        type="file"
                                        accept=".csv"
                                        className="hidden"
                                        onChange={handleFileUpload}
                                        disabled={isUploading}
                                        ref={fileInputRef}
                                    />
                                </label>
                                <button onClick={() => setIsAddSiteOpen(true)} className="bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:shadow-[0_0_20px_rgba(16,185,129,0.5)] flex items-center transition-all">
                                    <Plus className="w-5 h-5 mr-2" />
                                    Créer un Site
                                </button>
                            </>
                        )}
                    </div>
                )}
            </div>

            {/* Sites Table */}
            <div className="glass-card rounded-2xl overflow-hidden border-slate-200 dark:border-white/5 shadow-sm">
                <div className="p-4 border-b border-slate-200 dark:border-white/5 flex items-center justify-between bg-white/[0.02]">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Liste des Bâtiments</h3>
                    <div className="flex items-center gap-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 dark:text-muted-foreground" />
                            <input
                                type="text"
                                placeholder="Rechercher (nom, ville)..."
                                value={search}
                                onChange={(e) => setSearch(e.target.value)}
                                className="bg-slate-100 dark:bg-black/40 border border-slate-200 dark:border-white/10 focus:border-primary/50 text-sm text-slate-900 dark:text-white rounded-lg pl-9 pr-4 py-2 outline-none w-48 sm:w-64 transition-all"
                            />
                        </div>
                        <button className="p-2 bg-slate-100 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-500 dark:text-muted-foreground hover:bg-slate-200 dark:hover:bg-white/5 transition-colors">
                            <Filter className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50/50 dark:bg-black/20 text-[11px] uppercase tracking-wider text-slate-500 dark:text-muted-foreground/80 border-b border-slate-200 dark:border-white/5">
                                <th className="px-6 py-4 font-semibold">Nom du Site</th>
                                <th className="px-6 py-4 font-semibold text-center">Type</th>
                                <th className="px-6 py-4 font-semibold text-center">Localisation</th>
                                <th className="px-6 py-4 font-semibold text-center">Zones Actives</th>
                                <th className="px-6 py-4 font-semibold text-center">Statut</th>
                                <th className="px-6 py-4 font-semibold text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                            {loading ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500 dark:text-muted-foreground animate-pulse">
                                        Chargement des sites...
                                    </td>
                                </tr>
                            ) : filteredSites.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500 dark:text-muted-foreground">
                                        Aucun site ne correspond à votre recherche.
                                    </td>
                                </tr>
                            ) : (
                                filteredSites.map((site) => (
                                    <tr key={site.id} className="bg-white/50 dark:bg-transparent hover:bg-slate-50 dark:hover:bg-white/[0.02] transition-colors group">
                                        <td className="px-6 py-4">
                                            <div className="flex items-center">
                                                <div className="h-10 w-10 rounded-lg bg-slate-100 dark:bg-slate-900 flex items-center justify-center border border-slate-200 dark:border-white/10 mr-4 group-hover:border-primary/40 transition-colors">
                                                    <Building className="h-5 w-5 text-slate-500 dark:text-muted-foreground group-hover:text-primary transition-colors" />
                                                </div>
                                                <div>
                                                    <p className="font-bold text-slate-900 dark:text-white text-sm">{site.name}</p>
                                                    <p className="text-[10px] uppercase text-slate-500 dark:text-muted-foreground mt-0.5 tracking-widest">{site.organization?.name ? `Client : ${site.organization.name}` : "Client non défini"}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-white/10">
                                                {site.type || "Bureaux"}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-center flex justify-center items-center">
                                            <MapPin className="h-4 w-4 text-slate-400 mr-2" />
                                            <span className="font-bold text-slate-900 dark:text-white">{site.postalCode ? `${site.postalCode} ` : ''}{site.city}</span>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="flex items-center justify-center">
                                                <Activity className="h-4 w-4 text-emerald-400 mr-2" />
                                                <span className="font-bold text-slate-900 dark:text-white">{site.zonesCount}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {(() => {
                                                const ui = getStatusUI(site.statusColor);
                                                return (
                                                    <span className={`inline-flex items-center justify-center text-[10px] font-bold uppercase tracking-widest ${ui.classes}`}>
                                                        <span className={`w-1.5 h-1.5 rounded-full ${ui.bg} mr-1.5 ${site.statusColor !== 'green' ? 'animate-pulse' : ''}`}></span>
                                                        {ui.text}
                                                    </span>
                                                )
                                            })()}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <a href={`/sites/${site.id}`} className="px-4 py-2 text-xs font-bold text-slate-900 dark:text-white bg-primary hover:bg-emerald-400 rounded-lg transition-colors shadow-sm inline-block">
                                                Accéder au site
                                            </a>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal: Add Site */}
            {
                isAddSiteOpen && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm px-4">
                        <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                            <button onClick={() => setIsAddSiteOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white">
                                <Plus className="h-5 w-5 rotate-45" />
                            </button>
                            <h2 className="text-xl font-bold mb-6 text-slate-900 dark:text-white flex items-center">
                                <Plus className="w-5 h-5 mr-2 text-primary" />
                                Créer un Nouveau Site
                            </h2>
                            <form onSubmit={handleCreateSite} className="space-y-4">
                                <div>
                                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Nom du bâtiment *</label>
                                    <input type="text" required value={newSite.name} onChange={e => setNewSite({ ...newSite, name: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors" placeholder="Ex: Tour Alpha" />
                                </div>

                                <div>
                                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Type de bâtiment *</label>
                                    <select value={newSite.type} onChange={e => setNewSite({ ...newSite, type: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors">
                                        <option value="Bureaux">Bureaux / Tertiaire</option>
                                        <option value="Magasin">Magasin / Retail</option>
                                        <option value="Usine">Usine / Industriel</option>
                                        <option value="Logistique">Logistique / Entrepôt</option>
                                    </select>
                                </div>

                                <div className="bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-200 dark:border-white/10 mt-4">
                                    <label className="text-sm font-bold text-slate-900 dark:text-white mb-2 block">Localisation</label>
                                    <div className="space-y-3">
                                        <div>
                                            <label className="text-xs text-slate-500 dark:text-slate-400">Adresse</label>
                                            <input type="text" value={newSite.address} onChange={e => setNewSite({ ...newSite, address: e.target.value })} className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors" />
                                        </div>
                                        <div className="grid grid-cols-2 gap-4">
                                            <div>
                                                <label className="text-xs text-slate-500 dark:text-slate-400">Code postal</label>
                                                <input type="text" value={newSite.postalCode} onChange={e => setNewSite({ ...newSite, postalCode: e.target.value })} className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors" placeholder="ex: 75000" />
                                            </div>
                                            <div>
                                                <label className="text-xs text-slate-500 dark:text-slate-400">Ville *</label>
                                                <input type="text" required value={newSite.city} onChange={e => setNewSite({ ...newSite, city: e.target.value })} className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors" />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="text-xs text-slate-500 dark:text-slate-400">Pays</label>
                                            <input type="text" value={newSite.country} onChange={e => setNewSite({ ...newSite, country: e.target.value })} className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:outline-none focus:border-primary/50 transition-colors" />
                                        </div>
                                    </div>
                                </div>

                                <button type="submit" className="w-full py-3 mt-6 bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                                    Créer le Site
                                </button>
                            </form>
                        </div>
                    </div>
                )
            }
        </div >
    );
}

