// services/documentService.ts

import { msalInstance } from "../utils/msalInstance";
import { loginRequest } from "./authConfig";
import type { PreviewResponse } from "./previewService";

const API_BASE = import.meta.env.VITE_API_BASE || "";
//const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

/**
 * Récupère une URL SAS directement depuis l'ID base64 du document
 */
 export const getPreviewUrlFromId = async (id: string): Promise<string> => {
    const account = msalInstance.getAllAccounts()[0];
    if (!account) throw new Error("No active account! Trigger login.");
  
    const tokenResponse = await msalInstance.acquireTokenSilent({
      ...loginRequest,
      account,
    });
  
    console.log("🔍 [DocumentService] ID base64 reçu:", id);
  
    try {
      // Décoder l'ID pour obtenir le chemin
      const decoded = atob(id);
      console.log("🔧 [DocumentService] ID décodé:", decoded);
      
      // Extraire le chemin du blob
      if (decoded.includes('blob.core.windows.net')) {
        const url = new URL(decoded);
        const path = url.pathname.split('/docs/')[1];
        console.log("✅ [DocumentService] Chemin extrait:", path);
        
        // Appeler l'API SAS avec le chemin correct
        const res = await fetch(`${API_BASE}/api/sas?path=${encodeURIComponent(path)}`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${tokenResponse.accessToken}`,
          },
        });
  
        if (!res.ok) {
          const errorText = await res.text();
          throw new Error(`Erreur API SAS: ${res.status} - ${errorText}`);
        }
  
        const data: PreviewResponse = await res.json();
        return data.url;
      } else {
        throw new Error("ID ne contient pas d'URL de blob valide");
      }
      
    } catch (error) {
      console.error("❌ [DocumentService] Erreur:", error);
      throw error;
    }
  };
