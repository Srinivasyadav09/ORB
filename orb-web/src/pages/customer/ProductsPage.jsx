import { useEffect, useState } from "react";
import { Search } from "lucide-react";
import ProductGrid from "../../components/products/ProductGrid";
import { Page, PageTitle } from "../../components/layout/Page";
import { useCart } from "../../context/CartContext";
import { useProducts } from "../../context/ProductsContext";
import Button from "../../components/common/Button";
import EmptyState from "../../components/common/EmptyState";
import Loading from "../../components/common/Loading";

const PAGE_SIZE = 12;

export default function ProductsPage() {
  const [search, setSearch] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [sort, setSort] = useState("newest");
  const [maxPrice, setMaxPrice] = useState("");
  const [availableOnly, setAvailableOnly] = useState(false);
  const [page, setPage] = useState(1);
  const { add } = useCart();
  const { products, categories, pagination, loading, error, categoriesLoading, categoriesError, loadProducts, loadCategories } = useProducts();

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const query = { page, page_size: PAGE_SIZE, sort };
      if (search.trim()) query.search = search.trim();
      if (categoryId) query.category_id = categoryId;
      if (maxPrice !== "") query.max_price = maxPrice;
      if (availableOnly) query.available = true;
      loadProducts(query);
    }, search.trim() ? 250 : 0);
    return () => window.clearTimeout(timer);
  }, [search, categoryId, sort, maxPrice, availableOnly, page, loadProducts]);

  const updateFilter = setter => event => {
    setter(event.target.value);
    setPage(1);
  };
  const pageLabel = pagination.pages ? `Page ${pagination.page} of ${pagination.pages}` : "No pages";
  const retry = () => {
    const query = { page, page_size: PAGE_SIZE, sort };
    if (search.trim()) query.search = search.trim();
    if (categoryId) query.category_id = categoryId;
    if (maxPrice !== "") query.max_price = maxPrice;
    if (availableOnly) query.available = true;
    loadProducts(query);
  };

  return <Page>
    <PageTitle label="MARKETPLACE" title="All Products" subtitle="Browse products currently offered by marketplace farmers."/>
    <div className="shop-layout">
      <aside className="filters">
        <strong>Filters</strong>
        <label className="search"><Search size={15}/><input name="search" value={search} onChange={updateFilter(setSearch)} placeholder="Search products..."/></label>
        <h4>Categories</h4>
        <label className="check"><input type="radio" name="category" checked={!categoryId} onChange={() => { setCategoryId(""); setPage(1); }}/>All</label>
        {categories.map(category => <label className="check" key={category.id}><input type="radio" name="category" checked={categoryId === category.id} onChange={() => { setCategoryId(category.id); setPage(1); }}/>{category.name}</label>)}
        {categoriesError && <div role="alert" className="form-error">Categories could not be loaded. <button type="button" className="text-action" onClick={loadCategories}>Retry</button></div>}
        {categoriesLoading && <small role="status">Loading categories…</small>}
        <h4>Maximum price</h4>
        <label className="search">₹<input aria-label="Maximum price" type="number" min="0" step="0.01" value={maxPrice} onChange={updateFilter(setMaxPrice)} placeholder="No maximum"/></label>
        <label className="check"><input type="checkbox" checked={availableOnly} onChange={event => { setAvailableOnly(event.target.checked); setPage(1); }}/>Available only</label>
        <h4>Sort By</h4>
        <select value={sort} onChange={updateFilter(setSort)}>
          <option value="newest">Newest</option>
          <option value="oldest">Oldest</option>
          <option value="price_low">Price: Low to High</option>
          <option value="price_high">Price: High to Low</option>
          <option value="name">Name</option>
        </select>
      </aside>
      <main>
        <div className="result-bar"><span>{pagination.total} products</span><span>{pageLabel}</span></div>
        {loading ? <Loading label="Loading products…"/> : error ? <EmptyState title="Products could not be loaded" description={error.message || "Please try again."} action={<Button variant="outline" onClick={retry}>Try again</Button>}/> : products.length ? <ProductGrid products={products} onAdd={add}/> : <EmptyState title="No products found" description="Try adjusting your search or filters."/>}
        <div className="pagination-controls" aria-label="Product pages">
          <Button variant="outline" disabled={loading || page <= 1} onClick={() => setPage(value => Math.max(1, value - 1))}>Previous</Button>
          <span>{pageLabel}</span>
          <Button variant="outline" disabled={loading || !pagination.pages || page >= pagination.pages} onClick={() => setPage(value => value + 1)}>Next</Button>
        </div>
      </main>
    </div>
  </Page>;
}
