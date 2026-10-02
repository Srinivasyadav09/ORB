import { ApiError } from "./client";

export function unwrapResponse(value) {
  return value && typeof value === "object" && !Array.isArray(value) && Object.hasOwn(value, "data") ? value.data : value;
}

export function requireRecord(value, domain) {
  const result = unwrapResponse(value);
  if (!result || typeof result !== "object" || Array.isArray(result)) {
    throw new ApiError(`The ${domain} service returned an invalid response.`);
  }
  return result;
}

export function requireList(value, domain) {
  const result = unwrapResponse(value);
  const items = Array.isArray(result) ? result : result?.items;
  if (!Array.isArray(items)) throw new ApiError(`The ${domain} service must return an array or an { items } collection.`);
  return items;
}

const number = value => value == null ? 0 : Number(value);
const displayDate = value => value ? new Date(value).toLocaleDateString("en-GB") : "";

export function normalizeCategory(value) {
  const row = requireRecord(value, "categories");
  if (!row.id || typeof row.name !== "string") throw new ApiError("Category response is missing id or name.");
  return { ...row, id: row.id, name: row.name, description: row.description ?? null, imageUrl: row.image_url ?? null, isActive: Boolean(row.is_active), createdAt: row.created_at, updatedAt: row.updated_at };
}

export function normalizeProduct(value) {
  const row = requireRecord(value, "products");
  if (!row.id || typeof row.name !== "string" || row.price == null) throw new ApiError("Product response is missing id, name, or price.");
  const category = row.category && typeof row.category === "object" ? row.category : null;
  const farmer = row.farmer && typeof row.farmer === "object" ? row.farmer : null;
  return {
    ...row, id: row.id, name: row.name,
    category: category?.name || "Other", categoryId: category?.id ?? row.category_id ?? null,
    price: number(row.price), unit: row.unit, qty: number(row.available_quantity),
    availableQuantity: number(row.available_quantity), isAvailable: Boolean(row.is_available),
    status: row.status, active: row.status === "ACTIVE", description: row.description || "",
    image: row.image_url || "", imageUrl: row.image_url || "",
    farmer: farmer?.farm_name || farmer?.full_name || "",
    farmerId: farmer?.id ?? row.farmer_id ?? null,
    farmerLocation: farmer?.farm_location || "",
    farmerImageUrl: farmer?.farm_image_url || "",
    farmerVerified: farmer?.verification_status === "COMPLETED",
    createdAt: row.created_at, updatedAt: row.updated_at
  };
}

export function normalizeAddress(value) {
  const row = requireRecord(value, "addresses");
  if (!row.id || typeof row.address_line_1 !== "string" || typeof row.city !== "string") throw new ApiError("Address response is missing id, address_line_1, or city.");
  return {
    ...row, id: row.id, label: row.label || "Address", fullName: row.full_name,
    phone: row.phone, line1: row.address_line_1, addressLine1: row.address_line_1,
    addressLine2: row.address_line_2 ?? null, city: row.city, state: row.state,
    postalCode: row.postal_code, country: row.country, latitude: row.latitude,
    longitude: row.longitude, isDefault: Boolean(row.is_default),
    createdAt: row.created_at, updatedAt: row.updated_at
  };
}

export function normalizeCustomer(value) {
  const row = requireRecord(value, "customer profile");
  if (!row.id || typeof row.full_name !== "string") throw new ApiError("Customer response is missing id or full_name.");
  return { ...row, id: row.id, fullName: row.full_name, phone: row.phone || "", email: row.email, profileImageUrl: row.profile_image_url ?? null, createdAt: row.created_at, updatedAt: row.updated_at };
}

export function normalizeFarmer(value) {
  const row = requireRecord(value, "farmer profile");
  if (!row.id || typeof row.full_name !== "string") throw new ApiError("Farmer response is missing id or full_name.");
  return { ...row, id: row.id, fullName: row.full_name, phone: row.phone || "", email: row.email, farmName: row.farm_name || "", location: row.farm_location, farmDescription: row.farm_description || "", farmImage: row.farm_image_url || "", verification: row.verification_status, submittedAt: row.verification_submitted_at, completedAt: row.verification_completed_at, createdAt: row.created_at, updatedAt: row.updated_at };
}

export function normalizeVerification(value) {
  const row = requireRecord(value, "farmer verification");
  return { status: row.status, submittedAt: row.submitted_at, completedAt: row.completed_at ?? null, statusMessage: row.status_message };
}

export function normalizeCart(value) {
  const row = requireRecord(value, "cart");
  if (!row.id || !Array.isArray(row.items)) throw new ApiError("Cart response is missing id or items.");
  return { ...row, id: row.id, items: row.items.map(item => ({ ...item, id: item.id, productId: item.product_id, productName: item.product_name, productImageUrl: item.product_image_url, unitPrice: number(item.unit_price), quantity: Number(item.quantity), availableStock: number(item.available_stock), lineTotal: number(item.line_total), isAvailable: Boolean(item.is_available), availabilityReason: item.availability_reason ?? null })), itemCount: Number(row.item_count), subtotal: number(row.subtotal), deliveryFee: number(row.delivery_fee), totalAmount: number(row.total_amount), createdAt: row.created_at, updatedAt: row.updated_at };
}

export function normalizeOrder(value) {
  const row = requireRecord(value, "orders");
  if (!row.id || typeof row.status !== "string") throw new ApiError("Order response is missing id or status.");
  // GET /orders returns OrderListItem records; GET /orders/{id} adds items and delivery_address.
  const items = (row.items || []).map(line => ({
    ...line, id: line.id, productId: line.product_id, farmerId: line.farmer_id,
    productName: line.product_name, productImageUrl: line.product_image_url,
    quantity: Number(line.quantity), unitPrice: number(line.unit_price), lineTotal: number(line.line_total)
  }));
  const deliveryAddress = row.delivery_address ? {
    ...row.delivery_address, fullName: row.delivery_address.full_name,
    addressLine1: row.delivery_address.address_line_1,
    addressLine2: row.delivery_address.address_line_2 ?? null,
    postalCode: row.delivery_address.postal_code
  } : undefined;
  return {
    ...row, id: row.id, orderNumber: row.order_number, date: displayDate(row.created_at),
    status: row.status, paymentMethod: row.payment_method, paymentStatus: row.payment_status,
    subtotal: number(row.subtotal), deliveryFee: number(row.delivery_fee),
    total: number(row.total_amount), totalAmount: number(row.total_amount), currency: row.currency,
    items, address: deliveryAddress, deliveryAddress, createdAt: row.created_at, updatedAt: row.updated_at
  };
}

export function normalizeProfile(value, domain = "profile") {
  return domain === "farmer" ? normalizeFarmer(value) : normalizeCustomer(value);
}
