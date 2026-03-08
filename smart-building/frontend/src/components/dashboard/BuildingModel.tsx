"use client";

import { useMemo, useState, useRef, useEffect } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls, Box, Html } from "@react-three/drei";
import * as THREE from "three";
import { Thermometer, Wind, MapPin, Layers, Settings2, Info, Users, Expand, Shrink } from "lucide-react";
import { cn } from "@/lib/utils";

interface BuildingModelProps {
    siteName?: string;
    zones?: any[];
    forceMockData?: boolean;
}

// Composant pour une "pièce" ou une "zone" dynamique
function Room({ position, size, zone, activeLayer, forceMockData }: any) {
    const [hovered, setHovered] = useState(false);

    const hasSensors = forceMockData || (zone.sensors && zone.sensors.length > 0);

    // Simulation de données temps réel par défaut pour le rendu visuel SEULEMENT si des capteurs existent
    const temperature = hasSensors ? (zone.temperature ?? (20 + Math.random() * 5)) : null; // 20 à 25°C
    const co2 = hasSensors ? (zone.co2 ?? (400 + Math.random() * 600)) : null; // 400 à 1000 ppm
    const isOccupied = hasSensors ? (zone.isOccupied ?? (Math.random() > 0.5)) : null;

    // Logique de coloration par couche (Layer)
    let baseColor = hasSensors ? "#334155" : "#cbd5e1"; // Ardoise si capteur, Gris clair si vide
    let opacity = hasSensors ? 0.6 : 0.2; // Plus transparent si vide
    let emissionColor = "#000000";

    if (hasSensors) {
        if (activeLayer === "temperature" && temperature !== null) {
            baseColor = temperature > 24 ? "#ef4444" : temperature < 21 ? "#3b82f6" : "#10b981";
        } else if (activeLayer === "co2" && co2 !== null) {
            baseColor = co2 > 800 ? "#f59e0b" : "#10b981"; // Orange si > 800ppm, vert sinon
        } else if (activeLayer === "occupancy" && isOccupied !== null) {
            baseColor = isOccupied ? "#8b5cf6" : "#475569"; // Violet si occupé, gris si vide
        }
    }

    if (hovered) {
        emissionColor = baseColor;
    }

    return (
        <group position={position}>
            {/* Sol de la pièce */}
            <Box args={[size[0] - 0.2, 0.1, size[2] - 0.2]} position={[0, -0.05, 0]}>
                <meshStandardMaterial color={baseColor} opacity={opacity} transparent />
            </Box>

            {/* Murs en verre (Glassmorphism 3D) */}
            <Box
                args={[size[0] - 0.2, size[1], size[2] - 0.2]}
                position={[0, size[1] / 2, 0]}
                onPointerOver={() => setHovered(true)}
                onPointerOut={() => setHovered(false)}
                onClick={() => console.log("Clic sur la zone:", zone.name)}
            >
                <meshPhysicalMaterial
                    color={baseColor}
                    emissive={emissionColor}
                    emissiveIntensity={hovered ? 0.5 : 0}
                    transmission={0.9}
                    opacity={opacity}
                    roughness={0.1}
                    metalness={0.1}
                    transparent
                />
            </Box>

            {/* Infobulle / Tag de la pièce */}
            <Html position={[0, size[1] + 0.3, 0]} center zIndexRange={[100, 0]} style={{ pointerEvents: "none" }}>
                <div className={`transition-all duration-300 ${hovered ? 'opacity-100 scale-110 translate-y-[-10px]' : 'opacity-80 scale-100'}`}>
                    <div className="glass px-3 py-2 rounded-xl text-slate-900 dark:text-white shadow-2xl whitespace-nowrap min-w-[140px] backdrop-blur-md border border-slate-200/50 dark:border-white/10 bg-white/80 dark:bg-black/60">
                        <p className="text-xs font-bold text-slate-900 dark:text-white/90 mb-1 border-b border-slate-200 dark:border-white/10 pb-1 flex justify-between items-center">
                            <span className="flex items-center"><MapPin className="w-3 h-3 mr-1 text-primary/70" /> {zone.name}</span>
                            {hovered && <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse ml-2" />}
                        </p>

                        <div className="flex flex-col gap-1.5 mt-1.5">
                            {(activeLayer === "temperature" || activeLayer === "all") && (
                                <div className="flex items-center justify-between text-[11px]">
                                    <span className="flex items-center text-slate-500 dark:text-muted-foreground"><Thermometer className="w-3 h-3 mr-1" /> Temp</span>
                                    <span className={`font-mono font-bold ${temperature === null ? 'text-slate-500' : temperature > 24 ? 'text-red-400' : temperature < 21 ? 'text-blue-400' : 'text-emerald-400'}`}>
                                        {temperature !== null ? `${temperature.toFixed(1)}°C` : 'N/A'}
                                    </span>
                                </div>
                            )}
                            {(activeLayer === "co2" || activeLayer === "all") && (
                                <div className="flex items-center justify-between text-[11px]">
                                    <span className="flex items-center text-slate-500 dark:text-muted-foreground"><Wind className="w-3 h-3 mr-1" /> CO2</span>
                                    <span className={`font-mono font-bold ${co2 === null ? 'text-slate-500' : co2 > 800 ? 'text-orange-400' : 'text-emerald-400'}`}>
                                        {co2 !== null ? `${co2.toFixed(0)} ppm` : 'N/A'}
                                    </span>
                                </div>
                            )}
                            {(activeLayer === "occupancy" || activeLayer === "all") && (
                                <div className="flex items-center justify-between text-[11px]">
                                    <span className="flex items-center text-slate-500 dark:text-muted-foreground"><Users className="w-3 h-3 mr-1" /> Bureau</span>
                                    <span className={`font-mono font-bold ${isOccupied === null ? 'text-slate-500' : isOccupied ? 'text-purple-400' : 'text-slate-400'}`}>
                                        {isOccupied !== null ? (isOccupied ? 'Occupé' : 'Vide') : 'N/A'}
                                    </span>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </Html>
        </group>
    );
}

export function BuildingModel({ siteName = "Bâtiment Principal", zones = [], forceMockData = false }: BuildingModelProps) {
    const [selectedFloor, setSelectedFloor] = useState("Tous");
    const [activeLayer, setActiveLayer] = useState("temperature"); // temperature, co2, occupancy, all

    const [isExpanded, setIsExpanded] = useState(false);
    const containerRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleFullscreenChange = () => {
            setIsExpanded(!!document.fullscreenElement);
        };
        document.addEventListener('fullscreenchange', handleFullscreenChange);
        return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
    }, []);

    const toggleFullscreen = async () => {
        if (!document.fullscreenElement) {
            if (containerRef.current?.requestFullscreen) {
                await containerRef.current.requestFullscreen();
            }
        } else {
            if (document.exitFullscreen) {
                await document.exitFullscreen();
            }
        }
    };

    // Fix for Demo: If we force mock data (because site has a gateway) but the site has NO zones configured yet,
    // we inject default mock zones so the 3D twin isn't completely empty!
    const displayZones = useMemo(() => {
        if (forceMockData && (!zones || zones.length === 0)) {
            if (siteName.toLowerCase().includes('hotel')) {
                return [
                    { id: 'mock-h1', name: 'Réception & Lobby', floor: 'RDC', position: [-2, 0, 1], size: [4, 1.5, 3] },
                    { id: 'mock-h2', name: 'Restaurant', floor: 'RDC', position: [2.5, 0, 1], size: [3, 1.5, 3] },
                    { id: 'mock-h3', name: 'Chambre 101', floor: 'Étage 1', position: [-2.5, 0, 1], size: [2, 1.5, 2] },
                    { id: 'mock-h4', name: 'Chambre 102', floor: 'Étage 1', position: [0.5, 0, 1], size: [2, 1.5, 2] },
                    { id: 'mock-h5', name: 'Suite 103', floor: 'Étage 1', position: [3.5, 0, 1], size: [2.5, 1.5, 2] },
                    { id: 'mock-h6', name: 'Chambre 201', floor: 'Étage 2', position: [-2.5, 0, 1], size: [2, 1.5, 2] },
                    { id: 'mock-h7', name: 'Chambre 202', floor: 'Étage 2', position: [0.5, 0, 1], size: [2, 1.5, 2] },
                    { id: 'mock-h8', name: 'Suite Présidentielle', floor: 'Étage 2', position: [3.5, 0, 1], size: [2.5, 1.5, 2] },
                ];
            } else {
                return [
                    { id: 'mock-1', name: 'Zone Principale', floor: 'RDC', position: [-2, 0, 0], size: [3, 1.5, 3] },
                    { id: 'mock-2', name: 'Zone Secondaire', floor: 'RDC', position: [2, 0, 0], size: [2.5, 1.5, 2.5] }
                ];
            }
        }
        return zones || [];
    }, [zones, forceMockData, siteName]);

    const availableFloors = useMemo(() => {
        return displayZones.length > 0 ? ["Tous", ...Array.from(new Set(displayZones.map(z => z.floor || "RDC")))] : ["Tous"];
    }, [displayZones]);

    const getFloorOffset = (floorName: string) => {
        if (!floorName) return 0;
        const low = floorName.toLowerCase();
        if (low.includes("1")) return 3.5;
        if (low.includes("2")) return 7.0;
        if (low.includes("3")) return 10.5;
        return 0; // RDC
    };

    const currentFloorZones = useMemo(() => {
        return selectedFloor === "Tous"
            ? displayZones
            : displayZones.filter(z => (z.floor || "RDC") === selectedFloor);
    }, [displayZones, selectedFloor]);

    // Calcule la taille totale du plancher dynamiquement pour le background
    const floorWidth = 10;
    const floorDepth = 10;

    return (
        <div ref={containerRef} className={cn(
            "w-full relative flex flex-col pointer-events-auto overflow-hidden shadow-inner transition-all duration-300",
            isExpanded ? "fixed inset-0 z-[100] bg-slate-100 dark:bg-slate-900 rounded-none w-screen h-screen" : "h-full bg-slate-50 dark:bg-black/20 rounded-xl"
        )}>
            {/* Si c'est en plein écran, on rajoute un bouton fermer en haut à droite avec plus de padding */}
            <button
                onClick={toggleFullscreen}
                className={cn(
                    "absolute z-20 p-3 bg-white/90 dark:bg-black/80 backdrop-blur-xl border border-slate-200 dark:border-white/10 rounded-2xl text-slate-500 hover:text-primary hover:bg-white dark:hover:bg-black transition-all shadow-xl hover:scale-105 active:scale-95",
                    isExpanded ? "bottom-6 right-6" : "bottom-4 right-4"
                )}
                title={isExpanded ? "Fermer le mode plein écran" : "Agrandir le jumeau numérique"}
            >
                {isExpanded ? <Shrink className="w-6 h-6" /> : <Expand className="w-5 h-5" />}
            </button>

            {/* UI Overlay: Filters & Controls */}

            {displayZones.length === 0 && (
                <div className="absolute inset-0 z-20 flex flex-col items-center justify-center bg-slate-50/80 dark:bg-black/80 backdrop-blur-sm rounded-xl">
                    <div className="glass px-6 py-8 rounded-2xl flex flex-col items-center text-center max-w-sm border border-slate-200 dark:border-white/10 shadow-xl">
                        <Layers className="w-12 h-12 text-slate-400 mb-4" />
                        <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-2">Jumeau Numérique Vide</h3>
                        <p className="text-sm text-slate-500">Ce site n'a pas encore de zones virtuelles (espaces, bureaux). Veuillez synchroniser les capteurs ou d'ajouter manuellement vos zones via le portail de Gestion de Parc.</p>
                    </div>
                </div>
            )}

            <div className={`absolute top-4 left-4 right-4 z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pointer-events-none ${displayZones.length === 0 ? 'opacity-30' : ''}`}>

                {/* Visual Layers / Filtres Métiers */}
                <div className="flex gap-2 pointer-events-auto bg-white/80 dark:bg-black/60 backdrop-blur-md p-1.5 rounded-xl border border-slate-200 dark:border-white/10 shadow-lg">
                    <button
                        onClick={() => setActiveLayer("temperature")}
                        className={`flex items-center px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${activeLayer === "temperature" ? "bg-primary text-white shadow-md" : "text-slate-500 hover:text-slate-900 dark:hover:text-white"}`}
                    >
                        <Thermometer className="w-3.5 h-3.5 mr-1.5" /> Thermique
                    </button>
                    <button
                        onClick={() => setActiveLayer("co2")}
                        className={`flex items-center px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${activeLayer === "co2" ? "bg-orange-500 text-white shadow-md" : "text-slate-500 hover:text-slate-900 dark:hover:text-white"}`}
                    >
                        <Wind className="w-3.5 h-3.5 mr-1.5" /> Qualité d'Air
                    </button>
                    <button
                        onClick={() => setActiveLayer("occupancy")}
                        className={`flex items-center px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${activeLayer === "occupancy" ? "bg-purple-500 text-white shadow-md" : "text-slate-500 hover:text-slate-900 dark:hover:text-white"}`}
                    >
                        <Users className="w-3.5 h-3.5 mr-1.5" /> Occupation
                    </button>
                </div>

                {/* Floor Selector */}
                <div className="flex items-center gap-2 pointer-events-auto">
                    <div className="flex bg-white/80 dark:bg-black/60 backdrop-blur-md border border-slate-200 dark:border-white/10 rounded-xl overflow-hidden shadow-lg p-1">
                        {availableFloors.map(floor => (
                            <button
                                key={floor}
                                onClick={() => setSelectedFloor(floor)}
                                className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${selectedFloor === floor ? "bg-slate-200 dark:bg-white/20 text-slate-900 dark:text-white" : "text-slate-500 hover:text-slate-900 dark:hover:text-white"}`}
                            >
                                {floor}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Bottom Legend */}
            <div className="absolute bottom-4 left-4 z-10 pointer-events-none p-3 bg-white/80 dark:bg-black/60 backdrop-blur-md border border-slate-200 dark:border-white/10 rounded-xl shadow-lg">
                <p className="text-[10px] uppercase font-bold text-slate-500 mb-2 tracking-widest flex items-center"><Info className="w-3 h-3 mr-1" /> Légende Temps Réel</p>
                <div className="flex items-center gap-4 text-xs font-medium text-slate-700 dark:text-slate-300">
                    {activeLayer === "temperature" && (
                        <>
                            <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-blue-500 mr-1.5 shadow-[0_0_5px_rgba(59,130,246,0.5)]"></span> &lt; 21°C (Froid)</span>
                            <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 mr-1.5 shadow-[0_0_5px_rgba(16,185,129,0.5)]"></span> Idéal</span>
                            <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-red-500 mr-1.5 shadow-[0_0_5px_rgba(239,68,68,0.5)]"></span> &gt; 24°C (Chaud)</span>
                        </>
                    )}
                    {activeLayer === "co2" && (
                        <>
                            <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-emerald-500 mr-1.5 shadow-[0_0_5px_rgba(16,185,129,0.5)]"></span> &lt; 800 ppm</span>
                            <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-orange-500 mr-1.5 shadow-[0_0_5px_rgba(245,158,11,0.5)]"></span> &gt; 800 ppm (Aérer)</span>
                        </>
                    )}
                    {activeLayer === "occupancy" && (
                        <>
                            <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-slate-400 mr-1.5 shadow-[0_0_5px_rgba(148,163,184,0.5)]"></span> Salle Vide</span>
                            <span className="flex items-center"><span className="w-2.5 h-2.5 rounded-full bg-purple-500 mr-1.5 shadow-[0_0_5px_rgba(139,92,246,0.5)]"></span> Occupé (Actif)</span>
                        </>
                    )}
                </div>
            </div>

            {/* 3D Canvas */}
            <Canvas camera={{ position: [8, 12, 12], fov: 45 }} className="flex-1 pointer-events-auto">
                <ambientLight intensity={0.6} />
                <pointLight position={[10, 20, 10]} intensity={1.5} color="#ffffff" castShadow />
                <pointLight position={[-10, 15, -10]} intensity={0.5} color="#8b5cf6" />

                {/* Main Ground / Structure boundary */}
                {selectedFloor === "Tous" ? (
                    availableFloors.filter(f => f !== "Tous").map(f => {
                        const yOffset = getFloorOffset(f);
                        return (
                            <Box key={f} args={[floorWidth, 0.1, floorDepth]} position={[0, yOffset - 0.1, 0]}>
                                <meshStandardMaterial color="#0f172a" opacity={yOffset > 0 ? 0.3 : 0.8} transparent />
                                <lineSegments>
                                    <edgesGeometry args={[new THREE.BoxGeometry(floorWidth, 0.1, floorDepth)]} />
                                    <lineBasicMaterial color="#334155" opacity={0.6} transparent />
                                </lineSegments>
                                {yOffset > 0 && (
                                    <Html position={[-floorWidth / 2 + 0.5, 0.2, floorDepth / 2 - 0.5]} transform rotation={[-Math.PI / 2, 0, 0]}>
                                        <div className="text-slate-500 font-extrabold text-2xl opacity-40 pointer-events-none select-none tracking-widest uppercase">
                                            {f}
                                        </div>
                                    </Html>
                                )}
                            </Box>
                        );
                    })
                ) : (
                    <Box args={[floorWidth, 0.1, floorDepth]} position={[0, -0.1, 0]}>
                        <meshStandardMaterial color="#0f172a" opacity={0.8} transparent />
                        <lineSegments>
                            <edgesGeometry args={[new THREE.BoxGeometry(floorWidth, 0.1, floorDepth)]} />
                            <lineBasicMaterial color="#334155" />
                        </lineSegments>
                    </Box>
                )}

                {/* Zones rendering */}
                <group position={[0, 0, 0]}>
                    {currentFloorZones.map((z, idx) => {
                        const yOffset = selectedFloor === "Tous" ? getFloorOffset(z.floor || "RDC") : 0;
                        const pos = z.position || [(idx % 3) * 3 - 3, 0, Math.floor(idx / 3) * 3 - 1.5];
                        const stableKey = z.id || `zone-${z.name || 'unnamed'}-${idx}-${pos[0]}-${pos[1]}-${pos[2]}`;
                        return (
                            <Room
                                key={stableKey}
                                position={[pos[0], pos[1] + yOffset, pos[2]]}
                                size={z.size || [2.5, 1.5, 2.5]}
                                zone={z}
                                activeLayer={activeLayer}
                                forceMockData={forceMockData}
                            />
                        );
                    })}
                </group>

                {/* Interactivity Controls */}
                <OrbitControls
                    enablePan={true}
                    minPolarAngle={0}
                    maxPolarAngle={Math.PI / 2.1} // Prevent looking completely from below
                    minDistance={5}
                    maxDistance={45}
                    autoRotate={selectedFloor === "Tous"}
                    autoRotateSpeed={0.5}
                    target={[0, selectedFloor === "Tous" ? 4 : 0, 0]}
                />
            </Canvas>
        </div>
    );
}
