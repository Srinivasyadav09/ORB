import { apiClient } from "./client";

export const cartApi = {
  get() { return apiClient.get("/cart"); },
  add(product_id, quantity) { return apiClient.post("/cart/items", { product_id, quantity }); },
  update(product_id, quantity) { return apiClient.patch(`/cart/items/${encodeURIComponent(product_id)}`, { quantity }); },
  remove(product_id) { return apiClient.delete(`/cart/items/${encodeURIComponent(product_id)}`); },
  clear() { return apiClient.delete("/cart"); }
};
