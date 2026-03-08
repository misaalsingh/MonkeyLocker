const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface UserStatus {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  is_deleted: boolean;
  is_oauth_user: boolean;
  face_enrolled: boolean;
  face_enrolled_at: string | null;
  created_at: string;
  last_login_at: string | null;
  deactivated_at: string | null;
  deactivation_reason: string | null;
  deleted_at: string | null;
}

export interface UserUpdate {
  firstname?: string;
  lastname?: string;
  username?: string;
  email?: string;
  password?: string;
  age?: number;
}

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

export async function updateMe(fields: UserUpdate): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/monkey/users/me`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(fields),
  });
  return handleResponse<{ message: string }>(res);
}

export async function getMyStatus(): Promise<UserStatus> {
  const res = await fetch(`${BASE_URL}/monkey/users/me/status`, {
    headers: authHeader(),
  });
  return handleResponse<UserStatus>(res);
}

export async function deactivateAccount(reason?: string): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/monkey/users/me/deactivate`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify({ reason }),
  });
  return handleResponse<{ message: string }>(res);
}

export async function reactivateAccount(): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/monkey/users/me/reactivate`, {
    method: "POST",
    headers: authHeader(),
  });
  return handleResponse<{ message: string }>(res);
}

export async function deleteAccountPermanent(): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/monkey/users/me/permanent`, {
    method: "DELETE",
    headers: authHeader(),
  });
  return handleResponse<{ message: string }>(res);
}

export async function enrollFace(image: File): Promise<{ message: string }> {
  const form = new FormData();
  form.append("face_image", image);
  const res = await fetch(`${BASE_URL}/monkey/users/me/face`, {
    method: "POST",
    headers: authHeader(),
    body: form,
  });
  return handleResponse<{ message: string }>(res);
}

export async function removeFace(): Promise<{ message: string }> {
  const res = await fetch(`${BASE_URL}/monkey/users/me/face`, {
    method: "DELETE",
    headers: authHeader(),
  });
  return handleResponse<{ message: string }>(res);
}

export async function verifyFace(
  image: File
): Promise<{ verified: boolean; confidence: number }> {
  const form = new FormData();
  form.append("face_image", image);
  const res = await fetch(`${BASE_URL}/monkey/users/me/face/verify`, {
    method: "POST",
    headers: authHeader(),
    body: form,
  });
  return handleResponse<{ verified: boolean; confidence: number }>(res);
}
