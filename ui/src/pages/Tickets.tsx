import { useEffect, useState } from "react";
import { AgentAPI, TicketsAPI, Ticket, Message } from "@/lib/api";

export default function Tickets() {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [selected, setSelected] = useState<Ticket|undefined>();
  const [msgs, setMsgs] = useState<Message[]>([]);
  const [newTitle, setNewTitle] = useState("");
  const [newMsg, setNewMsg] = useState("");
  const [agentQ, setAgentQ] = useState("Опиши шаги решения");
  const [err, setErr] = useState<string|null>(null);
  const [busy, setBusy] = useState(false);

  async function loadTickets() {
    setErr(null);
    try { setTickets(await TicketsAPI.list()); }
    catch (e:any) { setErr(String(e.message||e)); }
  }
  async function loadMessages(id:number) {
    setErr(null);
    try { setMsgs(await TicketsAPI.messages(id)); }
    catch (e:any) { setErr(String(e.message||e)); }
  }

  useEffect(()=>{ loadTickets(); }, []);
  useEffect(()=>{ if (selected) loadMessages(selected.id); }, [selected?.id]);

  async function createTicket() {
    setBusy(true); setErr(null);
    try {
      const t = await TicketsAPI.create(newTitle || "New ticket");
      setTickets([t, ...tickets]);
      setSelected(t);
      setNewTitle("");
    } catch(e:any){ setErr(String(e.message||e)); }
    finally { setBusy(false); }
  }

  async function sendMessage() {
    if (!selected) return;
    setBusy(true); setErr(null);
    try {
      const m = await TicketsAPI.addMessage(selected.id, "user", newMsg);
      setMsgs([...msgs, m]); setNewMsg("");
    } catch(e:any){ setErr(String(e.message||e)); }
    finally { setBusy(false); }
  }

  async function askAgent() {
    if (!selected) return;
    setBusy(true); setErr(null);
    try {
      await AgentAPI.answerTicket(selected.id, agentQ, true, 5, 0.2);
      await loadMessages(selected.id);
    } catch(e:any){ setErr(String(e.message||e)); }
    finally { setBusy(false); }
  }

  return (
    <div className="grid md:grid-cols-3 gap-6">
      <div className="bg-white border rounded p-4 space-y-3 md:col-span-1">
        <div className="flex gap-2">
          <input className="flex-1 border rounded px-2 py-1" placeholder="Ticket title"
                 value={newTitle} onChange={e=>setNewTitle(e.target.value)} />
          <button disabled={busy} className="px-3 py-1 rounded bg-blue-600 text-white disabled:opacity-60"
                  onClick={createTicket}>Create</button>
        </div>
        <ul className="divide-y max-h-[60vh] overflow-auto">
          {tickets.map(t=>(
            <li key={t.id}
                className={"py-2 cursor-pointer "+(selected?.id===t.id?"font-semibold":"")}
                onClick={()=>setSelected(t)}>
              <div className="text-sm">{t.title}</div>
              <div className="text-xs text-slate-500">{t.status}</div>
            </li>
          ))}
        </ul>
      </div>

      <div className="bg-white border rounded p-4 space-y-3 md:col-span-2">
        {selected ? (
          <>
            <h2 className="font-semibold">Ticket #{selected.id}: {selected.title}</h2>
            <div className="border rounded p-3 h-[40vh] overflow-auto bg-slate-50">
              {msgs.map(m=>(
                <div key={m.id} className="mb-3">
                  <div className="text-xs text-slate-500">{m.role}</div>
                  <div className="whitespace-pre-wrap">{m.content}</div>
                </div>
              ))}
            </div>
            <div className="flex gap-2">
              <input className="flex-1 border rounded px-2 py-1" placeholder="Ваше сообщение…"
                     value={newMsg} onChange={e=>setNewMsg(e.target.value)} />
              <button disabled={busy || !newMsg.trim()} className="px-3 py-1 rounded bg-emerald-600 text-white disabled:opacity-60"
                      onClick={sendMessage}>Send</button>
            </div>
            <div className="border-t pt-3">
              <label className="block text-sm mb-1">Вопрос агенту</label>
              <div className="flex gap-2">
                <input className="flex-1 border rounded px-2 py-1"
                       value={agentQ} onChange={e=>setAgentQ(e.target.value)} />
                <button disabled={busy} className="px-3 py-1 rounded bg-indigo-600 text-white disabled:opacity-60"
                        onClick={askAgent}>Ask Agent</button>
              </div>
            </div>
          </>
        ) : (
          <div className="text-slate-500">Выберите тикет</div>
        )}
        {err && <div className="text-red-600 text-sm mt-2">{err}</div>}
      </div>
    </div>
  );
}
