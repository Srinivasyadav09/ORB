import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Eye, Pencil, Plus, ToggleLeft, ToggleRight } from "lucide-react";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import EmptyState from "../../components/common/EmptyState";
import Loading from "../../components/common/Loading";
import { Page, PageTitle } from "../../components/layout/Page";
import { useFarmerProducts } from "../../context/FarmerProductsContext";
import { apiErrorMessage } from "../../utils/apiErrorMessage";

export default function FarmerProductsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { products, pagination, loading, error, loadProducts, setProductStatus, deactivateProduct } = useFarmerProducts();
  const [actionError, setActionError] = useState(null);
  const [success, setSuccess] = useState(location.state?.success || "");
  const [pendingId, setPendingId] = useState(null);

  const updateStatus = async product => {
    setPendingId(product.id);
    setActionError(null);
    setSuccess("");
    try {
      const nextStatus = product.status === "ACTIVE" ? "INACTIVE" : "ACTIVE";
      await setProductStatus(product.id, nextStatus);
      setSuccess(nextStatus === "ACTIVE" ? "Product activated." : "Product marked inactive.");
    } catch (requestError) {
      setActionError(apiErrorMessage(requestError));
    } finally { setPendingId(null); }
  };

  const deactivate = async product => {
    setPendingId(product.id);
    setActionError(null);
    setSuccess("");
    try {
      await deactivateProduct(product.id);
      setSuccess("Product deactivated.");
    } catch (requestError) {
      setActionError(apiErrorMessage(requestError, { notFound: "This product no longer exists or is not yours." }));
    } finally { setPendingId(null); }
  };

  const pageLabel = pagination.pages ? `Page ${pagination.page} of ${pagination.pages}` : "No pages";
  return <Page>
    <PageTitle label="INVENTORY" title="My Products" subtitle="Manage your product listings and available quantities." action={<Button icon={Plus} onClick={() => navigate("/farmer/products/new")}>Add Product</Button>}/>
    {success && <p role="status" className="success-message">{success}</p>}
    {actionError && <p role="alert" className="form-error">{actionError}</p>}
    {error && <div role="alert" className="form-error">{apiErrorMessage(error, { notFound: "Farmer inventory could not be found." })} <Button variant="outline" onClick={() => loadProducts(pagination.page)}>Try again</Button></div>}
    {loading ? <Loading label="Loading your products…"/> : !error && !products.length ? <EmptyState title="No products yet" description="Add your first farm product to start selling on ORB." action={<Button icon={Plus} onClick={() => navigate("/farmer/products/new")}>Add Product</Button>}/> : !error && <>
      <section className="farmer-table">{products.map(product => <div key={product.id}>
        {product.image ? <img src={product.image} alt={product.name}/> : <div className="product-image-empty farmer-product-image-empty" aria-label="No product image available"/>}
        <span><strong>{product.name}</strong><small>{product.category} • ₹{product.price}/{product.unit}</small></span>
        <span>Available quantity: <strong>{product.availableQuantity} {product.unit}</strong></span>
        <span className="updated">{product.status}</span>
        <Badge>{product.isAvailable ? "Available" : "Unavailable"}</Badge>
        <div className="inventory-actions">
          <button title={product.status === "ACTIVE" ? "Mark inactive" : "Activate product"} aria-label={product.status === "ACTIVE" ? `Mark ${product.name} inactive` : `Activate ${product.name}`} disabled={pendingId === product.id} onClick={() => updateStatus(product)}>{product.status === "ACTIVE" ? <ToggleRight/> : <ToggleLeft/>}</button>
          <button title="Edit product" aria-label={`Edit ${product.name}`} disabled={pendingId === product.id} onClick={() => navigate(`/farmer/products/${product.id}/edit`)}><Pencil size={16}/></button>
          <button title="Deactivate product" aria-label={`Deactivate ${product.name}`} disabled={pendingId === product.id || product.status === "INACTIVE"} onClick={() => deactivate(product)}><Eye size={16}/></button>
        </div>
      </div>)}</section>
      <div className="pagination-controls" aria-label="Inventory pages">
        <Button variant="outline" disabled={loading || pagination.page <= 1} onClick={() => loadProducts(pagination.page - 1)}>Previous</Button>
        <span>{pageLabel} · {pagination.total} products</span>
        <Button variant="outline" disabled={loading || !pagination.pages || pagination.page >= pagination.pages} onClick={() => loadProducts(pagination.page + 1)}>Next</Button>
      </div>
    </>}
  </Page>;
}
