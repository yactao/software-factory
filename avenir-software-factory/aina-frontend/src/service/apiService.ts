


//const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

const API_BASE = import.meta.env.VITE_API_BASE || "";

export interface ApiResponse<T = any> {
  answer: string;
  rows?: T[];
  used_docs?: any[];
  citations?: any[];
  conversation_id?: string;
  model?: string;
}

export interface SearchResponse {
  answer: string;
  used_docs?: any[];
  conversation_id?: string;
  model?: string;
}

export const callApi = async <T = any>(
  endpoint: string,
  payload: Record<string, any>
): Promise<ApiResponse<T>> => {
  const token = localStorage.getItem("saas_auth_token");
  let accessToken = token ? token : "mock-token";

  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return res.json();
};

// Nouvelle fonction spécifique pour la recherche
export const callSearchApi = async (
  payload: { prompt: string; conversation_id?: string }
): Promise<SearchResponse> => {
  const token = localStorage.getItem("saas_auth_token");
  let accessToken = token || "mock-token";

  const res = await fetch(`${API_BASE}/api/search`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return res.json();
};
