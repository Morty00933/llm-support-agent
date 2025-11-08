import { useMemo, useState } from "react";
import {
  KBAPI,
  KBArchiveRequest,
  KBReindexRequest,
  KBSearchHit,
} from "@/lib/api";

type MetadataEntry = {
  id: string;
  key: string;
  value: string;
};

type ChunkDraft = {
  id: string;
  content: string;
  language: string;
  tags: string;
  metadataEntries: MetadataEntry[];
};

function parseTags(value: string): string[] | undefined {
  const tags = value
    .split(",")
    .map((tag) => tag.trim().toLowerCase())
    .filter(Boolean);
  return tags.length ? Array.from(new Set(tags)).sort() : undefined;
}

type MetadataCompileResult = {
  value?: Record<string, unknown>;
  error?: string;
};

function coerceMetadataValue(value: string): unknown {
  const trimmed = value.trim();
  if (!trimmed) return undefined;
  const lower = trimmed.toLowerCase();
  if (lower === "true") return true;
  if (lower === "false") return false;
  if (/^-?\d+(\.\d+)?$/.test(trimmed)) {
    const num = Number(trimmed);
    return Number.isNaN(num) ? trimmed : num;
  }
  if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
    try {
      return JSON.parse(trimmed);
    } catch (err: any) {
      throw new Error(`Invalid JSON value: ${err.message ?? err}`);
    }
  }
  return trimmed;
}

function compileMetadata(entries: MetadataEntry[]): MetadataCompileResult {
  if (!entries.length) return {};
  const payload: Record<string, unknown> = {};
  for (const entry of entries) {
    const key = entry.key.trim();
    if (!key) continue;
    if (payload[key] !== undefined) {
      return { error: `Duplicate key "${key}"` };
    }
    try {
      const coerced = coerceMetadataValue(entry.value);
      if (typeof coerced === "undefined") continue;
      payload[key] = coerced;
    } catch (err: any) {
      return { error: String(err?.message ?? err) };
    }
  }
  return Object.keys(payload).length ? { value: payload } : {};
}

function emptyChunk(seed: number): ChunkDraft {
  return {
    id: `chunk-${seed}`,
    content: "",
    language: "",
    tags: "",
    metadataEntries: [],
  };
}

export default function KB() {
  const [source, setSource] = useState("docs");
  const [defaultLanguage, setDefaultLanguage] = useState("en");
  const [defaultTags, setDefaultTags] = useState("");
  const [chunks, setChunks] = useState<ChunkDraft[]>([emptyChunk(1)]);
  const [q, setQ] = useState("");
  const [limit, setLimit] = useState(5);
  const [searchSource, setSearchSource] = useState("");
  const [searchTags, setSearchTags] = useState("");
  const [searchLanguage, setSearchLanguage] = useState("");
  const [includeArchived, setIncludeArchived] = useState(false);
  const [includeMetadata, setIncludeMetadata] = useState(true);
  const [results, setResults] = useState<KBSearchHit[]>([]);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [seed, setSeed] = useState(1);
  const [metadataSeed, setMetadataSeed] = useState(0);

  const chunkCount = useMemo(() => chunks.length, [chunks]);

  function updateChunk(id: string, patch: Partial<ChunkDraft>) {
    setChunks((current) =>
      current.map((chunk) => (chunk.id === id ? { ...chunk, ...patch } : chunk))
    );
  }

  function addChunk() {
    const next = seed + 1;
    setSeed(next);
    setChunks((current) => [...current, emptyChunk(next)]);
  }

  function removeChunk(id: string) {
    setChunks((current) => current.filter((chunk) => chunk.id !== id));
  }

  function addMetadataEntry(chunkId: string) {
    const next = metadataSeed + 1;
    setMetadataSeed(next);
    setChunks((current) =>
      current.map((chunk) =>
        chunk.id === chunkId
          ? {
              ...chunk,
              metadataEntries: [
                ...chunk.metadataEntries,
                { id: `meta-${next}`, key: "", value: "" },
              ],
            }
          : chunk
      )
    );
  }

  function updateMetadataEntry(
    chunkId: string,
    entryId: string,
    patch: Partial<MetadataEntry>
  ) {
    setChunks((current) =>
      current.map((chunk) =>
        chunk.id === chunkId
          ? {
              ...chunk,
              metadataEntries: chunk.metadataEntries.map((entry) =>
                entry.id === entryId ? { ...entry, ...patch } : entry
              ),
            }
          : chunk
      )
    );
  }

  function removeMetadataEntry(chunkId: string, entryId: string) {
    setChunks((current) =>
      current.map((chunk) =>
        chunk.id === chunkId
          ? {
              ...chunk,
              metadataEntries: chunk.metadataEntries.filter(
                (entry) => entry.id !== entryId
              ),
            }
          : chunk
      )
    );
  }

  async function onUpsert() {
    setErr(null);
    setMsg(null);
    setBusy(true);
    try {
      const payloadChunks = chunks
        .map((chunk) => {
          const content = chunk.content.trim();
          if (!content) return null;
          const { value: metadata, error: metadataError } = compileMetadata(
            chunk.metadataEntries
          );
          if (metadataError) {
            throw new Error(`Chunk ${chunk.id}: ${metadataError}`);
          }
          const language = chunk.language.trim().toLowerCase();
          return {
            content,
            language: language || undefined,
            tags: parseTags(chunk.tags),
            metadata,
          };
        })
        .filter((chunk): chunk is NonNullable<typeof chunk> => chunk !== null);

      if (!payloadChunks.length) {
        throw new Error("Add at least one non-empty chunk before uploading");
      }

      const normalizedDefaultLanguage = defaultLanguage.trim().toLowerCase();
      const payload = {
        source,
        chunks: payloadChunks,
        default_language: normalizedDefaultLanguage || undefined,
        default_tags: parseTags(defaultTags),
      };
      const r = await KBAPI.upsert(payload);
      const summary = r.summary;
      setMsg(
        `Upserted: ${summary.created} new, ${summary.updated} updated, ${summary.skipped} skipped`
      );
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function onSearch(preserveMessage = false) {
    setErr(null);
    if (!preserveMessage) setMsg(null);
    setBusy(true);
    setResults([]);
    try {
      const r = await KBAPI.search({
        query: q,
        limit,
        source: searchSource || undefined,
        tags: parseTags(searchTags),
        language: searchLanguage || undefined,
        include_metadata: includeMetadata,
        include_archived: includeArchived,
      });
      setResults(r.results);
    } catch (e: any) {
      setErr(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  async function mutateChunk(action: () => Promise<void>) {
    setErr(null);
    setMsg(null);
    setBusy(true);
    try {
      await action();
      await onSearch(true);
    } catch (e: any) {
      setBusy(false);
      setErr(String(e.message || e));
    }
  }

  async function onArchive(hit: KBSearchHit, archived: boolean) {
    const payload: KBArchiveRequest = { ids: [hit.id], archived };
    await mutateChunk(async () => {
      await KBAPI.archive(payload);
      setMsg(archived ? "Chunk archived" : "Chunk restored");
    });
  }

  async function onDelete(hit: KBSearchHit) {
    await mutateChunk(async () => {
      await KBAPI.remove({ ids: [hit.id] });
      setMsg("Chunk deleted");
    });
  }

  async function onReindex(hit: KBSearchHit) {
    const payload: KBReindexRequest = { ids: [hit.id], include_archived: true };
    await mutateChunk(async () => {
      await KBAPI.reindex(payload);
      setMsg("Chunk reindexed");
    });
  }

  return (
    <div className="grid xl:grid-cols-2 gap-6">
      <div className="bg-white border rounded p-4 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Curate knowledge base</h2>
          <span className="text-xs text-slate-500">{chunkCount} chunk(s)</span>
        </div>
        <label className="text-sm">Source</label>
        <input
          className="w-full border rounded px-2 py-1"
          value={source}
          onChange={(e) => setSource(e.target.value)}
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <label className="text-sm flex flex-col">
            <span>Default language</span>
            <input
              className="border rounded px-2 py-1 mt-1"
              placeholder="en"
              value={defaultLanguage}
              onChange={(e) => setDefaultLanguage(e.target.value)}
            />
          </label>
          <label className="text-sm flex flex-col">
            <span>Default tags</span>
            <input
              className="border rounded px-2 py-1 mt-1"
              placeholder="faq, onboarding"
              value={defaultTags}
              onChange={(e) => setDefaultTags(e.target.value)}
            />
          </label>
        </div>
        <div className="space-y-4">
          {chunks.map((chunk) => {
            const trimmed = chunk.content.trim();
            const charCount = trimmed.length;
            const wordCount = trimmed ? trimmed.split(/\s+/).length : 0;
            const { value: metadataValue, error: metadataError } = compileMetadata(
              chunk.metadataEntries
            );
            const metadataPreview = metadataValue ?? {};

            return (
              <div key={chunk.id} className="border rounded p-3 space-y-3 bg-slate-50">
                <div className="flex justify-between items-center text-xs text-slate-500">
                  <span>Chunk {chunk.id}</span>
                  <button
                    className="text-red-600"
                    type="button"
                  onClick={() => removeChunk(chunk.id)}
                  disabled={chunks.length === 1}
                >
                  Remove
                </button>
              </div>
              <label className="text-xs uppercase tracking-wide text-slate-500">
                Content
              </label>
              <textarea
                className="w-full h-24 border rounded px-2 py-1"
                value={chunk.content}
                onChange={(e) => updateChunk(chunk.id, { content: e.target.value })}
              />
              <div className="flex flex-wrap gap-4 text-xs text-slate-500">
                <span>{charCount} characters</span>
                <span>{wordCount} words</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
                <label className="text-xs flex flex-col">
                  <span>Language</span>
                  <input
                    className="border rounded px-2 py-1 mt-1"
                    placeholder="en"
                    value={chunk.language}
                    onChange={(e) => updateChunk(chunk.id, { language: e.target.value })}
                  />
                </label>
                <label className="text-xs flex flex-col md:col-span-2">
                  <span>Tags (comma separated)</span>
                  <input
                    className="border rounded px-2 py-1 mt-1"
                    placeholder="faq, onboarding"
                    value={chunk.tags}
                    onChange={(e) => updateChunk(chunk.id, { tags: e.target.value })}
                  />
                </label>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs uppercase tracking-wide text-slate-500">
                    Metadata fields
                  </span>
                  <button
                    type="button"
                    className="text-xs text-blue-600"
                    onClick={() => addMetadataEntry(chunk.id)}
                  >
                    + Add field
                  </button>
                </div>
                {chunk.metadataEntries.length === 0 && (
                  <p className="text-xs text-slate-500">
                    Optional key/value pairs for ranking, quality scores or filters.
                  </p>
                )}
                <div className="space-y-2">
                  {chunk.metadataEntries.map((entry) => (
                    <div key={entry.id} className="grid grid-cols-6 gap-2 items-center">
                      <input
                        className="col-span-2 border rounded px-2 py-1 text-xs"
                        placeholder="quality_score"
                        value={entry.key}
                        onChange={(e) =>
                          updateMetadataEntry(chunk.id, entry.id, {
                            key: e.target.value,
                          })
                        }
                      />
                      <input
                        className="col-span-3 border rounded px-2 py-1 text-xs"
                        placeholder="0.9"
                        value={entry.value}
                        onChange={(e) =>
                          updateMetadataEntry(chunk.id, entry.id, {
                            value: e.target.value,
                          })
                        }
                      />
                      <button
                        type="button"
                        className="text-xs text-red-600"
                        onClick={() => removeMetadataEntry(chunk.id, entry.id)}
                      >
                        Remove
                      </button>
                    </div>
                  ))}
                </div>
                {metadataError && (
                  <div className="text-xs text-red-600">{metadataError}</div>
                )}
                <div className="bg-white border rounded p-2">
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <span>Preview</span>
                    <span>auto-updates</span>
                  </div>
                  <pre className="mt-1 text-xs text-slate-700 whitespace-pre-wrap break-words">
                    {JSON.stringify(metadataPreview, null, 2) || "{}"}
                  </pre>
                </div>
              </div>
            </div>
            );
          })}
          <button
            type="button"
            onClick={addChunk}
            className="px-3 py-2 rounded border border-dashed border-slate-400 text-slate-600"
          >
            + Add chunk
          </button>
        </div>
        <button
          disabled={busy}
          onClick={onUpsert}
          className="px-3 py-2 rounded bg-emerald-600 text-white disabled:opacity-60"
        >
          Upload
        </button>
        {msg && <div className="text-emerald-700 text-sm">{msg}</div>}
        {err && <div className="text-red-600 text-sm">{err}</div>}
      </div>

      <div className="bg-white border rounded p-4 space-y-4">
        <h2 className="font-semibold">Search & manage KB</h2>
        <input
          className="w-full border rounded px-2 py-1"
          placeholder="query..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          <label className="text-sm flex flex-col">
            <span>Limit</span>
            <input
              type="number"
              min={1}
              max={50}
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
        <div className="flex flex-wrap items-center gap-4 text-sm">
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              className="rounded border"
              checked={includeMetadata}
              onChange={(e) => setIncludeMetadata(e.target.checked)}
            />
            Include metadata
          </label>
          <label className="inline-flex items-center gap-2">
            <input
              type="checkbox"
              className="rounded border"
              checked={includeArchived}
              onChange={(e) => setIncludeArchived(e.target.checked)}
            />
            Include archived
          </label>
        </div>
        <button
          type="button"
          disabled={busy}
          onClick={() => {
            void onSearch();
          }}
          className="px-3 py-2 rounded bg-blue-600 text-white disabled:opacity-60"
        >
          Search
        </button>
        <ul className="divide-y">
          {results.map((r) => {
            const meta = (r.metadata || {}) as Record<string, unknown>;
            const tags = Array.isArray(meta.tags)
              ? (meta.tags as unknown[]).map((tag) => String(tag))
              : [];
            const charCount = meta.char_count as number | string | undefined;
            const wordCount = meta.word_count as number | string | undefined;
            const language = typeof meta.language === "string" ? meta.language : undefined;

            return (
              <li key={r.id} className="py-3 space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <div className="flex flex-wrap gap-2">
                    <span>{r.source}</span>
                    <span>score {r.score.toFixed(4)}</span>
                    <span>sim {r.similarity.toFixed(4)}</span>
                    {r.updated_at && <span>updated {new Date(r.updated_at).toLocaleString()}</span>}
                    {r.archived && <span className="text-orange-600">archived</span>}
                  </div>
                  <div className="flex gap-2">
                    <button
                      type="button"
                      className="text-xs text-blue-600"
                      onClick={() => onReindex(r)}
                      disabled={busy}
                    >
                      Reindex
                    </button>
                    <button
                      type="button"
                      className="text-xs text-amber-600"
                      onClick={() => onArchive(r, !r.archived)}
                      disabled={busy}
                    >
                      {r.archived ? "Restore" : "Archive"}
                    </button>
                    <button
                      type="button"
                      className="text-xs text-red-600"
                      onClick={() => onDelete(r)}
                      disabled={busy}
                    >
                      Delete
                    </button>
                  </div>
                </div>
                <div className="whitespace-pre-wrap">{r.chunk}</div>
                {includeMetadata && (
                  <div className="text-xs text-slate-500 space-y-1">
                    {language && <div>language: {language}</div>}
                    {tags.length > 0 && <div>tags: {tags.join(", ")}</div>}
                    <div className="flex flex-wrap gap-3">
                      <span>chars: {String(charCount ?? "-")}</span>
                      <span>words: {String(wordCount ?? "-")}</span>
                      {typeof meta.quality_score !== "undefined" && (
                        <span>quality: {String(meta.quality_score)}</span>
                      )}
                    </div>
                  </div>
                )}
              </li>
            );
          })}
          {results.length === 0 && (
            <li className="text-sm text-slate-500 py-6 text-center">No results yet</li>
          )}
        </ul>
      </div>
    </div>
  );
}
