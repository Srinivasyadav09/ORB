import { useState } from "react";
import { ArrowLeft, Check } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import Card from "../../components/common/Card";
import DeliveryAddressSelector from "../../components/customer/DeliveryAddressSelector";
import { Page } from "../../components/layout/Page";
import { useCart } from "../../context/CartContext";
import { useOrders } from "../../context/OrdersContext";
import { useAddresses } from "../../context/AddressesContext";

export default function CheckoutPage() {
  const navigate = useNavigate();
  const { cart, subtotal, serverCart, loading: cartLoading, error: cartError, refresh: refreshCart } = useCart();
  const { selectedAddress, loading: addressesLoading } = useAddresses();
  const { createOrder, creating } = useOrders();
  const [placedOrder, setPlacedOrder] = useState(null);
  const [submitError, setSubmitError] = useState("");

  const submitOrder = async () => {
    if (creating || !selectedAddress?.id) return;
    setSubmitError("");
    const result = await createOrder(selectedAddress.id);
    if (!result.ok) {
      setSubmitError(result.message);
      return;
    }
    setPlacedOrder(result.order);
    // Checkout atomically clears the cart server-side; refetch to update the header and cart UI.
    try { await refreshCart(); } catch { /* The successful order response still confirms checkout. */ }
  };

  if (placedOrder) return <Page><div className="success"><span><Check size={35}/></span><h1>Order placed</h1><p>Order <strong>{placedOrder.orderNumber}</strong> has been confirmed by ORB.</p><p>Status: <strong>{placedOrder.status}</strong> · Payment: <strong>{placedOrder.paymentMethod} / {placedOrder.paymentStatus}</strong></p><p>Order total: <strong>₹{placedOrder.total}</strong></p><Button onClick={() => navigate(`/customer/orders/${placedOrder.id}`)}>View Order Details</Button></div></Page>;

  if (cartLoading || addressesLoading) return <Page><p role="status">Loading checkout details…</p></Page>;
  if (cartError) return <Page><div role="alert" className="empty"><h2>Cart could not be loaded</h2><p>{cartError}</p><Button variant="outline" onClick={() => refreshCart()}>Try again</Button></div></Page>;
  if (!cart.length) return <Page><div className="empty"><h2>Your cart is empty</h2><p>Add products before checkout.</p><Button onClick={() => navigate("/customer/products")}>Browse Products</Button></div></Page>;

  return <Page>
    <button className="back-button" onClick={() => navigate("/customer/cart")}><ArrowLeft size={15}/> Back to Cart</button>
    <div className="checkout"><Card>
      <span className="section-label">CHECKOUT</span><h1>Delivery & Payment</h1>
      <DeliveryAddressSelector/>
      <h3>Payment method</h3>
      <div className="payment-options"><label className="payment selected"><input type="radio" name="payment" checked readOnly/><span><strong>Cash on Delivery (COD)</strong><small>Payment is due on delivery. Online payment is not available.</small></span></label></div>
      {submitError && <p role="alert" className="cart-message">{submitError}</p>}
    </Card><aside className="summary"><h3>Order Summary</h3>
      {serverCart.items.map(line => <div className="summary-row" key={line.id}><span>{line.productName} × {line.quantity}</span><b>₹{line.lineTotal}</b></div>)}
      <hr/><div className="summary-row"><span>Cart subtotal</span><b>₹{subtotal}</b></div>
      <div className="summary-row"><span>Delivery fee</span><b>₹{serverCart.deliveryFee}</b></div>
      <hr/><div className="summary-row total"><span>Total</span><b>₹{serverCart.totalAmount}</b></div>
      <hr/><p className="muted">Final values are revalidated by the backend when you place your order.</p>
      <Button className="full" disabled={creating || !selectedAddress?.id || cart.length === 0} onClick={submitOrder}>{creating ? "Placing order…" : "Place COD Order"}</Button>
      {!selectedAddress?.id && <small role="status">Select or add a saved delivery address to place your order.</small>}
    </aside></div>
  </Page>;
}
