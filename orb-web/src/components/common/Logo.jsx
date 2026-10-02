import { Leaf } from "lucide-react";

export default function Logo() {
  return (
    <div className="logo">
      <span className="logo-box">
        <Leaf size={22} />
      </span>
      <span>
        <strong>ORB</strong>
        <small>Online Raithu Bazaar</small>
      </span>
    </div>
  );
}
