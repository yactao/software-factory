// previewService.ts - Version avec meilleure gestion d'erreurs
import { msalInstance } from "../utils/msalInstance";
import { loginRequest } from "./authConfig";

const API_BASE = import.meta.env.VITE_API_BASE || "";

export interface PreviewResponse {
  url: string;
  container: string;
  blob: string;
  expires_in_minutes: number;
}

/**
 * Récupère une URL SAS valide depuis le backend
 * @param blobName - Nom du blob (ex: "44_39_mdm_plan_de_campagne_103_103_mdm_plan_de_campagne.pdf")
 */
export const getPreviewUrl = async (blobName: string): Promise<string> => {
  console.log("📁 [PreviewService] Génération SAS pour:", blobName);

  // ===== Authentification =====
  const account = msalInstance.getAllAccounts()[0];
  if (!account) {
    throw new Error("Aucun compte actif. Veuillez vous reconnecter.");
  }

  const tokenResponse = await msalInstance.acquireTokenSilent({
    ...loginRequest,
    account,
  });

  // ===== Nettoyer le nom du blob =====
  const cleanBlobName = blobName
    .trim()
    .replace(/^\/+/, '') // Supprimer les / au début
    .replace(/"/g, '');  // Supprimer les guillemets

  console.log("🧹 [PreviewService] Blob nettoyé:", cleanBlobName);

  // ===== Appel API avec retry =====
  const maxRetries = 2;
  let lastError: Error | null = null;

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      console.log(`🚀 [PreviewService] Tentative ${attempt}/${maxRetries}`);
      
      const timestamp = Date.now();
      const apiUrl = `${API_BASE}/api/sas?path=${encodeURIComponent(cleanBlobName)}&ttl=60&t=${timestamp}`;
      
      console.log("📡 [PreviewService] URL API:", apiUrl);

      const res = await fetch(apiUrl, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${tokenResponse.accessToken}`,
          'Cache-Control': 'no-cache, no-store, must-revalidate',
          'Pragma': 'no-cache',
        },
      });

      console.log("📊 [PreviewService] Statut HTTP:", res.status);

      if (!res.ok) {
        const errorBody = await res.text();
        console.error("❌ [PreviewService] Erreur API:", errorBody);
        
        // Parser le JSON d'erreur si possible
        try {
          const errorJson = JSON.parse(errorBody);
          throw new Error(
            `Fichier introuvable (${res.status}). Chemins essayés: ${errorJson.detail?.tried_paths?.join(', ') || cleanBlobName}`
          );
        } catch {
          throw new Error(`Erreur API (${res.status}): ${errorBody}`);
        }
      }

      // ===== Succès ! =====
      const data: PreviewResponse = await res.json();
      console.log("✅ [PreviewService] URL SAS reçue:", data.url);
      console.log("📦 [PreviewService] Container:", data.container);
      console.log("📄 [PreviewService] Blob:", data.blob);
      console.log("⏰ [PreviewService] Expire dans:", data.expires_in_minutes, "minutes");

      // Vérifier que l'URL n'est pas vide
      if (!data.url) {
        throw new Error("L'API a retourné une URL vide");
      }

      return data.url;

    } catch (error) {
      lastError = error as Error;
      console.warn(`⚠️ [PreviewService] Tentative ${attempt} échouée:`, error);
      
      // Attendre avant de réessayer
      if (attempt < maxRetries) {
        await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
      }
    }
  }

  // ===== Échec après tous les retries =====
  console.error("🚨 [PreviewService] Toutes les tentatives ont échoué");
  throw lastError || new Error("Impossible de générer l'URL SAS");
};

/**
 * Vérifie si une URL SAS est expirée
 */
export const isSasExpired = (sasUrl: string): boolean => {
  try {
    const url = new URL(sasUrl);
    const expiryParam = url.searchParams.get('se');
    
    if (!expiryParam) {
      console.warn("⚠️ Pas de paramètre 'se' trouvé dans l'URL");
      return true; // Considérer comme expiré par sécurité
    }
    
    const expiryTime = new Date(expiryParam);
    const now = new Date();
    
    const isExpired = expiryTime <= now;
    
    if (isExpired) {
      console.warn(`⏰ URL SAS expirée depuis ${Math.floor((now.getTime() - expiryTime.getTime()) / 1000)}s`);
    }
    
    return isExpired;
    
  } catch (error) {
    console.error("❌ Erreur vérification expiration:", error);
    return true;
  }
};
