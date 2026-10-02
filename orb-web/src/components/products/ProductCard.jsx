import { useState } from "react";
import { ShoppingCart } from "lucide-react";
import { Link } from "react-router-dom";

export default function ProductCard({ product, onAdd }) {
  const [notice, setNotice] = useState("");
  const [adding, setAdding] = useState(false);
  const addToCart = async () => {
    if (adding) return;
    setAdding(true);
    try {
      const result = await onAdd(product);
      setNotice(result?.ok ? `${product.name} added to cart.` : result?.message || "Could not add this product to your cart.");
    } catch (error) {
      setNotice(error?.message || "Could not add this product to your cart.");
    } finally {
      setAdding(false);
    }
  };
  const image = product.image || product.image_url;
  const available = product.isAvailable ?? product.is_available;
  return <article className="product-card">
    <Link to={`/customer/products/${product.id}`} aria-label={`View ${product.name}`}>
      {image ? <img src={image} alt={product.name}/> : <div className="product-image-empty" aria-label="No product image available"/>}
    </Link>
    <div>
      <div className="product-line"><h3><Link to={`/customer/products/${product.id}`}>{product.name}</Link></h3><b>₹{product.price}/{product.unit}</b></div>
      <div className="product-availability" role="status">{available ? "Available" : "Currently unavailable"}</div>
      {product.farmer && <p>By <strong>{product.farmer}</strong></p>}
      <button onClick={addToCart} disabled={!available || adding}><ShoppingCart size={14}/> {adding ? "Adding…" : "Add to Cart"}</button>
      {notice && <small role="status" className="product-notice">{notice}</small>}
    </div>
  </article>;
}
