import { useState } from "react";
import { KBAPI } from "@/lib/api";

export default function KB() {
  const [source, setSource] = useState("docs");
  const [chunks, setChunks] = useState<string>("FAQ 1\n---\nFAQ 2");
  const [q, setQ] = useState("");
  const [results, setResults] = useState<{id:number;source:string;chunk:string;score:number}[]>([]);
  const [msg, setMsg] = useState<string|null>(null);
  const [err, setErr] = useState<string|null>(null);
  const [busy, setBusy] = useState(false);

  async function onUpsert() {
    setErr(null); setMsg(null); setBusy(true);
    try {
      const parts = chunks.split(/\n---+\n/).map(s=>s.trim()).filter(Boolean).map(content=>({content}));
      const r = await KBAPI.upsert(source, parts);
      setMsg(`Inserted: ${r.inserted}`);
    } catch (e:any) {
      setErr(String(e.message||e));
    } finally { setBusy(false); }
  }

  async function onSearch() {
    setErr(null); setMsg(null); setBusy(true); setResults([]);
    try {
      const r = await KBAPI.search(q, 5);
      setResults(r.results);
    } catch (e:any) {
      setErr(String(e.message||e));
    } finally { setBusy(false); }
  }

  return (
    <div className="grid md:grid-cols-2 gap-6">
      <div className="bg-white border rounded p-4 space-y-3">
        <h2 className="font-semibold">Upsert KB</h2>
        <label className="text-sm">Source</label>
        <input className="w-full border rounded px-2 py-1" value={source} onChange={e=>setSource(e.target.value)}/>
        <label className="text-sm">Chunks (split by "---")</label>
        <textarea className="w-full h-40 border rounded px-2 py-1" value={chunks} onChange={e=>setChunks(e.target.value)}/>
        <button disabled={busy} onClick={onUpsert} className="px-3 py-2 rounded bg-emerald-600 text-white disabled:opacity-60">Upload</button>
        {msg && <div className="text-emerald-700 text-sm">{msg}</div>}
        {err && <div className="text-red-600 text-sm">{err}</div>}
      </div>

      <div className="bg-white border rounded p-4 space-y-3">
        <h2 className="font-semibold">Search KB</h2>
        <input className="w-full border rounded px-2 py-1" placeholder="query..." value={q} onChange={e=>setQ(e.target.value)}/>
        <button disabled={busy} onClick={onSearch} className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-60">Search</button>
        <ul className="divide-y">
          {results.map(r=>(
            <li key={r.id} className="py-2">
              <div className="text-xs text-slate-500">{r.source} • score {r.score.toFixed(4)}</div>
              <div className="whitespace-pre-wrap">{r.chunk}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
