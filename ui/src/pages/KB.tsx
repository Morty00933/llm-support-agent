import { useState } from "react";
import { KBAPI, KBSearchHit } from "@/lib/api";

function parseTags(value: string): string[] | undefined {
  const tags = value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
  return tags.length ? tags : undefined;
}

export default function KB() {
  const [source, setSource] = useState("docs");
  const [chunks, setChunks] = useState<string>("FAQ 1\n---\nFAQ 2");
  const [defaultLanguage, setDefaultLanguage] = useState("");
  const [defaultTags, setDefaultTags] = useState("");
  const [q, setQ] = useState("");
  const [limit, setLimit] = useState(5);
  const [searchSource, setSearchSource] = useState("");
  const [searchTags, setSearchTags] = useState("");
  const [searchLanguage, setSearchLanguage] = useState("");
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [results, setResults] = useState<KBSearchHit[]>([]);
  const [msg, setMsg] = useState<string|null>(null);
  const [err, setErr] = useState<string|null>(null);
  const [busy, setBusy] = useState(false);

  async function onUpsert() {
    setErr(null); setMsg(null); setBusy(true);
    try {
      const parts = chunks
        .split(/\n---+\n/)
        .map((s) => s.trim())
        .filter(Boolean)
        .map((content) => ({ content }));
      const payload = {
        source,
        chunks: parts,
        default_language: defaultLanguage || undefined,
        default_tags: parseTags(defaultTags),
      };
      const r = await KBAPI.upsert(payload);
      const summary = r.summary;
      setMsg(
        `Upserted: ${summary.created} new, ${summary.updated} updated, ${summary.skipped} skipped`
      );
    } catch (e:any) {
      setErr(String(e.message||e));
    } finally { setBusy(false); }
  }

  async function onSearch() {
    setErr(null); setMsg(null); setBusy(true); setResults([]);
    try {
      const r = await KBAPI.search({
        query: q,
        limit,
        source: searchSource || undefined,
        tags: parseTags(searchTags),
        language: searchLanguage || undefined,
        include_metadata: includeMetadata,
      });
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <label className="text-sm flex flex-col">
            <span>Default language (optional)</span>
            <input
              className="border rounded px-2 py-1 mt-1"
              placeholder="en"
              value={defaultLanguage}
              onChange={(e) => setDefaultLanguage(e.target.value)}
            />
          </label>
          <label className="text-sm flex flex-col">
            <span>Default tags (comma separated)</span>
            <input
              className="border rounded px-2 py-1 mt-1"
              placeholder="faq, onboarding"
              value={defaultTags}
              onChange={(e) => setDefaultTags(e.target.value)}
            />
          </label>
        </div>
        <label className="text-sm">Chunks (split by "---")</label>
        <textarea className="w-full h-40 border rounded px-2 py-1" value={chunks} onChange={e=>setChunks(e.target.value)}/>
        <button disabled={busy} onClick={onUpsert} className="px-3 py-2 rounded bg-emerald-600 text-white disabled:opacity-60">Upload</button>
        {msg && <div className="text-emerald-700 text-sm">{msg}</div>}
        {err && <div className="text-red-600 text-sm">{err}</div>}
      </div>

      <div className="bg-white border rounded p-4 space-y-3">
        <h2 className="font-semibold">Search KB</h2>
        <input className="w-full border rounded px-2 py-1" placeholder="query..." value={q} onChange={e=>setQ(e.target.value)}/>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <label className="text-sm flex flex-col">
            <span>Limit</span>
            <input
              type="number"
              min={1}
              max={20}
              className="border rounded px-2 py-1 mt-1"
              value={limit}
              onChange={(e) => setLimit(Number(e.target.value) || 5)}
            />
          </label>
          <label className="text-sm flex flex-col">
            <span>Source filter</span>
            <input
              className="border rounded px-2 py-1 mt-1"
              placeholder="docs"
              value={searchSource}
              onChange={(e) => setSearchSource(e.target.value)}
            />
          </label>
          <label className="text-sm flex flex-col">
            <span>Tags filter</span>
            <input
              className="border rounded px-2 py-1 mt-1"
              placeholder="faq, onboarding"
              value={searchTags}
              onChange={(e) => setSearchTags(e.target.value)}
            />
          </label>
          <label className="text-sm flex flex-col">
            <span>Language filter</span>
            <input
              className="border rounded px-2 py-1 mt-1"
              placeholder="en"
              value={searchLanguage}
              onChange={(e) => setSearchLanguage(e.target.value)}
            />
          </label>
        </div>
        <label className="inline-flex items-center text-sm gap-2">
          <input
            type="checkbox"
            className="rounded border"
            checked={includeMetadata}
            onChange={(e) => setIncludeMetadata(e.target.checked)}
          />
          Include metadata in results
        </label>
        <button disabled={busy} onClick={onSearch} className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-60">Search</button>
        <ul className="divide-y">
          {results.map(r=>(
            <li key={r.id} className="py-2">
              <div className="text-xs text-slate-500">{r.source} • score {r.score.toFixed(4)}</div>
              <div className="whitespace-pre-wrap">{r.chunk}</div>
              {includeMetadata && r.metadata && (() => {
                const meta = r.metadata as Record<string, unknown>;
                const language = typeof meta.language === "string" ? meta.language : undefined;
                const tags = Array.isArray(meta.tags)
                  ? (meta.tags as unknown[]).map((tag) => String(tag))
                  : [];
                const charCount = meta.char_count as number | string | undefined;
                const wordCount = meta.word_count as number | string | undefined;
                return (
                  <div className="text-xs text-slate-500 mt-1 space-y-1">
                    {language && <div>language: {language}</div>}
                    {tags.length > 0 && <div>tags: {tags.join(", ")}</div>}
                    <div className="flex flex-wrap gap-2">
                      <span>chars: {String(charCount ?? "-")}</span>
                      <span>words: {String(wordCount ?? "-")}</span>
                    </div>
                  </div>
                );
              })()}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
