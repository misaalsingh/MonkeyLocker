const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface Event {
  id: number;
  event_type: string;
  event_category: string;
  success: boolean;
  user_id: number | null;
  ip_address: string | null;
  user_agent: string | null;
  confidence_score: number | null;
  error_message: string | null;
  event_metadata: Record<string, unknown> | null;
  created_at: string;
}

export interface EventStats {
  total: number;
  successful: number;
  failed: number;
  success_rate: number;
  by_type: Record<string, number>;
  recent_failed_logins: { ip_address: string; created_at: string }[];
}

export interface SecurityAlerts {
  failed_login_count: number;
  unique_ip_count: number;
  alerts: { severity: "HIGH" | "MEDIUM" | "LOW"; message: string }[];
}

export interface ActivityDay {
  date: string;
  count: number;
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

export interface EventFilters {
  event_type?: string;
  success?: boolean;
  days?: number;
  skip?: number;
  limit?: number;
}

export async function getEvents(filters: EventFilters = {}): Promise<Event[]> {
  const params = new URLSearchParams();
  if (filters.event_type) params.set("event_type", filters.event_type);
  if (filters.success !== undefined) params.set("success", String(filters.success));
  if (filters.days) params.set("days", String(filters.days));
  if (filters.skip) params.set("skip", String(filters.skip));
  if (filters.limit) params.set("limit", String(filters.limit));

  const res = await fetch(`${BASE_URL}/monkey/events/?${params}`, {
    headers: authHeader(),
  });
  return handleResponse<Event[]>(res);
}

export async function getEventTypes(): Promise<string[]> {
  const res = await fetch(`${BASE_URL}/monkey/events/all-types`, {
    headers: authHeader(),
  });
  return handleResponse<string[]>(res);
}

export async function getEvent(eventId: number): Promise<Event> {
  const res = await fetch(`${BASE_URL}/monkey/events/${eventId}`, {
    headers: authHeader(),
  });
  return handleResponse<Event>(res);
}

export async function getEventStats(days = 7): Promise<EventStats> {
  const res = await fetch(`${BASE_URL}/monkey/events/stats/summary?days=${days}`, {
    headers: authHeader(),
  });
  return handleResponse<EventStats>(res);
}

export async function getSecurityAlerts(days = 7): Promise<SecurityAlerts> {
  const res = await fetch(`${BASE_URL}/monkey/events/stats/security-alerts?days=${days}`, {
    headers: authHeader(),
  });
  return handleResponse<SecurityAlerts>(res);
}

export async function getActivityTimeline(days = 7): Promise<ActivityDay[]> {
  const res = await fetch(`${BASE_URL}/monkey/events/stats/activity-timeline?days=${days}`, {
    headers: authHeader(),
  });
  return handleResponse<ActivityDay[]>(res);
}
