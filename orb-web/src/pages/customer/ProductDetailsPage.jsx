import { useEffect, useState } from "react";
import { ArrowLeft, BadgeCheck, MapPin, ShoppingCart } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Button from "../../components/common/Button";
import Card from "../../components/common/Card";
import EmptyState from "../../components/common/EmptyState";
import Loading from "../../components/common/Loading";
import { Page } from "../../components/layout/Page";
import { useCart } from "../../context/CartContext";
import { productApi } from "../../services/api/productApi";
import { normalizeProduct } from "../../services/api/normalize";

export default function ProductDetailsPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const { add } = useCart();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [retryKey, setRetryKey] = useState(0);
  const [cartMessage, setCartMessage] = useState("");
  const [adding, setAdding] = useState(false);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    setProduct(null);
    productApi.get(productId)
      .then(response => { if (active) setProduct(normalizeProduct(response)); })
      .catch(requestError => { if (active) setError(requestError); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [productId, retryKey]);

  if (loading) return <Page><Loading label="Loading product…"/></Page>;
  if (error?.status === 404) return <Page><EmptyState title="Product not found" description="This product may no longer be available." action={<Button onClick={() => navigate("/customer/products")}>Browse Products</Button>}/></Page>;
  if (error?.status === 422) return <Page><EmptyState title="Invalid product link" description="This product link is invalid. Browse the marketplace to find an available product." action={<Button onClick={() => navigate("/customer/products")}>Browse Products</Button>}/></Page>;
  if (error) return <Page><EmptyState title="Product could not be loaded" description={error.message || "Please try again."} action={<Button variant="outline" onClick={() => setRetryKey(value => value + 1)}>Try again</Button>}/></Page>;
  if (!product) return <Page><EmptyState title="Product not found" description="This product may no longer be available." action={<Button onClick={() => navigate("/customer/products")}>Browse Products</Button>}/></Page>;

  const available = product.isAvailable;
  const addToCart = async () => {
    if (adding) return;
    setAdding(true);
    const result = await add(product);
    setCartMessage(result?.ok ? `${product.name} added to cart.` : result?.message || "Could not add this product to your cart.");
    setAdding(false);
  };
  return <Page>
    <button className="back-button" onClick={() => navigate("/customer/products")}><ArrowLeft size={15}/> Back to Products</button>
    <div className="detail-grid product-detail-layout" style={{ marginTop: 18 }}>
      <Card>{product.image ? <img src={product.image} alt={product.name} className="product-detail-image"/> : <div className="product-image-empty product-detail-image" aria-label="No product image available"/>}</Card>
      <Card>
        <span className="section-label">{product.category}</span>
        <h1>{product.name}</h1>
        <h2>₹{product.price}/{product.unit}</h2>
        <p role="status">{available ? `${product.availableQuantity} ${product.unit} available` : "Currently unavailable"}</p>
        {product.description && <p>{product.description}</p>}
        <Button icon={ShoppingCart} disabled={!available || adding} onClick={addToCart}>{adding ? "Adding…" : "Add to Cart"}</Button>
        {cartMessage && <p role="status">{cartMessage}</p>}
        <p><Link to="/customer/cart" className="text-action">Go to cart</Link></p>
        <hr/>
        <div className="farmer-profile-summary"><span className="role-icon green"><MapPin/></span><div><span className="section-label">GROWN BY</span><h3>{product.farmer}</h3>{product.farmerLocation && <p className="muted"><MapPin size={14}/> {product.farmerLocation}</p>}</div></div>
        {product.farmerVerified && <p className="verification-label"><BadgeCheck size={16}/> Verified ORB farmer</p>}
      </Card>
    </div>
  </Page>;
}
