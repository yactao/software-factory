"use client";

import React, { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { io, Socket } from "socket.io-client";
import { Building2, Layers, ThermometerSun, Wind, Users, Activity, ChevronsUpDown, Cpu, Search, CheckCircle2, ChevronDown, ChevronRight, Building, MapPin, LayoutGrid, Thermometer, Plus, X, Zap, ArrowLeft, Sun, CloudRain, AlertTriangle, ShieldCheck, Filter, RefreshCw, Power, Lightbulb, Video, Router, Server, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { useTenant } from "@/lib/TenantContext";
import { EnergyChart } from "@/components/dashboard/EnergyChart";
import { StatsCard } from "@/components/dashboard/StatsCard";

// Types
interface Sensor {
    id: string;
    name: string;
    type: string;
}

interface Zone {
    id: string;
    name: string;
    floor: string;
    type?: string;
    sensors?: Sensor[];
}

interface Site {
    id: string;
    name: string;
    type?: string;
    description?: string;
    address: string;
    postalCode?: string;
    city: string;
    status: string;
    zones: Zone[];
    organizationId?: string;
    organization?: { id: string; name: string };
    gateways?: any[];
}

export default function SiteDashboardPage() {
    const params = useParams();
    const router = useRouter();
    const siteId = params.id as string;
    const { authFetch, currentTenant } = useTenant();

    const [site, setSite] = useState<Site | null>(null);
    const [loading, setLoading] = useState(true);
    const [expandedFloors, setExpandedFloors] = useState<Record<string, boolean>>({});

    // Modal States
    const [isEquipementModalOpen, setIsEquipementModalOpen] = useState(false);
    const [selectedZone, setSelectedZone] = useState<Zone | null>(null);
    const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});

    // Tabs States
    const [activeTab, setActiveTab] = useState("dashboard");

    // Remote Control Mock States
    const [hvacState, setHvacState] = useState(true);
    const [hvacTemp, setHvacTemp] = useState(22.0);
    const [lightsState, setLightsState] = useState(false);

    // Mock Data for site dashboard
    const [siteEnergyData] = useState([
        { id: "1", timestamp: new Date(new Date().setHours(0, 0, 0, 0)).toISOString(), value: 450, sensor: { type: "energy", unit: "W" } },
        { id: "2", timestamp: new Date(new Date().setHours(4, 0, 0, 0)).toISOString(), value: 420, sensor: { type: "energy", unit: "W" } },
        { id: "3", timestamp: new Date(new Date().setHours(8, 0, 0, 0)).toISOString(), value: 1200, sensor: { type: "energy", unit: "W" } },
        { id: "4", timestamp: new Date(new Date().setHours(12, 0, 0, 0)).toISOString(), value: 3500, sensor: { type: "energy", unit: "W" } },
        { id: "5", timestamp: new Date(new Date().setHours(16, 0, 0, 0)).toISOString(), value: 3200, sensor: { type: "energy", unit: "W" } },
        { id: "6", timestamp: new Date(new Date().setHours(20, 0, 0, 0)).toISOString(), value: 1500, sensor: { type: "energy", unit: "W" } },
        { id: "7", timestamp: new Date(new Date().setHours(23, 59, 0, 0)).toISOString(), value: 600, sensor: { type: "energy", unit: "W" } },
    ]);
    const [alerts] = useState([
        { id: 1, type: "error", message: "Code Erreur CVC: EXT-01 (Groupe Froid)", time: "Il y a 10 min" },
        { id: 2, type: "warning", message: "Capteur CO2 Salle Réunion Offline", time: "Il y a 2h" }
    ]);
    const [rules] = useState([
        { id: 1, message: "Règle activée: Baisse consigne CVC (-2°C) suite à dlcissement Tarif", time: "08:30" },
        { id: 2, message: "Règle activée: Extinction éclairage oublié RDC", time: "20:15 hier" }
    ]);

    // Modales states
    const [isAddZoneOpen, setIsAddZoneOpen] = useState(false);
    const [newZone, setNewZone] = useState({ name: "", type: "Office", floor: "RDC" });
    const isAdmin = currentTenant?.role === "ENERGY_MANAGER" || currentTenant?.role === "SUPER_ADMIN";

    const fetchSiteDetails = async (isSilentRefresh = false) => {
        if (!isSilentRefresh) setLoading(true);
        try {
            // Fetch all sites for now and find. Ideally GET /api/sites/:id
            const res = await authFetch("http://localhost:3001/api/sites");
            if (res.ok) {
                const data = await res.json();
                const found = data.find((s: Record<string, unknown>) => s.id === siteId);
                setSite(found || null);
                // Auto-expand first floor if exists and it's the initial load
                if (found && found.zones && found.zones.length > 0 && !isSilentRefresh) {
                    const firstFloor = found.zones[0].floor || "RDC";
                    setExpandedFloors(prev => Object.keys(prev).length === 0 ? { [firstFloor]: true } : prev);
                }
            }
        } catch (err) {
            console.error("Failed to fetch site", err);
        } finally {
            setLoading(false);
        }
    };

    const handleEquipmentAction = async (equipmentId: string, actionName: string, value?: string | number | boolean) => {
        try {
            const res = await authFetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'}/api/equipment/action`, {
                method: "POST",
                body: JSON.stringify({ equipmentId, action: actionName, value })
            });
            if (!res.ok) {
                console.error("Failed to execute action");
            }
        } catch (err) {
            console.error("Action error:", err);
        }
    };

    useEffect(() => {
        fetchSiteDetails();

        // Setup WebSocket for realtime refresh
        const socket: Socket = io(process.env.NEXT_PUBLIC_API_URL || "");

        socket.on("connect", () => {
            console.log("WebSocket connected for Realtime IoT Data");
        });

        socket.on("refresh_data", (data: { all?: boolean; siteId?: string }) => {
            // If it's a global refresh or specifically for our site
            if (data.all || data.siteId === siteId) {
                console.log("Realtime update received! Refreshing site data...");
                fetchSiteDetails(true); // Silent refresh, no loading spinner
            }
        });

        return () => {
            socket.disconnect();
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [siteId, authFetch]);

    const handleCreateZone = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            const res = await authFetch("http://localhost:3001/api/zones", {
                method: "POST",
                body: JSON.stringify({ ...newZone, siteId: siteId })
            });
            if (res.ok) {
                setIsAddZoneOpen(false);
                setNewZone({ name: "", type: "Office", floor: "RDC" });
                await fetchSiteDetails();
                if (newZone.floor) setExpandedFloors(prev => ({ ...prev, [newZone.floor]: true }));
            }
        } catch (e) {
            console.error(e);
        }
    };

    const handleDeleteZone = async (zoneId: string, e: React.MouseEvent) => {
        e.stopPropagation();
        if (!window.confirm("Êtes-vous sûr de vouloir supprimer cette zone ?")) return;
        try {
            const res = await authFetch(`http://localhost:3001/api/zones/${zoneId}`, {
                method: "DELETE",
            });
            if (res.ok) {
                await fetchSiteDetails();
            }
        } catch (error) {
            console.error("Failed to delete zone", error);
        }
    };

    if (loading) return <div className="p-12 text-center text-slate-500">Chargement du site...</div>;
    if (!site) return <div className="p-12 text-center text-rose-500">Site introuvable.</div>;

    // Group zones by floor
    const zonesByFloor = site.zones?.reduce((acc: Record<string, Zone[]>, zone: Zone) => {
        const floor = zone.floor || "RDC";
        if (!acc[floor]) acc[floor] = [];
        acc[floor].push(zone);
        return acc;
    }, {}) || {};

    const toggleFloor = (floor: string) => {
        setExpandedFloors(prev => ({ ...prev, [floor]: !prev[floor] }));
    };

    const hasEquipments = (site?.gateways?.length ?? 0) > 0 || site?.zones?.some((z: any) => (z.sensors?.length ?? 0) > 0) || false;

    return (
        <div className="space-y-6 max-w-[1400px] mx-auto pb-12 pt-4">
            {/* Header & Breadcrumb */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 pb-6 border-b border-slate-200 dark:border-white/5">
                <div>
                    <button
                        onClick={() => router.push((site?.organization?.id || site?.organizationId) ? `/clients/${site?.organization?.id || site?.organizationId}` : '/sites')}
                        className="flex items-center text-xs font-bold text-slate-500 hover:text-primary mb-3 transition-colors uppercase tracking-wider"
                    >
                        <ArrowLeft className="w-3 h-3 mr-1" /> Retour au client de rattachement
                    </button>
                    <div className="flex items-center text-slate-900 dark:text-white mb-2">
                        <Building2 className="h-8 w-8 mr-3 text-primary" />
                        <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-white/60 bg-clip-text text-transparent">
                            {site.name}
                        </h1>
                        <span className="ml-4 px-2.5 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider bg-slate-100 dark:bg-white/5 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-white/10">
                            {site.type || "Bureaux"}
                        </span>
                    </div>
                    <p className="text-slate-500 dark:text-muted-foreground font-medium flex items-center">
                        <MapPin className="h-4 w-4 mr-1.5 text-slate-400" />
                        {site.address}, {site.postalCode ? `${site.postalCode} ` : ''}{site.city}
                    </p>
                </div>

                <div className="flex gap-4">
                    {/* Health Score Site */}
                    <div className="flex items-center gap-3 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 shadow-sm">
                        <ShieldCheck className="h-6 w-6 text-emerald-500" />
                        <div>
                            <p className="text-[10px] text-emerald-600 dark:text-emerald-400 uppercase font-bold tracking-widest leading-tight">Santé Site</p>
                            <h4 className="text-sm font-bold text-slate-900 dark:text-white leading-tight">95/100</h4>
                        </div>
                    </div>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex space-x-4 mb-2 border-b border-slate-200 dark:border-white/5 pb-4">
                <button
                    onClick={() => setActiveTab('dashboard')}
                    className={`px-5 py-2.5 text-sm font-bold rounded-xl transition-all flex items-center ${activeTab === 'dashboard' ? 'bg-primary text-white shadow-md' : 'bg-slate-100 dark:bg-white/5 text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}
                >
                    <LayoutGrid className="w-4 h-4 mr-2" /> Tableau de Bord
                </button>
                <button
                    onClick={() => setActiveTab('equipments')}
                    className={`px-5 py-2.5 text-sm font-bold rounded-xl transition-all flex items-center ${activeTab === 'equipments' ? 'bg-primary text-white shadow-md' : 'bg-slate-100 dark:bg-white/5 text-slate-500 hover:text-slate-900 dark:hover:text-white'}`}
                >
                    <Power className="w-4 h-4 mr-2" /> Actionneurs & Pilotage
                </button>
            </div>

            {activeTab === 'dashboard' && (
                <>
                    {/* Metrics Row */}
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
                        <StatsCard title="Conso. Globale (Live)" value={hasEquipments ? "3,500 W" : "0 W"} trend={hasEquipments ? "+5%" : "--"} trendUp={false} icon={Zap} color="cyan" />
                        <StatsCard title="Conso. CVC (Live)" value={hasEquipments ? "2,100 W" : "0 W"} trend={hasEquipments ? "-2%" : "--"} trendUp={true} icon={ThermometerSun} color="orange" />
                        <StatsCard title="Qualité Air Moyenne" value={hasEquipments ? "480 ppm" : "--"} trend={hasEquipments ? "Excellent" : "--"} trendUp={true} icon={Wind} color="green" />
                        <StatsCard title="Zones Connectées" value={hasEquipments ? (site.zones?.length?.toString() || "0") : "0"} trend={hasEquipments ? "Global: OK" : "En attente"} trendUp={true} icon={Activity} color="purple" />
                    </div>

                    {/* Main Content Grid */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                        {/* Left: Energy Charts (Span 2) */}
                        <div className="lg:col-span-2 glass-card p-6 rounded-2xl border-slate-200 dark:border-white/5 flex flex-col h-[400px]">
                            <div className="flex justify-between items-center mb-6">
                                <div>
                                    <h3 className="text-base font-bold text-slate-900 dark:text-white">Analyse des Consommations</h3>
                                    <p className="text-xs text-slate-500 dark:text-muted-foreground">Comparaison Globale vs Système CVC</p>
                                </div>
                                <div className="flex space-x-2">
                                    <span className="flex items-center text-[10px] font-bold text-cyan-500 bg-cyan-500/10 px-2 py-1 rounded">Globale</span>
                                    <span className="flex items-center text-[10px] font-bold text-orange-500 bg-orange-500/10 px-2 py-1 rounded">CVC</span>
                                </div>
                            </div>
                            <div className="flex-1 w-full bg-slate-50 dark:bg-black/20 rounded-xl p-4 flex flex-col border border-slate-100 dark:border-white/5 relative h-64">
                                {hasEquipments ? <EnergyChart data={siteEnergyData} /> : <div className="flex-1 flex items-center justify-center text-sm text-slate-500">Aucune donnée de consommation disponible</div>}
                            </div>
                        </div>

                        {/* Right: Feeds (Errors & Rules) */}
                        <div className="lg:col-span-1 flex flex-col gap-4">
                            {/* Alerts Feed */}
                            <div className="glass-card p-5 rounded-2xl flex-1 border-slate-200 dark:border-white/5 flex flex-col">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center mb-4">
                                    <AlertTriangle className="h-4 w-4 mr-2 text-rose-500" />
                                    Anomalies du site
                                </h3>
                                <div className="space-y-3 flex-1 overflow-y-auto">
                                    {hasEquipments && alerts.length > 0 ? alerts.map(a => (
                                        <div key={a.id} className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
                                            <p className="text-xs font-bold text-slate-900 dark:text-white mb-1">{a.message}</p>
                                            <p className="text-[10px] text-slate-500">{a.time}</p>
                                        </div>
                                    )) : (
                                        <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                            <p className="text-xs py-4">Aucune anomalie détectée</p>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Rules Feed */}
                            <div className="glass-card p-5 rounded-2xl flex-1 border-slate-200 dark:border-white/5 flex flex-col">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center mb-4">
                                    <Cpu className="h-4 w-4 mr-2 text-primary" />
                                    Historique des Règles
                                </h3>
                                <div className="space-y-3 flex-1 overflow-y-auto">
                                    {hasEquipments && rules.length > 0 ? rules.map(r => (
                                        <div key={r.id} className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg">
                                            <p className="text-xs font-bold text-slate-900 dark:text-white mb-1">{r.message}</p>
                                            <p className="text-[10px] text-slate-500">{r.time}</p>
                                        </div>
                                    )) : (
                                        <div className="flex flex-col items-center justify-center h-full text-slate-500">
                                            <p className="text-xs py-4">Aucune règle configurée</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                    </div>

                    {/* Locaux / Zones (Arborescence) */}
                    <div className="glass-card rounded-2xl p-6 border-slate-200 dark:border-white/5">
                        <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-white/5">
                            <div>
                                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center">
                                    <Layers className="h-5 w-5 mr-2 text-primary" />
                                    Arborescence Technique (Locaux)
                                </h3>
                                <p className="text-xs text-slate-500 mt-1">Gérez les zones virtuelles et les capteurs affectés à ce bâtiment.</p>
                            </div>
                            {isAdmin && (
                                <button onClick={() => setIsAddZoneOpen(true)} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 dark:bg-white/5 dark:hover:bg-white/10 text-slate-900 dark:text-white border border-slate-200 dark:border-white/10 font-bold rounded-xl transition-all shadow-sm flex items-center text-sm">
                                    <Plus className="h-4 w-4 mr-2 text-emerald-500" /> Ajouter Zone
                                </button>
                            )}
                        </div>

                        <div className="space-y-6">
                            {Object.keys(zonesByFloor).length === 0 ? (
                                <div className="flex flex-col items-center justify-center p-12 text-slate-500 dark:text-muted-foreground border-2 border-dashed border-slate-200 dark:border-white/10 rounded-xl">
                                    <LayoutGrid className="h-10 w-10 mb-3 opacity-20" />
                                    <p className="text-sm">Aucune zone configurée pour ce bâtiment.</p>
                                </div>
                            ) : (
                                Object.entries(zonesByFloor).sort().map(([floor, zones]) => (
                                    <div key={floor} className="border border-slate-200 dark:border-white/10 rounded-2xl overflow-hidden shadow-sm">
                                        {/* Floor Header */}
                                        <button
                                            onClick={() => toggleFloor(floor)}
                                            className="w-full flex items-center justify-between p-4 bg-slate-50 dark:bg-white/[0.02] hover:bg-slate-100 dark:hover:bg-white/5 transition-colors"
                                        >
                                            <div className="flex items-center">
                                                <div className="w-8 h-8 rounded-lg bg-emerald-500/10 flex items-center justify-center mr-3">
                                                    <span className="font-bold text-emerald-600 dark:text-emerald-400 text-sm">{floor}</span>
                                                </div>
                                                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase">Niveau</h3>
                                                <span className="ml-4 px-2.5 py-1 bg-slate-200 dark:bg-black/40 rounded-full text-[10px] font-bold text-slate-600 dark:text-slate-300 shadow-inner">{zones.length} Zones</span>
                                            </div>
                                            {expandedFloors[floor] ? <ChevronDown className="h-5 w-5 text-slate-500" /> : <ChevronRight className="h-5 w-5 text-slate-500" />}
                                        </button>

                                        {/* Zones Grid */}
                                        {expandedFloors[floor] && (
                                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-white dark:bg-black/20">
                                                {zones.map(zone => (
                                                    <div key={zone.id} className="p-4 bg-slate-50 dark:bg-[#0B1120] rounded-xl border border-slate-200 dark:border-white/10 hover:border-primary/40 transition-all group">
                                                        <div className="flex justify-between items-start mb-4">
                                                            <div className="flex flex-col">
                                                                <h4 className="font-bold text-sm text-slate-900 dark:text-white group-hover:text-primary transition-colors">{zone.name}</h4>
                                                                <span className="text-[10px] text-slate-500 uppercase tracking-widest">{zone.type}</span>
                                                            </div>
                                                            {isAdmin && (
                                                                <button onClick={(e) => handleDeleteZone(zone.id, e)} className="p-1 hover:bg-rose-500/10 hover:text-rose-500 text-slate-400 rounded transition-colors opacity-0 group-hover:opacity-100" title="Supprimer la zone">
                                                                    <Trash2 className="h-4 w-4" />
                                                                </button>
                                                            )}
                                                        </div>

                                                        <div className="grid grid-cols-2 gap-2 mb-4">
                                                            {hasEquipments ? (
                                                                <>
                                                                    <div className="bg-white dark:bg-white/5 p-2 rounded-lg flex flex-col justify-center border border-slate-100 dark:border-white/5 shadow-sm">
                                                                        <span className="text-[9px] text-slate-500 uppercase mb-0.5">Climat</span>
                                                                        <span className="text-xs font-bold text-slate-900 dark:text-white flex items-center"><Thermometer className="h-3 w-3 text-orange-400 mr-1" /> 22.5°C</span>
                                                                    </div>
                                                                    <div className="bg-white dark:bg-white/5 p-2 rounded-lg flex flex-col justify-center border border-slate-100 dark:border-white/5 shadow-sm">
                                                                        <span className="text-[9px] text-slate-500 uppercase mb-0.5">Présence</span>
                                                                        <span className="text-xs font-bold text-emerald-500 dark:text-emerald-400 flex items-center"><Users className="h-3 w-3 mr-1" /> Oui</span>
                                                                    </div>
                                                                </>
                                                            ) : (
                                                                <div className="col-span-2 bg-white dark:bg-white/5 p-2 rounded-lg flex items-center justify-center border border-slate-100 dark:border-white/5 shadow-sm text-slate-400 text-[10px] uppercase font-bold tracking-widest">
                                                                    Aucun capteur
                                                                </div>
                                                            )}
                                                        </div>
                                                        <button
                                                            onClick={() => {
                                                                setSelectedZone(zone);
                                                                // auto-expand zone in modal
                                                                setExpandedRows({ [zone.id]: true });
                                                                setIsEquipementModalOpen(true);
                                                            }}
                                                            className="w-full py-1.5 text-[10px] font-bold uppercase tracking-widest text-primary bg-primary/10 hover:bg-primary/20 rounded transition-colors group-hover:bg-primary group-hover:text-white"
                                                        >
                                                            Détails Capteurs & Équipements
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </>
            )}

            {activeTab === 'equipments' && (
                <div className="space-y-6 mt-6">
                    <div className="glass-card rounded-2xl p-6 border-slate-200 dark:border-white/5">
                        <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-white/5">
                            <div>
                                <h3 className="text-lg font-bold text-slate-900 dark:text-white flex items-center">
                                    <Power className="h-5 w-5 mr-2 text-primary" />
                                    Interface de Pilotage
                                </h3>
                                <p className="text-xs text-slate-500 mt-1">Gérez et pilotez à distance l&apos;ensemble des équipements et actionneurs de vos zones.</p>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {hasEquipments ? (
                                <>
                                    {/* CVC Control */}
                                    <div className="p-5 rounded-xl border border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-black/20">
                                        <div className="flex justify-between items-center mb-4">
                                            <div className="flex items-center">
                                                <div className={`p-2 rounded-lg mr-3 ${hvacState ? 'bg-orange-500/10 text-orange-500' : 'bg-white dark:bg-white/5 text-slate-400'}`}>
                                                    <ThermometerSun className="w-5 h-5" />
                                                </div>
                                                <div>
                                                    <h4 className="font-bold text-sm text-slate-900 dark:text-white">Climatisation (CVC)</h4>
                                                    <span className={`text-[10px] font-bold uppercase ${hvacState ? 'text-emerald-500' : 'text-slate-500'}`}>{hvacState ? 'Allumé' : 'Éteint'}</span>
                                                </div>
                                            </div>
                                            {/* Toggle UI */}
                                            <button
                                                onClick={() => {
                                                    const newState = !hvacState;
                                                    setHvacState(newState);
                                                    handleEquipmentAction("cvc-global", "toggle_hvac", newState);
                                                }}
                                                className={`w-12 h-6 rounded-full relative transition-colors ${hvacState ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`}
                                            >
                                                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${hvacState ? 'left-7' : 'left-1'}`} />
                                            </button>
                                        </div>
                                        {hvacState && (
                                            <div className="pt-4 border-t border-slate-200 dark:border-white/5">
                                                <label className="text-xs font-bold text-slate-500 mb-2 block">Consigne Actuelle (Globale)</label>
                                                <div className="flex justify-between items-center bg-white dark:bg-white/5 p-2 rounded-lg border border-slate-200 dark:border-white/5">
                                                    <button
                                                        onClick={() => {
                                                            const newT = Math.max(16, hvacTemp - 0.5);
                                                            setHvacTemp(newT);
                                                            handleEquipmentAction("cvc-global", "set_temp", newT);
                                                        }}
                                                        className="h-8 w-8 rounded flex items-center justify-center text-slate-500 hover:text-primary hover:bg-primary/10 transition-colors"
                                                    >
                                                        -
                                                    </button>
                                                    <span className="text-lg font-bold text-slate-900 dark:text-white">{hvacTemp.toFixed(1)}°C</span>
                                                    <button
                                                        onClick={() => {
                                                            const newT = Math.min(30, hvacTemp + 0.5);
                                                            setHvacTemp(newT);
                                                            handleEquipmentAction("cvc-global", "set_temp", newT);
                                                        }}
                                                        className="h-8 w-8 rounded flex items-center justify-center text-slate-500 hover:text-primary hover:bg-primary/10 transition-colors"
                                                    >
                                                        +
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    {/* Lights Control */}
                                    <div className="p-5 rounded-xl border border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-black/20">
                                        <div className="flex justify-between items-center mb-2">
                                            <div className="flex items-center">
                                                <div className={`p-2 rounded-lg mr-3 ${lightsState ? 'bg-yellow-400/10 text-yellow-500' : 'bg-white dark:bg-white/5 text-slate-400'}`}>
                                                    <Lightbulb className="w-5 h-5" />
                                                </div>
                                                <div>
                                                    <h4 className="font-bold text-sm text-slate-900 dark:text-white">Éclairage</h4>
                                                    <span className={`text-[10px] font-bold uppercase ${lightsState ? 'text-yellow-500' : 'text-slate-500'}`}>{lightsState ? 'Allumé (100%)' : 'Éteint'}</span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => {
                                                    const newState = !lightsState;
                                                    setLightsState(newState);
                                                    handleEquipmentAction("lights-global", "toggle_lights", newState);
                                                }}
                                                className={`w-12 h-6 rounded-full relative transition-colors ${lightsState ? 'bg-primary' : 'bg-slate-300 dark:bg-slate-700'}`}
                                            >
                                                <div className={`absolute top-1 w-4 h-4 rounded-full bg-white transition-all ${lightsState ? 'left-7' : 'left-1'}`} />
                                            </button>
                                        </div>
                                    </div>

                                    {/* Camera Stream Placeholder */}
                                    <div className="p-5 rounded-xl border border-slate-200 dark:border-white/5 bg-slate-50 dark:bg-black/20">
                                        <div className="flex items-center mb-4">
                                            <div className="p-2 rounded-lg mr-3 bg-red-500/10 text-red-500">
                                                <Video className="w-5 h-5" />
                                            </div>
                                            <div>
                                                <h4 className="font-bold text-sm text-slate-900 dark:text-white">Caméra Thermique</h4>
                                                <span className="text-[10px] font-bold uppercase text-red-500 flex items-center">
                                                    <span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-1 animate-pulse" /> Live
                                                </span>
                                            </div>
                                        </div>
                                        <div className="w-full aspect-video bg-black rounded-lg overflow-hidden relative group border border-slate-800">
                                            <video
                                                src="https://cdn.pixabay.com/video/2019/04/10/22818-331295328_large.mp4"
                                                autoPlay
                                                loop
                                                muted
                                                playsInline
                                                className="opacity-70 group-hover:opacity-100 transition-opacity w-full h-full object-cover filter sepia hue-rotate-[180deg] saturate-200 contrast-125"
                                            />
                                            <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 pt-8">
                                                <p className="text-[9px] text-white/70 font-mono tracking-widest flex justify-between">
                                                    <span>HALL — CAM 01</span>
                                                    <span className="text-red-500 animate-pulse">REC</span>
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </>
                            ) : (
                                <div className="col-span-1 md:col-span-2 lg:col-span-3 text-center py-12 text-slate-500 flex flex-col items-center">
                                    <Power className="h-10 w-10 mb-3 opacity-20" />
                                    <p className="text-sm">Aucun équipement ou système pilotable dans ce bâtiment.</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Equipements Modal for Selected Zone */}
            {isEquipementModalOpen && selectedZone && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
                    <div className="w-full max-w-5xl bg-slate-50 dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 flex flex-col shadow-2xl overflow-hidden max-h-[90vh]">
                        {/* Header */}
                        <div className="p-6 border-b border-slate-200 dark:border-white/10 bg-white dark:bg-black/20 flex justify-between items-center z-10">
                            <div>
                                <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center">
                                    <ThermometerSun className="w-6 h-6 mr-3 text-primary" />
                                    Équipements & Contrôles — {selectedZone.name}
                                </h2>
                                <p className="text-xs text-slate-500 mt-1 uppercase tracking-widest">{selectedZone.type} • Niveau {selectedZone.floor}</p>
                            </div>
                            <button onClick={() => setIsEquipementModalOpen(false)} className="text-slate-400 hover:text-slate-600 dark:hover:text-white bg-slate-100 dark:bg-white/5 p-2 rounded-full transition-colors"><X className="h-5 w-5" /></button>
                        </div>

                        <div className="flex flex-col md:flex-row flex-1 overflow-hidden h-full">
                            {/* Left Col: Table Capteurs */}
                            <div className="w-full md:w-2/3 border-r border-slate-200 dark:border-white/5 flex flex-col bg-white dark:bg-transparent overflow-hidden">
                                <div className="p-4 border-b border-slate-200 dark:border-white/5 flex justify-between items-center bg-slate-50/50 dark:bg-white/[0.02]">
                                    <h3 className="text-sm font-bold text-slate-900 dark:text-white">Liste des Capteurs</h3>
                                    <div className="flex gap-2">
                                        <button className="p-1.5 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded overflow-hidden text-slate-400 hover:text-primary transition-colors"><RefreshCw className="h-3.5 w-3.5" /></button>
                                    </div>
                                </div>
                                <div className="flex-1 overflow-y-auto custom-scrollbar p-0">
                                    <table className="w-full text-left border-collapse">
                                        <thead>
                                            <tr className="border-b border-slate-200 dark:border-white/10 bg-slate-50/80 dark:bg-black/40 text-[10px] font-bold text-slate-500 uppercase tracking-widest sticky top-0 backdrop-blur-md z-10">
                                                <th className="p-4 w-8"></th>
                                                <th className="p-4">Équipement ↓</th>
                                                <th className="p-4">Propriétés Live</th>
                                            </tr>
                                        </thead>
                                        <tbody className="text-sm">
                                            {selectedZone.sensors && selectedZone.sensors.length > 0 && (
                                                <tr
                                                    onClick={() => setExpandedRows(prev => ({ ...prev, [selectedZone.id]: !prev[selectedZone.id] }))}
                                                    className="border-b border-slate-100 dark:border-white/5 bg-slate-100/50 dark:bg-white/[0.04] cursor-pointer group"
                                                >
                                                    <td className="p-4 text-slate-400">
                                                        {expandedRows[selectedZone.id] ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                                                    </td>
                                                    <td className="p-4 font-bold text-slate-900 dark:text-white">
                                                        {`Passerelle Ubot-${selectedZone.name.toUpperCase().replace(/\s/g, '-')}`}
                                                    </td>
                                                    <td className="p-4">
                                                        <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest bg-emerald-500/10 text-emerald-500 rounded border border-emerald-500/20">Online</span>
                                                    </td>
                                                </tr>
                                            )}
                                            {/* Sensors */}
                                            {expandedRows[selectedZone.id] && selectedZone.sensors?.map((sensor: { id: string; name: string; type: string }) => {
                                                const type = sensor.type.toLowerCase();
                                                let Pills = <span className="px-2.5 py-1 text-xs font-bold bg-slate-100 dark:bg-white/10 text-slate-400 rounded-md">-</span>;

                                                if (type.includes('temp') || type.includes('ambiance')) {
                                                    Pills = (
                                                        <div className="flex gap-2">
                                                            <span className="px-2.5 py-1 text-[11px] font-bold bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 rounded-md shadow-sm">21.5 °C</span>
                                                            <span className="px-2.5 py-1 text-[11px] font-bold bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 rounded-md shadow-sm">48.2 %RH</span>
                                                            <span className="px-2.5 py-1 text-[11px] font-bold bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 rounded-md shadow-sm">120 lx</span>
                                                        </div>
                                                    );
                                                } else if (type.includes('présence') || type.includes('motion')) {
                                                    Pills = (
                                                        <div className="flex gap-2">
                                                            <span className="px-2.5 py-1 text-[11px] font-bold bg-[#142A38] dark:bg-slate-700 text-white rounded-md shadow-sm">Motion (Active)</span>
                                                        </div>
                                                    );
                                                } else if (type.includes('co2')) {
                                                    Pills = (
                                                        <div className="flex gap-2">
                                                            <span className="px-2.5 py-1 text-[11px] font-bold bg-orange-500/10 text-orange-600 dark:text-orange-400 rounded-md shadow-sm">520 ppm</span>
                                                        </div>
                                                    );
                                                }

                                                return (
                                                    <tr key={sensor.id} className="border-b border-slate-50 dark:border-white/[0.02] hover:bg-slate-50/50 dark:hover:bg-white/[0.01] transition-colors">
                                                        <td className="p-4 border-l-2 border-slate-200 dark:border-white/10 translate-x-4 h-full" />
                                                        <td className="py-3 px-4 text-slate-700 dark:text-slate-300 flex items-center pl-8 text-xs font-medium border-l border-slate-200 dark:border-white/5 relative">
                                                            <div className="absolute left-0 top-1/2 w-4 border-t border-slate-200 dark:border-white/10"></div>
                                                            {sensor.name}
                                                        </td>
                                                        <td className="p-4">
                                                            {Pills}
                                                        </td>
                                                    </tr>
                                                );
                                            })}

                                            {(!selectedZone.sensors || selectedZone.sensors.length === 0) && (
                                                <tr>
                                                    <td colSpan={3} className="p-8 text-center text-slate-500 italic bg-slate-50/20 dark:bg-black/10">
                                                        Aucun capteur rattaché dans cette zone.
                                                    </td>
                                                </tr>
                                            )}
                                        </tbody>
                                    </table>
                                </div>
                            </div>

                            {/* Right Col: Liste des Équipements */}
                            <div className="w-full md:w-1/3 flex flex-col bg-slate-50/50 dark:bg-black/20 overflow-y-auto border-l border-slate-200 dark:border-white/5">
                                <div className="p-4 border-b border-slate-200 dark:border-white/5">
                                    <h3 className="text-sm font-bold text-slate-900 dark:text-white flex items-center">
                                        <Server className="w-4 h-4 mr-2 text-primary" /> Équipements de la zone
                                    </h3>
                                </div>
                                <div className="p-4 space-y-4">
                                    {(selectedZone.sensors && selectedZone.sensors.length > 0) ? (
                                        <>
                                            <div className="p-3 bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 rounded-xl shadow-sm hover:border-primary/30 transition-colors">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="flex items-center">
                                                        <Router className="w-4 h-4 mr-2 text-slate-400" />
                                                        <h4 className="font-bold text-sm text-slate-900 dark:text-white">Passerelle Ubot</h4>
                                                    </div>
                                                    <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest bg-emerald-500/10 text-emerald-500 rounded border border-emerald-500/20">Online</span>
                                                </div>
                                                <div className="flex justify-between items-end">
                                                    <p className="text-xs text-slate-500 font-mono tracking-wider">ID: GTW-8829-AB</p>
                                                </div>
                                            </div>

                                            <div className="p-3 bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 rounded-xl shadow-sm hover:border-primary/30 transition-colors">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="flex items-center">
                                                        <ThermometerSun className="w-4 h-4 mr-2 text-slate-400" />
                                                        <h4 className="font-bold text-sm text-slate-900 dark:text-white">Contrôleur CVC</h4>
                                                    </div>
                                                    <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest bg-emerald-500/10 text-emerald-500 rounded border border-emerald-500/20">Online</span>
                                                </div>
                                                <div className="flex justify-between items-end">
                                                    <p className="text-xs text-slate-500 font-mono tracking-wider">ID: THM-2241-CD</p>
                                                    <button
                                                        onClick={() => {
                                                            const newState = !hvacState;
                                                            setHvacState(newState);
                                                            handleEquipmentAction("cvc-local", "toggle_hvac", newState);
                                                        }}
                                                        className={`px-3 py-1 rounded text-xs font-bold transition-all ${hvacState ? 'bg-orange-500 hover:bg-orange-600 text-white shadow-sm' : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300'}`}
                                                    >
                                                        {hvacState ? 'Allumé' : 'Éteint'}
                                                    </button>
                                                </div>
                                            </div>

                                            <div className="p-3 bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 rounded-xl shadow-sm hover:border-primary/30 transition-colors">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="flex items-center">
                                                        <Lightbulb className="w-4 h-4 mr-2 text-slate-400" />
                                                        <h4 className="font-bold text-sm text-slate-900 dark:text-white">Éclairage DALI</h4>
                                                    </div>
                                                    <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest bg-emerald-500/10 text-emerald-500 rounded border border-emerald-500/20">Online</span>
                                                </div>
                                                <div className="flex justify-between items-end">
                                                    <p className="text-xs text-slate-500 font-mono tracking-wider">ID: LGT-1049-EF</p>
                                                    <button
                                                        onClick={() => {
                                                            const newState = !lightsState;
                                                            setLightsState(newState);
                                                            handleEquipmentAction("lights-local", "toggle_lights", newState);
                                                        }}
                                                        className={`px-3 py-1 rounded text-xs font-bold transition-all ${lightsState ? 'bg-yellow-400 hover:bg-yellow-500 text-slate-900 shadow-sm' : 'bg-slate-200 dark:bg-slate-800 text-slate-600 dark:text-slate-300'}`}
                                                    >
                                                        {lightsState ? 'Allumé' : 'Éteint'}
                                                    </button>
                                                </div>
                                            </div>

                                            <div className="p-3 bg-white dark:bg-white/[0.02] border border-slate-200 dark:border-white/5 rounded-xl shadow-sm hover:border-primary/30 transition-colors">
                                                <div className="flex justify-between items-start mb-2">
                                                    <div className="flex items-center">
                                                        <Video className="w-4 h-4 mr-2 text-slate-400" />
                                                        <h4 className="font-bold text-sm text-slate-900 dark:text-white">Caméra Thermique</h4>
                                                    </div>
                                                    <span className="px-2 py-0.5 text-[9px] font-bold uppercase tracking-widest bg-amber-500/10 text-amber-500 rounded border border-amber-500/20">Standby</span>
                                                </div>
                                                <div className="flex justify-between items-end mt-1">
                                                    <p className="text-xs text-slate-500 font-mono tracking-wider">ID: CAM-TH-01</p>
                                                    <span className="px-3 py-1 text-[10px] font-bold text-red-500 bg-red-500/10 rounded flex items-center">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-red-500 mr-1 animate-pulse" /> Live Feed
                                                    </span>
                                                </div>
                                            </div>
                                        </>
                                    ) : (
                                        <div className="p-8 text-center text-slate-500 italic bg-slate-50/20 dark:bg-black/10 rounded-xl border border-dashed border-slate-200 dark:border-white/5">
                                            Aucun équipement connectable dans cette zone.
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )
            }

            {/* Modal: Add Zone */}
            {
                isAddZoneOpen && (
                    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                        <div className="w-full max-w-md bg-white dark:bg-[#0B1120] rounded-2xl border border-slate-200 dark:border-white/10 p-6 shadow-2xl relative">
                            <button onClick={() => setIsAddZoneOpen(false)} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 dark:hover:text-white"><X className="h-5 w-5" /></button>
                            <h2 className="text-xl font-bold mb-6 text-slate-900 dark:text-white flex items-center"><Plus className="w-5 h-5 mr-2 text-primary" /> Nouvelle Zone</h2>
                            <form onSubmit={handleCreateZone} className="space-y-4">
                                <div><label className="text-sm font-bold text-slate-700 dark:text-slate-300">Nom de la Zone</label>
                                    <input type="text" required value={newZone.name} onChange={e => setNewZone({ ...newZone, name: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:border-primary focus:ring-1 focus:ring-primary outline-none transition-all" placeholder="ex: Open Space Ouest" /></div>

                                <div className="grid grid-cols-2 gap-4">
                                    <div><label className="text-sm font-bold text-slate-700 dark:text-slate-300">Type de Pièce</label>
                                        <select value={newZone.type} onChange={e => setNewZone({ ...newZone, type: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:border-primary outline-none transition-all">
                                            <option value="Office">Bureau</option><option value="Meeting Room">Salle de Réunion</option><option value="Hall">Hall / Accueil</option><option value="Storage">Stockage</option><option value="Retail">Espace de Vente</option>
                                        </select></div>
                                    <div><label className="text-sm font-bold text-slate-700 dark:text-slate-300">Étage (Niveau)</label>
                                        <input type="text" required value={newZone.floor} onChange={e => setNewZone({ ...newZone, floor: e.target.value })} className="w-full p-2.5 mt-1 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-lg text-slate-900 dark:text-white focus:border-primary outline-none transition-all" placeholder="ex: R+1" /></div>
                                </div>

                                <button type="submit" className="w-full py-3 mt-6 bg-primary hover:bg-emerald-400 text-white font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.4)]">Créer la Zone</button>
                            </form>
                        </div>
                    </div>
                )}
        </div>
    );
}
