import Button from "../common/Button";
import Logo from "../common/Logo";

export default function PublicHeader({ onLogin, onFarmer }) {
  return <header className="public-header"><Logo/><nav><a href="#about">About</a><a href="#how">How it works</a><a href="#contact">Contact</a></nav><div><Button variant="outline" onClick={onLogin}>Sign in</Button><Button onClick={onFarmer}>Become a Farmer</Button></div></header>;
}
