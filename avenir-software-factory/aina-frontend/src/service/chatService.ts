

//const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const API_BASE = import.meta.env.VITE_API_BASE || "";

export interface Conversation {
  conversation_id: string;
  title: string;
  last_activity_utc: string;
  last_route: string;
}

export interface ChatMessage {
  role: string;
  route: string;
  message: string;
  timestamp_utc: string;
  meta?: any;
}


export interface DeleteAllResponse {
  deleted: boolean;
  route: string;
  conversations: string[];
  items: number;
}

export const agentRouteMap: Record<string, string> = {
  // Agents historiques
  "Aïna DOC": "rag",
  "Aïna Finance": "finance",
  "Aïna Search": "search",
  "Aïna Trading": "trading",
  "Aïna Vision": "vision",
  "Aïna Plaques": "vision-plaque",

  // 🚀 Agents Software Factory (Routés vers l'Orchestrateur / Worker asynchrone)
  "Aïna Architecte & PO": "dev",
  "Aïna FinOps Lead": "dev",
  "Aïna Clean Coder": "dev",
  "Aïna CISO": "dev",
  "Aïna Pentester": "dev",
  "Aïna Data Engineer": "dev",
  "Aïna Data Quality": "dev",
  "Aïna Data Governance": "dev",
  "Aïna Fullstack Node/React": "dev",
  "Aïna Compta": "finance",
  "Aïna RH & Recrutement": "rag"
};

const getAccessToken = async (): Promise<string> => {
  const token = localStorage.getItem("saas_auth_token");
  return token ? token : "mock-token";
};


export const chatService = {
  list: async (routeName: string): Promise<Conversation[]> => {
    const accessToken = await getAccessToken();

    const res = await fetch(`${API_BASE}/api/chat/list/${routeName}`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    const data = await res.json();
    return data.conversations || data; // Support both formats
  },

  history: async (conversationId: string): Promise<{ messages: ChatMessage[] }> => {
    const accessToken = await getAccessToken();

    const res = await fetch(`${API_BASE}/api/chat/history?conversation_id=${encodeURIComponent(conversationId)}`, {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return res.json();
  },

  rename: async (conversationId: string, title: string): Promise<void> => {
    const accessToken = await getAccessToken();

    const res = await fetch(`${API_BASE}/api/chat/rename`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${accessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ conversation_id: conversationId, title }),
    });

    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  },

  delete: async (conversationId: string): Promise<void> => {
    const accessToken = await getAccessToken();

    const res = await fetch(`${API_BASE}/api/chat/clear?conversation_id=${encodeURIComponent(conversationId)}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  },
  // Nouvelle méthode pour supprimer toutes les conversations d'une route
  deleteAll: async (routeName: string): Promise<DeleteAllResponse> => {
    const accessToken = await getAccessToken();

    const res = await fetch(`${API_BASE}/api/chat/clear-all/${encodeURIComponent(routeName)}`, {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    });

    if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
    return res.json();
  },
};
