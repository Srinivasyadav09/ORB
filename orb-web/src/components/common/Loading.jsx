export default function Loading({ label = "Loading…" }) {
  return <div role="status" aria-live="polite" style={{ padding: 24, textAlign: "center", color: "var(--muted)" }}>{label}</div>;
}
