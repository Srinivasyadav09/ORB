import { useState } from "react";
import { Eye } from "lucide-react";

export default function PasswordField({ label = "Password", name = "password", required = false, minLength, autoComplete, confirm = false }) {
  const [visible, setVisible] = useState(false);
  return <div className="field"><span>{label}</span><div><input name={name} type={visible ? "text" : "password"} placeholder={confirm ? "Confirm your password" : "Enter your password"} required={required} minLength={minLength} autoComplete={autoComplete}/><button className="eye" type="button" onClick={() => setVisible(value => !value)} aria-label={visible ? "Hide password" : "Show password"}><Eye size={16}/></button></div></div>;
}
