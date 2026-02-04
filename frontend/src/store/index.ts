import { create } from 'zustand';
import { persist, devtools } from 'zustand/middleware';
import type { User, Theme, AppSettings, Toast, FeatureFlags, Ticket } from '../types';

// ===== Auth Store =====

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  setUser: (user: User | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  devtools(
    persist(
      (set) => ({
        user: null,
        isAuthenticated: false,
        isLoading: true,

        setUser: (user) =>
          set({
            user,
            isAuthenticated: !!user,
            isLoading: false,
          }),

        setLoading: (isLoading) => set({ isLoading }),

        logout: () =>
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
          }),
      }),
      { name: 'auth-store' }
    ),
    { name: 'AuthStore' }
  )
);

// ===== Settings Store =====

interface SettingsState {
  settings: AppSettings;
  featureFlags: FeatureFlags | null;
  
  setTheme: (theme: Theme) => void;
  setLanguage: (language: string) => void;
  toggleSidebar: () => void;
  setFeatureFlags: (flags: FeatureFlags) => void;
  updateSettings: (settings: Partial<AppSettings>) => void;
}

const defaultSettings: AppSettings = {
  theme: 'system',
  language: 'en',
  sidebarCollapsed: false,
  notificationsEnabled: true,
};

export const useSettingsStore = create<SettingsState>()(
  devtools(
    persist(
      (set) => ({
        settings: defaultSettings,
        featureFlags: null,

        setTheme: (theme) =>
          set((state) => ({
            settings: { ...state.settings, theme },
          })),

        setLanguage: (language) =>
          set((state) => ({
            settings: { ...state.settings, language },
          })),

        toggleSidebar: () =>
          set((state) => ({
            settings: {
              ...state.settings,
              sidebarCollapsed: !state.settings.sidebarCollapsed,
            },
          })),

        setFeatureFlags: (featureFlags) => set({ featureFlags }),

        updateSettings: (newSettings) =>
          set((state) => ({
            settings: { ...state.settings, ...newSettings },
          })),
      }),
      { name: 'settings-store' }
    ),
    { name: 'SettingsStore' }
  )
);

// ===== Toast Store =====

interface ToastState {
  toasts: Toast[];
  
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
  clearToasts: () => void;
}

export const useToastStore = create<ToastState>()(
  devtools(
    (set) => ({
      toasts: [],

      addToast: (toast) =>
        set((state) => ({
          toasts: [
            ...state.toasts,
            {
              ...toast,
              id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            },
          ],
        })),

      removeToast: (id) =>
        set((state) => ({
          toasts: state.toasts.filter((t) => t.id !== id),
        })),

      clearToasts: () => set({ toasts: [] }),
    }),
    { name: 'ToastStore' }
  )
);

// ===== Tickets Store =====

interface TicketsState {
  tickets: Ticket[];
  selectedTicket: Ticket | null;
  isLoading: boolean;
  filters: {
    status?: string;
    search?: string;
    assignedTo?: number;
  };
  pagination: {
    total: number;
    limit: number;
    offset: number;
  };
  
  setTickets: (tickets: Ticket[]) => void;
  addTicket: (ticket: Ticket) => void;
  updateTicket: (id: number, updates: Partial<Ticket>) => void;
  removeTicket: (id: number) => void;
  setSelectedTicket: (ticket: Ticket | null) => void;
  setLoading: (loading: boolean) => void;
  setFilters: (filters: Partial<TicketsState['filters']>) => void;
  setPagination: (pagination: Partial<TicketsState['pagination']>) => void;
}

export const useTicketsStore = create<TicketsState>()(
  devtools(
    (set) => ({
      tickets: [],
      selectedTicket: null,
      isLoading: false,
      filters: {},
      pagination: {
        total: 0,
        limit: 20,
        offset: 0,
      },

      setTickets: (tickets) => set({ tickets }),

      addTicket: (ticket) =>
        set((state) => ({
          tickets: [ticket, ...state.tickets],
        })),

      updateTicket: (id, updates) =>
        set((state) => ({
          tickets: state.tickets.map((t) =>
            t.id === id ? { ...t, ...updates } : t
          ),
          selectedTicket:
            state.selectedTicket?.id === id
              ? { ...state.selectedTicket, ...updates }
              : state.selectedTicket,
        })),

      removeTicket: (id) =>
        set((state) => ({
          tickets: state.tickets.filter((t) => t.id !== id),
          selectedTicket:
            state.selectedTicket?.id === id ? null : state.selectedTicket,
        })),

      setSelectedTicket: (selectedTicket) => set({ selectedTicket }),

      setLoading: (isLoading) => set({ isLoading }),

      setFilters: (filters) =>
        set((state) => ({
          filters: { ...state.filters, ...filters },
        })),

      setPagination: (pagination) =>
        set((state) => ({
          pagination: { ...state.pagination, ...pagination },
        })),
    }),
    { name: 'TicketsStore' }
  )
);

// ===== Chat Store (for agent conversations) =====

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  metadata?: Record<string, unknown>;
}

interface ChatState {
  messages: ChatMessage[];
  isLoading: boolean;
  streamingContent: string;
  
  addMessage: (message: Omit<ChatMessage, 'id' | 'timestamp'>) => string;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  appendStreamingContent: (content: string) => void;
  clearStreamingContent: () => void;
  setLoading: (loading: boolean) => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set) => ({
      messages: [],
      isLoading: false,
      streamingContent: '',

      addMessage: (message) => {
        const id = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        set((state) => ({
          messages: [
            ...state.messages,
            {
              ...message,
              id,
              timestamp: new Date(),
            },
          ],
        }));
        return id;
      },

      updateMessage: (id, updates) =>
        set((state) => ({
          messages: state.messages.map((m) =>
            m.id === id ? { ...m, ...updates } : m
          ),
        })),

      appendStreamingContent: (content) =>
        set((state) => ({
          streamingContent: state.streamingContent + content,
        })),

      clearStreamingContent: () => set({ streamingContent: '' }),

      setLoading: (isLoading) => set({ isLoading }),

      clearMessages: () => set({ messages: [], streamingContent: '' }),
    }),
    { name: 'ChatStore' }
  )
);
