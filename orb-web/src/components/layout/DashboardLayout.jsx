import { useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { X } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { useCart } from "../../context/CartContext";
import AppFooter from "./AppFooter";
import AppHeader from "./AppHeader";

const destinations = {
  customer: { home: "/customer", products: "/customer/products" },
  farmer: { home: "/farmer", products: "/farmer/products" }
};

export default function DashboardLayout({ role }) {
  const [mobile, setMobile] = useState(false);
  const { count } = useCart();
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const exit = () => { signOut(); navigate("/"); };
  const links = destinations[role];
  return <div className="app"><AppHeader role={role} cartCount={count} setMobile={setMobile} pathname={location.pathname}/>{mobile && <div className="mobile-drawer"><button onClick={() => setMobile(false)}><X/> Close</button><NavLink to={links.home} onClick={() => setMobile(false)}>Home / Dashboard</NavLink><NavLink to={links.products} onClick={() => setMobile(false)}>Products</NavLink>{role === "farmer" && <><NavLink to="/farmer/orders" onClick={() => setMobile(false)}>Orders</NavLink><NavLink to="/farmer/profile" onClick={() => setMobile(false)}>Profile</NavLink><NavLink to="/farmer/verification" onClick={() => setMobile(false)}>Verification</NavLink></>}<button onClick={exit}>Log out</button></div>}<main><Outlet key={`${location.pathname}${location.search}`}/></main><AppFooter onExit={exit}/></div>;
}
