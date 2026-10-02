export default function Badge({ children }) {
  return <span className={`status ${String(children).toLowerCase()}`}>{children}</span>;
}
