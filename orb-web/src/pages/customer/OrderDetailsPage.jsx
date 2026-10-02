import { useEffect, useState } from "react";
import { ArrowLeft, MapPin } from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";
import Badge from "../../components/common/Badge";
import Button from "../../components/common/Button";
import Card from "../../components/common/Card";
import { Page } from "../../components/layout/Page";
import { useOrders } from "../../context/OrdersContext";
import { apiErrorMessage } from "../../utils/apiErrorMessage";

export default function OrderDetailsPage() {
  const navigate = useNavigate();
  const { orderId } = useParams();
  const { getOrder } = useOrders();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setOrder(null);
    setError("");
    getOrder(orderId).then(value => { if (active) setOrder(value); })
      .catch(cause => { if (active) setError(apiErrorMessage(cause, { notFound: "This order was not found." })); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [getOrder, orderId, retry]);

  if (loading) return <Page><p role="status">Loading order details…</p></Page>;
  if (error) return <Page><button className="back-button" onClick={() => navigate("/customer/orders")}><ArrowLeft size={15}/> Back to Orders</button><div className="empty" role="alert"><h2>Order details unavailable</h2><p>{error}</p><Button variant="outline" onClick={() => setRetry(value => value + 1)}>Try again</Button></div></Page>;
  if (!order) return <Page><div className="empty"><h2>Order not found</h2><Button onClick={() => navigate("/customer/orders")}>Back to Orders</Button></div></Page>;

  const address = order.deliveryAddress || {};
  return <Page>
    <button className="back-button" style={{ marginBottom: 18 }} onClick={() => navigate("/customer/orders")}><ArrowLeft size={15}/> Back to Orders</button>
    <div className="order-detail-title"><div><span className="section-label">ORDER DETAILS</span><h1>Order {order.orderNumber}</h1><p>Placed on {order.date}</p></div><Badge>{order.status}</Badge></div>
    <div className="detail-grid"><Card><h3>Products in this order</h3>{order.items.map(line => <div className="order-detail-product" key={line.id}><div className="detail-item">{line.productImageUrl ? <img src={line.productImageUrl} alt={line.productName}/> : <div className="product-image-empty" aria-label="No product image available"/>}<span><strong>{line.productName}</strong><small>₹{line.unitPrice}/{line.unit} × {line.quantity}</small></span><b>₹{line.lineTotal}</b></div></div>)}</Card>
      <Card><h3>Delivery Information</h3><p className="address"><MapPin size={18}/><span><strong>{address.fullName}</strong><br/>{address.addressLine1}{address.addressLine2 ? <><br/>{address.addressLine2}</> : null}<br/>{address.city}, {address.state} {address.postalCode}, {address.country}</span></p><p className="muted">Phone: {address.phone}</p><h3>Payment Information</h3><p className="muted">{order.paymentMethod} · {order.paymentStatus}</p><hr/><div className="summary-row"><span>Subtotal</span><b>₹{order.subtotal}</b></div><div className="summary-row"><span>Delivery charge</span><b>₹{order.deliveryFee}</b></div><div className="total"><span>Total Amount</span><b>₹{order.total}</b></div></Card>
    </div>
  </Page>;
}
