import { apiClient } from "./client";

const farmerPath = "/farmers/me/products";
export const productApi = {
  list(query) { return apiClient.get("/products", { query }); },
  get(id) { return apiClient.get(`/products/${encodeURIComponent(id)}`); },
  listMine(query) { return apiClient.get(farmerPath, { query }); },
  getMine(id) { return apiClient.get(`${farmerPath}/${encodeURIComponent(id)}`); },
  create(product) { return apiClient.post(farmerPath, product); },
  update(id, changes) { return apiClient.patch(`${farmerPath}/${encodeURIComponent(id)}`, changes); },
  remove(id) { return apiClient.delete(`${farmerPath}/${encodeURIComponent(id)}`); }
};
