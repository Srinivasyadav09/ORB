export default function Card({ as: Element = "section", className = "", children, ...props }) {
  return <Element className={`panel ${className}`.trim()} {...props}>{children}</Element>;
}
