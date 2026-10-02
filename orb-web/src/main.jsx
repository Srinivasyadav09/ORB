import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./app/App";
import { AuthProvider } from "./context/AuthContext";
import { CartProvider } from "./context/CartContext";
import { CustomerProvider } from "./context/CustomerContext";
import { FarmerProvider } from "./context/FarmerContext";
import { ProductsProvider } from "./context/ProductsContext";
import { FarmerProductsProvider } from "./context/FarmerProductsContext";
import { OrdersProvider } from "./context/OrdersContext";
import { AddressesProvider } from "./context/AddressesContext";
import { RatingsProvider } from "./context/RatingsContext";
import { NotificationsProvider } from "./context/NotificationsContext";
import "./styles/index.css";

createRoot(document.getElementById("root")).render(
  <BrowserRouter>
    <AuthProvider>
      <CustomerProvider>
        <FarmerProvider>
          <FarmerProductsProvider>
            <ProductsProvider>
              <OrdersProvider>
                <AddressesProvider>
                  <RatingsProvider>
                    <NotificationsProvider>
                      <CartProvider><App /></CartProvider>
                    </NotificationsProvider>
                  </RatingsProvider>
                </AddressesProvider>
              </OrdersProvider>
            </ProductsProvider>
          </FarmerProductsProvider>
        </FarmerProvider>
      </CustomerProvider>
    </AuthProvider>
  </BrowserRouter>
);
