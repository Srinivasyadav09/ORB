import { Link } from "react-router-dom";
import { Search } from "lucide-react";
import { Page } from "../components/layout/Page";

export default function NotFoundPage() {
  return <Page><div className="empty"><Search size={40}/><h2>Page not found</h2><p>The page you are looking for does not exist.</p><Link to="/" className="btn primary">Return to ORB</Link></div></Page>;
}
