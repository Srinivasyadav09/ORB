import { useState } from "react";
import { MapPin, Pencil, Phone, UserRound } from "lucide-react";
import Button from "../../components/common/Button";
import Badge from "../../components/common/Badge";
import Card from "../../components/common/Card";
import Verification from "../../components/farmer/Verification";
import Input from "../../components/common/Input";
import { Page } from "../../components/layout/Page";
import { useFarmer } from "../../context/FarmerContext";
import { useFarmerProducts } from "../../context/FarmerProductsContext";

export default function FarmerProfilePage() {
  const { profile, verification, loading, profileError, refreshProfile, saveProfile, saving, saveError, success } = useFarmer();
  const { activeCount } = useFarmerProducts();
  const [editing, setEditing] = useState(false);
  const [formError, setFormError] = useState("");

  const save = async event => {
    event.preventDefault();
    const values = Object.fromEntries(new FormData(event.currentTarget).entries());
    const payload = {
      full_name: values.full_name,
      phone: values.phone,
      farm_location: values.farm_location,
      farm_name: values.farm_name.trim() || null,
      farm_description: values.farm_description.trim() || null,
      farm_image_url: values.farm_image_url.trim() || null
    };
    const result = await saveProfile(payload);
    if (!result.ok) {
      setFormError(result.message);
      return;
    }
    setFormError("");
    setEditing(false);
  };

  if (loading) return <Page><p role="status">Loading farmer profile…</p></Page>;
  if (profileError && !profile) return <Page><div role="alert" className="empty"><h2>Farmer profile could not be loaded</h2><p>{profileError}</p><Button variant="outline" onClick={() => refreshProfile()}>Try again</Button></div></Page>;
  if (!profile) return <Page><div role="alert" className="empty"><h2>Farmer profile unavailable</h2><p>Sign in with a farmer account to view this profile.</p></div></Page>;

  const image = profile.farmImage;
  return <Page><section className="profile"><div className="profile-cover" style={image ? { backgroundImage: `linear-gradient(90deg,#164f3570,#164f3520),url("${image}")` } : {}}/>
    <div className="profile-body"><div className="profile-avatar">{image ? <img src={image} alt="Farm"/> : <UserRound/>}</div><Badge>{verification?.status || profile.verification}</Badge>
      {saveError && <p role="alert">{saveError}</p>}{success && <p role="status" className="muted">{success}</p>}
      {editing ? <form onSubmit={save} className="profile-edit"><div className="form-grid">
        <Input label="Full name" name="full_name" defaultValue={profile.fullName} required minLength={2} maxLength={120}/>
        <Input label="Phone" name="phone" type="tel" defaultValue={profile.phone || ""} required minLength={8} maxLength={20}/>
        <Input label="Farm location" name="farm_location" defaultValue={profile.location} required minLength={2} maxLength={300}/>
        <Input label="Farm name" name="farm_name" defaultValue={profile.farmName || ""} minLength={2} maxLength={160}/>
        <Input label="Farm image URL" name="farm_image_url" type="url" defaultValue={profile.farmImage || ""} maxLength={2048}/>
        <label className="field full"><span>Farm description</span><textarea name="farm_description" rows="4" maxLength={4000} defaultValue={profile.farmDescription || ""}/></label>
      </div>
        {formError && <p role="alert">{formError}</p>}
        <Button type="submit" disabled={saving}>{saving ? "Saving…" : "Save Farm Profile"}</Button> <Button type="button" variant="outline" disabled={saving} onClick={() => { setEditing(false); setFormError(""); }}>Cancel</Button>
      </form> : <>
        <h1>{profile.fullName}</h1><p className="muted">{profile.farmName || "—"} · {profile.location}</p>
        <div className="profile-contact"><span><Phone size={15}/>{profile.phone || "—"}</span><span><MapPin size={15}/>{profile.location}</span></div>
        <div className="profile-grid"><div><small>Farm</small><strong>{profile.farmName || "—"}</strong></div><div><small>Products</small><strong>{activeCount === null ? "—" : `${activeCount} active listings`}</strong></div><div><small>Verification</small><strong>{verification?.status || profile.verification}</strong></div><div><small>Submitted</small><strong>{verification?.submittedAt ? new Date(verification.submittedAt).toLocaleDateString("en-IN") : "—"}</strong></div></div>
        {profile.farmDescription && <p className="farmer-bio">{profile.farmDescription}</p>}
        <Card><h3>Verification Status</h3><Verification/></Card><Button icon={Pencil} onClick={() => setEditing(true)}>Edit Farm Details</Button>
      </>}
    </div>
  </section></Page>;
}
