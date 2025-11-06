import { useState } from "react";
import { AgentAPI } from "@/lib/api";

export default function Agent() {
  const [q, setQ] = useState("How to reset my password?");
  const [reply, setReply] = useState("");
  const [meta, setMeta] = useState<any>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string|null>(null);

  async function ask() {
    setBusy(true); setErr(null); setReply(""); setMeta(null);
    try {
      const r = await AgentAPI.ask(q, 5, 0.2);
      setReply(r.reply || "");
      setMeta({ used_context: r.used_context, kb_hits: r.kb_hits, escalated: r.escalated, reason: r.reason });
    } catch(e:any){ setErr(String(e.message||e)); }
    finally { setBusy(false); }
  }

  return (
    <div className="grid gap-4">
      <div className="bg-white border rounded p-4 space-y-3">
        <h2 className="font-semibold">Ask Agent</h2>
        <input className="w-full border rounded px-2 py-1" value={q} onChange={e=>setQ(e.target.value)} />
        <button disabled={busy} onClick={ask} className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-60">Ask</button>
        {err && <div className="text-red-600 text-sm">{err}</div>}
      </div>
      {reply && (
        <div className="bg-white border rounded p-4">
          <h3 className="font-semibold mb-2">Answer</h3>
          <div className="whitespace-pre-wrap">{reply}</div>
        </div>
      )}
      {meta && (
        <div className="bg-white border rounded p-4 text-sm text-slate-700">
          <div><b>Escalated:</b> {String(meta.escalated)}</div>
          <div><b>Reason:</b> {meta.reason}</div>
          {meta.used_context && (
            <>
              <div className="mt-2 font-semibold">Used context</div>
              <div className="whitespace-pre-wrap">{meta.used_context}</div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
