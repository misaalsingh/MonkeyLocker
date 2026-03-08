const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface User {
  id: number;
  username: string;
  email: string;
  is_oauth_user: boolean;
  profile_picture?: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function authHeader(): Record<string, string> {
  const token = localStorage.getItem("token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }
  return res.json();
}

// ── Endpoints ─────────────────────────────────────────────────────────────────

export async function register(
  username: string,
  email: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, email, password }),
  });
  return handleResponse<TokenResponse>(res);
}

export async function login(
  email: string,
  password: string
): Promise<TokenResponse> {
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse<TokenResponse>(res);
}

/** Redirects the browser to Google's login page via the backend. */
export function googleLogin(): void {
  window.location.href = `${BASE_URL}/api/auth/google/login`;
}

/** Verifies a Google ID token from the frontend Google SDK (alternative flow). */
export async function googleVerify(id_token: string): Promise<TokenResponse> {
  const res = await fetch(`${BASE_URL}/api/auth/google/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id_token }),
  });
  return handleResponse<TokenResponse>(res);
}

export async function getMe(): Promise<User> {
  const res = await fetch(`${BASE_URL}/api/auth/me`, {
    headers: authHeader(),
  });
  return handleResponse<User>(res);
}

export async function logout(): Promise<void> {
  await fetch(`${BASE_URL}/api/auth/logout`, {
    method: "POST",
    headers: authHeader(),
  });
}

export async function refreshToken(): Promise<{ access_token: string }> {
  const res = await fetch(`${BASE_URL}/api/auth/refresh`, {
    method: "POST",
    headers: authHeader(),
  });
  return handleResponse<{ access_token: string }>(res);
}

export async function enrollFace(userId: number, image: File): Promise<{ message: string }> {
  const form = new FormData();
  form.append("user_id", String(userId));
  form.append("face_image", image);
  const res = await fetch(`${BASE_URL}/api/auth/enroll-face`, {
    method: "POST",
    body: form,
  });
  return handleResponse<{ message: string }>(res);
}

export async function loginFace(image: File): Promise<TokenResponse & { confidence: number }> {
  const form = new FormData();
  form.append("face_image", image);
  const res = await fetch(`${BASE_URL}/api/auth/login-face`, {
    method: "POST",
    body: form,
  });
  return handleResponse<TokenResponse & { confidence: number }>(res);
}
