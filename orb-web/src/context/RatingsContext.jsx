import { createContext, useContext, useMemo, useState } from "react";
import { readStoredValue, writeStoredValue } from "../utils/storage";
import { useOrders } from "./OrdersContext";
const RatingsContext = createContext(null);
const KEY = "orb-ratings";
export function RatingsProvider({ children }) {
  const { orders, updateOrderRating } = useOrders();
  const [ratings, setRatings] = useState(() => readStoredValue(KEY, []));
  const value = useMemo(() => ({ ratings, rateProduct({ orderId, productId, rating, review = "" }) {
    const order = orders.find(item => item.id === orderId);
    if (!order || order.status !== "Delivered") return { ok: false, message: "You can rate products after delivery." };
    const item = order.items.find(line => (line.productId ?? line.product?.id) === productId);
    if (!item) return { ok: false, message: "Product not found in this order." };
    if (item.rating) return { ok: false, message: "You have already rated this product." };
    const saved = { orderId, productId, rating, review: review.trim(), createdAt: new Date().toISOString() };
    const next = [...ratings, saved]; setRatings(next); writeStoredValue(KEY, next); updateOrderRating(orderId, productId, rating, review.trim());
    return { ok: true, message: "Thank you for your rating." };
  } }), [ratings, orders, updateOrderRating]);
  return <RatingsContext.Provider value={value}>{children}</RatingsContext.Provider>;
}
export function useRatings() { const context = useContext(RatingsContext); if (!context) throw new Error("useRatings must be used within RatingsProvider"); return context; }
