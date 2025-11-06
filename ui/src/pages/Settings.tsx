import { useAuth } from "@/store/auth";
import { useState } from "react";

export default function Settings() {
  const { apiBase, setApiBase, tenant, setTenant, token, reset } = useAuth();
  const [b, setB] = useState(apiBase);
  const [t, setT] = useState(tenant);

  function save() {
    setApiBase(b || "/api");
    setTenant(Number(t)||1);
  }

  return (
    <div className="max-w-xl bg-white border rounded p-4 space-y-3">
      <h2 className="font-semibold">Settings</h2>
      <div>
        <label className="text-sm block">API Base</label>
        <input className="w-full border rounded px-2 py-1" value={b} onChange={e=>setB(e.target.value)}/>
        <div className="text-xs text-slate-500 mt-1">Обычно: <code>/api</code>. Бэкенд слушает на <code>/api/v1/*</code>.</div>
      </div>
      <div>
        <label className="text-sm block">Tenant ID</label>
        <input type="number" min={1} className="w-40 border rounded px-2 py-1"
               value={t} onChange={e=>setT(Number(e.target.value)||1)} />
      </div>
      <div className="flex gap-2">
        <button className="px-3 py-1 rounded bg-blue-600 text-white" onClick={save}>Save</button>
        <button className="px-3 py-1 rounded border" onClick={()=>location.reload()}>Reload</button>
      </div>

      <div className="border-t pt-3">
        <div className="text-sm">Token: {token ? <code className="break-all">{token}</code> : <i>none</i>}</div>
        {token && <button className="mt-2 px-3 py-1 rounded border" onClick={reset}>Logout (clear token)</button>}
      </div>
    </div>
  );
}
