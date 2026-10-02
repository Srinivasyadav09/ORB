import { useState } from "react";
import { Plus, Pencil, Trash2 } from "lucide-react";
import Button from "../common/Button";
import Input from "../common/Input";
import { useAuth } from "../../context/AuthContext";
import { useAddresses } from "../../context/AddressesContext";

const blankAddress = { label: "", full_name: "", phone: "", address_line_1: "", address_line_2: "", city: "", state: "", postal_code: "", country: "" };

export default function DeliveryAddressSelector({ compact = false }) {
  const { addresses, addAddress, updateAddress, deleteAddress, selectedAddressId, selectAddress, loading, error, pending, refresh } = useAddresses();
  const { user } = useAuth();
  const userName = user?.customer_profile?.full_name || "";
  const userPhone = user?.customer_profile?.phone || "";
  const [editingId, setEditingId] = useState(null);
  const [formOpen, setFormOpen] = useState(false);
  const [formValues, setFormValues] = useState(blankAddress);
  const [formError, setFormError] = useState("");
  const [message, setMessage] = useState("");

  const beginAdd = () => {
    setEditingId(null);
    setFormOpen(true);
    setFormValues({ ...blankAddress, full_name: userName, phone: userPhone });
    setFormError("");
    setMessage("");
  };
  const beginEdit = address => {
    setEditingId(address.id);
    setFormOpen(true);
    setFormValues({
      label: address.label || "", full_name: address.fullName || "", phone: address.phone || "",
      address_line_1: address.addressLine1 || "", address_line_2: address.addressLine2 || "",
      city: address.city || "", state: address.state || "", postal_code: address.postalCode || "", country: address.country || ""
    });
    setFormError("");
    setMessage("");
  };
  const saveAddress = async event => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const payload = Object.fromEntries(form.entries());
    payload.address_line_2 = payload.address_line_2 || null;
    payload.label = payload.label || null;
    setFormError("");
    const result = editingId ? await updateAddress(editingId, payload) : await addAddress(payload);
    if (!result.ok) {
      setFormError(result.message);
      return;
    }
    setEditingId(null);
    setFormOpen(false);
    setFormValues(blankAddress);
    setMessage(editingId ? "Address updated." : "Address saved.");
  };
  const removeAddress = async id => {
    const result = await deleteAddress(id);
    setMessage(result.ok ? "Address deleted." : "");
  };
  const chooseDefault = async id => {
    const result = await selectAddress(id);
    setMessage(result.ok ? "Default delivery address updated." : "");
  };

  return <section className={compact ? "delivery" : "address-section"}>
    <h3>Delivery Address</h3>
    {loading ? <p role="status">Loading saved addresses…</p> : error && !addresses.length ? <div role="alert"><p>{error}</p><Button variant="outline" onClick={refresh}>Try again</Button></div> : <>
      {error && <p role="alert">{error}</p>}
      {!addresses.length && <p className="muted">No saved addresses yet. Add a delivery address to continue.</p>}
      <div className="saved-addresses">{addresses.map(address => <div className="address-option" key={address.id}>
        <label><input type="radio" name={compact ? "saved-address-cart" : "saved-address-checkout"} checked={selectedAddressId === address.id} disabled={pending} onChange={() => chooseDefault(address.id)}/><strong>{address.label || "Saved address"}{address.isDefault && " · Default"}</strong><small>{address.fullName} · {address.addressLine1}{address.addressLine2 ? `, ${address.addressLine2}` : ""}, {address.city}, {address.state} {address.postalCode}, {address.country}</small></label>
        <div className="address-actions"><button type="button" aria-label={`Edit ${address.label || "address"}`} disabled={pending} onClick={() => beginEdit(address)}><Pencil size={14}/></button><button type="button" aria-label={`Delete ${address.label || "address"}`} disabled={pending} onClick={() => removeAddress(address.id)}><Trash2 size={14}/></button></div>
      </div>)}</div>
    </>}
    {formOpen && <form className="address-form" onSubmit={saveAddress}>
      <div className="form-grid">
        <Input label="Address label" name="label" placeholder="Home, Work…" value={formValues.label} onChange={event => setFormValues(current => ({ ...current, label: event.target.value }))}/>
        <Input label="Full name" name="full_name" placeholder="Recipient name" required value={formValues.full_name} onChange={event => setFormValues(current => ({ ...current, full_name: event.target.value }))}/>
        <Input label="Phone" name="phone" type="tel" placeholder="Phone number" required value={formValues.phone} onChange={event => setFormValues(current => ({ ...current, phone: event.target.value }))}/>
        <Input label="Address line 1" name="address_line_1" placeholder="House, street, area" required value={formValues.address_line_1} onChange={event => setFormValues(current => ({ ...current, address_line_1: event.target.value }))}/>
        <Input label="Address line 2" name="address_line_2" placeholder="Apartment, landmark (optional)" value={formValues.address_line_2} onChange={event => setFormValues(current => ({ ...current, address_line_2: event.target.value }))}/>
        <Input label="City" name="city" placeholder="City" required value={formValues.city} onChange={event => setFormValues(current => ({ ...current, city: event.target.value }))}/>
        <Input label="State" name="state" placeholder="State" required value={formValues.state} onChange={event => setFormValues(current => ({ ...current, state: event.target.value }))}/>
        <Input label="Postal code" name="postal_code" placeholder="Postal code" required value={formValues.postal_code} onChange={event => setFormValues(current => ({ ...current, postal_code: event.target.value }))}/>
        <Input label="Country" name="country" placeholder="Country" required value={formValues.country} onChange={event => setFormValues(current => ({ ...current, country: event.target.value }))}/>
      </div>
      {formError && <p role="alert">{formError}</p>}
      <div className="form-actions"><Button type="button" variant="outline" disabled={pending} onClick={() => { setEditingId(null); setFormOpen(false); setFormValues(blankAddress); setFormError(""); }}>Cancel</Button><Button type="submit" disabled={pending}>{pending ? "Saving…" : editingId ? "Update Address" : "Save Address"}</Button></div>
    </form>}
    {!formOpen && <button type="button" className="text-action" disabled={loading || pending} onClick={beginAdd}><Plus size={15}/> Add a different address</button>}
    {message && <p role="status" className="muted">{message}</p>}
  </section>;
}
