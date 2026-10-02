import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import { cartApi } from "../services/api/cartApi";
import { normalizeCart } from "../services/api/normalize";
import { apiErrorMessage } from "../utils/apiErrorMessage";

const CartContext = createContext(null);
const emptyCart = { items: [], itemCount: 0, subtotal: 0, deliveryFee: 0, totalAmount: 0 };

function presentCart(cart) {
  return cart.items.map(line => ({
    ...line,
    product: {
      id: line.productId,
      name: line.productName,
      image: line.productImageUrl,
      price: line.unitPrice,
      unit: line.unit,
      qty: line.availableStock,
      isAvailable: line.isAvailable
    },
    qty: line.quantity
  }));
}

export function CartProvider({ children }) {
  const { user, status } = useAuth();
  const [serverCart, setServerCart] = useState(emptyCart);
  const [cartOwner, setCartOwner] = useState(null);
  const [loading, setLoading] = useState(status === "loading");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const requestId = useRef(0);
  const mutationLock = useRef(false);
  const customerId = status === "authenticated" && user?.role === "CUSTOMER" ? user.id : null;

  const refresh = useCallback(async () => {
    const id = ++requestId.current;
    if (!customerId) {
      setServerCart(emptyCart);
      setCartOwner(null);
      setError("");
      setLoading(false);
      return emptyCart;
    }
    setLoading(true);
    setError("");
    try {
      const next = normalizeCart(await cartApi.get());
      if (id === requestId.current) {
        setServerCart(next);
        setCartOwner(customerId);
      }
      return next;
    } catch (cause) {
      if (id === requestId.current) {
        setServerCart(emptyCart);
        setCartOwner(customerId);
        setError(apiErrorMessage(cause, { notFound: "Your cart could not be found." }));
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
    refresh().catch(() => {});
  }, [status, customerId, refresh]);

  const mutate = useCallback(async (operation, { refetch = false } = {}) => {
    if (!customerId) return { ok: false, message: "Sign in with a customer account to use the cart." };
    if (mutationLock.current) return { ok: false, message: "A cart update is already in progress." };
    mutationLock.current = true;
    setPending(true);
    setError("");
    try {
      const result = await operation();
      if (refetch) await refresh();
      else {
        setServerCart(normalizeCart(result));
        setCartOwner(customerId);
      }
      return { ok: true, message: "Cart updated." };
    } catch (cause) {
      const message = apiErrorMessage(cause, { notFound: "This product is no longer in your cart." });
      // A conflict can indicate stale stock or availability; refresh the server-owned snapshot.
      if ([404, 409].includes(cause?.status)) {
        try { await refresh(); } catch { /* Preserve the original mutation error. */ }
      }
      setError(message);
      return { ok: false, message };
    } finally {
      mutationLock.current = false;
      setPending(false);
    }
  }, [customerId, refresh]);

  const add = useCallback((product, quantity = 1) => mutate(
    () => cartApi.add(product.id, quantity)
  ), [mutate]);

  const changeQty = useCallback((id, delta) => {
    const line = serverCart.items.find(item => item.productId === id);
    if (!line) return Promise.resolve({ ok: false, message: "This product is no longer in your cart." });
    return mutate(() => cartApi.update(id, Math.max(1, line.quantity + delta)));
  }, [mutate, serverCart.items]);

  const remove = useCallback(id => mutate(() => cartApi.remove(id), { refetch: true }), [mutate]);
  const clear = useCallback(() => mutate(() => cartApi.clear(), { refetch: true }), [mutate]);
  const visibleCart = cartOwner === customerId ? serverCart : emptyCart;
  const cart = useMemo(() => presentCart(visibleCart), [visibleCart]);
  const value = useMemo(() => ({
    cart, serverCart: visibleCart, count: visibleCart.itemCount, subtotal: visibleCart.subtotal,
    deliveryFee: visibleCart.deliveryFee, totalAmount: visibleCart.totalAmount,
    loading, error, pending, refresh, add, changeQty, remove, clear
  }), [cart, visibleCart, loading, error, pending, refresh, add, changeQty, remove, clear]);

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);
  if (!context) throw new Error("useCart must be used within CartProvider");
  return context;
}
