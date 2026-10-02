import { apiClient } from "./client";

export const orderApi = {
  list(query) { return apiClient.get("/orders", { query }); },
  get(id) { return apiClient.get(`/orders/${encodeURIComponent(id)}`); },
  create({ address_id, payment_method = "COD" }) {
    return apiClient.post("/orders", { address_id, payment_method });
  }
};
