import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import { customerApi } from "../services/api/customerApi";
import { normalizeCustomer } from "../services/api/normalize";
import { apiErrorMessage } from "../utils/apiErrorMessage";

const CustomerContext = createContext(null);

export function CustomerProvider({ children }) {
  const { user, status } = useAuth();
  const [profileState, setProfileState] = useState(null);
  const [profileOwner, setProfileOwner] = useState(null);
  const [loading, setLoading] = useState(status === "loading");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const requestId = useRef(0);
  const customerId = status === "authenticated" && user?.role === "CUSTOMER" ? user.id : null;

  const refreshProfile = useCallback(async () => {
    const id = ++requestId.current;
    if (!customerId) {
      setProfileState(null);
      setProfileOwner(null);
      setError("");
      setLoading(false);
      return null;
    }
    setLoading(true);
    setError("");
    try {
      const next = normalizeCustomer(await customerApi.getProfile());
      if (id === requestId.current) {
        setProfileState(next);
        setProfileOwner(customerId);
      }
      return next;
    } catch (cause) {
      if (id === requestId.current) {
        setProfileState(null);
        setProfileOwner(customerId);
        setError(apiErrorMessage(cause, { notFound: "Your customer profile could not be found." }));
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
    refreshProfile().catch(() => {});
  }, [status, customerId, refreshProfile]);

  const updateProfile = useCallback(async changes => {
    if (!customerId) return { ok: false, message: "Sign in with a customer account to update your profile." };
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const updated = normalizeCustomer(await customerApi.updateProfile(changes));
      setProfileState(updated);
      setProfileOwner(customerId);
      try { await refreshProfile(); } catch { /* PATCH response remains server-authoritative if refetch is unavailable. */ }
      setSuccess("Profile updated successfully.");
      return { ok: true };
    } catch (cause) {
      const message = apiErrorMessage(cause, { notFound: "Your customer profile could not be found." });
      setError(message);
      return { ok: false, message };
    } finally {
      setSaving(false);
    }
  }, [customerId, refreshProfile]);

  const profile = profileOwner === customerId ? profileState : null;
  const value = useMemo(() => ({ profile, loading, saving, error, success, refreshProfile, updateProfile }), [profile, loading, saving, error, success, refreshProfile, updateProfile]);
  return <CustomerContext.Provider value={value}>{children}</CustomerContext.Provider>;
}

export function useCustomer() {
  const context = useContext(CustomerContext);
  if (!context) throw new Error("useCustomer must be used within CustomerProvider");
  return context;
}
