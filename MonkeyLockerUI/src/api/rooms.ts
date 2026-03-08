const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface Room {
  id: number;
  name: string;
  description: string | null;
  created_by: number;
  is_private: boolean;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export interface RoomMember {
  room_id: number;
  user_id: number;
  role: "admin" | "moderator" | "member";
  joined_at: string;
}

export interface RoomDetail extends Room {
  members: RoomMember[];
}

export interface CreateRoomPayload {
  name: string;
  description?: string;
  is_private?: boolean;
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

export async function createRoom(payload: CreateRoomPayload): Promise<Room> {
  const res = await fetch(`${BASE_URL}/api/rooms/`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeader() },
    body: JSON.stringify(payload),
  });
  return handleResponse<Room>(res);
}

export async function listRooms(): Promise<Room[]> {
  const res = await fetch(`${BASE_URL}/api/rooms/`, {
    headers: authHeader(),
  });
  return handleResponse<Room[]>(res);
}

export async function getRoom(roomId: number): Promise<RoomDetail> {
  const res = await fetch(`${BASE_URL}/api/rooms/${roomId}`, {
    headers: authHeader(),
  });
  return handleResponse<RoomDetail>(res);
}

export async function joinRoom(roomId: number): Promise<RoomMember> {
  const res = await fetch(`${BASE_URL}/api/rooms/${roomId}/join`, {
    method: "POST",
    headers: authHeader(),
  });
  return handleResponse<RoomMember>(res);
}

export async function leaveRoom(roomId: number): Promise<void> {
  await fetch(`${BASE_URL}/api/rooms/${roomId}/leave`, {
    method: "DELETE",
    headers: authHeader(),
  });
}

export async function deleteRoom(roomId: number): Promise<void> {
  await fetch(`${BASE_URL}/api/rooms/${roomId}`, {
    method: "DELETE",
    headers: authHeader(),
  });
}

export async function listMembers(roomId: number): Promise<RoomMember[]> {
  const res = await fetch(`${BASE_URL}/api/rooms/${roomId}/members`, {
    headers: authHeader(),
  });
  return handleResponse<RoomMember[]>(res);
}
