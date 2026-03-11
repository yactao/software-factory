// src/service/visionService.ts
import { msalInstance } from "../utils/msalInstance";
import { loginRequest } from "./authConfig";

const API_BASE = import.meta.env.VITE_API_BASE || "";

// src/service/visionService.ts
export interface VisionResponse {
  response_text: string;
  surfaces?: Record<string, number>;
  perimeters?: Record<string, number>;
  detections?: Array<{
    tag_name: string;
    probability: number;
    bounding_box?: any;
  }>;
  annotations?: VisionAnnotation[];
  annotations_version?: number;
  conversation_id?: string;
  vision_file_sas?: string;
  vision_annotated_sas?: string; // ← URL SAS de l'image annotée
  annotated_image_b64?: string;
  meta?: {
    vision_annotated_blob_path?: string;
    vision_annotated_sas?: string;
    vision_file_path?: string;
    annotations?: VisionAnnotation[];
    annotations_version?: number;
    [key: string]: any;
  };
}

export type VisionBBox = {
  x: number;
  y: number;
  w: number;
  h: number;
};

export type VisionAnnotation = {
  id: string;
  label: string;
  bbox: VisionBBox;
  confidence?: number;
  source?: "ai" | "user";
  version?: number;
};

export type VisionAnnotationContext = {
  conversation_id?: string | null;
  vision_file_path?: string;
  vision_annotated_blob_path?: string;
  message_timestamp?: string;
};

/** Payload unique pour le backend : image + dimensions + toutes les annotations (remplace create/update/delete) */
export type VisionEditSavePayload = {
  image: string;
  image_width: number | null;
  image_height: number | null;
  annotations: Array<{
    id: string;
    label: string;
    bbox: { x: number; y: number; w: number; h: number };
    bbox_px?: { x: number; y: number; w: number; h: number };
  }>;
};

// Ajouter cette fonction pour récupérer l'image annotée depuis l'URL SAS
export const getAnnotatedImageFromSAS = async (sasUrl: string): Promise<string> => {
  try {
    const response = await fetch(sasUrl);
    if (!response.ok) throw new Error('Failed to fetch annotated image');
    
    const blob = await response.blob();
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64 = reader.result as string;
        // Extraire seulement la partie base64 (sans le préfixe data:image/...)
        const base64Data = base64.split(',')[1];
        resolve(base64Data);
      };
      reader.onerror = reject;
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.error('Error fetching annotated image from SAS:', error);
    throw error;
  }
};

export const askVisionQuestion = async (
  file: File | null | undefined,
  prompt: string,
  conversationId?: string,
  mPerPixel?: number,
  ratio?: string,
  returnImage: boolean = true
): Promise<VisionResponse> => {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) throw new Error("No active account! Trigger login.");

  const tokenResponse = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account,
  });

  const formData = new FormData();
  
  // Ajouter le fichier seulement s'il est fourni (première requête)
  if (file) {
    formData.append("file", file);
  }
  
  formData.append("prompt", prompt);
  
  if (mPerPixel) {
    formData.append("m_per_pixel", mPerPixel.toString());
  }
  
  if (ratio) {
    formData.append("ratio", ratio);
  }
  
  formData.append("return_image", returnImage.toString());
  
  if (conversationId) {
    formData.append("conversation_id", conversationId);
  }

  const res = await fetch(`${API_BASE}/api/vision`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${tokenResponse.accessToken}`,
    },
    body: formData,
  });

  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return res.json();
};

export const cleanupVisionFile = async (conversationId: string): Promise<void> => {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) throw new Error("No active account! Trigger login.");

  const tokenResponse = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account,
  });

  const res = await fetch(`${API_BASE}/api/vision/cleanup`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${tokenResponse.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ conversation_id: conversationId }),
  });

  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
};

export const createVisionAnnotation = async (
  context: VisionAnnotationContext,
  annotation: Omit<VisionAnnotation, "id"> & { id?: string }
): Promise<VisionAnnotation> => {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) throw new Error("No active account! Trigger login.");

  const tokenResponse = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account,
  });

  const res = await fetch(`${API_BASE}/api/vision/annotations`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${tokenResponse.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...context,
      annotation,
    }),
  });

  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return res.json();
};

export const updateVisionAnnotation = async (
  context: VisionAnnotationContext,
  annotation: VisionAnnotation
): Promise<VisionAnnotation> => {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) throw new Error("No active account! Trigger login.");

  const tokenResponse = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account,
  });

  const res = await fetch(`${API_BASE}/api/vision/annotations/${annotation.id}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${tokenResponse.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      ...context,
      annotation,
    }),
  });

  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return res.json();
};

export const deleteVisionAnnotation = async (
  context: VisionAnnotationContext,
  annotationId: string
): Promise<void> => {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) throw new Error("No active account! Trigger login.");

  const tokenResponse = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account,
  });

  const res = await fetch(`${API_BASE}/api/vision/annotations/${annotationId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${tokenResponse.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(context),
  });

  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
};

/** Envoie au backend un seul JSON : image + dimensions + toutes les annotations (remplace create/update/delete) */
export const saveVisionAnnotations = async (
  context: VisionAnnotationContext,
  payload: VisionEditSavePayload
): Promise<{ annotations?: VisionAnnotation[] }> => {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) throw new Error("No active account! Trigger login.");

  const tokenResponse = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account,
  });

  const res = await fetch(`${API_BASE}/api/vision/annotations/save`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${tokenResponse.accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ ...context, ...payload }),
  });

  if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
  return res.json();
};
