const rawBaseUrl = import.meta.env.VITE_API_BASE_URL || "";

export const env = Object.freeze({
  apiBaseUrl: rawBaseUrl.replace(/\/$/, ""),
  authTokenKey: "orb-auth-token"
});
