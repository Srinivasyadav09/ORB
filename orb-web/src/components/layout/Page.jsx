import { ArrowRight } from "lucide-react";

export function Page({ children }) {
  return <div className="page">{children}</div>;
}

export function PageTitle({ label, title, subtitle, action }) {
  return <div className="page-title"><div><span className="section-label">{label}</span><h1>{title}</h1>{subtitle && <p>{subtitle}</p>}</div>{action}</div>;
}

export function SectionHead({ label, title, action, onClick }) {
  return <div className="section-head"><div><span className="section-label">{label}</span><h2>{title}</h2></div>{action && <button onClick={onClick}>{action}<ArrowRight size={15}/></button>}</div>;
}
