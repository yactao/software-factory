"use client";

import { useState, useEffect } from "react";
import { Building2, Search, Plus, Filter, MoreVertical, Briefcase, Activity, Target, Shield, MapPin, Signal } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTenant } from "@/lib/TenantContext";
import { useRouter } from "next/navigation";

export default function ClientsPage() {
    const { authFetch, currentTenant } = useTenant();
    const router = useRouter();
    const [organizations, setOrganizations] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    // Add Client Modal
    const [isAddClientOpen, setIsAddClientOpen] = useState(false);
    const [newClient, setNewClient] = useState({
        name: "",
        type: "Corporate",
        country: "France",
        contactFirstName: "",
        contactLastName: "",
        city: "",
        address: "",
        postalCode: "",
        phone: "",
        email: "",
        establishmentDate: "",
        legalForm: "SAS"
    });

    // Edit Client Modal
    const [isEditClientOpen, setIsEditClientOpen] = useState(false);
    const [editClient, setEditClient] = useState<any>(null);

    // Delete Client Modal
    const [isDeleteClientOpen, setIsDeleteClientOpen] = useState(false);
    const [clientToDelete, setClientToDelete] = useState<any>(null);

    const fetchOrganizations = async () => {
        setLoading(true);
        try {
            const res = await authFetch("http://localhost:3001/api/organizations");
            if (res.ok) {
                const data = await res.json();
                if (currentTenant?.id && currentTenant.id !== '11111111-1111-1111-1111-111111111111') {
                    setOrganizations(data.filter((org: any) => org.id === currentTenant.id));
                } else {
                    setOrganizations(data);
                }
            }
        } catch (err) {
            console.error("Failed to fetch clients", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchOrganizations();
    }, [authFetch]);

    const handleCreateClient = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await authFetch("http://localhost:3001/api/organizations", {
                method: "POST",
                body: JSON.stringify(newClient)
            });
            if (res.ok) {
                setIsAddClientOpen(false);
                setNewClient({ name: "", type: "Corporate", country: "France", contactFirstName: "", contactLastName: "", city: "", postalCode: "", address: "", phone: "", email: "", establishmentDate: "", legalForm: "SAS" });
                await fetchOrganizations();
                window.dispatchEvent(new Event("clients_updated"));
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleUpdateClient = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!editClient) return;
        try {
            const { name, type, country, contactFirstName, contactLastName, city, address, postalCode, phone, email, establishmentDate, legalForm } = editClient;
            const res = await authFetch(`http://localhost:3001/api/organizations/${editClient.id}`, {
                method: "PUT",
                body: JSON.stringify({ name, type, country, contactFirstName, contactLastName, city, address, postalCode, phone, email, establishmentDate, legalForm })
            });
            if (res.ok) {
                setIsEditClientOpen(false);
                setEditClient(null);
                await fetchOrganizations();
                window.dispatchEvent(new Event("clients_updated"));
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleDeleteClient = async () => {
        if (!clientToDelete) return;
        try {
            const res = await authFetch(`http://localhost:3001/api/organizations/${clientToDelete.id}`, {
                method: "DELETE"
            });
            if (res.ok) {
                setIsDeleteClientOpen(false);
                setClientToDelete(null);
                await fetchOrganizations();
                window.dispatchEvent(new Event("clients_updated"));
            }
        } catch (e) {
            console.error(e);
        }
    };

    if (currentTenant?.role === "CLIENT") {
        return <div className="p-8 text-slate-500">Accès non autorisé.</div>;
    }

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto pb-12 pt-4">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 border-b border-slate-200 dark:border-white/5 pb-6">
                <div>
                    <h2 className="text-xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-white/60 bg-clip-text text-transparent mb-1">
                        Gestion de Parc (Clients)
                    </h2>
                    <p className="text-slate-500 dark:text-muted-foreground text-sm font-medium">
                        Gérez vos clients et accédez à leurs infrastructures.
                    </p>
                </div>

                <div className="flex items-center gap-3">
                    <button onClick={() => router.push('/sites')} className="bg-slate-100 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10 text-slate-900 dark:text-white px-5 py-2.5 rounded-xl text-sm font-bold flex items-center transition-all">
                        <Building2 className="w-5 h-5 mr-2" />
                        Voir tous les sites
                    </button>
                    <button onClick={() => setIsAddClientOpen(true)} className="bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white px-5 py-2.5 rounded-xl text-sm font-bold shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:shadow-[0_0_20px_rgba(16,185,129,0.5)] flex items-center transition-all">
                        <Plus className="w-5 h-5 mr-2" />
                        Nouveau Client
                    </button>
                </div>
            </div>

            {/* Quick KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="glass-card p-6 rounded-2xl border-slate-200 dark:border-white/5">
                    <div className="flex items-center gap-4">
                        <div className="h-12 w-12 rounded-xl bg-primary/20 flex items-center justify-center border border-primary/30">
                            <Briefcase className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500 dark:text-muted-foreground font-medium uppercase tracking-wider">Total Clients</p>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">{organizations.length}</h3>
                        </div>
                    </div>
                </div>

                <div className="glass-card p-6 rounded-2xl border-slate-200 dark:border-white/5">
                    <div className="flex items-center gap-4">
                        <div className="h-12 w-12 rounded-xl bg-cyan-500/20 flex items-center justify-center border border-cyan-500/30">
                            <Building2 className="h-6 w-6 text-cyan-500" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500 dark:text-muted-foreground font-medium uppercase tracking-wider">Sites Déployés</p>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
                                {organizations.reduce((acc, org) => acc + (org.sitesCount || 0), 0)}
                            </h3>
                        </div>
                    </div>
                </div>

                <div className="glass-card p-6 rounded-2xl border-slate-200 dark:border-white/5">
                    <div className="flex items-center gap-4">
                        <div className="h-12 w-12 rounded-xl bg-amber-500/20 flex items-center justify-center border border-amber-500/30">
                            <Signal className="h-6 w-6 text-amber-500" />
                        </div>
                        <div>
                            <p className="text-sm text-slate-500 dark:text-muted-foreground font-medium uppercase tracking-wider">Ubots (Gateways)</p>
                            <h3 className="text-2xl font-bold text-slate-900 dark:text-white">
                                {organizations.reduce((acc, org) => acc + (org.gatewaysCount || 0), 0)}
                            </h3>
                        </div>
                    </div>
                </div>
            </div>

            {/* Organizations Table */}
            <div className="glass-card rounded-2xl overflow-visible border-slate-200 dark:border-white/5 shadow-sm">
                <div className="p-4 border-b border-slate-200 dark:border-white/5 flex items-center justify-between bg-white/[0.02] rounded-t-2xl">
                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Liste des Clients</h3>
                    <div className="flex items-center gap-2">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 dark:text-muted-foreground" />
                            <input
                                type="text"
                                placeholder="Rechercher..."
                                className="bg-slate-100 dark:bg-black/40 border border-slate-200 dark:border-white/10 focus:border-primary/50 text-sm text-slate-900 dark:text-white rounded-lg pl-9 pr-4 py-2 outline-none w-48 sm:w-64 transition-all"
                            />
                        </div>
                        <button className="p-2 bg-slate-100 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-500 dark:text-muted-foreground hover:bg-slate-200 dark:hover:bg-white/5 transition-colors">
                            <Filter className="h-4 w-4" />
                        </button>
                    </div>
                </div>

                <div className="overflow-visible min-h-[300px]">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-slate-50/50 dark:bg-black/20 text-[11px] uppercase tracking-wider text-slate-500 dark:text-muted-foreground/80 border-b border-slate-200 dark:border-white/5">
                                <th className="px-6 py-4 font-semibold">Nom de l'Organisation</th>
                                <th className="px-6 py-4 font-semibold text-center">Type</th>
                                <th className="px-6 py-4 font-semibold text-center">Établissements (Sites)</th>
                                <th className="px-6 py-4 font-semibold text-center">Ubots (Gateways)</th>
                                <th className="px-6 py-4 font-semibold text-center">Statut Licence</th>
                                <th className="px-6 py-4 font-semibold text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-white/5">
                            {loading ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500 dark:text-muted-foreground">
                                        Chargement des clients B2B...
                                    </td>
                                </tr>
                            ) : organizations.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500 dark:text-muted-foreground">
                                        Aucune organisation cliente trouvée.
                                    </td>
                                </tr>
                            ) : (
                                organizations.map((org) => (
                                    <tr key={org.id} className="bg-white/50 dark:bg-transparent hover:bg-slate-50 dark:hover:bg-white/[0.02] transition-colors group">
                                        <td className="px-6 py-4 cursor-pointer" onClick={() => window.location.href = `/clients/${org.id}`}>
                                            <div className="flex items-center">
                                                <div className="h-10 w-10 rounded-lg bg-slate-100 dark:bg-slate-900 flex items-center justify-center border border-slate-200 dark:border-white/10 mr-4 group-hover:border-primary/40 group-hover:bg-primary/5 transition-colors">
                                                    {org.name === "UBBEE" ? (
                                                        <Shield className="h-5 w-5 text-primary" />
                                                    ) : (
                                                        <Briefcase className="h-5 w-5 text-slate-500 dark:text-muted-foreground group-hover:text-primary transition-colors" />
                                                    )}
                                                </div>
                                                <div>
                                                    <p className="font-bold text-slate-900 dark:text-white text-sm group-hover:text-primary transition-colors">{org.name}</p>
                                                    <p className="text-xs text-slate-500 dark:text-muted-foreground mt-0.5">{(org.gatewaysCount || 0) > 0 ? "Actif" : "En configuration"}</p>
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <span className="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-white/10">
                                                {org.type || "Corporate"}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="flex items-center justify-center">
                                                <MapPin className="h-4 w-4 text-slate-400 dark:text-muted-foreground mr-1.5" />
                                                <span className="font-bold text-slate-900 dark:text-white">{org.sitesCount}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            <div className="flex items-center justify-center">
                                                <Signal className="h-4 w-4 text-slate-400 dark:text-muted-foreground mr-1.5" />
                                                <span className="font-bold text-slate-900 dark:text-white">{org.gatewaysCount || 0}</span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 text-center">
                                            {org.name === "UBBEE" ? (
                                                <span className="text-[11px] font-bold text-primary flex justify-center items-center">SUPER_ADMIN</span>
                                            ) : (
                                                <span className="inline-flex items-center justify-center text-[10px] font-bold uppercase tracking-widest text-emerald-500 dark:text-emerald-400">
                                                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mr-1.5 animate-pulse"></span>
                                                    Actif
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-right">
                                            <div className="flex justify-end relative group/menu">
                                                <button className="p-2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/10 rounded-lg transition-colors focus:ring-0">
                                                    <MoreVertical className="h-5 w-5" />
                                                </button>
                                                {/* Menu Action (visible on focus/hover within group) */}
                                                <div className="absolute right-0 top-full mt-1 w-36 bg-white dark:bg-slate-800 rounded-xl shadow-xl border border-slate-200 dark:border-white/10 opacity-0 invisible group-focus-within/menu:opacity-100 group-focus-within/menu:visible group-hover/menu:opacity-100 group-hover/menu:visible transition-all z-20 overflow-hidden">
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); setEditClient({ ...org }); setIsEditClientOpen(true); }}
                                                        className="w-full text-left px-4 py-2.5 text-xs font-bold text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-white/5 transition-colors border-b border-slate-100 dark:border-white/5"
                                                    >
                                                        Modifier
                                                    </button>
                                                    <button
                                                        onClick={(e) => { e.stopPropagation(); setClientToDelete(org); setIsDeleteClientOpen(true); }}
                                                        className="w-full text-left px-4 py-2.5 text-xs font-bold text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors"
                                                    >
                                                        Supprimer
                                                    </button>
                                                </div>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal: Add Client */}
            {isAddClientOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                        <button onClick={() => setIsAddClientOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"><Activity className="h-5 w-5 rotate-45" /></button>
                        <h2 className="text-xl font-bold mb-6 text-slate-900 dark:text-white flex items-center">
                            <Plus className="h-5 w-5 mr-2 text-primary" />
                            Créer un Client
                        </h2>
                        <form onSubmit={handleCreateClient} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
                            {/* Identité */}
                            <div className="bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-200 dark:border-white/10 space-y-4">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2">Identité de l'entreprise</h3>
                                <div>
                                    <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Raison sociale *</label>
                                    <input
                                        type="text"
                                        required
                                        value={newClient.name}
                                        onChange={e => setNewClient({ ...newClient, name: e.target.value })}
                                        className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        placeholder="ex: Décathlon France"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Forme Juridique *</label>
                                        <select
                                            required
                                            value={newClient.legalForm}
                                            onChange={e => setNewClient({ ...newClient, legalForm: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        >
                                            <option value="SAS">SAS</option>
                                            <option value="SARL">SARL</option>
                                            <option value="SA">SA</option>
                                            <option value="EURL">EURL</option>
                                            <option value="Auto-entreprise">Auto-entreprise</option>
                                            <option value="Autre">Autre</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Date de création *</label>
                                        <input
                                            type="date"
                                            required
                                            value={newClient.establishmentDate}
                                            onChange={e => setNewClient({ ...newClient, establishmentDate: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Secteur d'Activité / Type *</label>
                                    <select
                                        required
                                        value={newClient.type}
                                        onChange={e => setNewClient({ ...newClient, type: e.target.value })}
                                        className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                    >
                                        <option value="Retail">Retail & Distribution</option>
                                        <option value="Corporate">Bureaux (Corporate)</option>
                                        <option value="Industrial">Usine / Logistique</option>
                                        <option value="Hospitality">Hôtellerie / Santé</option>
                                    </select>
                                </div>
                            </div>

                            {/* Coordonnées */}
                            <div className="bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-200 dark:border-white/10 space-y-4">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2">Coordonnées</h3>
                                <div>
                                    <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Adresse professionnelle *</label>
                                    <input
                                        type="text"
                                        required
                                        value={newClient.address}
                                        onChange={e => setNewClient({ ...newClient, address: e.target.value })}
                                        className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        placeholder="ex: 12 Rue de la Paix"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Ville</label>
                                        <input
                                            type="text"
                                            value={newClient.city}
                                            onChange={e => setNewClient({ ...newClient, city: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                            placeholder="ex: Paris"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Code postal *</label>
                                        <input
                                            type="text"
                                            required
                                            value={newClient.postalCode}
                                            onChange={e => setNewClient({ ...newClient, postalCode: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                            placeholder="ex: 75000"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Pays</label>
                                        <input
                                            type="text"
                                            value={newClient.country}
                                            onChange={e => setNewClient({ ...newClient, country: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                            placeholder="ex: France"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Prénom du contact *</label>
                                        <input
                                            type="text"
                                            required
                                            value={newClient.contactFirstName}
                                            onChange={e => setNewClient({ ...newClient, contactFirstName: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                            placeholder="ex: Jean"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Nom du contact *</label>
                                        <input
                                            type="text"
                                            required
                                            value={newClient.contactLastName}
                                            onChange={e => setNewClient({ ...newClient, contactLastName: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                            placeholder="ex: Dupont"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Téléphone *</label>
                                        <input
                                            type="tel"
                                            required
                                            value={newClient.phone}
                                            onChange={e => setNewClient({ ...newClient, phone: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                            placeholder="+33 1 23 45 67 89"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Adresse e-mail</label>
                                        <input
                                            type="email"
                                            value={newClient.email}
                                            onChange={e => setNewClient({ ...newClient, email: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                            placeholder="contact@entreprise.fr"
                                        />
                                    </div>
                                </div>
                            </div>


                            <button type="submit" className="w-full py-3 mt-4 bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                                Créer le Client
                            </button>
                            <button type="button" onClick={() => setIsAddClientOpen(false)} className="w-full py-3 mt-2 bg-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-white font-bold rounded-xl transition-all">
                                Annuler
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal: Edit Client */}
            {isEditClientOpen && editClient && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                        <button onClick={() => setIsEditClientOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"><Activity className="h-5 w-5 rotate-45" /></button>
                        <h2 className="text-xl font-bold mb-6 text-slate-900 dark:text-white flex items-center">
                            <Briefcase className="h-5 w-5 mr-2 text-primary" />
                            Modifier le Client
                        </h2>
                        <form onSubmit={handleUpdateClient} className="space-y-4 max-h-[70vh] overflow-y-auto pr-2 custom-scrollbar">
                            <div className="bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-200 dark:border-white/10 space-y-4">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2">Identité de l'entreprise</h3>
                                <div>
                                    <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Raison sociale *</label>
                                    <input
                                        type="text"
                                        required
                                        value={editClient.name}
                                        onChange={e => setEditClient({ ...editClient, name: e.target.value })}
                                        className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Forme Juridique</label>
                                        <select
                                            value={editClient.legalForm || "SAS"}
                                            onChange={e => setEditClient({ ...editClient, legalForm: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        >
                                            <option value="SAS">SAS</option>
                                            <option value="SARL">SARL</option>
                                            <option value="SA">SA</option>
                                            <option value="EURL">EURL</option>
                                            <option value="Auto-entreprise">Auto-entreprise</option>
                                            <option value="Autre">Autre</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Date de création</label>
                                        <input
                                            type="date"
                                            value={editClient.establishmentDate || ""}
                                            onChange={e => setEditClient({ ...editClient, establishmentDate: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                </div>
                                <div>
                                    <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Secteur d'Activité / Type</label>
                                    <select
                                        value={editClient.type || "Corporate"}
                                        onChange={e => setEditClient({ ...editClient, type: e.target.value })}
                                        className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                    >
                                        <option value="Retail">Retail & Distribution</option>
                                        <option value="Corporate">Bureaux (Corporate)</option>
                                        <option value="Industrial">Usine / Logistique</option>
                                        <option value="Hospitality">Hôtellerie / Santé</option>
                                    </select>
                                </div>
                            </div>

                            <div className="bg-slate-50 dark:bg-white/5 p-4 rounded-xl border border-slate-200 dark:border-white/10 space-y-4">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-2">Coordonnées</h3>
                                <div>
                                    <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Adresse professionnelle</label>
                                    <input
                                        type="text"
                                        value={editClient.address || ""}
                                        onChange={e => setEditClient({ ...editClient, address: e.target.value })}
                                        className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                    />
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Ville</label>
                                        <input
                                            type="text"
                                            value={editClient.city || ""}
                                            onChange={e => setEditClient({ ...editClient, city: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Code postal</label>
                                        <input
                                            type="text"
                                            value={editClient.postalCode || ""}
                                            onChange={e => setEditClient({ ...editClient, postalCode: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Pays</label>
                                        <input
                                            type="text"
                                            value={editClient.country || ""}
                                            onChange={e => setEditClient({ ...editClient, country: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Prénom du contact</label>
                                        <input
                                            type="text"
                                            value={editClient.contactFirstName || ""}
                                            onChange={e => setEditClient({ ...editClient, contactFirstName: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Nom du contact</label>
                                        <input
                                            type="text"
                                            value={editClient.contactLastName || ""}
                                            onChange={e => setEditClient({ ...editClient, contactLastName: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Téléphone</label>
                                        <input
                                            type="tel"
                                            value={editClient.phone || ""}
                                            onChange={e => setEditClient({ ...editClient, phone: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-slate-500 dark:text-slate-400">Adresse e-mail</label>
                                        <input
                                            type="email"
                                            value={editClient.email || ""}
                                            onChange={e => setEditClient({ ...editClient, email: e.target.value })}
                                            className="w-full p-2.5 mt-1 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white font-medium focus:ring-1 focus:ring-primary outline-none transition-all"
                                        />
                                    </div>
                                </div>
                            </div>

                            <button type="submit" className="w-full py-3 mt-4 bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]">
                                Sauvegarder
                            </button>
                            <button type="button" onClick={() => setIsEditClientOpen(false)} className="w-full py-3 mt-2 bg-transparent text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-white font-bold rounded-xl transition-all">
                                Annuler
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal: Delete Client Confirmation */}
            {isDeleteClientOpen && clientToDelete && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-sm bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                        <button onClick={() => setIsDeleteClientOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"><Activity className="h-5 w-5 rotate-45" /></button>
                        <div className="flex flex-col items-center text-center">
                            <div className="w-16 h-16 bg-red-500/20 text-red-500 rounded-full flex items-center justify-center mb-4">
                                <Target className="w-8 h-8" />
                            </div>
                            <h2 className="text-xl font-bold mb-2 text-slate-900 dark:text-white">
                                Supprimer le client ?
                            </h2>
                            <p className="text-slate-500 dark:text-muted-foreground text-sm mb-6">
                                Êtes-vous sûr de vouloir supprimer définitivement <strong>{clientToDelete.name}</strong> ? Cette action supprimera également tous ses sites, zones et utilisateurs associés.
                            </p>
                            <div className="flex gap-3 w-full">
                                <button onClick={() => setIsDeleteClientOpen(false)} className="flex-1 py-2.5 bg-slate-100 dark:bg-white/5 hover:bg-slate-200 dark:hover:bg-white/10 text-slate-900 dark:text-white font-bold rounded-xl transition-all">
                                    Annuler
                                </button>
                                <button onClick={handleDeleteClient} className="flex-1 py-2.5 bg-red-500 hover:bg-red-600 text-white font-bold rounded-xl shadow-[0_0_15px_rgba(239,68,68,0.4)] transition-all">
                                    Confirmer
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
