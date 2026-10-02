export default function Button({ children, variant = "primary", icon: Icon, onClick, className = "", ...props }) {
  return <button className={`btn ${variant} ${className}`} onClick={onClick} {...props}>{Icon && <Icon size={17}/>} {children}</button>;
}
