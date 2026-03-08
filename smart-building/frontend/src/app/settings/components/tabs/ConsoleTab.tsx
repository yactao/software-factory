import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Shield, Cpu, Activity, RefreshCw } from 'lucide-react';

export function ConsoleTab() {
    const [activeChannel, setActiveChannel] = useState<'audit' | 'system' | 'iot'>('system');
    const [logs, setLogs] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const endOfLogsRef = useRef<HTMLDivElement>(null);

    const fetchLogs = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('hubbee_token');
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001'}/api/logs/${activeChannel}`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            if (res.ok) {
                const data = await res.json();
                if (activeChannel === 'audit') {
                    // data is an array of objects
                    setLogs(data);
                } else {
                    // data.logs is an array of objects for files
                    setLogs(data.logs || []);
                }
                setTimeout(() => {
                    endOfLogsRef.current?.scrollIntoView({ behavior: "smooth" });
                }, 100);
            } else {
                setLogs([{ message: `Erreur ${res.status}: L'accès à ce canal est restreint ou indisponible.` }]);
            }
        } catch (err) {
            setLogs([{ message: `Erreur de connexion au terminal.` }]);
        }
        setLoading(false);
    };

    useEffect(() => {
        fetchLogs();
    }, [activeChannel]);

    const renderLogEntry = (log: any, index: number) => {
        if (activeChannel === 'audit') {
            return (
                <div key={index} className="flex gap-4 text-sm font-mono border-b border-emerald-900/30 py-2">
                    <span className="text-emerald-500 whitespace-nowrap">[{new Date(log.timestamp).toLocaleString()}]</span>
                    <span className="text-cyan-400 w-48 truncate">[{log.user?.email || 'System'}]</span>
                    <span className="text-yellow-400 font-bold w-32">{log.action}</span>
                    <span className="text-slate-300 flex-1">{log.resource}</span>
                </div>
            );
        }

        // System or IoT logs
        const time = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : 'N/A';
        const levelStr = log.level ? log.level.toUpperCase() : 'INFO';
        const levelColor = levelStr === 'ERROR' ? 'text-rose-500' : (levelStr === 'WARN' ? 'text-amber-500' : 'text-blue-400');

        return (
            <div key={index} className="flex gap-4 text-sm font-mono border-b border-slate-800/50 py-1 hover:bg-white/[0.02]">
                <span className="text-slate-500 whitespace-nowrap">[{time}]</span>
                <span className={`${levelColor} font-bold w-16`}>{levelStr}</span>
                <span className="text-slate-300 break-words flex-1">{log.message || JSON.stringify(log)}</span>
            </div>
        );
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center">
                        <Terminal className="w-6 h-6 mr-3 text-emerald-500" /> Console & Logs
                    </h2>
                    <p className="text-slate-500 dark:text-slate-400 mt-1">Supervisez l'activité globale de la plateforme en temps réel.</p>
                </div>
                <button
                    onClick={fetchLogs}
                    disabled={loading}
                    className="flex items-center px-4 py-2 bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors"
                >
                    <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} /> Rafraîchir
                </button>
            </div>

            <div className="flex gap-2 p-1 bg-slate-100 dark:bg-[#0B1120] rounded-xl w-fit border border-slate-200 dark:border-white/5">
                <button
                    onClick={() => setActiveChannel('audit')}
                    className={`px-4 py-2 rounded-lg flex items-center text-sm font-bold transition-all ${activeChannel === 'audit'
                            ? 'bg-white dark:bg-slate-800 shadow-sm text-slate-900 dark:text-white border border-slate-200 dark:border-white/10'
                            : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                >
                    <Shield className="w-4 h-4 mr-2" /> Historique Métier
                </button>
                <button
                    onClick={() => setActiveChannel('system')}
                    className={`px-4 py-2 rounded-lg flex items-center text-sm font-bold transition-all ${activeChannel === 'system'
                            ? 'bg-white dark:bg-slate-800 shadow-sm text-slate-900 dark:text-white border border-slate-200 dark:border-white/10'
                            : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                >
                    <Activity className="w-4 h-4 mr-2" /> Logs API (Erreurs)
                </button>
                <button
                    onClick={() => setActiveChannel('iot')}
                    className={`px-4 py-2 rounded-lg flex items-center text-sm font-bold transition-all ${activeChannel === 'iot'
                            ? 'bg-white dark:bg-slate-800 shadow-sm text-slate-900 dark:text-white border border-slate-200 dark:border-white/10'
                            : 'text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                        }`}
                >
                    <Cpu className="w-4 h-4 mr-2" /> Traffic IoT (MQTT)
                </button>
            </div>

            <div className="bg-[#050505] border border-slate-800 rounded-xl overflow-hidden shadow-2xl">
                <div className="flex items-center px-4 py-2 bg-slate-900 border-b border-slate-800">
                    <div className="flex gap-1.5 mr-4">
                        <div className="w-3 h-3 rounded-full bg-rose-500"></div>
                        <div className="w-3 h-3 rounded-full bg-amber-500"></div>
                        <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                    </div>
                    <div className="text-xs font-mono text-slate-500">
                        hubbee-vps@root:~_{activeChannel}_logs
                    </div>
                </div>

                <div className="p-4 h-[500px] overflow-y-auto custom-scrollbar">
                    {loading && logs.length === 0 ? (
                        <div className="flex items-center justify-center h-full text-emerald-500 font-mono text-sm">
                            <RefreshCw className="w-5 h-5 mr-3 animate-spin" /> Fetching secure logs...
                        </div>
                    ) : logs.length === 0 ? (
                        <div className="text-slate-500 font-mono text-sm">Aucun événement enregistré dans ce canal.</div>
                    ) : (
                        <div className="space-y-1">
                            {logs.map((log, index) => renderLogEntry(log, index))}
                            <div ref={endOfLogsRef} />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
