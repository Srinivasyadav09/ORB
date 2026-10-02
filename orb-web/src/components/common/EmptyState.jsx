export default function EmptyState({ icon: Icon, title, description, action }) {
  return <div className="empty">{Icon && <Icon size={40}/>}<h2>{title}</h2><p>{description}</p>{action}</div>;
}
