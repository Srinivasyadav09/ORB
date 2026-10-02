import { useState } from "react";
import { CircleUserRound, Settings } from "lucide-react";
import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import { Page } from "../../components/layout/Page";
import { useCustomer } from "../../context/CustomerContext";
import { useAddresses } from "../../context/AddressesContext";

export default function CustomerAccountPage() {
  const { profile, loading, saving, error, success, refreshProfile, updateProfile } = useCustomer();
  const { addresses, selectedAddress, loading: addressesLoading } = useAddresses();
  const [editing, setEditing] = useState(false);
  const [formError, setFormError] = useState("");

  const save = async event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget).entries());
    const result = await updateProfile({ full_name: values.full_name, phone: values.phone });
    if (!result.ok) {
      setFormError(result.message);
      return;
    }
    setFormError("");
    setEditing(false);
  };

  if (loading) return <Page><p role="status">Loading your customer profile…</p></Page>;
  if (error && !profile) return <Page><div role="alert" className="empty"><h2>Profile could not be loaded</h2><p>{error}</p><Button variant="outline" onClick={() => refreshProfile()}>Try again</Button></div></Page>;
  if (!profile) return <Page><div role="alert" className="empty"><h2>Customer profile unavailable</h2><p>Sign in with a customer account to view your profile.</p></div></Page>;

  return <Page><section className="profile"><div className="account-cover"/>
    <div className="profile-body"><div className="profile-avatar">{profile.profileImageUrl ? <img src={profile.profileImageUrl} alt="Profile"/> : <CircleUserRound/>}</div>
      <h1>{profile.fullName}</h1><p className="muted">Manage your account and delivery preferences.</p>
      {error && <p role="alert">{error}</p>}{success && <p role="status" className="muted">{success}</p>}
      {editing ? <form className="profile-edit" onSubmit={save}>
        <div className="form-grid"><Input label="Full name" name="full_name" defaultValue={profile.fullName} required minLength={2} maxLength={120}/><Input label="Phone" name="phone" type="tel" defaultValue={profile.phone || ""} required minLength={8} maxLength={20}/></div>
        {formError && <p role="alert">{formError}</p>}
        <Button type="submit" disabled={saving}>{saving ? "Saving…" : "Save profile"}</Button> <Button type="button" variant="outline" disabled={saving} onClick={() => { setEditing(false); setFormError(""); }}>Cancel</Button>
      </form> : <>
        <div className="profile-grid"><div><small>Full Name</small><strong>{profile.fullName || "—"}</strong></div><div><small>Email</small><strong>{profile.email || "—"}</strong></div><div><small>Phone</small><strong>{profile.phone || "—"}</strong></div><div><small>Saved Addresses</small><strong>{addressesLoading ? "Loading…" : `${addresses.length} address${addresses.length === 1 ? "" : "es"}`}</strong></div><div><small>Default Location</small><strong>{addressesLoading ? "Loading…" : selectedAddress ? `${selectedAddress.city}, ${selectedAddress.state}` : "No default address"}</strong></div></div>
        <Button icon={Settings} onClick={() => setEditing(true)}>Edit Account</Button>
      </>}
    </div>
  </section></Page>;
}
