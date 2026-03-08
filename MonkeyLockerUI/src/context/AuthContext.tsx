import { createContext, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { getMe, logout as apiLogout } from "../api/auth";
import type { User } from "../api/auth";

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (token: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  // On mount, if a token exists try to restore the user session
  useEffect(() => {
    if (token) {
      getMe()
        .then(setUser)
        .catch(() => {
          // Token is invalid or expired — clear it
          localStorage.removeItem("token");
          setToken(null);
        })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  async function login(newToken: string) {
    localStorage.setItem("token", newToken);
    setToken(newToken);
    const me = await getMe();
    setUser(me);
  }

  function logout() {
    apiLogout().catch(() => {}); // best-effort server logout log
    localStorage.removeItem("token");
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
