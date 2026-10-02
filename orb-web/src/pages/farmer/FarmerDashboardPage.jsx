import { Package, ShoppingBag, Star } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Badge from "../../components/common/Badge";
import Card from "../../components/common/Card";
import Stat from "../../components/farmer/Stat";
import Verification from "../../components/farmer/Verification";
import { Page } from "../../components/layout/Page";
import { useFarmer } from "../../context/FarmerContext";
import { useFarmerProducts } from "../../context/FarmerProductsContext";

export default function FarmerDashboardPage() {
  const { profile, loading: profileLoading, profileError, refreshProfile } = useFarmer();
  const { pagination: productPagination, loading: productsLoading, activeCount } = useFarmerProducts();
  const navigate = useNavigate();
  return <Page><div className="dashboard-title"><div><span className="section-label">FARMER DASHBOARD</span><h1>Welcome, {profileLoading ? "…" : profile?.fullName || "Farmer"}</h1><p>Manage your farm and products from one place.</p></div>{profile?.verification && <Badge>{profile.verification}</Badge>}</div>{profileError && <div role="alert" className="form-error">{profileError} <button type="button" className="text-action" onClick={() => refreshProfile()}>Retry</button></div>}<div className="stats farmer-stats"><Stat label="Total Products" value={productsLoading ? "…" : productPagination.total} icon={ShoppingBag}/><Stat label="Active Products" value={productsLoading || activeCount === null ? "…" : activeCount} icon={Package}/><Stat label="Orders" value="Unavailable" icon={Package}/><Stat label="Sales" value="Unavailable" icon={Package}/><Stat label="Average Rating" value="Not available" icon={Star}/></div><div className="dashboard-grid"><Card><div className="card-heading"><h3>Orders</h3><button className="text-action" onClick={() => navigate("/farmer/orders")}>View details</button></div><p className="muted">Farmer order data is not available from the backend yet.</p></Card><Card><div className="card-heading"><h3>Farmer Verification</h3><button className="text-action" onClick={() => navigate("/farmer/verification")}>Details</button></div><Verification/></Card></div></Page>;
}
