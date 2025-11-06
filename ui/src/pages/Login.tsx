import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/store/auth";
import { AuthAPI } from "@/lib/api";

export default function Login() {
  const nav = useNavigate();
  const { tenant, setToken } = useAuth();
  const [email, setEmail] = useState("user@example.com");
  const [password, setPassword] = useState("secret");
  const [err, setErr] = useState<string|null>(null);
  const [load, setLoad] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null); setLoad(true);
    try {
      const { access_token } = await AuthAPI.login(email, password, tenant);
      setToken(access_token);
      nav("/kb");
    } catch (e:any) {
      setErr(String(e.message||e));
    } finally {
      setLoad(false);
    }
  }

  return (
    <div className="max-w-md mx-auto bg-white border rounded p-6 space-y-4 mt-10">
      <h1 className="text-xl font-semibold">Login</h1>
      {err && <div className="text-red-600 text-sm">{err}</div>}
      <form onSubmit={onSubmit} className="space-y-3">
        <div>
          <label className="block text-sm">Email</label>
          <input className="w-full border rounded px-3 py-2"
                 value={email} onChange={e=>setEmail(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm">Password</label>
          <input className="w-full border rounded px-3 py-2" type="password"
                 value={password} onChange={e=>setPassword(e.target.value)} />
        </div>
        <button disabled={load} className="px-4 py-2 rounded bg-blue-600 text-white disabled:opacity-60">
          {load ? "Signing in..." : "Sign in"}
        </button>
      </form>
    </div>
  );
}
