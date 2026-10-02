import { useState } from "react";
import { ArrowLeft, CircleUserRound, MapPin, UserRound } from "lucide-react";
import { useLocation, useNavigate } from "react-router-dom";
import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import Logo from "../../components/common/Logo";
import PasswordField from "../../components/auth/PasswordField";
import { useAuth } from "../../context/AuthContext";

export default function AuthPage() {
  const [error, setError] = useState("");
  const location = useLocation();
  const navigate = useNavigate();
  const { login, registerCustomer, registerFarmer } = useAuth();
  const [submitting, setSubmitting] = useState(false);
  const farmer = new URLSearchParams(location.search).get("role") === "farmer";
  const role = farmer ? "farmer" : "customer";
  const isSignup = location.pathname === "/signup";

  const submit = async (event) => {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    const password = values.get("password");
    if (isSignup && password !== values.get("confirmPassword")) {
      setError("Passwords do not match.");
      return;
    }
    setError("");
    setSubmitting(true);
    try {
      const credentials = { email: String(values.get("email")).trim(), password: String(password) };
      const user = isSignup
        ? farmer
          ? await registerFarmer({
              ...credentials,
              full_name: String(values.get("fullName")).trim(),
              phone: String(values.get("phone")).trim(),
              farm_location: String(values.get("location")).trim(),
              farm_image_url: String(values.get("farm_image_url") || "").trim() || null,
            })
          : await registerCustomer({
              ...credentials,
              full_name: String(values.get("fullName")).trim(),
              phone: String(values.get("phone")).trim(),
            })
        : await login(credentials);

      const actualRole = user.role;
      const rolePath = actualRole === "FARMER" ? "/farmer" : actualRole === "CUSTOMER" ? "/customer" : "/";
      const requestedPath = location.state?.from?.pathname;
      const matchesRole = actualRole === "FARMER"
        ? requestedPath?.startsWith("/farmer")
        : actualRole === "CUSTOMER" && requestedPath?.startsWith("/customer");
      navigate(matchesRole ? requestedPath : rolePath, { replace: true });
    } catch (requestError) {
      setError(requestError?.message || "Unable to authenticate. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };
  const toggleAuthMode = () =>
    navigate(`${isSignup ? "/login" : "/signup"}?role=${role}`, {
      state: location.state,
    });

  return (
    <div className="auth-page">
      <button className="back-button" onClick={() => navigate("/")}>
        <ArrowLeft size={16} /> Back to ORB
      </button>
      <div className="auth-layout">
        <section className="auth-side">
          <span className="eyebrow">
            {farmer ? "FARMER REGISTRATION" : "CUSTOMER ACCOUNT"}
          </span>
          <h1>
            {farmer ? "Grow together with ORB." : "Fresh food, closer to home."}
          </h1>
          <p>
            {farmer
              ? "List your farm products and reach customers directly through a trusted local marketplace."
              : "Buy quality agricultural products from verified local farmers."}
          </p>
          <div className="auth-side-stat">
            <strong>{farmer ? "3-stage" : "100%"}</strong>
            <span>
              {farmer ? "verification process" : "farmer transparency"}
            </span>
          </div>
        </section>
        <section className="auth-form">
          <Logo />
          <h2>
            {isSignup
              ? "Create your account"
              : `Welcome ${farmer ? "Farmer" : "to ORB"}`}
          </h2>
          <p className="muted">
            {isSignup
              ? "Enter your details to get started."
              : "Sign in to continue to Online Raithu Bazaar."}
          </p>
          <form onSubmit={submit}>
            {isSignup && (
              <>
                <Input
                  label="Full Name"
                  name="fullName"
                  placeholder="Enter your full name"
                  icon={UserRound}
                  required
                />
                <Input
                  label="Phone Number"
                  name="phone"
                  type="tel"
                  placeholder="Enter phone number"
                  icon={UserRound}
                  required
                  pattern="[+0-9 ()-]{8,}"
                />
              </>
            )}
            <Input
              label="Email"
              name="email"
              placeholder="Please enter your email"
              type="email"
              icon={CircleUserRound}
              required
            />
            <PasswordField
              required
              minLength={8}
              autoComplete={isSignup ? "new-password" : "current-password"}
            />
            {isSignup && (
              <PasswordField
                label="Confirm Password"
                name="confirmPassword"
                required
                minLength={8}
                autoComplete="new-password"
                confirm
              />
            )}
            {farmer && isSignup && (
              <>
                <Input
                  label="Farm Location"
                  name="location"
                  placeholder="Enter farm location"
                  icon={MapPin}
                  required
                />
                <Input
                  label="Farm Image URL (optional)"
                  name="farm_image_url"
                  type="url"
                  placeholder="https://example.com/farm-image.jpg"
                />
              </>
            )}
            {!isSignup && (
              <div className="form-meta">
                <span>You'll stay signed in on this browser.</span>
                <a href="#forgot">Forgot password?</a>
              </div>
            )}
            {error && (
              <p role="alert" className="muted" style={{ color: "#b5473c" }}>
                {error}
              </p>
            )}
            <Button type="submit" className="full" disabled={submitting}>
              {isSignup
                ? farmer
                  ? "Submit Farmer Application"
                  : "Create Customer Account"
                : submitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>
          {!farmer && (
            <>
              <div className="divider">
                <span>OR</span>
              </div>
              <Button variant="outline" className="full">
                G&nbsp;&nbsp; Continue with Google
              </Button>
            </>
          )}
          <p className="switch">
            {isSignup ? "Already have an account?" : "Don't have an account?"}{" "}
            <button onClick={toggleAuthMode}>
              {isSignup ? "Sign in" : "Sign up"}
            </button>
          </p>
        </section>
      </div>
    </div>
  );
}
