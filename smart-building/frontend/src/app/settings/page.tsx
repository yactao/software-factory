"use client";

import { Settings, Bell, Network, Shield, Users, Clock, Palette, Webhook, Terminal } from "lucide-react";
import { cn } from "@/lib/utils";
import { useState } from "react";
import { useSettingsState } from "./useSettingsState";

// Import Tabs
import { SystemTab } from "./components/tabs/SystemTab";
import { UsersTab } from "./components/tabs/UsersTab";
import { PlanningTab } from "./components/tabs/PlanningTab";
import { AppearanceTab } from "./components/tabs/AppearanceTab";
import { IntegrationsTab } from "./components/tabs/IntegrationsTab";
import { NotificationsTab } from "./components/tabs/NotificationsTab";
import { RestrictedTab } from "./components/tabs/RestrictedTab";
import { ConsoleTab } from "./components/tabs/ConsoleTab";

// Import Modals
import { InviteUserModal } from "./components/modals/InviteUserModal";
import { AddExceptionModal } from "./components/modals/AddExceptionModal";
import { RoleProfileModal } from "./components/modals/RoleProfileModal";

export default function SettingsPage() {
    const [activeTab, setActiveTab] = useState("system");
    const state = useSettingsState(activeTab);

    const tabs = [
        { id: "system", label: "Système", icon: Settings },
        { id: "users", label: "Utilisateurs", icon: Users },
        { id: "planning", label: "Horaires Prédéfinis", icon: Clock },
        { id: "appearance", label: "Marque Blanche", icon: Palette },
        { id: "integrations", label: "API & Webhooks", icon: Webhook },
        { id: "notifications", label: "Notifications", icon: Bell },
        { id: "network", label: "Réseau & MQTT", icon: Network },
        { id: "logs", label: "Console & Logs", icon: Terminal },
        { id: "security", label: "Sécurité", icon: Shield },
    ];

    return (
        <div className="space-y-8 max-w-[1400px] mx-auto pt-4 pb-12">
            {/* Header */}
            <div className="border-b border-slate-200 dark:border-white/5 pb-6">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-2 flex items-center">
                    <Settings className="h-8 w-8 text-primary mr-3" />
                    Paramètres Avancés
                </h1>
                <p className="text-slate-500 dark:text-muted-foreground font-medium">Gestion fine de la plateforme, utilisateurs, et intégrations avec le SI.</p>
            </div>

            <div className="flex flex-col md:flex-row gap-8">
                {/* Settings Sidebar */}
                <div className="w-full md:w-64 flex flex-col gap-1">
                    {tabs.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={cn(
                                "w-full flex items-center px-4 py-3 rounded-xl text-sm font-bold transition-all text-left group",
                                activeTab === tab.id
                                    ? "bg-primary text-slate-900 dark:text-white shadow-md shadow-primary/20"
                                    : "text-slate-500 hover:text-slate-900 dark:hover:text-white hover:bg-slate-100 dark:hover:bg-white/5"
                            )}
                        >
                            <tab.icon className={cn("h-4 w-4 mr-3 transition-colors", activeTab === tab.id ? "text-slate-900 dark:text-white" : "text-slate-400 group-hover:text-primary")} />
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Settings Content Area */}
                <div className="flex-1 glass-card p-8 rounded-2xl min-h-[600px] border-slate-200 dark:border-white/5 animate-in fade-in zoom-in-95 duration-300">
                    {activeTab === "system" && <SystemTab state={state} />}
                    {activeTab === "users" && <UsersTab state={state} />}
                    {activeTab === "planning" && <PlanningTab state={state} />}
                    {activeTab === "appearance" && <AppearanceTab state={state} />}
                    {activeTab === "integrations" && <IntegrationsTab />}
                    {activeTab === "notifications" && <NotificationsTab state={state} />}
                    {activeTab === "logs" && <ConsoleTab />}
                    {["network", "security"].includes(activeTab) && <RestrictedTab activeTab={activeTab} />}
                </div>
            </div>

            {/* Modals */}
            <InviteUserModal state={state} />
            <AddExceptionModal state={state} />
            <RoleProfileModal state={state} />
        </div>
    );
}
