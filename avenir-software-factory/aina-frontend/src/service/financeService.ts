// src/service/financeService.ts
import { callApi } from "./apiService";

export type ChartType =
  | "bar"
  | "horizontal_bar"
  | "line"
  | "pie"
  | "bubble"
  | "none";

export interface ChartPoint {
  x: string;
  y: number;
}

export interface ChartSeries {
  label: string;
  points: ChartPoint[];
}

export interface FinanceChart {
  type: ChartType;
  title?: string;
  x_label?: string;
  y_label?: string;
  series: ChartSeries[];
}

export interface FinanceApiResponse {
  answer: string;
  chart?: FinanceChart;
  conversation_id?: string;
}

export const askFinanceQuestion = async (
  question: string,
  _topN: number = 10,
  conversationId?: string
): Promise<FinanceApiResponse> => {
  const payload = {
    question,
    conversation_id: conversationId,
  };

  const res = await callApi<never>("/api/aina/finance", payload);
  // callApi te renvoie le JSON brut, on le caste avec notre type finance
  return res as unknown as FinanceApiResponse;
};
