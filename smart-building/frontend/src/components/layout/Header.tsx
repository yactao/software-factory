"use client";

import { Bell, ChevronDown, User, Search, LogOut, Briefcase, Sun, Moon, Building2, CheckCircle2 } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";
import { useTenant } from "@/lib/TenantContext";
import { GlobalSearch } from "./GlobalSearch";
import { useTheme } from "next-themes";
import { usePathname } from "next/navigation";
import { WeatherWidget } from "../dashboard/WeatherWidget";

export function Header() {
    const { currentTenant, logout, switchTenant, authFetch } = useTenant();
    const pathname = usePathname();
    const { theme, setTheme } = useTheme();
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [isAlertsOpen, setIsAlertsOpen] = useState(false);
    const [alerts, setAlerts] = useState<any[]>([]);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const alertsRef = useRef<HTMLDivElement>(null);
    const isAdmin = currentTenant?.role === "SUPER_ADMIN" || currentTenant?.role === "ENERGY_MANAGER";
    const [organizations, setOrganizations] = useState<any[]>([]);

    useEffect(() => {
        if (isAdmin) {
            authFetch("http://localhost:3001/api/organizations")
                .then(r => r.ok && r.json())
                .then(data => {
                    if (data) {
                        setOrganizations(data);
                    }
                })
                .catch(console.error);
        }
    }, [isAdmin, authFetch]);

    useEffect(() => {
        if (!currentTenant?.id) return;
        const fetchAlerts = async () => {
            try {
                const res = await authFetch("http://localhost:3001/api/alerts");
                if (res.ok) {
                    const data = await res.json();
                    setAlerts(data.filter((a: any) => a.active));
                }
            } catch (err) {
                console.error("Failed to load alerts", err);
            }
        };
        fetchAlerts();
        const interval = setInterval(fetchAlerts, 60000);
        return () => clearInterval(interval);
    }, [currentTenant, authFetch]);

    // Close dropdowns
    useEffect(() => {
        function handleClickOutside(event: MouseEvent) {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsProfileOpen(false);
            }
            if (alertsRef.current && !alertsRef.current.contains(event.target as Node)) {
                setIsAlertsOpen(false);
            }
        }
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);
    return (
        <header className="sticky top-0 w-full h-16 bg-white/90 dark:bg-slate-950/90 backdrop-blur-2xl border-b border-slate-200 dark:border-white/5 z-40 px-6 flex items-center justify-between transition-colors">
            {/* Search Bar - Global OmniSearch Component */}
            <GlobalSearch />

            {/* Right Actions / Profile (UBBEE mode) */}
            <div className="flex items-center space-x-6">

                {/* Weather Geolocation */}
                <WeatherWidget />

                {/* Global Client Switcher */}
                {isAdmin && organizations.length > 0 && (
                    <div className="relative group/tenant mr-2 hidden md:block">
                        <div className={`flex flex-col items-end pr-4 border-r border-slate-200 dark:border-white/10 ${pathname.match(/\/(sites|clients)\/[^/]+/) ? 'opacity-50 cursor-not-allowed' : ''}`}>
                            <span className="text-[9px] text-slate-500 uppercase font-bold tracking-widest leading-tight">Contexte Client</span>
                            <div className={`flex items-center text-xs font-bold ${pathname.match(/\/(sites|clients)\/[^/]+/) ? 'text-slate-500' : 'cursor-pointer hover:text-primary transition-colors text-slate-900 dark:text-white'}`}>
                                {currentTenant?.name} {!pathname.match(/\/(sites|clients)\/[^/]+/) && <ChevronDown className="h-3 w-3 ml-1 opacity-50" />}
                            </div>
                        </div>
                        {/* Dropdown for Tenants */}
                        {!pathname.match(/\/(sites|clients)\/[^/]+/) && (
                            <div className="absolute top-full right-0 mt-1 pt-1 w-64 bg-transparent opacity-0 invisible group-hover/tenant:opacity-100 group-hover/tenant:visible transition-all z-50">
                                <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-white/10 rounded-xl shadow-xl overflow-hidden mt-1">
                                    <div className="p-2 border-b border-slate-100 dark:border-white/5 bg-slate-50 dark:bg-white/5">
                                        <p className="text-[10px] font-bold text-slate-500 uppercase px-2">Basculer le contexte vers :</p>
                                    </div>
                                    <div className="max-h-64 overflow-y-auto custom-scrollbar p-1">
                                        <button
                                            onClick={() => switchTenant('11111111-1111-1111-1111-111111111111', 'Tous les clients')}
                                            className={cn(
                                                "w-full text-left px-3 py-2 text-xs font-bold rounded-lg flex items-center transition-colors border border-transparent mb-1",
                                                currentTenant?.id === '11111111-1111-1111-1111-111111111111' ? "bg-primary text-white" : "text-primary hover:bg-primary/10"
                                            )}
                                        >
                                            <Briefcase className="w-4 h-4 mr-2" />
                                            Vue d'ensemble
                                        </button>
                                        <div className="h-px w-full bg-slate-200 dark:bg-white/10 my-1"></div>
                                        {organizations.map(org => (
                                            <button
                                                key={org.id}
                                                onClick={() => switchTenant(org.id, org.name)}
                                                className={cn(
                                                    "w-full text-left px-3 py-2 text-xs font-bold rounded-lg flex items-center transition-colors border border-transparent",
                                                    currentTenant?.id === org.id ? "bg-primary/10 text-primary border-primary/20" : "text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-white/5"
                                                )}
                                            >
                                                <Building2 className="w-3.5 h-3.5 mr-2 opacity-70" />
                                                {org.name}
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}

                <button
                    onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                    className="relative p-2 rounded-full hover:bg-slate-100 dark:hover:bg-white/5 text-slate-500 dark:text-muted-foreground hover:text-slate-900 dark:hover:text-white transition-colors"
                >
                    {theme === 'dark' ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
                </button>

                {/* Notifications Bell */}
                <div className="relative" ref={alertsRef}>
                    <button
                        onClick={() => setIsAlertsOpen(!isAlertsOpen)}
                        className="relative p-2 rounded-full hover:bg-slate-100 dark:hover:bg-white/5 text-slate-500 dark:text-muted-foreground hover:text-slate-900 dark:hover:text-white transition-colors"
                    >
                        <Bell className="h-5 w-5" />
                        {alerts.length > 0 && (
                            <span className="absolute top-1.5 right-1.5 h-2.5 w-2.5 rounded-full bg-red-500 border-2 border-white dark:border-slate-950 shadow-[0_0_8px_rgba(239,68,68,0.6)] animate-pulse"></span>
                        )}
                    </button>

                    {/* Alerts Dropdown */}
                    {isAlertsOpen && (
                        <div className="absolute right-0 mt-2 w-80 bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-white/10 shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 duration-200 origin-top-right">
                            <div className="px-4 py-2 border-b border-slate-100 dark:border-white/5 flex items-center justify-between">
                                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Notifications</h3>
                                <span className="text-[10px] font-bold bg-primary/10 text-primary px-2 py-0.5 rounded-full">{alerts.length} nouvelle(s)</span>
                            </div>
                            <div className="max-h-[300px] overflow-y-auto px-2 py-2 flex flex-col space-y-1 custom-scrollbar">
                                {alerts.length === 0 ? (
                                    <div className="px-4 py-6 text-center text-slate-500 dark:text-slate-400 text-sm">
                                        <CheckCircle2 className="w-8 h-8 mx-auto mb-2 text-primary opacity-50" />
                                        Aucune alerte en cours.
                                    </div>
                                ) : (
                                    alerts.map((alert: any) => (
                                        <div key={alert.id} className="p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-white/5 border border-transparent hover:border-slate-100 dark:hover:border-white/5 transition-colors cursor-pointer group">
                                            <div className="flex items-start">
                                                <div className={`mt-0.5 w-2 h-2 rounded-full flex-shrink-0 mr-3 shadow-sm ${alert.severity === 'critical' ? 'bg-red-500 shadow-red-500/50' : alert.severity === 'warning' ? 'bg-orange-500 shadow-orange-500/50' : 'bg-blue-500 shadow-blue-500/50'}`} />
                                                <div>
                                                    <p className="text-[13px] font-bold text-slate-900 dark:text-white leading-tight mb-1 group-hover:text-primary transition-colors">{alert.message}</p>
                                                    <div className="flex items-center text-[10px] text-slate-500 dark:text-slate-400 font-medium space-x-2">
                                                        <span>{new Date(alert.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                                        <span>•</span>
                                                        <span className="truncate max-w-[150px]">{alert.sensor?.name || 'Equipement inconnu'}</span>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                            {alerts.length > 0 && (
                                <div className="px-4 py-2 border-t border-slate-100 dark:border-white/5">
                                    <button className="w-full text-center text-[11px] font-bold text-primary hover:text-primary/80 transition-colors uppercase tracking-wider">
                                        Voir toutes les alertes
                                    </button>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Profile Button (V3) */}
                <div className="relative" ref={dropdownRef}>
                    <div
                        className={cn(
                            "flex items-center cursor-pointer transition-all rounded-full pr-3 pl-1 py-1 border hover:bg-slate-100 dark:bg-white/5",
                            isProfileOpen ? "border-primary/50 bg-slate-50 dark:bg-white/5" : "border-transparent"
                        )}
                        onClick={() => setIsProfileOpen(!isProfileOpen)}
                    >
                        <div className="h-9 w-9 flex items-center justify-center rounded-full border border-primary/50 text-primary bg-primary/10 mr-3 shadow-[0_0_10px_rgba(16,185,129,0.2)]">
                            <User className="h-5 w-5" />
                        </div>
                        <div className="flex flex-col mr-2">
                            <span className="text-sm font-bold text-slate-900 dark:text-white leading-tight">{currentTenant?.userName || "Chargement..."}</span>
                            <span className="text-[10px] text-primary uppercase tracking-wider font-bold">{currentTenant?.name || "..."}</span>
                        </div>
                        <ChevronDown className={cn("h-4 w-4 text-slate-500 dark:text-muted-foreground ml-2 transition-transform duration-200", isProfileOpen ? "rotate-180" : "")} />
                    </div>

                    {isProfileOpen && (
                        <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-slate-950 rounded-xl border border-slate-200 dark:border-white/10 shadow-2xl py-2 z-50 animate-in fade-in zoom-in-95 duration-200 origin-top-right">
                            <div className="px-4 py-2 border-b border-slate-100 dark:border-white/5 mb-2 bg-primary/5">
                                <p className="text-xs font-bold text-primary uppercase tracking-wider">Connecté en tant que</p>
                                <p className="text-[10px] text-slate-500 dark:text-muted-foreground">{currentTenant?.role}</p>
                            </div>

                            <ul className="flex flex-col px-2 space-y-1">
                                <li>
                                    <button
                                        onClick={logout}
                                        className="w-full text-left px-3 py-2 text-sm rounded-lg flex items-center transition-colors text-red-500 hover:bg-red-500/10"
                                    >
                                        <LogOut className="h-4 w-4 mr-3" />
                                        <div className="font-bold">Déconnexion</div>
                                    </button>
                                </li>
                            </ul>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}
