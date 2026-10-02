import { useEffect } from "react";
import { X } from "lucide-react";

export default function Modal({ open, onClose, title, children }) {
  useEffect(() => {
    if (!open) return undefined;
    const closeOnEscape = event => event.key === "Escape" && onClose?.();
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [open, onClose]);

  if (!open) return null;
  return <div role="presentation" onMouseDown={event => event.target === event.currentTarget && onClose?.()} style={{ position: "fixed", inset: 0, zIndex: 50, background: "#0006", display: "grid", placeItems: "center", padding: 20 }}>
    <section role="dialog" aria-modal="true" aria-label={title} className="panel" style={{ width: "min(520px, 100%)" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 16 }}><h2>{title}</h2><button type="button" className="round" onClick={onClose} aria-label="Close"><X size={17}/></button></div>
      {children}
    </section>
  </div>;
}
