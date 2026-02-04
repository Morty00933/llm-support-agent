/**
 * API Client - FIXED VERSION v2
 * 
 * FIXES:
 * 1. Added setTokens, clearTokens, getAccessToken, getRefreshToken methods
 * 2. Extended api object with token management
 * 3. Unified all API calls in one place
 * 4. CRITICAL: Increased timeout to 120s for LLM requests (was 30s)
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

// Token storage keys
const ACCESS_TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';

// Create axios instance with extended timeout for LLM
const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  // CRITICAL FIX: Increased from 30s to 120s for LLM requests
  // Ollama can take 18-60 seconds to generate responses
  timeout: 120000,
});

// Request interceptor - add auth token
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem(ACCESS_TOKEN_KEY);
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor - handle errors and token refresh
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // If 401 and not already retrying, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/v1/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token, refresh_token: newRefreshToken } = response.data;
          
          localStorage.setItem(ACCESS_TOKEN_KEY, access_token);
          if (newRefreshToken) {
            localStorage.setItem(REFRESH_TOKEN_KEY, newRefreshToken);
          }
          
          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
          }
          return axiosInstance(originalRequest);
        } catch (refreshError) {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem(ACCESS_TOKEN_KEY);
          localStorage.removeItem(REFRESH_TOKEN_KEY);
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token, redirect to login
        window.location.href = '/login';
      }
    }
    
    // Better error message for timeout
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      const customError = new Error('Request timed out. The AI is taking longer than expected. Please try again.');
      return Promise.reject(customError);
    }
    
    return Promise.reject(error);
  }
);

// ===== Token Management Methods =====

/**
 * Set access and refresh tokens
 */
function setTokens(accessToken: string, refreshToken?: string): void {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  }
}

/**
 * Clear all tokens
 */
function clearTokens(): void {
  localStorage.removeItem(ACCESS_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

/**
 * Get access token
 */
function getAccessToken(): string | null {
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

/**
 * Get refresh token
 */
function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

// ===== Extended API object =====

interface ApiClient extends AxiosInstance {
  setTokens: typeof setTokens;
  clearTokens: typeof clearTokens;
  getAccessToken: typeof getAccessToken;
  getRefreshToken: typeof getRefreshToken;
}

// Extend axios instance with token methods
const api = axiosInstance as ApiClient;
api.setTokens = setTokens;
api.clearTokens = clearTokens;
api.getAccessToken = getAccessToken;
api.getRefreshToken = getRefreshToken;

// ===== Auth API =====

export interface LoginCredentials {
  email: string;
  password: string;
  tenant_id?: number;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
  tenant_id: number;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface User {
  id: number;
  email: string;
  full_name: string | null;
  tenant_id: number;
  role: string;
  is_active: boolean;
  created_at: string;
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/v1/auth/login/json', {
      ...credentials,
      tenant_id: credentials.tenant_id || 1,
    });
    return response.data;
  },

  register: async (data: RegisterData): Promise<User> => {
    const response = await api.post<User>('/v1/auth/register', data);
    return response.data;
  },

  me: async (): Promise<User> => {
    const response = await api.get<User>('/v1/auth/me');
    return response.data;
  },

  refresh: async (refreshToken: string): Promise<TokenResponse> => {
    const response = await api.post<TokenResponse>('/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    return response.data;
  },

  logout: (): void => {
    api.clearTokens();
  },
};

// ===== Tickets API =====

export interface Ticket {
  id: number;
  tenant_id: number;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  source: string;
  assigned_to: number | null;
  created_by_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface CreateTicketData {
  title: string;
  description?: string;
  priority?: string;
  source?: string;
}

export interface UpdateTicketData {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  assigned_to?: number;
}

export interface Message {
  id: number;
  ticket_id: number;
  role: string;
  content: string;
  created_at: string;
  metadata?: Record<string, unknown>;
}

export interface CreateMessageData {
  content: string;
  role?: string;
  auto_respond?: boolean;
}

export const ticketsApi = {
  list: async (params?: { status?: string; skip?: number; limit?: number }): Promise<Ticket[]> => {
    const response = await api.get<Ticket[]>('/v1/tickets', { params });
    return response.data;
  },
  
  get: async (id: number): Promise<Ticket> => {
    const response = await api.get<Ticket>(`/v1/tickets/${id}`);
    return response.data;
  },
  
  create: async (data: CreateTicketData): Promise<Ticket> => {
    const response = await api.post<Ticket>('/v1/tickets', data);
    return response.data;
  },
  
  update: async (id: number, data: UpdateTicketData): Promise<Ticket> => {
    const response = await api.patch<Ticket>(`/v1/tickets/${id}`, data);
    return response.data;
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/v1/tickets/${id}`);
  },
  
  getMessages: async (ticketId: number): Promise<Message[]> => {
    const response = await api.get<Message[]>(`/v1/tickets/${ticketId}/messages`);
    return response.data;
  },
  
  createMessage: async (ticketId: number, data: CreateMessageData): Promise<Message> => {
    const response = await api.post<Message>(`/v1/tickets/${ticketId}/messages`, data);
    return response.data;
  },
};

// ===== Agent API =====

export interface AgentResponse {
  content: string;
  needs_escalation: boolean;
  escalation_reason: string | null;
  context_used: Array<{
    id: number;
    source: string;
    chunk: string;
    score: number;
  }>;
  model: string;
}

export const agentApi = {
  ask: async (params: {
    question: string;
    max_context?: number;
  }): Promise<AgentResponse> => {
    // Extended timeout for LLM requests
    const response = await api.post<AgentResponse>('/v1/agent/ask', params, {
      timeout: 180000, // 3 minutes for LLM
    });
    return response.data;
  },
  
  respond: async (ticketId: number, options?: {
    save_response?: boolean;
    max_context?: number;
  }): Promise<AgentResponse> => {
    // Extended timeout for LLM requests
    const response = await api.post<AgentResponse>(`/v1/agent/respond/${ticketId}`, options || {}, {
      timeout: 180000, // 3 minutes for LLM
    });
    return response.data;
  },
  
  health: async (): Promise<{
    ollama_available: boolean;
    chat_model: string;
    embed_model: string;
    models_loaded: string[];
  }> => {
    const response = await api.get('/v1/agent/health');
    return response.data;
  },
};

// ===== Knowledge Base API =====

export interface KBChunk {
  id: number;
  tenant_id: number;
  source: string;
  chunk: string;
  chunk_hash: string;
  metadata_json: Record<string, unknown> | null;
  version: number;
  is_current: boolean;
  created_at: string;
  updated_at: string;
}

export interface KBSearchResult {
  id: number;
  source: string;
  chunk: string;
  score: number;
  metadata_json?: Record<string, unknown>;
}

export const kbApi = {
  list: async (params?: { limit?: number; offset?: number }): Promise<KBChunk[]> => {
    const response = await api.get<KBChunk[]>('/v1/kb/chunks', { params });
    return response.data;
  },
  
  search: async (query: string, limit?: number): Promise<KBSearchResult[]> => {
    const response = await api.post<KBSearchResult[]>('/v1/kb/search', {
      query,
      limit: limit || 10,
    });
    return response.data;
  },
  
  create: async (data: { source: string; chunk: string; metadata?: Record<string, unknown> }): Promise<KBChunk> => {
    const response = await api.post<KBChunk>('/v1/kb/chunks', data);
    return response.data;
  },
  
  delete: async (id: number): Promise<void> => {
    await api.delete(`/v1/kb/chunks/${id}`);
  },
};

// ===== Tenants API =====

export interface TenantStats {
  tickets_by_status: Record<string, number>;
  total_users: number;
  total_kb_chunks: number;
}

export const tenantsApi = {
  getStats: async (): Promise<TenantStats> => {
    const response = await api.get<TenantStats>('/v1/tenants/current/stats');
    return response.data;
  },
};

// Export as both 'api' and 'apiClient' for compatibility
export { api, api as apiClient };
export default api;
