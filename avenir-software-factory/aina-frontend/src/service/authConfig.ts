// src/authConfig.ts

import { LogLevel, type Configuration } from "@azure/msal-browser";

export const msalConfig: Configuration = {
  auth: {
    clientId: "ec636c3a-d697-4788-bfa8-6fb96a83b71a", // 👉 Your FRONTEND App Registration Client ID
    authority: "https://login.microsoftonline.com/6bcca42d-d01b-4e42-be4b-2f55074eaa0d", // 👉 Your TENANT_ID
    redirectUri: window.location.origin, // e.g., http://localhost:3000
  },
  cache: {
    cacheLocation: "localStorage",
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (_level, message) => {
        console.log(message);
      },
      logLevel: LogLevel.Info,
    },
  },
};

export const loginRequest = {
  scopes: [
    "openid",
    "profile",
    "email",
    "api://53897d93-51e0-4d32-adde-b5dfc02075e9/ragapi", // ✅ une seule ressource
  ],
};
