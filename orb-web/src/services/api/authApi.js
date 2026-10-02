import { apiClient, getRefreshToken, setAuthTokens, setAuthToken, setRefreshToken } from "./client";

export const authApi = {
  async login(credentials) {
    const result = await apiClient.post("/auth/login", credentials);
    setAuthTokens(result);
    return result;
  },
  registerCustomer(payload) {
    return apiClient.post("/auth/register/customer", payload);
  },
  registerFarmer(payload) {
    return apiClient.post("/auth/register/farmer", payload);
  },
  async refresh() {
    const refresh_token = getRefreshToken();
    if (!refresh_token) throw new Error("No refresh token is available.");
    const result = await apiClient.post("/auth/refresh", { refresh_token });
    setAuthTokens(result);
    return result;
  },
  me() { return apiClient.get("/auth/me"); },
  async logout() {
    try { return await apiClient.post("/auth/logout"); }
    finally { setAuthToken(null); setRefreshToken(null); }
  }
};
