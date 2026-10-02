import { LogOut } from "lucide-react";
import Logo from "../common/Logo";

export default function AppFooter({ onExit }) {
  return <footer><Logo/><span>Fresh • Local • Trusted</span><button onClick={onExit}><LogOut size={14}/> Exit demo</button></footer>;
}
