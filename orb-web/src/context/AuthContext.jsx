import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { authApi } from "../services/api/authApi";
import { getAuthToken, getRefreshToken, setAuthToken, setRefreshToken } from "../services/api/client";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let active = true;
    const clearUser = () => {
      setUser(null);
      setStatus("unauthenticated");
    };
    window.addEventListener("orb:unauthorized", clearUser);

    const restore = async () => {
      if (!getAuthToken() && !getRefreshToken()) {
        if (active) clearUser();
        return;
      }
      try {
        if (!getAuthToken()) await authApi.refresh();
        const currentUser = await authApi.me();
        if (active) {
          setUser(currentUser);
          setStatus("authenticated");
        }
      } catch {
        setAuthToken(null);
        setRefreshToken(null);
        if (active) clearUser();
      }
    };
    restore();
    return () => {
      active = false;
      window.removeEventListener("orb:unauthorized", clearUser);
    };
  }, []);

  const login = useCallback(async credentials => {
    const result = await authApi.login(credentials);
    setUser(result.user);
    setStatus("authenticated");
    return result.user;
  }, []);

  const registerCustomer = useCallback(async payload => {
    await authApi.registerCustomer(payload);
    return login({ email: payload.email, password: payload.password });
  }, [login]);

  const registerFarmer = useCallback(async payload => {
    await authApi.registerFarmer(payload);
    return login({ email: payload.email, password: payload.password });
  }, [login]);

  const signOut = useCallback(async () => {
    const logoutRequest = getAuthToken() ? authApi.logout() : Promise.resolve();
    setAuthToken(null);
    setRefreshToken(null);
    setUser(null);
    setStatus("unauthenticated");
    try { await logoutRequest; } catch { /* Local sign-out still completes if the API is unreachable. */ }
  }, []);

  const value = useMemo(() => ({
    user,
    status,
    isLoading: status === "loading",
    isAuthenticated: status === "authenticated",
    login,
    registerCustomer,
    registerFarmer,
    signOut
  }), [user, status, login, registerCustomer, registerFarmer, signOut]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within AuthProvider");
  return context;
}
