import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import { productApi } from "../services/api/productApi";
import { normalizeProduct, requireList, requireRecord } from "../services/api/normalize";

const FarmerProductsContext = createContext(null);
const PAGE_SIZE = 20;

export function FarmerProductsProvider({ children }) {
  const { user, status: authStatus } = useAuth();
  const [products, setProducts] = useState([]);
  const [activeCount, setActiveCount] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, page_size: PAGE_SIZE, total: 0, pages: 0 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const requestId = useRef(0);
  const activeCountRequest = useRef(0);

  const loadProducts = useCallback(async (page = 1) => {
    if (!user || user.role !== "FARMER") return null;
    const id = ++requestId.current;
    setLoading(true);
    setError(null);
    try {
      const response = requireRecord(await productApi.listMine({ page, page_size: PAGE_SIZE }), "farmer products");
      const rows = requireList(response, "farmer products");
      if (id !== requestId.current) return null;
      const totalPages = Number(response.pages ?? (rows.length ? 1 : 0));
      if (page > totalPages) return loadProducts(totalPages || 1);
      setProducts(rows.map(normalizeProduct));
      setPagination({
        page: Number(response.page || page),
        page_size: Number(response.page_size || PAGE_SIZE),
        total: Number(response.total ?? rows.length),
        pages: totalPages
      });
      return response;
    } catch (requestError) {
      if (id !== requestId.current) return null;
      setProducts([]);
      setPagination({ page, page_size: PAGE_SIZE, total: 0, pages: 0 });
      setError(requestError);
      return null;
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, [user]);

  const loadActiveCount = useCallback(async () => {
    if (!user || user.role !== "FARMER") return null;
    const id = ++activeCountRequest.current;
    try {
      const response = requireRecord(await productApi.listMine({ page: 1, page_size: 1, status: "ACTIVE" }), "active farmer products");
      if (id === activeCountRequest.current) setActiveCount(Number(response.total ?? 0));
    } catch {
      if (id === activeCountRequest.current) setActiveCount(null);
    }
  }, [user]);

  useEffect(() => {
    if (authStatus === "authenticated" && user?.role === "FARMER") {
      loadProducts(1);
      loadActiveCount();
    } else if (authStatus !== "loading") {
      requestId.current += 1;
      activeCountRequest.current += 1;
      setProducts([]);
      setActiveCount(null);
      setPagination({ page: 1, page_size: PAGE_SIZE, total: 0, pages: 0 });
      setLoading(false);
      setError(null);
    }
  }, [authStatus, user, loadProducts, loadActiveCount]);

  const value = useMemo(() => ({
    products, pagination, loading, error, activeCount, loadProducts,
    async createProduct(payload) {
      const created = await productApi.create(payload);
      await loadProducts(1);
      await loadActiveCount();
      return normalizeProduct(created);
    },
    async updateProduct(id, payload) {
      const updated = await productApi.update(id, payload);
      await loadProducts(pagination.page);
      await loadActiveCount();
      return normalizeProduct(updated);
    },
    async deactivateProduct(id) {
      const updated = await productApi.remove(id);
      await loadProducts(pagination.page);
      await loadActiveCount();
      return normalizeProduct(updated);
    },
    async setProductStatus(id, status) {
      const updated = await productApi.update(id, { status });
      await loadProducts(pagination.page);
      await loadActiveCount();
      return normalizeProduct(updated);
    }
  }), [products, pagination, loading, error, activeCount, loadProducts, loadActiveCount]);

  return <FarmerProductsContext.Provider value={value}>{children}</FarmerProductsContext.Provider>;
}

export function useFarmerProducts() {
  const context = useContext(FarmerProductsContext);
  if (!context) throw new Error("useFarmerProducts must be used within FarmerProductsProvider");
  return context;
}
