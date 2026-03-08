import { Network, Shield } from "lucide-react";

export function RestrictedTab({ activeTab }: { activeTab: string }) {
    return (
        <div className="h-full flex flex-col items-center justify-center text-slate-500 dark:text-muted-foreground space-y-4 py-20">
            <LockIcon tab={activeTab} />
            <p className="text-sm font-bold text-orange-500/70 py-1 px-4 border border-orange-500/20 bg-orange-500/10 rounded-full">Zone restreinte par UBBEE Infrastructures</p>
            <p className="text-sm text-center max-w-sm">La gestion du réseau MQTT IoT et des protocoles de sécurité avancée et cryptage SSL sont gérés directement par nos équipes infogérance.</p>
        </div>
    );
}

function LockIcon({ tab }: { tab: string }) {
    if (tab === "network") return <Network className="h-16 w-16 opacity-20" />;
    return <Shield className="h-16 w-16 opacity-20" />;
}
