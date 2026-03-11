import { callApi } from "./apiService";

export const askTradingQuestion = async (question: string, top_k: number = 3, conversationId?: string) => {
    return callApi("/api/trading", { 
      question, 
      top_k,
      conversation_id: conversationId 
    });
  };
