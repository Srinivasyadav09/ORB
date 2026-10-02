export const routePaths = {
  home: "/customer",
  products: "/customer/products",
  cart: "/customer/cart",
  checkout: "/customer/checkout",
  orders: "/customer/orders",
  account: "/customer/account",
  farmerHome: "/farmer",
  farmerProducts: "/farmer/products",
  newFarmerProduct: "/farmer/products/new",
  farmerProfile: "/farmer/profile",
  farmerVerification: "/farmer/verification"
};

export const routeRoles = Object.freeze({
  customer: "CUSTOMER",
  farmer: "FARMER",
  admin: "ADMIN"
});
