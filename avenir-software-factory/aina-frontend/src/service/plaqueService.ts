import { msalInstance } from "../utils/msalInstance";
import { loginRequest } from "./authConfig";
import type { VisionResponse } from "./visionService";

const API_BASE =
  import.meta.env.VITE_API_BASE || "";

export type PlaqueVisionResponse = VisionResponse;

export const askPlaqueQuestion = async (
  file: File | null | undefined,
  prompt: string,
  conversationId?: string,
  returnImage: boolean = true
): Promise<PlaqueVisionResponse> => {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) throw new Error("No active account! Trigger login.");

  const tokenResponse = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account,
  });

  const formData = new FormData();

  if (file) {
    formData.append("file", file);
  }

  formData.append("prompt", prompt);
  formData.append("return_image", returnImage.toString());

  if (conversationId) {
    formData.append("conversation_id", conversationId);
  }

  // 👉 Appel direct du nouvel endpoint plaques
  const res = await fetch(`${API_BASE}/api/vision/plaque`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${tokenResponse.accessToken}`,
    },
    body: formData,
  });

  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return res.json();
};
