import { useState } from "react";
import { Link } from "react-router-dom";
import Badge from "../../components/common/Badge";
import Button from "../../components/common/Button";
import { Page, PageTitle } from "../../components/layout/Page";
import { useOrders } from "../../context/OrdersContext";

const filters = [
  ["All Orders", "all"], ["Confirmed", "CONFIRMED"], ["Processing", "PROCESSING"],
  ["Shipped", "SHIPPED"], ["Delivered", "DELIVERED"], ["Cancelled", "CANCELLED"]
];

export default function OrdersPage() {
  const [filter, setFilter] = useState("all");
  const { orders, pagination, loading, error, refreshOrders } = useOrders();
  const visibleOrders = filter === "all" ? orders : orders.filter(order => order.status === filter);
  return <Page><PageTitle label="PURCHASE HISTORY" title="My Orders"/>
    <div className="tabs">{filters.map(([label, value]) => <button key={value} className={filter === value ? "active" : ""} onClick={() => setFilter(value)}>{label}</button>)}</div>
    {loading ? <p role="status">Loading your orders…</p> : error ? <div className="empty" role="alert"><h2>Order history could not be loaded</h2><p>{error}</p><Button variant="outline" onClick={() => refreshOrders(pagination.page)}>Try again</Button></div> : visibleOrders.length ? <>
      {visibleOrders.map(order => <article className="order-card" key={order.id}><div><strong>Order {order.orderNumber}</strong><small>Placed on {order.date} · Payment {order.paymentStatus}</small></div><div/><strong>₹{order.total}</strong><Badge>{order.status}</Badge><Link className="btn outline" to={`/customer/orders/${order.id}`}>View Details</Link></article>)}
      <div className="form-actions"><Button variant="outline" disabled={pagination.page <= 1} onClick={() => refreshOrders(pagination.page - 1)}>Previous</Button><span>Page {pagination.page} of {Math.max(1, pagination.pages)}</span><Button variant="outline" disabled={pagination.page >= pagination.pages} onClick={() => refreshOrders(pagination.page + 1)}>Next</Button></div>
    </> : <div className="empty"><h2>{filter === "all" ? "No orders yet" : `No ${filter.toLowerCase()} orders`}</h2><p>Your backend-confirmed orders will appear here.</p></div>}
  </Page>;
}
