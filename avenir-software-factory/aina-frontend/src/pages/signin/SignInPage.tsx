import { useLocation, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "";

const SignInPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  // 🌙 Force Dark Mode on Mount
  useEffect(() => {
    document.documentElement.classList.add('dark');
    // Auto-redirect if already logged in
    if (localStorage.getItem("saas_auth_token")) {
      navigate("/", { replace: true });
    }
  }, [navigate]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      if (!response.ok) {
        throw new Error("Identifiants invalides");
      }

      const data = await response.json();
      localStorage.setItem("saas_auth_token", data.token);
      localStorage.setItem("saas_user", JSON.stringify(data.user));

      const from = (location.state as any)?.from?.pathname || "/";
      navigate(from, { replace: true });
    } catch (err: any) {
      console.error("Login failed:", err);
      setError(err.message || "La connexion a échoué. Veuillez réessayer.");
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center 
                      bg-gradient-to-r from-white via-slate-100 to-sky-100
                      dark:from-gray-950 dark:via-gray-900 dark:to-indigo-950
                      animate-gradient-x transition-colors duration-300
                      p-6">
      <div className="text-center max-w-md w-full bg-white/80 dark:bg-gray-800/80 backdrop-blur-lg rounded-2xl p-8 shadow-xl">
        <img
          src="/logo-blue.png"
          alt="Aïna Logo"
          className="mx-auto h-16 w-auto mb-6"
        />
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
          Bienvenue dans Aïna SaaS
        </h1>
        <p className="text-gray-700 dark:text-gray-300 mb-8">
          Connectez-vous pour accéder à votre espace Marketplace d'agents IA.
        </p>
        <form onSubmit={handleLogin} className="space-y-4">
          {error && <div className="text-red-500 bg-red-100/10 p-2 rounded">{error}</div>}
          <input
            type="email"
            placeholder="Adresse email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:ring-2 focus:ring-indigo-500"
          />
          <input
            type="password"
            placeholder="Mot de passe"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="w-full px-4 py-2 border border-gray-300 rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-white focus:ring-2 focus:ring-indigo-500"
          />
          <button
            type="submit"
            className="w-full py-3 px-6 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-lg shadow-md transition transform hover:scale-105 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
          >
            🔐 Se Connecter
          </button>
        </form>
        <p className="mt-6 text-xs text-gray-500 dark:text-gray-400">
          (Utilisez email: admin@aina-saas.local / password: admin)
        </p>
      </div>
    </div>
  );
};

export default SignInPage;