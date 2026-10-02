import { ArrowLeft } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Card from "../../components/common/Card";
import Verification from "../../components/farmer/Verification";
import { Page, PageTitle } from "../../components/layout/Page";

export default function FarmerVerificationPage() {
  const navigate = useNavigate();
  return <Page><button className="back-button" onClick={() => navigate("/farmer")}><ArrowLeft size={15}/> Back to Dashboard</button><PageTitle label="FARMER ONBOARDING" title="Verification Status" subtitle="Track the review status of your farmer application."/><Card><Verification/></Card></Page>;
}
