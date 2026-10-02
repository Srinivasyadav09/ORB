import { apiClient } from "./client";

export const addressApi = {
  list() { return apiClient.get("/addresses"); },
  getDefault() { return apiClient.get("/addresses/default"); },
  get(id) { return apiClient.get(`/addresses/${encodeURIComponent(id)}`); },
  create(address) { return apiClient.post("/addresses", address); },
  update(id, changes) { return apiClient.patch(`/addresses/${encodeURIComponent(id)}`, changes); },
  remove(id) { return apiClient.delete(`/addresses/${encodeURIComponent(id)}`); },
  setDefault(id) { return apiClient.patch(`/addresses/${encodeURIComponent(id)}/default`); }
};
