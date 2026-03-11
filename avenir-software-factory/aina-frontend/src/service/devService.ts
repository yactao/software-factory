// src/service/devService.ts
const API_BASE = import.meta.env.VITE_API_BASE || "";

export interface DevResponse {
    answer: string;
    conversation_id: string;
    used_docs?: any[];
    model?: string;
}

const getAccessToken = async (): Promise<string> => {
    const token = localStorage.getItem("saas_auth_token");
    return token ? token : "mock-token";
};

export const askDevQuestion = async (
    question: string,
    conversationId?: string
): Promise<DevResponse> => {
    const accessToken = await getAccessToken();

    const payload = {
        question,
        conversation_id: conversationId,
    };

    const response = await fetch(`${API_BASE}/api/chat/dev`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken}`,
        },
        body: JSON.stringify(payload),
    });

    if (!response.ok) {
        throw new Error(`Erreur API Dev: ${response.statusText}`);
    }

    return response.json();
}
