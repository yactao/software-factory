"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useTenant } from "@/lib/TenantContext";
import { Lock, Mail, ArrowRight, Loader2, Hexagon } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LoginPage() {
    const router = useRouter();
    const { login } = useTenant();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setIsLoading(true);

        try {
            const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3001";
            const res = await fetch(`${API_URL}/api/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });

            if (res.ok) {
                const data = await res.json();
                // We'll add JWT token logic in TenantContext next
                await login(data.access_token, data.user);
                router.push("/");
            } else {
                setError("Email ou mot de passe incorrect");
            }
        } catch (err) {
            setError("Impossible de contacter le serveur d'authentification.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-slate-50 dark:bg-[#0B1120] relative overflow-hidden">
            {/* Background Decorations */}
            <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-primary/10 to-transparent pointer-events-none"></div>
            <div className="absolute top-1/4 -left-64 w-[500px] h-[500px] bg-emerald-500/20 rounded-full blur-[120px] pointer-events-none mix-blend-screen"></div>
            <div className="absolute bottom-1/4 -right-64 w-[500px] h-[500px] bg-cyan-500/10 rounded-full blur-[120px] pointer-events-none mix-blend-screen"></div>

            <div className="w-full max-w-md p-8 glass-card rounded-3xl border border-slate-200 dark:border-white/10 relative z-10 shadow-2xl">
                <style>{`
                    @keyframes spin-honeycomb {
                        0% { transform: rotateY(-270deg) rotateX(15deg) scale(0.6); opacity: 0; }
                        45% { transform: rotateY(15deg) rotateX(5deg) scale(1.05); opacity: 1; }
                        100% { transform: rotateY(0deg) rotateX(0deg) scale(1); opacity: 1; }
                    }
                    .animate-spin-3d {
                        animation: spin-honeycomb 2.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards;
                        transform-style: preserve-3d;
                    }
                    @keyframes hex-1-anim {
                        0%, 50% { transform: translateZ(8px) translateX(12px) scale(1); }
                        100% { transform: translateZ(0px) translateX(-16px) scale(1); }
                    }
                    @keyframes hex-2-anim {
                        0%, 50% { transform: translateZ(0px) translateX(12px) scale(1); opacity: 0.6; stroke-width: 2; }
                        100% { transform: translateZ(0px) translate(36px, 28px) scale(0.65); opacity: 1; stroke-width: 3; }
                    }
                    @keyframes hex-3-anim {
                        0%, 50% { transform: translateZ(-8px) translateX(12px) scale(1); opacity: 0.4; stroke-width: 2; }
                        100% { transform: translateZ(0px) translate(40px, -34px) scale(0.40); opacity: 1; stroke-width: 4; }
                    }

                    .hex-1 { animation: hex-1-anim 2.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }
                    .hex-2 { animation: hex-2-anim 2.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }
                    .hex-3 { animation: hex-3-anim 2.5s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; }
                `}</style>
                <div className="flex flex-col items-center mb-10">
                    <div className="relative w-32 h-24 mb-6" style={{ perspective: '1000px' }}>
                        {/* Glow effect */}
                        <div className="absolute inset-0 bg-emerald-500/15 blur-2xl rounded-full"></div>
                        <div className="w-full h-full relative animate-spin-3d flex items-center justify-center">
                            {/* Small */}
                            <Hexagon className="absolute w-20 h-20 text-emerald-400 hex-3" />
                            {/* Medium */}
                            <Hexagon className="absolute w-20 h-20 text-emerald-500 hex-2" />
                            {/* Large front */}
                            <Hexagon className="absolute w-20 h-20 text-emerald-500 drop-shadow-[0_0_15px_rgba(16,185,129,0.5)] hex-1" strokeWidth={2} />
                        </div>
                    </div>
                    <h1 className="text-4xl font-extrabold bg-gradient-to-r from-slate-900 to-slate-600 dark:from-white dark:to-white/60 bg-clip-text text-transparent mb-1 tracking-tight">
                        UBBEE
                    </h1>
                    <p className="text-[11px] font-bold text-emerald-500 uppercase tracking-[0.3em] mb-4">
                        smart building
                    </p>
                    <p className="text-sm text-slate-500 dark:text-muted-foreground text-center">
                        Identifiez-vous pour accéder à votre espace de supervision énergétique.
                    </p>
                </div>

                {error && (
                    <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-xl flex items-start animate-in fade-in slide-in-from-top-2">
                        <p className="text-sm text-red-500 font-medium">{error}</p>
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Adresse Email</label>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Mail className="h-5 w-5 text-slate-400" />
                            </div>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/50 focus:border-primary/50 outline-none transition-all placeholder:text-slate-400"
                                placeholder="admin@ubbee.fr"
                                required
                            />
                        </div>
                    </div>

                    <div className="space-y-2">
                        <div className="flex items-center justify-between">
                            <label className="text-sm font-medium text-slate-700 dark:text-slate-300">Mot de Passe</label>
                        </div>
                        <div className="relative">
                            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                                <Lock className="h-5 w-5 text-slate-400" />
                            </div>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full pl-10 pr-4 py-3 bg-white dark:bg-black/40 border border-slate-200 dark:border-white/10 rounded-xl text-slate-900 dark:text-white focus:ring-2 focus:ring-primary/50 focus:border-primary/50 outline-none transition-all placeholder:text-slate-400"
                                placeholder="••••••••"
                                required
                            />
                        </div>
                    </div>

                    <div className="pt-2">
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full py-3.5 bg-primary hover:bg-emerald-400 text-slate-900 dark:text-white font-bold rounded-xl transition-all flex items-center justify-center shadow-[0_0_15px_rgba(16,185,129,0.3)] hover:shadow-[0_0_25px_rgba(16,185,129,0.5)] disabled:opacity-70 disabled:cursor-not-allowed group"
                        >
                            {isLoading ? (
                                <Loader2 className="w-5 h-5 animate-spin" />
                            ) : (
                                <>
                                    Se Connecter
                                    <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
