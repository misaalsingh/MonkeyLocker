import { useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function AuthCallback() {
  const [searchParams] = useSearchParams();
  const { login } = useAuth();
  const navigate = useNavigate();
  const ran = useRef(false);

  useEffect(() => {
    // Guard against React StrictMode double-invoke
    if (ran.current) return;
    ran.current = true;

    const token = searchParams.get("token");
    const error = searchParams.get("message");

    if (error) {
      navigate(`/login?error=${encodeURIComponent(error)}`, { replace: true });
      return;
    }

    if (!token) {
      navigate("/login?error=No+token+received", { replace: true });
      return;
    }

    login(token)
      .then(() => navigate("/dashboard", { replace: true }))
      .catch(() => navigate("/login?error=Login+failed", { replace: true }));
  }, []);

  return (
    <div style={styles.page}>
      <p style={styles.text}>Signing you in...</p>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  text: {
    color: "#666",
    fontSize: "16px",
  },
};
