export default function Input({ label, placeholder, type = "text", icon: Icon, className = "", ...props }) {
  return <label className={`field ${className}`.trim()}><span>{label}</span><div>{Icon && <Icon size={16}/>}<input type={type} placeholder={placeholder} {...props}/></div></label>;
}
