import { create } from "zustand";

type AuthState = {
  token: string | null;
  tenant: number;
  apiBase: string;
  setToken: (t: string | null) => void;
  setTenant: (id: number) => void;
  setApiBase: (b: string) => void;
  reset: () => void;
};

const envApiBase = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.trim();
const defaultApiBase = (envApiBase && envApiBase.length > 0)
  ? envApiBase.replace(/\/$/, "")
  : window.location.origin.replace(/\/$/, "");

const saved = {
  token: localStorage.getItem("token"),
  tenant: Number(localStorage.getItem("tenant") || "1"),
  apiBase: localStorage.getItem("apiBase") || defaultApiBase
};

export const useAuth = create<AuthState>((set) => ({
  token: saved.token,
  tenant: saved.tenant,
  apiBase: saved.apiBase,
  setToken: (t) => {
    if (t) localStorage.setItem("token", t);
    else localStorage.removeItem("token");
    set({ token: t });
  },
  setTenant: (id) => {
    localStorage.setItem("tenant", String(id));
    set({ tenant: id });
  },
  setApiBase: (b) => {
    const normalized = b.replace(/\/$/, "");
    localStorage.setItem("apiBase", normalized);
    set({ apiBase: normalized });
  },
  reset: () => {
    localStorage.removeItem("token");
    set({ token: null, apiBase: defaultApiBase });
  }
}));
