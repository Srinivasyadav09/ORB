import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import { farmerApi } from "../services/api/farmerApi";
import { normalizeFarmer, normalizeVerification } from "../services/api/normalize";
import { apiErrorMessage } from "../utils/apiErrorMessage";

const FarmerContext = createContext(null);

export function FarmerProvider({ children }) {
  const { user, status } = useAuth();
  const [profileState, setProfileState] = useState(null);
  const [profileOwner, setProfileOwner] = useState(null);
  const [verificationState, setVerificationState] = useState(null);
  const [verificationOwner, setVerificationOwner] = useState(null);
  const [loading, setLoading] = useState(status === "loading");
  const [verificationLoading, setVerificationLoading] = useState(status === "loading");
  const [profileError, setProfileError] = useState("");
  const [verificationError, setVerificationError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [success, setSuccess] = useState("");
  const requestId = useRef(0);
  const verificationRequestId = useRef(0);
  const farmerId = status === "authenticated" && user?.role === "FARMER" ? user.id : null;

  const refreshProfile = useCallback(async () => {
    const id = ++requestId.current;
    if (!farmerId) {
      setProfileState(null);
      setProfileOwner(null);
      setProfileError("");
      setLoading(false);
      return null;
    }
    setLoading(true);
    setProfileError("");
    try {
      const next = normalizeFarmer(await farmerApi.getProfile());
      if (id === requestId.current) {
        setProfileState(next);
        setProfileOwner(farmerId);
      }
      return next;
    } catch (cause) {
      if (id === requestId.current) {
        setProfileState(null);
        setProfileOwner(farmerId);
        setProfileError(apiErrorMessage(cause, { notFound: "Your farmer profile could not be found." }));
      }
      throw cause;
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, [farmerId]);

  const refreshVerification = useCallback(async () => {
    const id = ++verificationRequestId.current;
    if (!farmerId) {
      setVerificationState(null);
      setVerificationOwner(null);
      setVerificationError("");
      setVerificationLoading(false);
      return null;
    }
    setVerificationLoading(true);
    setVerificationError("");
    try {
      const next = normalizeVerification(await farmerApi.getVerification());
      if (id === verificationRequestId.current) {
        setVerificationState(next);
        setVerificationOwner(farmerId);
      }
      return next;
    } catch (cause) {
      if (id === verificationRequestId.current) {
        setVerificationState(null);
        setVerificationOwner(farmerId);
        setVerificationError(apiErrorMessage(cause, { notFound: "Verification status could not be found." }));
      }
      throw cause;
    } finally {
      if (id === verificationRequestId.current) setVerificationLoading(false);
    }
  }, [farmerId]);

  useEffect(() => {
    if (status === "loading") {
      setLoading(true);
      setVerificationLoading(true);
      return;
    }
    refreshProfile().catch(() => {});
    refreshVerification().catch(() => {});
  }, [status, farmerId, refreshProfile, refreshVerification]);

  const saveProfile = useCallback(async changes => {
    if (!farmerId) return { ok: false, message: "Sign in with a farmer account to update your profile." };
    setSaving(true);
    setSaveError("");
    setSuccess("");
    try {
      const updated = normalizeFarmer(await farmerApi.updateProfile(changes));
      setProfileState(updated);
      setProfileOwner(farmerId);
      try { await refreshProfile(); } catch { /* PATCH response remains server-authoritative if refetch is unavailable. */ }
      setSuccess("Farmer profile updated successfully.");
      return { ok: true };
    } catch (cause) {
      const message = apiErrorMessage(cause, { notFound: "Your farmer profile could not be found." });
      setSaveError(message);
      return { ok: false, message };
    } finally {
      setSaving(false);
    }
  }, [farmerId, refreshProfile]);

  const profile = profileOwner === farmerId ? profileState : null;
  const verification = verificationOwner === farmerId ? verificationState : null;
  const value = useMemo(() => ({
    profile, verification, loading, verificationLoading, profileError, verificationError,
    saving, saveError, success, refreshProfile, refreshVerification, saveProfile
  }), [profile, verification, loading, verificationLoading, profileError, verificationError, saving, saveError, success, refreshProfile, refreshVerification, saveProfile]);
  return <FarmerContext.Provider value={value}>{children}</FarmerContext.Provider>;
}

export function useFarmer() {
  const context = useContext(FarmerContext);
  if (!context) throw new Error("useFarmer must be used within FarmerProvider");
  return context;
}
