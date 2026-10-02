import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { productApi } from "../services/api/productApi";
import { categoryApi } from "../services/api/categoryApi";
import { normalizeCategory, normalizeProduct, requireList, requireRecord } from "../services/api/normalize";

const ProductsContext = createContext(null);

export function ProductsProvider({ children }) {
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [pagination, setPagination] = useState({ page: 1, page_size: 8, total: 0, pages: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoriesLoading, setCategoriesLoading] = useState(true);
  const [categoriesError, setCategoriesError] = useState(null);
  const productRequest = useRef(0);
  const categoryRequest = useRef(0);

  const loadProducts = useCallback(async (query = {}) => {
    const requestId = ++productRequest.current;
    setLoading(true);
    setError(null);
    try {
      const response = requireRecord(await productApi.list(query), "products");
      const rows = requireList(response, "products");
      if (requestId !== productRequest.current) return null;
      setProducts(rows.map(normalizeProduct));
      setPagination({
        page: Number(response.page || query.page || 1),
        page_size: Number(response.page_size || query.page_size || rows.length),
        total: Number(response.total ?? rows.length),
        pages: Number(response.pages ?? (rows.length ? 1 : 0))
      });
      return response;
    } catch (requestError) {
      if (requestId !== productRequest.current) return null;
      setProducts([]);
      setPagination({ page: Number(query.page || 1), page_size: Number(query.page_size || 20), total: 0, pages: 0 });
      setError(requestError);
      return null;
    } finally {
      if (requestId === productRequest.current) setLoading(false);
    }
  }, []);

  const loadCategories = useCallback(async () => {
    const requestId = ++categoryRequest.current;
    setCategoriesLoading(true);
    setCategoriesError(null);
    try {
      const rows = requireList(await categoryApi.list(), "categories");
      if (requestId !== categoryRequest.current) return null;
      setCategories(rows.map(normalizeCategory));
      return rows;
    } catch (requestError) {
      if (requestId !== categoryRequest.current) return null;
      setCategories([]);
      setCategoriesError(requestError);
      return null;
    } finally {
      if (requestId === categoryRequest.current) setCategoriesLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProducts({ page: 1, page_size: 8, sort: "newest" });
    loadCategories();
  }, [loadProducts, loadCategories]);

  const value = useMemo(() => ({
    products, categories, pagination, loading, error, categoriesLoading, categoriesError,
    loadProducts, loadCategories,
    getProduct(id) { return products.find(product => String(product.id) === String(id)); },
  }), [products, categories, pagination, loading, error, categoriesLoading, categoriesError, loadProducts, loadCategories]);

  return <ProductsContext.Provider value={value}>{children}</ProductsContext.Provider>;
}

export function useProducts() {
  const context = useContext(ProductsContext);
  if (!context) throw new Error("useProducts must be used within ProductsProvider");
  return context;
}
