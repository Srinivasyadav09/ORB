import { Bell, Home, Menu, Package, Plus, ShoppingBag, ShoppingCart, UserRound } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";
import Logo from "../common/Logo";

const navigation = {
  customer: [["/customer", "Home", Home, path => path === "/customer"], ["/customer/products", "Products", ShoppingBag, path => path.startsWith("/customer/products")], ["/customer/cart", "Cart", ShoppingCart, path => path === "/customer/cart"], ["/customer/orders", "Orders", Package, path => path.startsWith("/customer/orders")]],
  farmer: [["/farmer", "Dashboard", Home, path => path === "/farmer"], ["/farmer/products", "My Products", ShoppingBag, path => path.startsWith("/farmer/products")], ["/farmer/orders", "Orders", Package, path => path.startsWith("/farmer/orders")], ["/farmer/profile", "Profile", UserRound, path => path === "/farmer/profile" || path === "/farmer/verification"]]
};

export default function AppHeader({ role, cartCount, setMobile, pathname }) {
  const navigate = useNavigate();
  return <header className="app-header"><Logo/><nav>{navigation[role].map(([to, label, Icon, activeFor]) => <NavLink end to={to} className={() => activeFor(pathname) ? "active" : ""} key={to}><Icon size={15}/>{label}{to === "/customer/cart" && cartCount > 0 && <b className="cart-badge">{cartCount}</b>}</NavLink>)}</nav><div className="header-actions"><button className="round"><Bell size={17}/></button><button className="avatar" onClick={() => navigate(role === "customer" ? "/customer/account" : "/farmer/profile")}>{role === "customer" ? "C" : "F"}</button><button className="mobile-toggle" onClick={() => setMobile(true)}><Menu/></button></div></header>;
}
