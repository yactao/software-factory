// src/service/emailService.ts frontend service 
import { callApi } from "./apiService";

export interface EmailQuestion {
  question: string;
 // graph_access_token: string;
}

export interface EmailRecipient {
  name?: string;
  address: string;
}

export interface EmailAttachment {
  id: string;
  name: string;
  contentType?: string;
  size?: number;
}

export interface EmailItem {
  message_id: string;
  subject: string;

  from?: EmailRecipient;
  to?: EmailRecipient[];
  cc?: EmailRecipient[];
  bcc?: EmailRecipient[];

  receivedDateTime?: string;
  isRead?: boolean;

  // list mode
  summary?: string;
  hasAttachments?: boolean;

  // detail mode
  body?: string;
  attachments?: EmailAttachment[];
}

export interface EmailResponse {
  answer: string;
  emails?: EmailItem[];
}

export const askEmailQuestion = async (question: string): Promise<EmailResponse> => {
  return callApi("/api/aina/email", { 
    question,
    //graph_access_token: accessToken 
  });
};

// src/service/emailService.ts

export async function downloadEmailAttachment(
  messageId: string,
  attachmentId: string,
  filename: string,
  ainaToken: string
) {
  const API_BASE = import.meta.env.VITE_API_BASE || "";
  const res = await fetch(
    //`http://localhost:8000/api/aina/email/${messageId}/attachments/${attachmentId}/download`,
    `${API_BASE}/api/aina/email/${messageId}/attachments/${attachmentId}/download`,
    {
      method: "GET",
      headers: {
        Authorization: `Bearer ${ainaToken}`,
        "Cache-Control": "no-store",
        Pragma: "no-cache",
      },
    }
  );

  if (!res.ok) {
    throw new Error("Erreur téléchargement pièce jointe");
  }

  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "piece-jointe";
  document.body.appendChild(a);
  a.click();
  a.remove();

  window.URL.revokeObjectURL(url);
}

