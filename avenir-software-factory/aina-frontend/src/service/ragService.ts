import { callApi } from "./apiService";

export const askRagQuestion = async (question: string, top_k: number = 3, conversationId?: string) => {
  return callApi("/api/chat/rag", {
    question,
    top_k,
    conversation_id: conversationId
  });
};
