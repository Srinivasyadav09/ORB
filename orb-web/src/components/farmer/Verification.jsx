import Button from "../common/Button";
import { useFarmer } from "../../context/FarmerContext";

const formatDate = value => value ? new Date(value).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "—";

export default function Verification() {
  const { verification, verificationLoading, verificationError, refreshVerification } = useFarmer();
  if (verificationLoading) return <p role="status">Loading verification status…</p>;
  if (verificationError) return <div role="alert"><p>{verificationError}</p><Button variant="outline" onClick={() => refreshVerification()}>Try again</Button></div>;
  if (!verification) return <p className="muted">Verification status is unavailable.</p>;

  return <div className="verification-panel">
    <div className="verification-summary"><span className="section-label">BACKEND VERIFICATION STATUS</span><strong>{verification.status}</strong><p>{verification.statusMessage}</p></div>
    <div className="verification-dates"><span><small>Submitted</small><strong>{formatDate(verification.submittedAt)}</strong></span>{verification.completedAt && <span><small>Completed</small><strong>{formatDate(verification.completedAt)}</strong></span>}</div>
  </div>;
}
