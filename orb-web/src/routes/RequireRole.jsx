import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Loading from "../components/common/Loading";

const ROLE_HOME = { CUSTOMER: "/customer", FARMER: "/farmer", ADMIN: "/" };
const LOGIN_ROLE = { CUSTOMER: "customer", FARMER: "farmer", ADMIN: "admin" };

export default function RequireRole({ role, children }) {
  const { user, status } = useAuth();
  const location = useLocation();
  if (status === "loading") return <Loading />;
  if (!user) return <Navigate to={`/login?role=${LOGIN_ROLE[role] || "customer"}`} replace state={{ from: location }} />;
  if (user.role !== role) return <Navigate to={ROLE_HOME[user.role] || "/"} replace />;
  return children;
}
