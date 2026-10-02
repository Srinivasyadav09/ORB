import { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import Loading from "../../components/common/Loading";
import EmptyState from "../../components/common/EmptyState";
import { Page } from "../../components/layout/Page";
import { useFarmerProducts } from "../../context/FarmerProductsContext";
import { categoryApi } from "../../services/api/categoryApi";
import { farmerApi } from "../../services/api/farmerApi";
import { productApi } from "../../services/api/productApi";
import { normalizeCategory, normalizeProduct, normalizeVerification, requireList } from "../../services/api/normalize";
import { apiErrorMessage } from "../../utils/apiErrorMessage";

const units = ["kg", "g", "bunch", "piece", "dozen", "litre"];
const statusChoices = status => status === "ACTIVE"
  ? ["ACTIVE", "INACTIVE"]
  : status === "INACTIVE" ? ["INACTIVE", "DRAFT", "ACTIVE"] : ["DRAFT", "ACTIVE", ...(status ? ["INACTIVE"] : [])];

export default function AddProductPage() {
  const navigate = useNavigate();
  const { productId } = useParams();
  const { createProduct, updateProduct } = useFarmerProducts();
  const [product, setProduct] = useState(null);
  const [categories, setCategories] = useState([]);
  const [verificationStatus, setVerificationStatus] = useState(null);
  const [verificationError, setVerificationError] = useState(null);
  const [loading, setLoading] = useState(true);
  const [categoriesError, setCategoriesError] = useState(null);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  const isEdit = Boolean(productId);

  const loadFormData = useCallback(async () => {
    setLoading(true);
    setError(null);
    setCategoriesError(null);
    setVerificationError(null);
    setVerificationStatus(null);
    const [categoryResult, productResult, verificationResult] = await Promise.allSettled([
      categoryApi.list(),
      isEdit ? productApi.getMine(productId) : Promise.resolve(null),
      farmerApi.getVerification()
    ]);

    if (categoryResult.status === "fulfilled") {
      try { setCategories(requireList(categoryResult.value, "categories").map(normalizeCategory)); }
      catch (parseError) { setCategoriesError(parseError); setCategories([]); }
    } else {
      setCategoriesError(categoryResult.reason);
      setCategories([]);
    }

    if (isEdit && productResult.status === "fulfilled") {
      try {
        const saved = normalizeProduct(productResult.value);
        setProduct(saved);
        setImageUrl(saved.imageUrl || "");
      } catch (parseError) { setError(parseError); }
    } else if (isEdit) {
      setError(productResult.reason);
    } else {
      setProduct(null);
      setImageUrl("");
    }

    if (verificationResult.status === "fulfilled") {
      try { setVerificationStatus(normalizeVerification(verificationResult.value).status); }
      catch (verificationParseError) { setVerificationError(verificationParseError); }
    } else {
      setVerificationError(verificationResult.reason);
    }
    setLoading(false);
  }, [isEdit, productId]);

  useEffect(() => { loadFormData(); }, [loadFormData]);

  const returnToProducts = () => navigate("/farmer/products");
  const submit = async event => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    const values = new FormData(event.currentTarget);
    const payload = {
      name: String(values.get("name")).trim(),
      category_id: String(values.get("category_id")),
      price: String(values.get("price")),
      unit: String(values.get("unit")),
      available_quantity: String(values.get("available_quantity")),
      image_url: String(values.get("image_url") || "").trim() || null,
      description: String(values.get("description") || "").trim() || null,
      status: String(values.get("status"))
    };
    try {
      if (isEdit) await updateProduct(productId, payload);
      else await createProduct(payload);
      navigate("/farmer/products", { replace: true, state: { success: isEdit ? "Product updated." : "Product created." } });
    } catch (requestError) {
      setError(requestError);
    } finally {
      setSubmitting(false);
    }
  };

  const canPublish = verificationStatus === "COMPLETED";
  if (loading) return <Page><Loading label={isEdit ? "Loading product…" : "Loading categories…"}/></Page>;
  if (isEdit && error?.status === 404) return <Page><EmptyState title="Product not found" description={apiErrorMessage(error, { notFound: "This product does not exist or is not owned by your account." })} action={<Button onClick={returnToProducts}>Back to Products</Button>}/></Page>;
  if (isEdit && error) return <Page><EmptyState title="Product could not be loaded" description={apiErrorMessage(error)} action={<Button variant="outline" onClick={loadFormData}>Try again</Button>}/></Page>;

  const currentStatus = product?.status || "DRAFT";
  const choices = statusChoices(product?.status);
  return <Page>
    <button className="back-button" onClick={returnToProducts}><ArrowLeft size={15}/> Back to Products</button>
    <form className="form-panel" onSubmit={submit}>
      <span className="section-label">FARMER INVENTORY</span>
      <h1>{isEdit ? "Edit Product" : "Add New Product"}</h1>
      <p className="muted">Publish and keep your product details up to date.</p>
      {categoriesError && <div role="alert" className="form-error">{apiErrorMessage(categoriesError)} <Button type="button" variant="outline" onClick={loadFormData}>Retry</Button></div>}
      {verificationError && <p role="alert" className="form-error">Verification status could not be loaded. Products can be saved as drafts; publishing will be checked by the server.</p>}
      {verificationStatus && <p className="muted">Farmer verification: <strong>{verificationStatus}</strong></p>}
      <div className="form-grid">
        <Input label="Product Name" name="name" placeholder="e.g. Fresh Tomatoes" defaultValue={product?.name} minLength="2" maxLength="160" required/>
        <label className="field"><span>Category</span><div><select name="category_id" defaultValue={product?.categoryId || ""} required disabled={!categories.length || Boolean(categoriesError)}><option value="" disabled>Choose a category</option>{categories.map(category => <option key={category.id} value={category.id}>{category.name}</option>)}</select></div></label>
        <Input label="Price (₹)" name="price" type="number" min="0.01" step="0.01" placeholder="Enter price" defaultValue={product?.price} required/>
        <div className="split-field"><Input label="Available Quantity" name="available_quantity" type="number" min="0" step="0.001" placeholder="Enter quantity" defaultValue={product?.availableQuantity ?? 0} required/><label className="field"><span>Unit</span><div><select name="unit" defaultValue={product?.unit || "kg"}>{units.map(unit => <option key={unit} value={unit}>{unit}</option>)}</select></div></label></div>
        <Input label="Product Image URL (optional)" name="image_url" type="text" placeholder="https://… or /uploads/image.jpg" value={imageUrl} onChange={event => setImageUrl(event.target.value)} maxLength="2048" className="full"/>
        {imageUrl && <img className="upload-preview" src={imageUrl} alt="Product preview"/>}
        <label className="field full"><span>Description</span><div className="textarea-wrap"><textarea name="description" rows="4" maxLength="4000" defaultValue={product?.description} placeholder="Describe your product..."/></div></label>
        <label className="field"><span>Product status</span><div><select name="status" defaultValue={currentStatus}>{choices.map(status => <option key={status} value={status} disabled={status === "ACTIVE" && !canPublish}>{status}</option>)}</select></div></label>
      </div>
      {!canPublish && <p className="muted">Only farmers with completed verification can activate products. The server enforces this when saving.</p>}
      {error && <p role="alert" className="form-error">{apiErrorMessage(error)}</p>}
      <div className="form-actions"><Button type="button" variant="outline" onClick={returnToProducts}>Cancel</Button><Button type="submit" disabled={submitting || !categories.length || Boolean(categoriesError)}>{submitting ? "Saving…" : isEdit ? "Save Changes" : "Create Product"}</Button></div>
    </form>
  </Page>;
}
