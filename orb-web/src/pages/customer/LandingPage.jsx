import { ArrowRight, BadgeCheck, Leaf, Star, Truck, Users, ShoppingBag } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import PublicHeader from "../../components/layout/PublicHeader";

export default function LandingPage() {
  const navigate = useNavigate();
  const customerLogin = () => navigate("/login?role=customer");
  const farmerLogin = () => navigate("/login?role=farmer");
  return <div className="landing"><PublicHeader onLogin={customerLogin} onFarmer={farmerLogin}/><main>
    <section className="hero"><div className="hero-copy"><span className="eyebrow"><Leaf size={14}/> FRESH • LOCAL • TRUSTED</span><h1>From local farms<br/>to your <em>home.</em></h1><p>ORB connects customers directly with local farmers so fresh agricultural products reach families faster, while farmers get a simple digital storefront.</p><div className="hero-buttons"><Button icon={ShoppingBag} onClick={customerLogin}>Shop as Customer</Button><Button variant="soft" icon={Leaf} onClick={farmerLogin}>Become a Farmer</Button></div><div className="trust"><span><BadgeCheck/> Verified farmers</span><span><Truck/> Reliable delivery</span><span><Star/> Product ratings</span></div></div>
      <div className="hero-image"><div className="hero-overlay"></div><div className="hero-floating"><span><Leaf/></span><div><strong>Good food.</strong><small>Brighter tomorrow.</small></div><BadgeCheck/></div><div className="hero-caption">Supporting farmers<br/>building a healthier tomorrow.</div></div>
    </section>
    <section className="role-grid" id="how"><article><div className="role-icon green"><Users/></div><h2>For Customers</h2><p>Discover fresh products, see who grew them, order for delivery, track your order and rate products after delivery.</p><button onClick={customerLogin}>Create customer account <ArrowRight size={16}/></button></article><article><div className="role-icon orange"><Leaf/></div><h2>For Farmers</h2><p>Create your farm profile, complete verification, list products and keep images and quantities updated every day.</p><button onClick={farmerLogin}>Register as a farmer <ArrowRight size={16}/></button></article></section>
    <section className="goal" id="about"><div><span className="section-label">OUR GOAL</span><h2>A marketplace built around trust.</h2></div><p>Customers know where their food comes from. Farmers get a direct digital storefront. ORB connects both sides with transparent products, delivery and reviews.</p></section>
  </main></div>;
}
