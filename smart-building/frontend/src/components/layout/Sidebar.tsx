"use client";

import { LayoutDashboard, Briefcase, BarChart2, Wifi, CloudUpload, Settings, FileText, Receipt, Hexagon, ChevronDown, Sparkles, AlertTriangle, ChevronLeft, ChevronRight, Terminal, Package } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { useTenant } from "@/lib/TenantContext";

type NavItemType = {
    name: string;
    href?: string;
    icon: any;
    hasSub?: boolean;
    subItems?: { name: string; href: string }[];
};

const navItems: NavItemType[] = [
    { name: "Accueil", href: "/", icon: LayoutDashboard },
    { name: "Gestion de Parc", href: "/clients", icon: Briefcase },
    { name: "Carte Globale", href: "/map", icon: Hexagon },
    { name: "Rapports Énergétiques", href: "/energy", icon: BarChart2 },
    { name: "Générateur d'IA", href: "/rules", icon: Sparkles },
    { name: "Alertes & Maint.", href: "/alerts", icon: AlertTriangle },
    {
        name: "Infrastructure IoT", icon: Wifi, hasSub: true, subItems: [
            { name: "Vue d'ensemble", href: "/network" },
            { name: "Console IoT Live", href: "/network/console" },
            { name: "Appairage (No-Code)", href: "/admin/integrations/mapping" }
        ]
    },
    {
        name: "Administration", icon: Settings, hasSub: true, subItems: [
            { name: "Paramétrages", href: "/settings" },
            { name: "Facturation", href: "/billing" },
            { name: "Licence", href: "/license" },
            { name: "Supervision Serveur", href: "/network/system-health" }
        ]
    }
];

interface SidebarProps {
    isCollapsed: boolean;
    onToggle: () => void;
}

export function Sidebar({ isCollapsed, onToggle }: SidebarProps) {
    const pathname = usePathname();
    const { currentTenant } = useTenant();
    const [expandedMenu, setExpandedMenu] = useState<string | null>(null);

    // If collapsed, we force collapse all submenus
    const actualExpandedMenu = isCollapsed ? null : expandedMenu;

    if (!currentTenant) return null;

    const filteredNavItems = navItems.map(item => {
        if (item.name === "Gestion de Parc") {
            return {
                ...item,
                href: currentTenant.role === "CLIENT" ? "/sites" : "/clients"
            };
        }
        return item;
    }).map((item) => {
        if (currentTenant.role === "CLIENT" && item.subItems) {
            return {
                ...item,
                subItems: item.subItems.filter(sub => !["/rules", "/network", "/settings", "/license", "/onboarding", "/admin/integrations/mapping", "/network/inventory", "/network/console"].includes(sub.href))
            };
        }
        return item;
    }).filter((item) => {
        if (currentTenant.role === "CLIENT") {
            if (item.subItems && item.subItems.length === 0) return false;
            if (item.href && ["/rules", "/network", "/settings", "/license", "/onboarding", "/admin/integrations/mapping", "/network/inventory", "/network/console"].includes(item.href)) {
                return false;
            }
        }
        return true;
    });

    // --- Active State Calculation ---
    // Finds the single most specific matching href to avoid overlapping active states
    let bestActiveHref = "";
    let maxMatchLength = 0;

    filteredNavItems.forEach(group => {
        if (group.href) {
            if (pathname === group.href || (group.href !== "/" && pathname.startsWith(group.href + "/"))) {
                if (group.href.length > maxMatchLength) {
                    maxMatchLength = group.href.length;
                    bestActiveHref = group.href;
                }
            }
        }
        if (group.subItems) {
            group.subItems.forEach((sub: any) => {
                if (pathname === sub.href || (sub.href !== "/" && pathname.startsWith(sub.href + "/"))) {
                    if (sub.href.length > maxMatchLength) {
                        maxMatchLength = sub.href.length;
                        bestActiveHref = sub.href;
                    }
                }
            });
        }
    });

    return (
        <aside
            className={cn(
                "fixed top-4 bottom-4 left-4 z-50 flex flex-col rounded-3xl transition-all duration-300 ease-out border border-slate-200/50 dark:border-white/5 shadow-2xl backdrop-blur-3xl overflow-hidden",
                isCollapsed ? "w-[72px]" : "w-64",
                "bg-white/80 dark:bg-slate-950/80"
            )}
        >
            {/* Logo Area */}
            <div className="h-20 flex items-center justify-center shrink-0 border-b border-slate-200/50 dark:border-white/5 relative">
                <Hexagon className={cn("text-primary stroke-[1.5] transition-all duration-300", isCollapsed ? "h-8 w-8" : "h-7 w-7 absolute left-5")} />
                {!isCollapsed && (
                    <div className="flex flex-col absolute left-14">
                        <span className="text-xl font-black bg-gradient-to-br from-slate-900 to-slate-500 dark:from-white dark:to-white/40 bg-clip-text text-transparent leading-none">
                            UBBEE
                        </span>
                        <span className="text-[8px] font-bold text-primary tracking-[0.2em] mt-1">
                            BY IOTEVA
                        </span>
                    </div>
                )}
            </div>

            {/* Navigation */}
            <nav className="flex-1 overflow-y-auto overflow-x-hidden py-6 px-3 space-y-1.5 scrollbar-hide">
                {filteredNavItems.map((item) => {
                    if (item.subItems) {
                        const isExpanded = actualExpandedMenu === item.name;
                        const isChildActive = item.subItems.some((sub: any) => sub.href === bestActiveHref);
                        return (
                            <div key={item.name} className="flex flex-col space-y-1 relative group">
                                <button
                                    onClick={() => !isCollapsed && setExpandedMenu(isExpanded ? null : item.name)}
                                    className={cn(
                                        "flex items-center rounded-xl transition-all duration-300 w-full overflow-hidden",
                                        isCollapsed ? "justify-center h-12 w-12 mx-auto" : "justify-between px-4 py-3",
                                        isChildActive && !isExpanded
                                            ? "bg-primary text-white shadow-md shadow-primary/20"
                                            : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white dark:hover:bg-white/5"
                                    )}
                                >
                                    <div className="flex items-center justify-center">
                                        <item.icon className={cn(
                                            "transition-colors shrink-0",
                                            isCollapsed ? "h-5 w-5" : "h-5 w-5 mr-3",
                                            isChildActive && !isCollapsed ? "text-white" : "",
                                            (!isChildActive || isCollapsed) && "group-hover:scale-110 duration-300"
                                        )} />
                                        {!isCollapsed && <span className="font-semibold text-sm">{item.name}</span>}
                                    </div>
                                    {!isCollapsed && (
                                        <ChevronDown className={cn(
                                            "h-4 w-4 transition-transform duration-300 shrink-0",
                                            isExpanded ? "rotate-180" : ""
                                        )} />
                                    )}
                                </button>

                                {/* Tooltip when collapsed */}
                                {isCollapsed && (
                                    <div className="absolute left-14 top-1/2 -translate-y-1/2 ml-2 px-3 py-1.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50 shadow-xl">
                                        {item.name}
                                    </div>
                                )}

                                {!isCollapsed && isExpanded && (
                                    <div className="mt-1.5 ml-5 pl-4 border-l-2 border-slate-200 dark:border-slate-800 space-y-1">
                                        {item.subItems.map((subItem: any) => {
                                            const isSubActive = subItem.href === bestActiveHref;

                                            return (
                                                <Link
                                                    key={subItem.name}
                                                    href={subItem.href}
                                                    className={cn(
                                                        "flex items-center px-4 py-2.5 rounded-lg transition-all duration-200 text-sm font-medium",
                                                        isSubActive
                                                            ? "bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-bold"
                                                            : "text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5"
                                                    )}
                                                >
                                                    {subItem.name}
                                                </Link>
                                            )
                                        })}
                                    </div>
                                )}
                            </div>
                        );
                    }

                    let isActive = false;
                    if (item.href && item.href === bestActiveHref) {
                        isActive = true;
                    }

                    return (
                        <div key={item.name} className="relative group">
                            <Link
                                href={item.href || "#"}
                                className={cn(
                                    "flex items-center rounded-xl transition-all duration-300",
                                    isCollapsed ? "justify-center h-12 w-12 mx-auto" : "justify-between px-4 py-3 w-full",
                                    isActive
                                        ? "bg-gradient-to-r from-primary to-emerald-400 text-white shadow-lg shadow-primary/25"
                                        : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-white dark:hover:bg-white/5"
                                )}
                            >
                                <div className="flex items-center justify-center">
                                    <item.icon className={cn(
                                        "transition-transform shrink-0",
                                        isCollapsed ? "h-5 w-5" : "h-5 w-5 mr-3",
                                        isActive ? "text-white" : "group-hover:scale-110 duration-300"
                                    )} />
                                    {!isCollapsed && <span className="font-semibold text-sm">{item.name}</span>}
                                </div>
                            </Link>

                            {/* Tooltip when collapsed */}
                            {isCollapsed && (
                                <div className="absolute left-14 top-1/2 -translate-y-1/2 ml-2 px-3 py-1.5 bg-slate-900 dark:bg-white text-white dark:text-slate-900 text-xs font-bold rounded-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 whitespace-nowrap z-50 shadow-xl">
                                    {item.name}
                                </div>
                            )}
                        </div>
                    );
                })}
            </nav>

            {/* Toggle Button / Footer */}
            <div className="p-3 border-t border-slate-200/50 dark:border-white/5 flex justify-center shrink-0">
                <button
                    onClick={onToggle}
                    className="flex justify-center flex-1 items-center h-10 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-500 dark:text-slate-400 transition-colors"
                    title={isCollapsed ? "Déployer le menu" : "Réduire le menu"}
                >
                    {isCollapsed ? <ChevronRight className="h-5 w-5" /> : <ChevronLeft className="h-5 w-5" />}
                </button>
            </div>
        </aside>
    );
}
