import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import { orderApi } from "../services/api/orderApi";
import { normalizeOrder } from "../services/api/normalize";
import { apiErrorMessage } from "../utils/apiErrorMessage";

const OrdersContext = createContext(null);

export function OrdersProvider({ children }) {
  const { user, status } = useAuth();
  const [orders, setOrders] = useState([]);
  const [orderOwner, setOrderOwner] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0, pages: 0 });
  const [loading, setLoading] = useState(status === "loading");
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const requestId = useRef(0);
  const createLock = useRef(false);
  const customerId = status === "authenticated" && user?.role === "CUSTOMER" ? user.id : null;

  const refreshOrders = useCallback(async (page = 1) => {
    const id = ++requestId.current;
    if (!customerId) {
      setOrders([]);
      setOrderOwner(null);
      setPagination({ page: 1, pageSize: 20, total: 0, pages: 0 });
      setError("");
      setLoading(false);
      return [];
    }
    setLoading(true);
    setError("");
    try {
      const response = await orderApi.list({ page, page_size: 20 });
      const rows = Array.isArray(response?.items) ? response.items : null;
      if (!rows) throw new Error("The orders service returned an invalid response.");
      const normalized = rows.map(normalizeOrder);
      if (id === requestId.current) {
        setOrders(normalized);
        setOrderOwner(customerId);
        setPagination({ page: response.page, pageSize: response.page_size, total: response.total, pages: response.pages });
      }
      return normalized;
    } catch (cause) {
      if (id === requestId.current) {
        setOrders([]);
        setOrderOwner(customerId);
        setError(apiErrorMessage(cause, { notFound: "Your order history could not be found." }));
      }
      throw cause;
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, [customerId]);

  useEffect(() => {
    if (status === "loading") {
      setLoading(true);
      return;
    }
    refreshOrders().catch(() => {});
  }, [status, customerId, refreshOrders]);

  const createOrder = useCallback(async addressId => {
    if (!customerId) return { ok: false, message: "Sign in with a customer account to place an order." };
    if (!addressId) return { ok: false, message: "Select a saved delivery address before placing your order." };
    if (createLock.current) return { ok: false, message: "Your order is already being submitted." };
    createLock.current = true;
    setCreating(true);
    setError("");
    try {
      const order = normalizeOrder(await orderApi.create({ address_id: addressId, payment_method: "COD" }));
      try { await refreshOrders(1); } catch { /* The created order response remains authoritative for confirmation. */ }
      return { ok: true, order };
    } catch (cause) {
      const message = apiErrorMessage(cause, { notFound: "The delivery address or cart could not be found." });
      setError(message);
      return { ok: false, message, status: cause?.status };
    } finally {
      createLock.current = false;
      setCreating(false);
    }
  }, [customerId, refreshOrders]);

  const getOrder = useCallback(async id => normalizeOrder(await orderApi.get(id)), []);
  const visibleOrders = orderOwner === customerId ? orders : [];
  const value = useMemo(() => ({
    orders: visibleOrders, pagination, loading, error, creating, refreshOrders, createOrder, getOrder
  }), [visibleOrders, pagination, loading, error, creating, refreshOrders, createOrder, getOrder]);
  return <OrdersContext.Provider value={value}>{children}</OrdersContext.Provider>;
}

export function useOrders() {
  const context = useContext(OrdersContext);
  if (!context) throw new Error("useOrders must be used within OrdersProvider");
  return context;
}
