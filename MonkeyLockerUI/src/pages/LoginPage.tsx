import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import GoogleLoginButton from "../components/GoogleLoginButton";

export default function LoginPage() {
  const { user, loading } = useAuth();

  if (loading) return null;
  if (user) return <Navigate to="/dashboard" replace />;

  return (
    <div style={styles.page}>
      <div style={styles.card}>
        <h1 style={styles.title}>MonkeyLocker</h1>
        <p style={styles.subtitle}>Sign in to continue</p>
        <GoogleLoginButton />
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  page: {
    minHeight: "100vh",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    background: "#f8f9fa",
  },
  card: {
    background: "#fff",
    borderRadius: "8px",
    padding: "48px 40px",
    boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
    width: "100%",
    maxWidth: "380px",
    display: "flex",
    flexDirection: "column",
    gap: "16px",
    alignItems: "center",
  },
  title: {
    margin: 0,
    fontSize: "24px",
    fontWeight: 700,
    color: "#1a1a1a",
  },
  subtitle: {
    margin: "0 0 8px",
    color: "#666",
    fontSize: "14px",
  },
};
