"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useTenant } from "@/lib/TenantContext";
import { Briefcase, Activity, Users, Settings, ArrowLeft, Building2, Plus, MapPin, Building, X, Mail, Shield, MoreVertical, Edit2, Trash2, CheckCircle2, Cpu, Eye, Lock } from "lucide-react";
import { BuildingModel } from "@/components/dashboard/BuildingModel";
import { cn } from "@/lib/utils";

export default function ClientDetailsPage() {
    const params = useParams();
    const router = useRouter();
    const { authFetch, currentTenant } = useTenant();
    const clientId = params.id as string;

    const [client, setClient] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState("infos");
    const [selectedTwinSiteId, setSelectedTwinSiteId] = useState<string>(""); // infos, dashboard, users

    // Add Site states
    const [isAddSiteOpen, setIsAddSiteOpen] = useState(false);
    const [newSite, setNewSite] = useState({ name: "", type: "Bureaux", address: "", postalCode: "", city: "", country: "" });
    const [isEditSiteOpen, setIsEditSiteOpen] = useState(false);
    const [editingSite, setEditingSite] = useState<any>({ id: "", name: "", type: "Bureaux", address: "", postalCode: "", city: "", country: "" });

    // Add User states
    const [usersList, setUsersList] = useState<any[]>([]);
    const [isAddUserOpen, setIsAddUserOpen] = useState(false);
    const [newUser, setNewUser] = useState({ name: "", email: "", role: "CLIENT", password: "password123" });
    const [menuOpenId, setMenuOpenId] = useState<string | null>(null);
    const [isEditUserOpen, setIsEditUserOpen] = useState(false);
    const [editingUser, setEditingUser] = useState({ id: "", name: "", email: "", role: "" });

    const isAdmin = currentTenant?.role === "ENERGY_MANAGER" || currentTenant?.role === "SUPER_ADMIN";

    const fetchClientDetails = async () => {
        try {
            const res = await authFetch(`http://localhost:3001/api/organizations`);
            if (res.ok) {
                const data = await res.json();
                const found = data.find((org: any) => org.id === clientId);
                setClient(found);
            }

            // Fetch associated users
            if (isAdmin) {
                const userRes = await authFetch(`http://localhost:3001/api/users?organizationId=${clientId}`);
                if (userRes.ok) {
                    const userData = await userRes.json();
                    setUsersList(userData);
                }
            }
        } catch (err) {
            console.error("Failed to fetch client details", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchClientDetails();
    }, [clientId, authFetch, isAdmin]);

    const handleCreateSite = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const payload = { ...newSite, organizationId: clientId };

            const res = await authFetch("http://localhost:3001/api/sites", {
                method: "POST",
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                setIsAddSiteOpen(false);
                setNewSite({ name: "", type: "Bureaux", address: "", postalCode: "", city: "", country: "" });
                await fetchClientDetails(); // Reload to get the new site
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleUpdateSite = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const { name, type, address, postalCode, city, country } = editingSite;
            const res = await authFetch(`http://localhost:3001/api/sites/${editingSite.id}`, {
                method: "PUT",
                body: JSON.stringify({ name, type, address, postalCode, city, country })
            });
            if (res.ok) {
                setIsEditSiteOpen(false);
                await fetchClientDetails();
            } else {
                console.error("Erreur serveur lors de la mise à jour");
                alert("Une erreur est survenue lors de la mise à jour du site.");
            }
        } catch (e) {
            console.error(e);
            alert("Erreur de connexion.");
        }
    };

    const handleDeleteSite = async (siteId: string, siteName: string) => {
        if (!confirm(`Voulez-vous vraiment supprimer le site "${siteName}" ?`)) return;
        try {
            const res = await authFetch(`http://localhost:3001/api/sites/${siteId}`, {
                method: "DELETE"
            });
            if (res.ok) {
                await fetchClientDetails();
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const payload = { ...newUser, organizationId: clientId };

            const res = await authFetch("http://localhost:3001/api/users", {
                method: "POST",
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                setIsAddUserOpen(false);
                setNewUser({ name: "", email: "", role: "CLIENT", password: "password123" });
                await fetchClientDetails(); // Reload to get the new user
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleUpdateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await authFetch(`http://localhost:3001/api/users/${editingUser.id}`, {
                method: "PUT",
                body: JSON.stringify({ name: editingUser.name, email: editingUser.email, role: editingUser.role })
            });
            if (res.ok) {
                setIsEditUserOpen(false);
                await fetchClientDetails();
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleDeleteUser = async (userId: string) => {
        if (!confirm("Voulez-vous vraiment supprimer cet utilisateur ?")) return;
        try {
            const res = await authFetch(`http://localhost:3001/api/users/${userId}`, {
                method: "DELETE"
            });
            if (res.ok) {
                setMenuOpenId(null);
                await fetchClientDetails();
            }
        } catch (e) {
            console.error(e);
        }
    };

    if (loading) return <div className="p-8 text-center text-slate-500">Chargement des données du client...</div>;
    if (!client) return <div className="p-8 text-center text-rose-500">Client introuvable.</div>;

    const tabs = [
        { id: "infos", title: "Informations & Sites", icon: Building2 },
        { id: "dashboard", title: "Tableau de Bord Client", icon: Activity },
        { id: "users", title: "Gestion Utilisateurs", icon: Users },
    ];

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto pb-12 pt-4">
            {/* Header / Breadcrumb */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 pb-6">
                <div>
                    <button
                        onClick={() => router.push('/clients')}
                        className="flex items-center text-xs font-bold text-slate-500 hover:text-primary mb-3 transition-colors uppercase tracking-wider"
                    >
                        <ArrowLeft className="w-3 h-3 mr-1" /> Retour à la liste
                    </button>
                    <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-white/60 bg-clip-text text-transparent flex items-center">
                        <Briefcase className="h-8 w-8 text-primary mr-3" />
                        {client.name}
                    </h1>
                    <p className="text-sm font-medium text-slate-500 dark:text-muted-foreground mt-1">
                        Secteur : {client.type} | ID : {client.id.split('-')[0]}
                    </p>
                </div>
            </div>

            {/* Custom Tabs Navigation */}
            <div className="flex space-x-2 border-b border-slate-200 dark:border-white/10 pb-0 overflow-x-auto custom-scrollbar">
                {tabs.map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`flex items-center px-5 py-3 text-sm font-bold transition-all border-b-2 whitespace-nowrap ${activeTab === tab.id
                            ? "border-primary text-primary"
                            : "border-transparent text-slate-500 dark:text-muted-foreground hover:text-slate-900 dark:hover:text-white"
                            }`}
                    >
                        <tab.icon className="w-4 h-4 mr-2" />
                        {tab.title}
                    </button>
                ))}
            </div>

            {/* Main Content Area based on activeTab */}
            <div className="pt-4">

                {/* 1. INFORMATIONS & SITES */}
                {activeTab === "infos" && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Details Card */}
                        <div className="lg:col-span-1 glass-card p-6 rounded-2xl border-slate-200 dark:border-white/5 space-y-4">
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white border-b border-slate-100 dark:border-white/10 pb-2">Coordonnées</h3>
                            <div>
                                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Adresse</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-300">{client.address || "Non renseignée"}</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-300">{client.city}, {client.country}</p>
                            </div>
                            <div>
                                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Contact</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-300">{client.phone || "N/A"}</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-300">{client.email || "N/A"}</p>
                            </div>
                            <div>
                                <p className="text-[10px] text-slate-500 uppercase tracking-widest font-bold">Informations légales</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-300">Forme juridique: {client.legalForm || "N/A"}</p>
                                <p className="text-sm font-medium text-slate-900 dark:text-slate-300">Date création: {client.establishmentDate || "N/A"}</p>
                            </div>

                            {/* Image du Bâtiment / Logo */}
                            <div className="mt-8 rounded-xl overflow-hidden border border-slate-200 dark:border-white/10 relative h-48 group">
                                <img
                                    src="https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?auto=format&fit=crop&q=80&w=800"
                                    alt="Siège"
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                                />
                                <div className="absolute inset-0 bg-gradient-to-t from-slate-900/60 to-transparent flex items-end p-4">
                                    <span className="text-white text-xs font-bold uppercase tracking-wider">Aperçu du Siège</span>
                                </div>
                            </div>
                        </div>

                        {/* Sites & Synoptique */}
                        <div className="lg:col-span-2 space-y-6">
                            {/* Sites List Summary */}
                            <div className="glass-card p-6 rounded-2xl border-slate-200 dark:border-white/5">
                                <div className="flex justify-between items-center mb-4">
                                    <h3 className="text-lg font-bold text-slate-900 dark:text-white">Sites rattachés (Gestion Parc)</h3>
                                    {isAdmin && (
                                        <button onClick={() => { setNewSite({ ...newSite, country: client?.country || "France" }); setIsAddSiteOpen(true); }} className="px-3 py-1.5 bg-primary/10 hover:bg-primary/20 text-primary rounded-lg text-xs font-bold transition-all flex items-center">
                                            <Plus className="h-3 w-3 mr-1" />
                                            Nouveau Site
                                        </button>
                                    )}
                                </div>

                                {client.sites && client.sites.length > 0 ? (
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4 max-h-[220px] overflow-y-auto custom-scrollbar pr-2">
                                        {client.sites.map((site: any) => (
                                            <div key={site.id}
                                                onClick={() => router.push(`/sites/${site.id}`)}
                                                className="p-3 bg-slate-50 dark:bg-black/20 hover:bg-slate-100 dark:hover:bg-white/5 border border-slate-200 dark:border-white/10 rounded-xl cursor-pointer transition-colors group">
                                                <div className="flex justify-between items-start mb-2">
                                                    <h4 className="font-bold text-slate-900 dark:text-white group-hover:text-primary transition-colors text-sm flex items-center">
                                                        <Building className="h-3 w-3 mr-1.5" />
                                                        {site.name}
                                                    </h4>
                                                    <div className="flex items-center space-x-2">
                                                        <span className="text-[9px] uppercase tracking-widest bg-emerald-500/10 text-emerald-500 px-1.5 py-0.5 rounded">Actif</span>
                                                        {isAdmin && (
                                                            <div className="flex space-x-1" onClick={(e) => e.stopPropagation()}>
                                                                <button onClick={() => { setEditingSite(site); setIsEditSiteOpen(true); }} className="text-slate-400 hover:text-slate-900 dark:hover:text-white p-1 rounded hover:bg-slate-200 dark:hover:bg-white/10 transition-colors">
                                                                    <Edit2 className="h-3 w-3" />
                                                                </button>
                                                                <button onClick={() => handleDeleteSite(site.id, site.name)} className="text-rose-400 hover:text-rose-600 p-1 rounded hover:bg-rose-50 dark:hover:bg-rose-500/10 transition-colors">
                                                                    <Trash2 className="h-3 w-3" />
                                                                </button>
                                                            </div>
                                                        )}
                                                    </div>
                                                </div>
                                                <p className="text-xs text-slate-500 flex items-center"><MapPin className="h-3 w-3 mr-1" /> {site.postalCode ? `${site.postalCode} ` : ''}{site.city}</p>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="text-sm text-slate-500 mb-4 p-4 border border-dashed border-slate-200 dark:border-white/10 rounded-xl">
                                        Aucun site n'est encore configuré pour ce client.
                                    </p>
                                )}
                            </div>

                            {/* Jumeau Numérique / Synoptique */}
                            <div className="glass-card p-5 rounded-2xl flex flex-col items-center justify-center border-slate-200 dark:border-white/5 relative h-[450px]">
                                <div className="w-full absolute top-5 left-5 z-10 pointer-events-none">
                                    <h3 className="text-base font-bold text-slate-900 dark:text-white pointer-events-auto">Jumeau Numérique (Synoptique Local)</h3>
                                    <p className="text-xs text-slate-500 mt-1 pointer-events-auto">Aperçu 3D interactif et supervision en temps réel.</p>
                                </div>

                                {client.sites && client.sites.length > 0 && (
                                    <select
                                        className="absolute top-5 right-5 z-20 bg-white/80 dark:bg-black/80 backdrop-blur-md border border-slate-200 dark:border-white/10 text-slate-900 dark:text-white text-xs font-bold rounded-xl px-4 py-2 outline-none shadow-lg cursor-pointer hover:border-primary/50 transition-colors"
                                        value={selectedTwinSiteId || (client.sites[0]?.id || '')}
                                        onChange={(e) => setSelectedTwinSiteId(e.target.value)}
                                    >
                                        {client.sites.map((site: any) => (
                                            <option key={site.id} value={site.id}>{site.name} ({site.city})</option>
                                        ))}
                                    </select>
                                )}

                                <div className="w-full h-full pointer-events-auto pt-7">
                                    {client.sites && client.sites.length > 0 ? (
                                        (() => {
                                            const activeTwinSite = client.sites.find((s: any) => s.id === selectedTwinSiteId) || client.sites[0];
                                            const isProjetY = client.name.toLowerCase().includes("projet y") || activeTwinSite?.name?.toLowerCase().includes("projet y");
                                            const forceMockData = !isProjetY || client.gatewaysCount > 0 || (activeTwinSite?.gateways?.length ?? 0) > 0 || activeTwinSite?.zones?.some((z: any) => (z.sensors?.length ?? 0) > 0) || false;
                                            return <BuildingModel siteName={activeTwinSite?.name || "Bâtiment"} zones={activeTwinSite?.zones || []} forceMockData={forceMockData} />;
                                        })()
                                    ) : (
                                        <div className="flex items-center justify-center h-full w-full bg-slate-50 dark:bg-black/20 rounded-xl border border-dashed border-slate-200 dark:border-white/10 mt-6">
                                            <p className="text-slate-500 font-medium">Bâtiment non modélisé. Configurez un premier site.</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* 2. TABLEAU DE BORD CLIENT */}
                {activeTab === "dashboard" && (
                    <div className="glass-card p-12 text-center rounded-2xl border-slate-200 dark:border-white/5">
                        <Activity className="w-12 h-12 text-slate-300 dark:text-slate-700 mx-auto mb-4" />
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Tableau de Bord Consolidé</h3>
                        <p className="text-sm text-slate-500 max-w-lg mx-auto">
                            Cette section regroupera les KPIS consolidés de tous les sites du client {client.name} (consommation totale, alertes cumulées, etc.).
                        </p>
                    </div>
                )}

                {/* 3. GESTION UTILISATEURS */}
                {activeTab === "users" && (
                    <div className="bg-white dark:bg-white/5 border border-slate-200 dark:border-white/10 rounded-3xl overflow-hidden shadow-xl shadow-slate-200/50 dark:shadow-none min-h-[400px]">
                        <div className="flex justify-between items-center p-6 border-b border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-slate-900/50">
                            <div>
                                <h3 className="text-xl font-black text-slate-900 dark:text-white flex items-center">
                                    <Users className="w-5 h-5 mr-3 text-primary" />
                                    Gestion des Utilisateurs
                                </h3>
                                <p className="text-sm text-slate-500 mt-1 font-medium ml-8">Supervisez les accès ({client.name})</p>
                            </div>
                            {isAdmin && (
                                <button onClick={() => setIsAddUserOpen(true)} className="flex items-center gap-2 bg-primary/10 hover:bg-primary/20 text-primary dark:bg-emerald-500/10 dark:text-emerald-400 dark:hover:bg-emerald-500/20 px-4 py-2 rounded-xl font-bold text-sm transition-colors border border-primary/20">
                                    <Mail className="w-4 h-4" /> Inviter
                                </button>
                            )}
                        </div>

                        {usersList.length > 0 ? (
                            <div className="overflow-x-auto">
                                <table className="w-full text-left">
                                    <thead className="bg-slate-50 dark:bg-slate-900/50 text-slate-500 text-xs uppercase tracking-wider font-bold">
                                        <tr>
                                            <th className="px-6 py-4">Collaborateur</th>
                                            <th className="px-6 py-4">Rôle</th>
                                            <th className="px-6 py-4">Statut</th>
                                            <th className="px-6 py-4 text-right">Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-200 dark:divide-white/5">
                                        {usersList.map((user: any) => (
                                            <tr key={user.id} className="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors group">
                                                <td className="px-6 py-4">
                                                    <div className="font-bold text-slate-900 dark:text-white">{user.name}</div>
                                                    <div className="text-xs text-slate-500 opacity-70"><a href={`mailto:${user.email}`} className="hover:text-primary">{user.email}</a></div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className={cn(
                                                        "px-2.5 py-1 font-bold rounded text-[10px] uppercase tracking-wider border",
                                                        user.role === "ENERGY_MANAGER" ? "bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400 border-orange-200 dark:border-orange-500/20" :
                                                            user.role === "TECHNICIAN" ? "bg-blue-50 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-200 dark:border-blue-500/20" :
                                                                "bg-slate-50 dark:bg-white/5 text-slate-500 border-slate-200 dark:border-white/10"
                                                    )}>
                                                        {user.role === "ENERGY_MANAGER" ? "Energy Manager" : user.role === "TECHNICIAN" ? "Technicien" : "Lecteur Invité"}
                                                    </span>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <span className="flex items-center gap-1.5 text-emerald-500 font-bold text-xs"><CheckCircle2 className="w-3.5 h-3.5" /> Actif</span>
                                                </td>
                                                <td className="px-6 py-4 text-right relative">
                                                    {isAdmin && (
                                                        <>
                                                            <button
                                                                onClick={() => setMenuOpenId(menuOpenId === user.id ? null : user.id)}
                                                                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/10 transition-colors"
                                                            >
                                                                <MoreVertical className="w-4 h-4" />
                                                            </button>

                                                            {menuOpenId === user.id && (
                                                                <div className="absolute right-12 top-10 bg-white dark:bg-[#0B1120] border border-slate-200 dark:border-white/10 shadow-lg rounded-xl overflow-hidden w-40 z-20">
                                                                    <button
                                                                        onClick={() => {
                                                                            setEditingUser({ id: user.id, name: user.name, email: user.email, role: user.role });
                                                                            setMenuOpenId(null);
                                                                            setIsEditUserOpen(true);
                                                                        }}
                                                                        className="w-full text-left px-4 py-3 text-sm text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-white/5 flex items-center transition-colors"
                                                                    >
                                                                        <Edit2 className="w-4 h-4 mr-2 opacity-70" /> Modifier
                                                                    </button>
                                                                    <button
                                                                        onClick={() => handleDeleteUser(user.id)}
                                                                        className="w-full text-left px-4 py-3 text-sm text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-500/10 flex items-center transition-colors"
                                                                    >
                                                                        <Trash2 className="w-4 h-4 mr-2" /> Supprimer
                                                                    </button>
                                                                </div>
                                                            )}
                                                        </>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center p-12 text-slate-500 border-2 border-dashed border-slate-200 dark:border-white/10 rounded-xl m-6">
                                <Users className="h-10 w-10 mb-3 opacity-20" />
                                <p className="text-sm font-medium">Aucun utilisateur rattaché à ce client.</p>
                            </div>
                        )}
                    </div>
                )}

            </div>

            {/* Modal: Add Site */}
            {isAddSiteOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                        <button onClick={() => setIsAddSiteOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"><X className="h-5 w-5" /></button>
                        <h2 className="text-xl font-bold mb-6 text-slate-900 dark:text-white">Ajouter un Site à {client.name}</h2>
                        <form onSubmit={handleCreateSite} className="space-y-4">
                            <div><label className="text-sm text-slate-500 dark:text-slate-400">Nom du bâtiment</label>
                                <input type="text" required value={newSite.name} onChange={e => setNewSite({ ...newSite, name: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" /></div>

                            <div><label className="text-sm text-slate-500 dark:text-slate-400">Type</label>
                                <select value={newSite.type} onChange={e => setNewSite({ ...newSite, type: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white">
                                    <option value="Bureaux">Bureaux</option><option value="Magasin">Magasin</option><option value="Usine">Usine</option><option value="Logistique">Logistique</option>
                                </select></div>

                            <div className="grid grid-cols-2 gap-4">
                                <div><label className="text-sm text-slate-500 dark:text-slate-400">Adresse</label>
                                    <input type="text" required value={newSite.address} onChange={e => setNewSite({ ...newSite, address: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" /></div>
                                <div><label className="text-sm text-slate-500 dark:text-slate-400">Code postal</label>
                                    <input type="text" required value={newSite.postalCode} onChange={e => setNewSite({ ...newSite, postalCode: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" placeholder="ex: 75000" /></div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div><label className="text-sm text-slate-500 dark:text-slate-400">Ville</label>
                                    <input type="text" required value={newSite.city} onChange={e => setNewSite({ ...newSite, city: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" /></div>
                                <div><label className="text-sm text-slate-500 dark:text-slate-400">Pays</label>
                                    <input type="text" required value={newSite.country} onChange={e => setNewSite({ ...newSite, country: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" placeholder="ex: France" /></div>
                            </div>

                            <button type="submit" className="w-full py-3 mt-4 bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]">Créer le Bâtiment</button>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal: Edit Site */}
            {isEditSiteOpen && editingSite && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                        <button onClick={() => setIsEditSiteOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"><X className="h-5 w-5" /></button>
                        <h2 className="text-xl font-bold mb-6 text-slate-900 dark:text-white flex items-center"><Edit2 className="w-5 h-5 mr-2 text-primary" /> Modifier le Bâtiment</h2>
                        <form onSubmit={handleUpdateSite} className="space-y-4">
                            <div><label className="text-sm text-slate-500 dark:text-slate-400">Nom du bâtiment</label>
                                <input type="text" required value={editingSite.name} onChange={e => setEditingSite({ ...editingSite, name: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" /></div>

                            <div><label className="text-sm text-slate-500 dark:text-slate-400">Type</label>
                                <select value={editingSite.type || "Bureaux"} onChange={e => setEditingSite({ ...editingSite, type: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white">
                                    <option value="Bureaux">Bureaux</option><option value="Magasin">Magasin</option><option value="Usine">Usine</option><option value="Logistique">Logistique</option>
                                </select></div>

                            <div className="grid grid-cols-2 gap-4">
                                <div><label className="text-sm text-slate-500 dark:text-slate-400">Adresse</label>
                                    <input type="text" value={editingSite.address || ""} onChange={e => setEditingSite({ ...editingSite, address: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" /></div>
                                <div><label className="text-sm text-slate-500 dark:text-slate-400">Code postal</label>
                                    <input type="text" value={editingSite.postalCode || ""} onChange={e => setEditingSite({ ...editingSite, postalCode: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" /></div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div><label className="text-sm text-slate-500 dark:text-slate-400">Ville</label>
                                    <input type="text" value={editingSite.city || ""} onChange={e => setEditingSite({ ...editingSite, city: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" /></div>
                                <div><label className="text-sm text-slate-500 dark:text-slate-400">Pays</label>
                                    <input type="text" value={editingSite.country || ""} onChange={e => setEditingSite({ ...editingSite, country: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white" /></div>
                            </div>

                            <button type="submit" className="w-full py-3 mt-4 bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]">Enregistrer</button>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal: Invite User */}
            {isAddUserOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 overflow-y-auto">
                    <div className="w-full max-w-2xl bg-white dark:bg-[#0B1120] rounded-3xl border border-slate-200 dark:border-white/10 p-8 shadow-2xl relative my-auto">
                        <button onClick={() => setIsAddUserOpen(false)} className="absolute top-6 right-6 text-slate-400 hover:text-slate-600 dark:hover:text-white transition-colors">
                            <X className="h-5 w-5" />
                        </button>

                        <div className="mb-8">
                            <h2 className="text-2xl font-black text-slate-900 dark:text-white flex items-center mb-2">
                                <Users className="w-6 h-6 mr-3 text-primary" />
                                Inviter un collaborateur
                            </h2>
                            <p className="text-sm text-slate-500 font-medium ml-9">
                                Ajoutez un membre à l'espace {client.name} et définissez ses droits d'accès.
                            </p>
                        </div>

                        <form onSubmit={handleCreateUser} className="space-y-8">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div>
                                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2">Nom complet</label>
                                    <input required type="text" value={newUser.name} onChange={e => setNewUser({ ...newUser, name: e.target.value })} placeholder="ex: Jean Dupont" className="w-full bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 outline-none focus:border-primary text-slate-900 dark:text-white transition-all font-medium" />
                                </div>
                                <div>
                                    <label className="text-sm font-bold text-slate-700 dark:text-slate-300 block mb-2">Email</label>
                                    <input required type="email" value={newUser.email} onChange={e => setNewUser({ ...newUser, email: e.target.value })} placeholder="jean@entreprise.com" className="w-full bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl px-4 py-3 outline-none focus:border-primary text-slate-900 dark:text-white transition-all font-medium" />
                                </div>
                            </div>

                            <div>
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white mb-4 border-b border-slate-100 dark:border-white/5 pb-2">
                                    Niveau d'Autorisation
                                </h3>

                                <div className="space-y-3">
                                    <label className={cn("flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all", newUser.role === "ENERGY_MANAGER" ? "border-orange-500 bg-orange-500/5" : "border-slate-100 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20")}>
                                        <input type="radio" name="role" value="ENERGY_MANAGER" checked={newUser.role === "ENERGY_MANAGER"} onChange={() => setNewUser({ ...newUser, role: "ENERGY_MANAGER" })} className="mt-1 mr-4 hidden" />
                                        <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 mr-4 shrink-0 transition-colors", newUser.role === "ENERGY_MANAGER" ? "border-orange-500" : "border-slate-300 dark:border-slate-600")}>
                                            {newUser.role === "ENERGY_MANAGER" && <div className="w-2.5 h-2.5 bg-orange-500 rounded-full" />}
                                        </div>
                                        <div>
                                            <span className={cn("text-base font-black flex items-center gap-2", newUser.role === "ENERGY_MANAGER" ? "text-orange-600" : "text-slate-700 dark:text-slate-300")}>
                                                <Lock className="w-4 h-4" /> Energy Manager
                                            </span>
                                            <span className="text-sm text-slate-500 mt-1 block">Accès total à la supervision, modification des consignes CVC, gestion des règles métiers et exports énergétiques avancés. Droit d'inviter d'autres techniciens.</span>
                                        </div>
                                    </label>

                                    <label className={cn("flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all", newUser.role === "TECHNICIAN" ? "border-blue-500 bg-blue-500/5" : "border-slate-100 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20")}>
                                        <input type="radio" name="role" value="TECHNICIAN" checked={newUser.role === "TECHNICIAN"} onChange={() => setNewUser({ ...newUser, role: "TECHNICIAN" })} className="mt-1 mr-4 hidden" />
                                        <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 mr-4 shrink-0 transition-colors", newUser.role === "TECHNICIAN" ? "border-blue-500" : "border-slate-300 dark:border-slate-600")}>
                                            {newUser.role === "TECHNICIAN" && <div className="w-2.5 h-2.5 bg-blue-500 rounded-full" />}
                                        </div>
                                        <div>
                                            <span className={cn("text-base font-black flex items-center gap-2", newUser.role === "TECHNICIAN" ? "text-blue-600" : "text-slate-700 dark:text-slate-300")}>
                                                <Cpu className="w-4 h-4" /> Technicien (Mainteneur)
                                            </span>
                                            <span className="text-sm text-slate-500 mt-1 block">Pilote le CVC et les équipements en temps réel, acquitte les alertes réseau/matériel. Ne peut pas modifier les scénarios AI ni inviter d'autres membres.</span>
                                        </div>
                                    </label>

                                    <label className={cn("flex items-start p-4 rounded-xl border-2 cursor-pointer transition-all", newUser.role === "CLIENT" ? "border-slate-400 bg-slate-50 dark:bg-white/5" : "border-slate-100 dark:border-white/10 hover:border-slate-300 dark:hover:border-white/20")}>
                                        <input type="radio" name="role" value="CLIENT" checked={newUser.role === "CLIENT"} onChange={() => setNewUser({ ...newUser, role: "CLIENT" })} className="mt-1 mr-4 hidden" />
                                        <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center mt-0.5 mr-4 shrink-0 transition-colors", newUser.role === "CLIENT" ? "border-slate-500" : "border-slate-300 dark:border-slate-600")}>
                                            {newUser.role === "CLIENT" && <div className="w-2.5 h-2.5 bg-slate-500 rounded-full" />}
                                        </div>
                                        <div>
                                            <span className={cn("text-base font-black flex items-center gap-2", newUser.role === "CLIENT" ? "text-slate-800 dark:text-white" : "text-slate-700 dark:text-slate-300")}>
                                                <Eye className="w-4 h-4" /> Lecteur (Read-Only)
                                            </span>
                                            <span className="text-sm text-slate-500 mt-1 block">Accès consultatif limité aux dashboards de KPI environnementaux et énergétiques. Aucune action autorisée (ni CVC, ni alertes).</span>
                                        </div>
                                    </label>
                                </div>
                            </div>

                            <button type="submit" className="w-full bg-primary hover:bg-emerald-500 text-white font-black py-4 rounded-xl transition-all disabled:opacity-50 mt-4 shadow-lg shadow-primary/30 active:scale-[0.98]">
                                Envoyer l'invitation à {client.name}
                            </button>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal: Edit User */}
            {isEditUserOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                    <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                        <button onClick={() => setIsEditUserOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"><X className="h-5 w-5" /></button>
                        <h2 className="text-xl font-bold mb-6 text-slate-900 dark:text-white flex items-center"><Edit2 className="w-5 h-5 mr-2 text-primary" /> Modifier l'Utilisateur</h2>
                        <form onSubmit={handleUpdateUser} className="space-y-4">
                            <div><label className="text-sm font-bold text-slate-700 dark:text-slate-300">Nom Complet</label>
                                <input type="text" required value={editingUser.name} onChange={e => setEditingUser({ ...editingUser, name: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:border-primary outline-none transition-all" /></div>

                            <div><label className="text-sm font-bold text-slate-700 dark:text-slate-300">Email</label>
                                <input type="email" required value={editingUser.email} onChange={e => setEditingUser({ ...editingUser, email: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:border-primary outline-none transition-all" /></div>

                            <div>
                                <label className="text-sm font-bold text-slate-700 dark:text-slate-300">Rôle</label>
                                <select value={editingUser.role} onChange={e => setEditingUser({ ...editingUser, role: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:border-primary outline-none transition-all">
                                    <option value="CLIENT">Client</option>
                                    <option value="ENERGY_MANAGER">Energy Manager</option>
                                </select>
                            </div>

                            <button type="submit" className="w-full py-3 mt-6 bg-primary hover:bg-emerald-400 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.4)] flex justify-center items-center">
                                Enregistrer les modifications
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
