import { apiClient } from "./client";

export const farmerApi = {
  getProfile() { return apiClient.get("/farmers/me"); },
  updateProfile(profile) { return apiClient.patch("/farmers/me", profile); },
  getVerification() { return apiClient.get("/farmers/me/verification"); },
  getPublicProfile(id) { return apiClient.get(`/farmers/${encodeURIComponent(id)}`); }
};
