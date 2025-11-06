import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "@/store/auth";

export default function Layout() {
  const { token, tenant, setTenant, reset } = useAuth();
  const nav = useNavigate();
  const logout = () => { reset(); nav("/login"); };

  return (
    <div className="min-h-screen">
      <header className="border-b bg-white">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="font-semibold">LLM Support Agent</Link>
          <nav className="flex gap-4">
            <NavLink to="/kb" className={({isActive})=>isActive?"font-semibold":"text-slate-600"}>KB</NavLink>
            <NavLink to="/tickets" className={({isActive})=>isActive?"font-semibold":"text-slate-600"}>Tickets</NavLink>
            <NavLink to="/agent" className={({isActive})=>isActive?"font-semibold":"text-slate-600"}>Agent</NavLink>
            <NavLink to="/settings" className={({isActive})=>isActive?"font-semibold":"text-slate-600"}>Settings</NavLink>
          </nav>
          <div className="flex items-center gap-3">
            <label className="text-sm text-slate-600">Tenant</label>
            <input
              type="number" min={1} value={tenant}
              onChange={(e)=>setTenant(Number(e.target.value)||1)}
              className="w-20 border rounded px-2 py-1"
            />
            {token
              ? <button className="px-3 py-1 border rounded" onClick={logout}>Logout</button>
              : <Link to="/login" className="px-3 py-1 border rounded">Login</Link>}
          </div>
        </div>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-6">
        <Outlet/>
      </main>
    </div>
  );
}
