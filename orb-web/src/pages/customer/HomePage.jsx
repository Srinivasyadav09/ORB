import { ShoppingBag } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import EmptyState from "../../components/common/EmptyState";
import Loading from "../../components/common/Loading";
import Benefits from "../../components/customer/Benefits";
import ProductGrid from "../../components/products/ProductGrid";
import { Page, SectionHead } from "../../components/layout/Page";
import { useCart } from "../../context/CartContext";
import { useProducts } from "../../context/ProductsContext";

export default function HomePage() {
  const navigate = useNavigate();
  const { add } = useCart();
  const { products, loading, error, loadProducts } = useProducts();
  const retry = () => loadProducts({ page: 1, page_size: 8, sort: "newest" });
  return <Page>
    <section className="market-hero"><div><span className="eyebrow">FRESH FROM FARMS</span><h1>Fresh from farms<br/>to your <em>home.</em></h1><p>Support local farmers and enjoy fresh, healthy and quality produce.</p><Button icon={ShoppingBag} onClick={() => navigate("/customer/products")}>Shop now</Button></div></section>
    <Benefits/>
    <section className="goal marketplace-intro"><div><span className="section-label">THE ORB MARKETPLACE</span><h2>Fresh, local, and easy to find.</h2></div><p>ORB brings nearby farmers and customers together. Explore seasonal produce and order fresh food directly from local farms.</p></section>
    <SectionHead label="MARKETPLACE" title="Featured products" action="View all" onClick={() => navigate("/customer/products")}/>
    {loading ? <Loading label="Loading products…"/> : error ? <EmptyState title="Products could not be loaded" description={error.message || "Please try again."} action={<Button variant="outline" onClick={retry}>Try again</Button>}/> : products.length ? <ProductGrid products={products.slice(0, 4)} onAdd={add}/> : <EmptyState title="No products available" description="There are no marketplace products to show right now."/>}
  </Page>;
}
