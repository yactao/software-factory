"use client";

import { useState, useEffect } from "react";
import { DndContext, useDraggable, useDroppable } from "@dnd-kit/core";
import { Activity, Database, GripVertical, Save, Wifi, Settings2, QrCode, MapPin, Building2, Hexagon, Layers, Search, Cpu, FileJson, Play } from "lucide-react";
import { useTenant } from "@/lib/TenantContext";

// --- DND COMPONENTS (Avancé) ---
function DraggableSourceKey({ id, text }: { id: string, text: string }) {
    const { attributes, listeners, setNodeRef, transform } = useDraggable({ id });
    const style = transform ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` } : undefined;

    return (
        <div ref={setNodeRef} style={style} {...listeners} {...attributes} className="p-3 mb-3 bg-white dark:bg-slate-800 rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 flex items-center cursor-grab active:cursor-grabbing hover:border-indigo-500 transition-colors z-10 relative">
            <GripVertical className="w-4 h-4 text-slate-400 mr-2" />
            <span className="font-mono text-sm font-bold text-slate-700 dark:text-slate-300">{"{ "}{text}{" }"}</span>
        </div>
    );
}

function DroppableTargetField({ id, label, mappedKey }: { id: string, label: string, mappedKey?: string }) {
    const { isOver, setNodeRef } = useDroppable({ id });

    return (
        <div ref={setNodeRef} className={`p-4 mb-4 rounded-xl border-2 border-dashed transition-all flex flex-col min-h-[80px] ${isOver ? "border-indigo-500 bg-indigo-500/10 shadow-[0_0_15px_rgba(99,102,241,0.2)]" : "border-slate-300 dark:border-slate-700"}`}>
            <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center">
                <Database className="w-3 h-3 mr-1" /> {label}
            </span>
            {mappedKey ? (
                <div className="bg-indigo-500 text-white p-2.5 rounded-lg text-sm font-bold flex items-center shadow-md">
                    Connecté : {mappedKey}
                </div>
            ) : (
                <div className="h-10 flex flex-1 items-center justify-center text-xs text-slate-400 dark:text-slate-500 italic bg-slate-100/50 dark:bg-slate-800/30 rounded-lg">
                    Glissez une clé JSON ici...
                </div>
            )}
        </div>
    );
}

// --- SHARED COMPONENTS ---
const LocationSelector = ({
    organizations,
    selectedOrgId, setSelectedOrgId,
    sites, selectedSiteId, setSelectedSiteId,
    zones, selectedZoneId, setSelectedZoneId,
    gateways, selectedGatewayId, setSelectedGatewayId
}: any) => (
    <div className="bg-white dark:bg-black/20 p-6 rounded-2xl border border-slate-200 dark:border-white/10 shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl -mr-10 -mt-10"></div>
        <h3 className="text-base font-bold text-slate-900 dark:text-white flex items-center mb-6 relative z-10">
            <MapPin className="w-5 h-5 mr-2 text-primary" /> Positionnement du Capteur
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 relative z-10">
            <div>
                <label className="text-xs font-bold text-slate-500 mb-2 flex items-center uppercase tracking-wider"><Building2 className="w-3 h-3 mr-1" /> Client / Organisation</label>
                <select
                    value={selectedOrgId}
                    onChange={e => { setSelectedOrgId(e.target.value); setSelectedSiteId(""); setSelectedZoneId(""); }}
                    className="w-full p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl text-sm font-medium text-slate-900 dark:text-white outline-none focus:border-primary transition-colors cursor-pointer"
                >
                    <option value="" className="text-slate-900 dark:text-white">Sélectionnez un client...</option>
                    {organizations.map((org: any) => (
                        <option key={org.id} value={org.id} className="text-slate-900 dark:text-white">{org.name}</option>
                    ))}
                </select>
            </div>
            <div>
                <label className="text-xs font-bold text-slate-500 mb-2 flex items-center uppercase tracking-wider"><Hexagon className="w-3 h-3 mr-1" /> Bâtiment / Site</label>
                <select
                    value={selectedSiteId}
                    onChange={e => { setSelectedSiteId(e.target.value); setSelectedZoneId(""); }}
                    disabled={!selectedOrgId}
                    className="w-full p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl text-sm font-medium text-slate-900 dark:text-white outline-none focus:border-primary transition-colors cursor-pointer disabled:opacity-50"
                >
                    <option value="" className="text-slate-900 dark:text-white">Sélectionnez un site...</option>
                    {sites?.map((site: any) => (
                        <option key={site.id} value={site.id} className="text-slate-900 dark:text-white">{site.name}</option>
                    ))}
                </select>
            </div>
            <div>
                <label className="text-xs font-bold text-slate-500 mb-2 flex items-center uppercase tracking-wider"><Layers className="w-3 h-3 mr-1" /> Espace / Zone</label>
                <select
                    value={selectedZoneId}
                    onChange={e => setSelectedZoneId(e.target.value)}
                    disabled={!selectedSiteId}
                    className="w-full p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl text-sm font-medium text-slate-900 dark:text-white outline-none focus:border-primary transition-colors cursor-pointer disabled:opacity-50"
                >
                    <option value="" className="text-slate-900 dark:text-white">Sélectionnez une zone...</option>
                    {zones?.map((zone: any) => (
                        <option key={zone.id} value={zone.id} className="text-slate-900 dark:text-white">{zone.name}</option>
                    ))}
                </select>
            </div>
            <div>
                <label className="text-xs font-bold text-slate-500 mb-2 flex items-center uppercase tracking-wider"><Wifi className="w-3 h-3 mr-1" /> U-Bot / Passerelle</label>
                <select
                    value={selectedGatewayId}
                    onChange={e => setSelectedGatewayId(e.target.value)}
                    disabled={!selectedSiteId}
                    className="w-full p-3 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl text-sm font-medium text-slate-900 dark:text-white outline-none focus:border-primary transition-colors cursor-pointer disabled:opacity-50"
                >
                    <option value="" className="text-slate-900 dark:text-white">Sélectionnez le U-Bot de rattachement...</option>
                    {gateways?.map((gw: any) => (
                        <option key={gw.id} value={gw.id} className="text-slate-900 dark:text-white">{gw.name} ({gw.serialNumber})</option>
                    ))}
                </select>
            </div>
        </div>
    </div>
);

// --- MAIN PAGE ---
export default function MappingPage() {
    const { authFetch } = useTenant();

    const [activeTab, setActiveTab] = useState<"simple" | "advanced">("simple");

    // Dynamic Location States
    const [organizations, setOrganizations] = useState<any[]>([]);
    const [selectedOrgId, setSelectedOrgId] = useState("");
    const [selectedSiteId, setSelectedSiteId] = useState("");
    const [selectedZoneId, setSelectedZoneId] = useState("");
    const [selectedGatewayId, setSelectedGatewayId] = useState("");

    useEffect(() => {
        const fetchOrgs = async () => {
            try {
                const res = await authFetch("http://localhost:3001/api/organizations");
                if (res.ok) {
                    const data = await res.json();
                    setOrganizations(data);
                }
            } catch (err) {
                console.error(err);
            }
        };
        fetchOrgs();
    }, [authFetch]);

    const activeOrg = organizations.find((o: any) => o.id === selectedOrgId);
    const sites = activeOrg?.sites || [];
    const activeSite = sites.find((s: any) => s.id === selectedSiteId);
    const zones = activeSite?.zones || [];
    const gateways = activeSite?.gateways || [];

    // States Avancés
    const [templateName, setTemplateName] = useState("Sonde Multi-paramètres (Custom MQTT)");
    const [topicPattern, setTopicPattern] = useState("zigbee2mqtt/0x00158d00045ab...");
    const [isSaving, setIsSaving] = useState(false);
    const [mappings, setMappings] = useState<Record<string, string>>({});

    const [jsonInput, setJsonInput] = useState('{\n  "temperature": 22.4,\n  "humidity": 45,\n  "battery": 98\n}');
    const [incomingSourceKeys, setIncomingSourceKeys] = useState<string[]>(["temperature", "humidity", "battery"]);

    // Analyser dynamiquement le JSON pour extraire les clés pointées (dot-notation)
    useEffect(() => {
        try {
            const obj = JSON.parse(jsonInput);
            const keys: string[] = [];
            const extractKeys = (o: any, prefix = '') => {
                for (const key in o) {
                    if (o[key] !== null && typeof o[key] === 'object' && !Array.isArray(o[key])) {
                        extractKeys(o[key], `${prefix}${key}.`);
                    } else {
                        keys.push(`${prefix}${key}`);
                    }
                }
            };
            extractKeys(obj);
            setIncomingSourceKeys(keys);
        } catch (e) {
            // Invalid JSON, on ignore on garde les anciennes clés
        }
    }, [jsonInput]);

    const standardFields = [
        { id: "mesure_temperature_celsius", label: "Température (°C)" },
        { id: "mesure_humidite", label: "Humidité (%)" },
        { id: "mesure_co2", label: "Taux de CO2 (ppm)" },
        { id: "etat_occupation", label: "Présence détectée (Bool)" },
        { id: "niveau_luminosite", label: "Luminosité (Lux)" },
        { id: "niveau_batterie", label: "Batterie Équipement (%)" }
    ];

    const handleDragEnd = (event: any) => {
        const { active, over } = event;
        if (over && over.id) {
            setMappings(prev => ({ ...prev, [over.id]: active.id }));
        }
    };

    const resetMapping = (targetFieldId: string) => {
        setMappings(prev => {
            const next = { ...prev };
            delete next[targetFieldId];
            return next;
        });
    };

    const saveMapping = async () => {
        const mappedItems = Object.entries(mappings).map(([target, source]) => ({ sourceKey: source, targetField: target }));

        // Mock save pour la démo
        setIsSaving(true);
        setTimeout(() => {
            alert(activeTab === "simple" ? "Équipement appairé et positionné avec succès !" : "Mapping avancé et positionnement sauvegardés avec succès !");
            setIsSaving(false);
        }, 1000);
    };

    return (
        <div className="max-w-[1400px] mx-auto p-6 space-y-8 pb-20 mt-4">
            {/* Header & Tabs */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white flex items-center mb-2">
                        <Activity className="w-8 h-8 mr-3 text-primary" /> Appairage & Hub IoT
                    </h1>
                    <p className="text-sm font-medium text-slate-500 dark:text-muted-foreground max-w-2xl">
                        Ajoutez de nouveaux équipements à votre parc ou configurez l'intégration d'anciens capteurs aux formats de données non standards.
                    </p>
                </div>
            </div>

            <div className="flex space-x-2 border-b border-slate-200 dark:border-white/10 pb-0 mb-8 overflow-x-auto custom-scrollbar">
                <button
                    onClick={() => setActiveTab('simple')}
                    className={`flex items-center px-6 py-4 text-sm font-bold transition-all border-b-2 whitespace-nowrap ${activeTab === 'simple'
                        ? 'border-primary text-primary bg-primary/5 dark:bg-primary/10 rounded-t-xl'
                        : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-white/5 rounded-t-xl'
                        }`}
                >
                    <Wifi className="w-5 h-5 mr-3" /> Nouveaux Équipements (Parc Simple)
                </button>
                <button
                    onClick={() => setActiveTab('advanced')}
                    className={`flex items-center px-6 py-4 text-sm font-bold transition-all border-b-2 whitespace-nowrap ${activeTab === 'advanced'
                        ? 'border-indigo-500 text-indigo-500 bg-indigo-500/5 dark:bg-indigo-500/10 rounded-t-xl'
                        : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-white/5 rounded-t-xl'
                        }`}
                >
                    <Settings2 className="w-5 h-5 mr-3" /> Équipements Existants (Interop. Avancée)
                </button>
            </div>

            {/* TAB: SIMPLE */}
            {activeTab === "simple" && (
                <div className="space-y-6 animate-in fade-in zoom-in-95 duration-300">
                    <div className="flex flex-col lg:flex-row gap-6">
                        <div className="flex-1 bg-white dark:bg-[#0B1120] p-8 rounded-2xl border border-slate-200 dark:border-white/10 shadow-sm relative overflow-hidden">
                            <div className="absolute top-0 right-0 p-8 opacity-5 pointer-events-none">
                                <QrCode className="w-48 h-48" />
                            </div>

                            <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center mb-2">
                                <QrCode className="w-6 h-6 mr-3 text-primary" /> Provisionnement Rapide (Plug & Play)
                            </h2>
                            <p className="text-sm text-slate-500 mb-8 max-w-xl">
                                Cette méthode est idéale pour les capteurs officiellement certifiés UBBEE ou pré-configurés. Entrez simplement l'identifiant réseau pour déclencher l'auto-découverte.
                            </p>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 relative z-10">
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-widest block">Type / Modèle de l'équipement</label>
                                    <select className="w-full p-3.5 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl text-sm font-medium text-slate-900 dark:text-white outline-none focus:border-primary transition-colors cursor-pointer appearance-none">
                                        <option>Sonde Multimédia UBBEE (Temp/Hum/CO2)</option>
                                        <option>Détecteur de Présence Infrarouge (PIR)</option>
                                        <option>Compteur d'Énergie Monophasé (Modbus/IP)</option>
                                        <option>Contrôleur CVC Tertiaire</option>
                                    </select>
                                </div>
                                <div className="space-y-2">
                                    <label className="text-xs font-bold text-slate-700 dark:text-slate-300 uppercase tracking-widest block">ID Matériel / Adresse MAC / DevEUI</label>
                                    <div className="flex gap-2">
                                        <input type="text" placeholder="ex: 00:1A:2B:3C:4D:5E" className="flex-1 p-3.5 bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl text-sm text-slate-900 dark:text-white outline-none focus:border-primary font-mono uppercase transition-colors" />
                                        <button className="px-5 bg-slate-100 dark:bg-white/10 text-slate-700 dark:text-white rounded-xl hover:bg-slate-200 dark:hover:bg-white/20 transition-colors flex items-center justify-center font-bold text-sm shadow-sm">
                                            <Search className="w-4 h-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="lg:w-1/3 bg-gradient-to-br from-primary/10 to-emerald-500/5 dark:from-primary/20 dark:to-emerald-500/10 p-8 rounded-2xl border border-primary/20 flex flex-col justify-center items-center text-center shadow-inner">
                            <div className="w-20 h-20 bg-white dark:bg-black/40 rounded-full flex items-center justify-center mb-6 border border-primary/30 shadow-lg relative">
                                <span className="absolute w-full h-full rounded-full border border-primary/50 animate-ping opacity-75"></span>
                                <Wifi className="w-10 h-10 text-primary" />
                            </div>
                            <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Prêt à appairer</h3>
                            <p className="text-xs font-medium text-slate-600 dark:text-slate-400 mb-8 max-w-xs">
                                Assurez-vous que le capteur est sous tension et en mode appairage (LED clignotante) avant de valider la configuration.
                            </p>
                            <button onClick={saveMapping} disabled={isSaving} className="w-full py-4 bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white font-bold rounded-xl shadow-[0_0_15px_rgba(16,185,129,0.4)] hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] transition-all flex items-center justify-center">
                                {isSaving ? <Activity className="w-5 h-5 animate-spin" /> : "Lancer le Provisionning"}
                            </button>
                        </div>
                    </div>

                    <LocationSelector
                        organizations={organizations} selectedOrgId={selectedOrgId} setSelectedOrgId={setSelectedOrgId}
                        sites={sites} selectedSiteId={selectedSiteId} setSelectedSiteId={setSelectedSiteId}
                        zones={zones} selectedZoneId={selectedZoneId} setSelectedZoneId={setSelectedZoneId}
                        gateways={gateways} selectedGatewayId={selectedGatewayId} setSelectedGatewayId={setSelectedGatewayId}
                    />
                </div>
            )}

            {/* TAB: ADVANCED */}
            {activeTab === "advanced" && (
                <div className="space-y-6 animate-in fade-in zoom-in-95 duration-300">
                    <LocationSelector
                        organizations={organizations} selectedOrgId={selectedOrgId} setSelectedOrgId={setSelectedOrgId}
                        sites={sites} selectedSiteId={selectedSiteId} setSelectedSiteId={setSelectedSiteId}
                        zones={zones} selectedZoneId={selectedZoneId} setSelectedZoneId={setSelectedZoneId}
                        gateways={gateways} selectedGatewayId={selectedGatewayId} setSelectedGatewayId={setSelectedGatewayId}
                    />

                    <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 bg-indigo-50 dark:bg-indigo-950/20 p-6 rounded-2xl border border-indigo-100 dark:border-indigo-500/20">
                        <div className="flex flex-col md:flex-row gap-4 w-full md:w-auto flex-1">
                            <div className="flex-1">
                                <label className="text-[10px] uppercase font-bold text-indigo-800/60 dark:text-indigo-300/60 block mb-1">Nom du Flux / Matériel Ancien</label>
                                <input
                                    type="text"
                                    value={templateName}
                                    onChange={(e) => setTemplateName(e.target.value)}
                                    className="text-sm font-bold text-slate-900 dark:text-white bg-white/50 dark:bg-black/20 border border-indigo-200 dark:border-indigo-500/30 rounded-lg p-2.5 outline-none focus:border-indigo-500 w-full"
                                />
                            </div>
                            <div className="flex-1">
                                <label className="text-[10px] uppercase font-bold text-indigo-800/60 dark:text-indigo-300/60 block mb-1">Topic MQTT Spécifique du Capteur</label>
                                <input
                                    type="text"
                                    value={topicPattern}
                                    onChange={(e) => setTopicPattern(e.target.value)}
                                    className="text-sm font-bold font-mono text-slate-900 dark:text-white bg-white/50 dark:bg-black/20 border border-indigo-200 dark:border-indigo-500/30 rounded-lg p-2.5 outline-none focus:border-indigo-500 w-full"
                                />
                            </div>
                        </div>
                        <button
                            onClick={saveMapping}
                            disabled={isSaving}
                            className="shrink-0 w-full md:w-auto px-8 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white font-bold rounded-xl shadow-[0_0_15px_rgba(79,70,229,0.4)] hover:shadow-[0_0_20px_rgba(79,70,229,0.5)] transition-all flex items-center justify-center disabled:opacity-50"
                        >
                            <Save className="w-4 h-4 mr-2" />
                            {isSaving ? "Traduction..." : "Traduire & Associer"}
                        </button>
                    </div>

                    <DndContext onDragEnd={handleDragEnd}>
                        <div className="grid grid-cols-1 md:grid-cols-12 gap-8 bg-white dark:bg-[#0B1120] p-8 rounded-2xl border border-slate-200 dark:border-white/10 shadow-sm">

                            {/* Colonne SOURCE (JSON entrant) */}
                            <div className="md:col-span-5 bg-slate-50 dark:bg-black/30 p-6 rounded-2xl border border-slate-200 dark:border-white/5 flex flex-col max-h-[600px]">
                                <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-200 dark:border-white/10 shrink-0">
                                    <div>
                                        <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-widest flex items-center">
                                            Payload Brut (Source)
                                        </h3>
                                        <p className="text-[10px] text-slate-500 mt-1">Collez ou captez le format JSON</p>
                                    </div>
                                    <button onClick={() => setJsonInput('{\n  "data": {\n    "temp_c": 21.5,\n    "hum_pct": 55\n  },\n  "v_bat": 3.7\n}')} className="flex items-center text-[10px] bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 px-3 py-1.5 rounded font-bold border border-red-500/20 transition-colors">
                                        <Play className="w-3 h-3 mr-1.5 fill-current" /> Simuler un Flux Live
                                    </button>
                                </div>

                                <div className="mb-6 shrink-0">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 flex items-center"><FileJson className="w-3 h-3 mr-1" /> Payload JSON Échantillon</label>
                                    <textarea
                                        value={jsonInput}
                                        onChange={(e) => setJsonInput(e.target.value)}
                                        className="w-full h-32 p-3 bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl font-mono text-xs text-slate-700 dark:text-slate-300 outline-none focus:border-indigo-500 resize-none transition-colors"
                                        spellCheck="false"
                                    />
                                </div>

                                <h4 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3 shrink-0">Variables Extractées (Glissez vers la droite)</h4>
                                <div className="space-y-3 flex-1 overflow-y-auto pr-2 custom-scrollbar">
                                    {incomingSourceKeys.map(key => {
                                        const isMapped = Object.values(mappings).includes(key);
                                        return (
                                            <div key={key} className={`transition-all ${isMapped ? "opacity-30 pointer-events-none grayscale" : ""}`}>
                                                <DraggableSourceKey id={key} text={key} />
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>

                            {/* Flèche visuelle */}
                            <div className="hidden md:flex md:col-span-2 items-center justify-center">
                                <div className="flex flex-col items-center opacity-40">
                                    <div className="w-px h-16 bg-slate-300 dark:bg-slate-700"></div>
                                    <Cpu className="w-8 h-8 text-indigo-500 my-4" />
                                    <div className="w-px h-16 bg-slate-300 dark:bg-slate-700"></div>
                                </div>
                            </div>

                            {/* Colonne DESTINATION */}
                            <div className="md:col-span-5 bg-indigo-50/30 dark:bg-indigo-900/10 p-6 rounded-2xl border border-indigo-100 dark:border-indigo-500/10">
                                <div className="flex items-center justify-between mb-6 pb-4 border-b border-indigo-100 dark:border-indigo-500/10">
                                    <div>
                                        <h3 className="text-sm font-bold text-indigo-900 dark:text-indigo-100 uppercase tracking-widest flex items-center">
                                            Modèle Cible UBBEE
                                        </h3>
                                        <p className="text-[10px] text-indigo-500 mt-1">Format standardisé attendu</p>
                                    </div>
                                    <Database className="w-5 h-5 text-indigo-400" />
                                </div>

                                <div className="space-y-4">
                                    {standardFields.map(field => (
                                        <div key={field.id} className="relative group">
                                            <DroppableTargetField
                                                id={field.id}
                                                label={field.label}
                                                mappedKey={mappings[field.id]}
                                            />
                                            {mappings[field.id] && (
                                                <button
                                                    onClick={() => resetMapping(field.id)}
                                                    className="absolute top-2 right-2 text-[10px] font-bold text-rose-500 opacity-0 group-hover:opacity-100 transition-opacity bg-rose-50 dark:bg-rose-500/10 px-2 py-1 rounded border border-rose-500/20 hover:bg-rose-100"
                                                >
                                                    Retirer
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    </DndContext>
                </div>
            )}
        </div>
    );
}
