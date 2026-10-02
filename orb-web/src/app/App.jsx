import { Route, Routes } from "react-router-dom";
import { useCart } from "../context/CartContext";
import CustomerLayout from "../components/layout/CustomerLayout";
import FarmerLayout from "../components/layout/FarmerLayout";
import LandingPage from "../pages/customer/LandingPage";
import AuthPage from "../pages/auth/AuthPage";
import HomePage from "../pages/customer/HomePage";
import ProductsPage from "../pages/customer/ProductsPage";
import ProductDetailsPage from "../pages/customer/ProductDetailsPage";
import CartPage from "../pages/customer/CartPage";
import OrdersPage from "../pages/customer/OrdersPage";
import OrderDetailsPage from "../pages/customer/OrderDetailsPage";
import CheckoutPage from "../pages/customer/CheckoutPage";
import CustomerAccountPage from "../pages/customer/CustomerAccountPage";
import FarmerDashboardPage from "../pages/farmer/FarmerDashboardPage";
import FarmerProductsPage from "../pages/farmer/FarmerProductsPage";
import AddProductPage from "../pages/farmer/AddProductPage";
import FarmerProfilePage from "../pages/farmer/FarmerProfilePage";
import FarmerVerificationPage from "../pages/farmer/FarmerVerificationPage";
import FarmerOrdersPage from "../pages/farmer/FarmerOrdersPage";
import NotFoundPage from "../pages/NotFoundPage";
import RequireRole from "../routes/RequireRole";
import { routeRoles } from "../routes/routeConfig";

function CartRoute() {
  const { cart, subtotal, deliveryFee, totalAmount, loading, error, pending, refresh, changeQty, remove } = useCart();
  return <CartPage cart={cart} subtotal={subtotal} deliveryFee={deliveryFee} totalAmount={totalAmount} loading={loading} error={error} pending={pending} refresh={refresh} changeQty={changeQty} remove={remove}/>;
}

export default function App() {
  return <Routes>
    <Route path="/" element={<LandingPage/>}/>
    <Route path="/login" element={<AuthPage/>}/>
    <Route path="/signup" element={<AuthPage/>}/>

    <Route path="/customer" element={<RequireRole role={routeRoles.customer}><CustomerLayout/></RequireRole>}>
      <Route index element={<HomePage/>}/>
      <Route path="products" element={<ProductsPage/>}/>
      <Route path="products/:productId" element={<ProductDetailsPage/>}/>
      <Route path="cart" element={<CartRoute/>}/>
      <Route path="checkout" element={<CheckoutPage/>}/>
      <Route path="orders" element={<OrdersPage/>}/>
      <Route path="orders/:orderId" element={<OrderDetailsPage/>}/>
      <Route path="account" element={<CustomerAccountPage/>}/>
    </Route>

    <Route path="/farmer" element={<RequireRole role={routeRoles.farmer}><FarmerLayout/></RequireRole>}>
      <Route index element={<FarmerDashboardPage/>}/>
      <Route path="products" element={<FarmerProductsPage/>}/>
      <Route path="products/new" element={<AddProductPage/>}/>
      <Route path="products/:productId/edit" element={<AddProductPage/>}/>
      <Route path="orders" element={<FarmerOrdersPage/>}/>
      <Route path="profile" element={<FarmerProfilePage/>}/>
      <Route path="verification" element={<FarmerVerificationPage/>}/>
    </Route>

    <Route path="*" element={<NotFoundPage/>}/>
  </Routes>;
}
