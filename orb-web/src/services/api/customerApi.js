import { apiClient } from "./client";

export const customerApi = {
  getProfile() { return apiClient.get("/customers/me"); },
  updateProfile(profile) { return apiClient.patch("/customers/me", profile); }
};
