import { Minus, Plus, ShoppingCart, Trash2 } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import EmptyState from "../../components/common/EmptyState";
import OrderSummary from "../../components/cart/OrderSummary";
import DeliveryAddressSelector from "../../components/customer/DeliveryAddressSelector";
import { Page, PageTitle } from "../../components/layout/Page";

export default function CartPage({ cart, subtotal, deliveryFee, totalAmount, loading, error, pending, refresh, changeQty, remove }) {
  const navigate = useNavigate();
  return <Page><PageTitle label="YOUR SHOPPING" title="Your Cart" action={<button className="text-action" onClick={() => navigate("/customer/products")}>Continue Shopping</button>}/>
    {loading ? <div role="status" className="cart-message">Loading your cart…</div> : error && !cart.length ? <div role="alert" className="cart-message"><p>{error}</p><Button onClick={refresh}>Try Again</Button></div> : <>{error && <p role="alert" className="cart-message">{error}</p>}{!cart.length ? <EmptyState icon={ShoppingCart} title="Your cart is empty" description="Add fresh products from local farmers." action={<Button onClick={() => navigate("/customer/products")}>Shop Products</Button>}/> : <div className="cart-layout"><section className="cart-list"><div className="cart-head"><span>Product</span><span>Price</span><span>Quantity</span><span>Total</span><span/></div>{cart.map(({ product, qty, lineTotal, availableStock, isAvailable, availabilityReason }) => <div className="cart-row" key={product.id}><div className="cart-product">{product.image ? <img src={product.image} alt={product.name}/> : <div className="product-image-empty" aria-label="No product image available"/>}<span><strong>{product.name}</strong>{!isAvailable && <small role="status">{availabilityReason || "Currently unavailable"}</small>}</span></div><span>₹{product.price}/{product.unit}</span><div className="qty"><button aria-label={`Decrease ${product.name}`} disabled={pending || qty <= 1 || !isAvailable} onClick={() => changeQty(product.id, -1)}><Minus size={13}/></button><b>{qty}</b><button aria-label={`Increase ${product.name}`} disabled={pending || !isAvailable || qty >= availableStock} onClick={() => changeQty(product.id, 1)}><Plus size={13}/></button></div><strong>₹{lineTotal}</strong><button className="delete" aria-label={`Remove ${product.name}`} disabled={pending} onClick={() => remove(product.id)}><Trash2 size={16}/></button></div>)}<DeliveryAddressSelector compact/></section><OrderSummary subtotal={subtotal} deliveryFee={deliveryFee} totalAmount={totalAmount} onCheckout={() => navigate("/customer/checkout")}/></div>}</>}
  </Page>;
}
