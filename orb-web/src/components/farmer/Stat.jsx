export default function Stat({ label, value, icon: Icon }) {
  return <div className="stat"><span><Icon size={20}/></span><small>{label}</small><strong>{value}</strong></div>;
}
