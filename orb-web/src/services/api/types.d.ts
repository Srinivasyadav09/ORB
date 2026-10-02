/** Wire DTOs mirror backend/app/schemas; IDs are UUID strings on the wire. */
export type Id = string;
export type UserRole = "CUSTOMER" | "FARMER" | "ADMIN";
export type VerificationStatus = "SUBMITTED" | "VERIFYING" | "COMPLETED" | "REJECTED";
export type ProductStatus = "DRAFT" | "ACTIVE" | "INACTIVE";
export type ProductUnit = "kg" | "g" | "bunch" | "piece" | "dozen" | "litre";
export type OrderStatus = "CONFIRMED" | "PROCESSING" | "SHIPPED" | "DELIVERED" | "CANCELLED";
export type PaymentMethod = "COD";

export interface ApiErrorBody { detail?: string | Array<{ msg?: string; loc?: unknown[]; type?: string }>; message?: string; error?: string }
export interface CustomerProfileSummary { full_name: string; profile_image_url: string | null }
export interface FarmerProfileSummary { full_name: string; farm_name: string | null; farm_location: string; farm_description: string | null; farm_image_url: string | null; verification_status: VerificationStatus; verification_submitted_at: string; verification_completed_at: string | null }
export interface ApiUser { id: Id; email: string; phone: string | null; role: UserRole; is_active: boolean; is_verified: boolean; customer_profile: CustomerProfileSummary | null; farmer_profile: FarmerProfileSummary | null }
export interface AuthCredentials { email: string; password: string }
export interface CustomerRegistration { email: string; password: string; full_name: string; phone: string }
export interface FarmerRegistration extends CustomerRegistration { farm_name?: string | null; farm_location: string; farm_description?: string | null; farm_image_url?: string | null }
export interface TokenResponse { access_token: string; refresh_token: string; token_type: "bearer"; expires_in: number; user: ApiUser }
export interface RefreshTokenRequest { refresh_token: string }
export interface LogoutResponse { message: string }

export interface CustomerDto { id: Id; full_name: string; email: string; phone: string | null; profile_image_url: string | null; created_at: string; updated_at: string }
export interface CustomerUpdateRequest { full_name?: string; phone?: string; profile_image_url?: string | null }
export interface FarmerDto { id: Id; full_name: string; email: string; phone: string | null; farm_name: string | null; farm_location: string; farm_description: string | null; farm_image_url: string | null; verification_status: VerificationStatus; verification_submitted_at: string; verification_completed_at: string | null; created_at: string; updated_at: string }
export interface FarmerUpdateRequest { full_name?: string; farm_name?: string | null; phone?: string; farm_location?: string; farm_description?: string | null; farm_image_url?: string | null }
export interface FarmerVerificationDto { status: VerificationStatus; submitted_at: string; completed_at: string | null; status_message: string }
export interface VerificationUpdateRequest { status: VerificationStatus }
export interface FarmerVerificationUpdateDto { farmer_id: Id; status: VerificationStatus; submitted_at: string; completed_at: string | null; status_message: string }

export interface CategoryDto { id: Id; name: string; description: string | null; image_url: string | null; is_active: boolean; created_at: string; updated_at: string }
export interface ProductFarmerSummary { id: Id; full_name: string; farm_name: string | null; farm_location: string; farm_image_url: string | null; verification_status: VerificationStatus }
export interface ProductCategorySummary { id: Id; name: string }
export interface ProductDto { id: Id; name: string; description?: string | null; price: string; unit: ProductUnit; available_quantity: string; is_available: boolean; status: ProductStatus; image_url: string | null; category: ProductCategorySummary; farmer: ProductFarmerSummary; created_at: string; updated_at: string }
export interface ProductWrite { name: string; description?: string | null; category_id: Id; price: number | string; unit: ProductUnit; available_quantity?: number | string; image_url?: string | null; status?: ProductStatus }
export interface ProductUpdate { name?: string; description?: string | null; category_id?: Id; price?: number | string; unit?: ProductUnit; available_quantity?: number | string; image_url?: string | null; status?: ProductStatus }
export interface Page<T> { items: T[]; page: number; page_size: number; total: number; pages: number }

export interface AddressDto { id: Id; full_name: string; phone: string; address_line_1: string; address_line_2: string | null; city: string; state: string; postal_code: string; country: string; latitude: string | null; longitude: string | null; label: string | null; is_default: boolean; created_at: string; updated_at: string }
export type AddressWrite = Omit<AddressDto, "id" | "created_at" | "updated_at">;
export type AddressUpdate = Partial<AddressWrite>;
export interface CartItemDto { id: Id; product_id: Id; product_name: string; product_image_url: string | null; unit: ProductUnit; unit_price: string; quantity: number; available_stock: string; line_total: string; is_available: boolean; availability_reason: string | null }
export interface CartDto { id: Id; items: CartItemDto[]; item_count: number; subtotal: string; delivery_fee: string; total_amount: string; created_at: string; updated_at: string }
export interface CartItemWrite { product_id: Id; quantity: number }

export interface DeliveryAddressSnapshot { full_name: string; phone: string; address_line_1: string; address_line_2: string | null; city: string; state: string; postal_code: string; country: string; latitude: string | null; longitude: string | null }
export interface OrderItemDto { id: Id; product_id: Id | null; farmer_id: Id | null; product_name: string; product_image_url: string | null; unit: ProductUnit; quantity: number; unit_price: string; line_total: string }
export interface OrderListItemDto { id: Id; order_number: string; status: OrderStatus; payment_method: PaymentMethod; payment_status: "PENDING"; subtotal: string; delivery_fee: string; total_amount: string; currency: string; created_at: string; updated_at: string }
export interface OrderDto extends OrderListItemDto { delivery_address: DeliveryAddressSnapshot; items: OrderItemDto[] }
export interface CreateOrderRequest { address_id: Id; payment_method?: PaymentMethod }

/** UI-normalized views; retain UUIDs and canonical backend status values. */
export interface Product { id: Id; name: string; category: string; categoryId: Id | null; price: number; unit: ProductUnit; qty: number; description: string; image: string; farmer: string; farmerId: Id | null; farmerLocation: string; farmerVerified: boolean; status: ProductStatus; active: boolean; createdAt: string; updatedAt: string }
export interface Address { id: Id; label: string; fullName: string; phone: string; line1: string; addressLine1: string; addressLine2: string | null; city: string; state: string; postalCode: string; country: string; isDefault: boolean }
export interface Order { id: Id; orderNumber: string; date: string; status: OrderStatus; items: Array<OrderItemDto & { productId: Id | null; productName: string; productImageUrl: string | null; unitPrice: number; lineTotal: number }>; subtotal: number; deliveryFee: number; total: number; paymentMethod: PaymentMethod; paymentStatus: "PENDING"; address?: DeliveryAddressSnapshot; createdAt: string; updatedAt: string }
