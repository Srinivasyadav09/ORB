import { Page, PageTitle } from "../../components/layout/Page";

export default function FarmerOrdersPage() {
  return <Page><PageTitle label="FARMER SALES" title="Orders" subtitle="Farmer order management is not available yet."/><div className="empty"><h2>No farmer order API is available</h2><p>Order management will be available when the backend provides farmer order endpoints.</p></div></Page>;
}
