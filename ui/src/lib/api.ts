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
  const normalizedBase = apiBase.replace(/\/$/, "");
  const hasVersionSuffix = /\/v\d+$/.test(normalizedBase);
  const prefix = hasVersionSuffix ? "" : "/v1";
  const res = await fetch(`${normalizedBase}${prefix}${path}`, {
    ...init,
    headers: apiHeaders(init.headers)
  });
  if (!res.ok) {
    let detail = "";
    let payload: any = null;
    try {
      payload = await res.json();
      detail = payload?.detail ?? JSON.stringify(payload);
      if (detail && typeof detail !== "string") {
        detail = String(detail);
      }
    } catch {}

    if (res.status === 401) {
      const { reset } = useAuth.getState();
      reset();
      const normalized = detail.toLowerCase();
      if (normalized.includes("signature has expired")) {
        throw new Error("Сессия истекла — авторизуйтесь снова.");
      }
      throw new Error(
        detail ? `HTTP 401 Unauthorized: ${detail}` : "Не удалось авторизоваться. Повторите вход."
      );
    }

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
export type KBChunkIn = {
  content: string;
  language?: string | null;
  tags?: string[];
  metadata?: Record<string, unknown>;
};

export type KBUpsertRequest = {
  source: string;
  chunks: KBChunkIn[];
  default_language?: string | null;
  default_tags?: string[];
};

export type KBUpsertSummary = {
  created: number;
  updated: number;
  skipped: number;
  processed?: number;
};

export type KBSearchRequest = {
  query: string;
  limit?: number;
  source?: string;
  tags?: string[];
  language?: string | null;
  include_metadata?: boolean;
  include_archived?: boolean;
};

export type KBSearchHit = {
  id: number;
  source: string;
  chunk: string;
  score: number;
  similarity: number;
  archived: boolean;
  updated_at?: string;
  archived_at?: string;
  metadata?: Record<string, unknown> | null;
};

export type KBArchiveRequest = {
  ids?: number[];
  source?: string;
  before?: string;
  archived?: boolean;
};

export type KBDeleteRequest = {
  ids?: number[];
  source?: string;
};

export type KBReindexRequest = {
  ids?: number[];
  source?: string;
  include_archived?: boolean;
  batch_size?: number;
};

export const KBAPI = {
  upsert: (payload: KBUpsertRequest) =>
    request<{ summary: KBUpsertSummary }>("/kb/upsert", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  search: (payload: KBSearchRequest) =>
    request<{ results: KBSearchHit[] }>("/kb/search", {
      method: "POST",
      body: JSON.stringify({ include_metadata: true, limit: 5, ...payload })
    }),
  archive: (payload: KBArchiveRequest) =>
    request<{ summary: { updated: number } }>("/kb/archive", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  remove: (payload: KBDeleteRequest) =>
    request<{ summary: { deleted: number } }>("/kb/delete", {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  reindex: (payload: KBReindexRequest) =>
    request<{ summary: { processed: number } }>("/kb/reindex", {
      method: "POST",
      body: JSON.stringify(payload)
    })
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
