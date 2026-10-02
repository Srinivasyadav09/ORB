import { apiClient } from "./client";

export const categoryApi = {
  list() { return apiClient.get("/categories"); },
  get(id) { return apiClient.get(`/categories/${encodeURIComponent(id)}`); }
};
