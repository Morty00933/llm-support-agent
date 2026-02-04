// ===== API Types =====

export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail?: string;
  instance?: string;
  errors?: Array<{ field: string; message: string }>;
  correlation_id?: string;
}

export interface PageMeta {
  total: number;
  limit: number;
  offset: number;
  has_next: boolean;
  has_prev: boolean;
  next_url?: string;
  prev_url?: string;
}

export interface Page<T> {
  items: T[];
  meta: PageMeta;
}

// ===== Auth Types =====

export interface User {
  id: number;
  email: string;
  name: string;
  role: 'admin' | 'agent' | 'viewer';
  tenant_id: number;
  avatar_url?: string;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name: string;
}

// ===== Ticket Types =====

export type TicketStatus = 
  | 'open'
  | 'in_progress'
  | 'pending_customer'
  | 'pending_agent'
  | 'escalated'
  | 'resolved'
  | 'closed'
  | 'reopened';

export type TicketPriority = 'critical' | 'high' | 'medium' | 'low';

export interface Tag {
  id: number;
  name: string;
  color?: string;
  description?: string;
}

export interface Category {
  id: number;
  name: string;
  slug: string;
  parent_id?: number;
  level: number;
  path: string;
}

export interface Ticket {
  id: number;
  tenant_id: number;
  title: string;
  description?: string;
  status: TicketStatus;
  priority: TicketPriority;
  category_id?: number;
  category?: Category;
  assigned_to?: number;
  assigned_at?: string;
  created_by?: number;
  source: string;
  tags: Tag[];
  custom_fields?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface CreateTicketRequest {
  title: string;
  description?: string;
  priority?: TicketPriority;
  category_id?: number;
  tags?: number[];
}

export interface UpdateTicketRequest {
  title?: string;
  description?: string;
  status?: TicketStatus;
  priority?: TicketPriority;
  category_id?: number;
  assigned_to?: number;
  tags?: number[];
}

// ===== Message Types =====

export type MessageRole = 'user' | 'assistant' | 'system';

export interface Message {
  id: number;
  ticket_id: number;
  role: MessageRole;
  content: string;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface CreateMessageRequest {
  content: string;
  role?: MessageRole;
}

// ===== KB Types =====

export interface KBChunk {
  id: number;
  tenant_id: number;
  source: string;
  chunk: string;
  chunk_hash: string;
  metadata?: Record<string, unknown>;
  version: number;
  is_current: boolean;
  archived_at?: string;
  created_at: string;
  updated_at: string;
}

export interface KBSearchResult {
  id: number;
  source: string;
  chunk: string;
  score: number;
  metadata?: Record<string, unknown>;
}

export interface CreateKBChunkRequest {
  source: string;
  chunk: string;
  metadata?: Record<string, unknown>;
}

export interface UpsertKBChunksRequest {
  source: string;
  chunks: Array<{
    chunk: string;
    metadata?: Record<string, unknown>;
  }>;
}

export interface UpsertKBChunksResponse {
  created: number;
  updated: number;
  skipped: number;
}

// ===== Agent Types =====

export interface AgentAnswerRequest {
  query: string;
  kb_limit?: number;
  temperature?: number;
  stream?: boolean;
}

export interface AgentAnswerResponse {
  reply: string;
  used_context?: string;
  kb_hits: KBSearchResult[];
  escalated: boolean;
  reason?: string;
}

export interface StreamChunk {
  type: 'content' | 'metadata' | 'done' | 'error';
  content?: string;
  metadata?: Record<string, unknown>;
}

// ===== SLA Types =====

export interface SLAPolicy {
  id: number;
  tenant_id: number;
  name: string;
  priority: TicketPriority;
  first_response_minutes: number;
  resolution_minutes: number;
  update_frequency_minutes?: number;
  business_hours_only: boolean;
  is_default: boolean;
}

export interface TicketSLA {
  id: number;
  ticket_id: number;
  policy_id?: number;
  first_response_due?: string;
  resolution_due?: string;
  next_update_due?: string;
  first_response_at?: string;
  resolved_at?: string;
  first_response_breached: boolean;
  resolution_breached: boolean;
  paused_at?: string;
  total_paused_minutes: number;
}

// ===== Feature Flags =====

export interface FeatureFlags {
  streaming_responses: boolean;
  ml_escalation: boolean;
  multi_model: boolean;
  semantic_dedup: boolean;
  auto_tagging: boolean;
  bidirectional_sync: boolean;
  webhooks: boolean;
  dark_mode: boolean;
  realtime_updates: boolean;
}

// ===== UI Types =====

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  duration?: number;
}

export type Theme = 'light' | 'dark' | 'system';

export interface AppSettings {
  theme: Theme;
  language: string;
  sidebarCollapsed: boolean;
  notificationsEnabled: boolean;
}
