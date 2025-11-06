import { useAuth } from "@/store/auth";

// Заголовки с JWT и X-Tenant-Id
export function apiHeaders(extra?: HeadersInit) {
  const { token, tenant } = useAuth.getState();
  const h: Record<string,string> = {
    "Content-Type": "application/json",
    "X-Tenant-Id": String(tenant)
  };
  if (token) h["Authorization"] = `Bearer ${token}`;
  return { ...h, ...(extra || {}) };
}

// Единый запрос
async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { apiBase } = useAuth.getState();
  const res = await fetch(`${apiBase}/v1${path}`, {
    ...init,
    headers: apiHeaders(init.headers)
  });
  if (!res.ok) {
    let detail = "";
    try {
      const j = await res.json();
      detail = (j as any)?.detail ?? JSON.stringify(j);
    } catch {}
    throw new Error(`HTTP ${res.status} ${res.statusText}${detail ? `: ${detail}` : ""}`);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json")
    ? (await res.json()) as T
    : (await res.text() as unknown as T);
}

// ---- Auth
export const AuthAPI = {
  login: (email: string, password: string, tenant: number) =>
    request<{ access_token: string }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password, tenant })
    })
};

// ---- KB
export type KBChunkIn = { content: string };
export const KBAPI = {
  upsert: (source: string, chunks: KBChunkIn[]) =>
    request<{ inserted: number }>("/kb/upsert", {
      method: "POST",
      body: JSON.stringify({ source, chunks })
    }),
  search: (query: string, limit = 5) =>
    request<{ results: { id: number; source: string; chunk: string; score: number }[] }>(
      "/kb/search",
      { method: "POST", body: JSON.stringify({ query, limit }) }
    )
};

// ---- Tickets
export type Ticket = { id: number; title: string; status: string };
export type Message = { id: number; role: "user"|"agent"|"system"; content: string };

export const TicketsAPI = {
  list: (limit=50, offset=0) =>
    request<Ticket[]>(`/tickets/?limit=${limit}&offset=${offset}`),
  create: (title: string) =>
    request<Ticket>("/tickets/", { method: "POST", body: JSON.stringify({ title }) }),
  messages: (ticketId: number) =>
    request<Message[]>(`/tickets/${ticketId}/messages`),
  addMessage: (ticketId: number, role: Message["role"], content: string) =>
    request<Message>(`/tickets/${ticketId}/messages`, {
      method: "POST", body: JSON.stringify({ role, content })
    })
};

// ---- Agent (support/answer; с фолбэком /agent/answer на всякий случай)
async function tryBoth<T>(primary: string, secondary: string, init: RequestInit): Promise<T> {
  const { apiBase } = useAuth.getState();
  try {
    return await request<T>(primary, init);
  } catch (e: any) {
    const msg = String(e?.message || "");
    if (msg.includes("HTTP 404")) {
      return await request<T>(secondary, init);
    }
    throw e;
  }
}

export const AgentAPI = {
  ask: (query: string, kb_limit=5, temperature=0.2) =>
    tryBoth<{ reply: string; used_context?: string; kb_hits?: any; escalated?: boolean; reason?: string }>(
      "/support/answer",
      "/agent/answer",
      { method: "POST", body: JSON.stringify({ query, kb_limit, temperature }) }
    ),

  answerTicket: (ticketId: number, query: string, save=true, kb_limit=5, temperature=0.2) =>
    tryBoth<{ reply: string; saved_message_id?: number }>(
      `/support/tickets/${ticketId}/answer?save=${save}`,
      `/agent/tickets/${ticketId}/answer?save=${save}`,
      { method: "POST", body: JSON.stringify({ query, kb_limit, temperature }) }
    )
};
