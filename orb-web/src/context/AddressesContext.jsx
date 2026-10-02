import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import { addressApi } from "../services/api/addressApi";
import { normalizeAddress, requireList } from "../services/api/normalize";
import { apiErrorMessage } from "../utils/apiErrorMessage";

const AddressesContext = createContext(null);

export function AddressesProvider({ children }) {
  const { user, status } = useAuth();
  const [addresses, setAddresses] = useState([]);
  const [selectedAddressId, setSelectedAddressId] = useState(null);
  const [loading, setLoading] = useState(status === "loading");
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);
  const requestId = useRef(0);
  const mutationLock = useRef(false);
  const customerId = status === "authenticated" && user?.role === "CUSTOMER" ? user.id : null;

  const refresh = useCallback(async () => {
    const id = ++requestId.current;
    if (!customerId) {
      setAddresses([]);
      setSelectedAddressId(null);
      setError("");
      setLoading(false);
      return [];
    }
    setLoading(true);
    setError("");
    try {
      const [listResult, defaultResult] = await Promise.allSettled([addressApi.list(), addressApi.getDefault()]);
      if (listResult.status === "rejected") throw listResult.reason;
      const next = requireList(listResult.value, "addresses").map(normalizeAddress);
      let defaultId = next.find(address => address.isDefault)?.id ?? null;
      if (defaultResult.status === "fulfilled") defaultId = normalizeAddress(defaultResult.value).id;
      else if (defaultResult.reason?.status !== 404) throw defaultResult.reason;
      if (id === requestId.current) {
        setAddresses(next);
        setSelectedAddressId(defaultId && next.some(address => address.id === defaultId) ? defaultId : null);
      }
      return next;
    } catch (cause) {
      if (id === requestId.current) {
        setAddresses([]);
        setSelectedAddressId(null);
        setError(apiErrorMessage(cause, { notFound: "Your saved addresses could not be found." }));
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

  const mutate = useCallback(async (operation, { refreshAfter = true } = {}) => {
    if (!customerId) return { ok: false, message: "Sign in with a customer account to manage addresses." };
    if (mutationLock.current) return { ok: false, message: "An address update is already in progress." };
    mutationLock.current = true;
    setPending(true);
    setError("");
    try {
      const result = await operation();
      if (refreshAfter) await refresh();
      return { ok: true, data: result };
    } catch (cause) {
      const message = apiErrorMessage(cause, { notFound: "This saved address could not be found." });
      setError(message);
      return { ok: false, message };
    } finally {
      mutationLock.current = false;
      setPending(false);
    }
  }, [customerId, refresh]);

  const addAddress = useCallback(payload => mutate(() => addressApi.create(payload)), [mutate]);
  const updateAddress = useCallback((id, payload) => mutate(() => addressApi.update(id, payload)), [mutate]);
  const deleteAddress = useCallback(id => mutate(() => addressApi.remove(id)), [mutate]);
  const selectAddress = useCallback(id => mutate(() => addressApi.setDefault(id)), [mutate]);
  const selectedAddress = addresses.find(address => address.id === selectedAddressId) ?? null;
  const value = useMemo(() => ({
    addresses, selectedAddressId, selectedAddress, loading, error, pending, refresh,
    addAddress, updateAddress, deleteAddress, selectAddress
  }), [addresses, selectedAddressId, selectedAddress, loading, error, pending, refresh, addAddress, updateAddress, deleteAddress, selectAddress]);

  return <AddressesContext.Provider value={value}>{children}</AddressesContext.Provider>;
}

export function useAddresses() {
  const context = useContext(AddressesContext);
  if (!context) throw new Error("useAddresses must be used within AddressesProvider");
  return context;
}
