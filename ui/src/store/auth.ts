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

const saved = {
  token: localStorage.getItem("token"),
  tenant: Number(localStorage.getItem("tenant") || "1"),
  apiBase: localStorage.getItem("apiBase") || "/api"
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
    localStorage.setItem("apiBase", b);
    set({ apiBase: b });
  },
  reset: () => {
    localStorage.removeItem("token");
    set({ token: null });
  }
}));
