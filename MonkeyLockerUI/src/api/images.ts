const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface RoomImage {
  id: number;
  room_id: number;
  uploaded_by: number | null;
  image_url: string;
  caption: string | null;
  uploaded_at: string;
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

/** Resolves local relative URLs to full backend URLs; passes S3 URLs through unchanged. */
export function resolveImageUrl(url: string): string {
  return url.startsWith("/") ? `${BASE_URL}${url}` : url;
}

export async function uploadImage(
  roomId: number,
  file: File,
  caption?: string
): Promise<RoomImage> {
  const form = new FormData();
  form.append("image", file);
  const url = caption
    ? `${BASE_URL}/api/rooms/${roomId}/images?caption=${encodeURIComponent(caption)}`
    : `${BASE_URL}/api/rooms/${roomId}/images`;
  const res = await fetch(url, {
    method: "POST",
    headers: authHeader(),
    body: form,
  });
  return handleResponse<RoomImage>(res);
}

export async function listImages(
  roomId: number,
  params?: { dateFrom?: string; dateTo?: string }
): Promise<RoomImage[]> {
  const url = new URL(`${BASE_URL}/api/rooms/${roomId}/images`);
  if (params?.dateFrom) url.searchParams.set("date_from", params.dateFrom);
  if (params?.dateTo) url.searchParams.set("date_to", params.dateTo);
  const res = await fetch(url.toString(), { headers: authHeader() });
  return handleResponse<RoomImage[]>(res);
}

export async function deleteImage(imageId: number): Promise<void> {
  await fetch(`${BASE_URL}/api/images/${imageId}`, {
    method: "DELETE",
    headers: authHeader(),
  });
}
