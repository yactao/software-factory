// searchService.ts
import { callApi } from "./apiService";

export interface SearchResponse {
  answer: string;
  citations?: { title: string; url: string }[];
  model?: string;
  grounded?: boolean;
  conversation_id?: string;
}

export const askSearchQuestion = async (prompt: string, conversationId?: string): Promise<SearchResponse> => {
  return callApi("/api/search", { 
    question: prompt,
    context: null,
    force_grounding: true,
    legacy_15: false,
    conversation_id: conversationId 
  });
};
