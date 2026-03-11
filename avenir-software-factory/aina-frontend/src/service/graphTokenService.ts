// src/service/graphTokenService.ts
import { msalInstance } from "../utils/msalInstance";

export const acquireGraphToken = async (): Promise<string> => {
  const account = msalInstance.getAllAccounts()[0];
  if (!account) throw new Error("Aucun compte connecté");

  try {
    const response = await msalInstance.acquireTokenSilent({
      scopes: ["https://graph.microsoft.com/Mail.Read", "https://graph.microsoft.com/User.Read"],
      account,
    });
    return response.accessToken;
  } catch (silentError) {
    // Si silent échoue (consentement manquant, etc.)
    try {
      const response = await msalInstance.acquireTokenPopup({
        scopes: ["https://graph.microsoft.com/Mail.Read", "https://graph.microsoft.com/User.Read"],
      });
      return response.accessToken;
    } catch (popupError) {
      throw new Error("Impossible d'obtenir les permissions pour lire vos emails.");
    }
  }
};
