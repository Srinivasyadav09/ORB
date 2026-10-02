import { CreditCard } from "lucide-react";
import Button from "../common/Button";

export default function OrderSummary({ subtotal, deliveryFee, totalAmount, onCheckout, checkoutLabel = "Proceed to Checkout", checkoutDisabled = false }) {
  return <aside className="summary"><h3>Order Summary</h3><div><span>Subtotal</span><b>₹{subtotal}</b></div><div><span>Delivery Charge</span><b>₹{deliveryFee}</b></div><hr/><div className="total"><span>Total</span><b>₹{totalAmount}</b></div><Button className="full" icon={CreditCard} disabled={checkoutDisabled} onClick={onCheckout}>{checkoutLabel}</Button><small>Secure payment • Address confirmation</small></aside>;
}
