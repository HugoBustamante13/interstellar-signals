import { useEffect, useRef, useState, type KeyboardEvent } from "react";

// On-board health assistant. Floating widget that talks to the backend (/api/chat).
// The backend answers in hybrid mode: offline rule-based core + optional LLM layer.
// Honesty note (challenge SI rule): the UI states that AI is used and that it is
// not medical advice. The bot speaks English; the rest of the app is in Spanish.

const ASTRONAUT_ID = "default";

// Ghost-text autocomplete: as you type, the best-matching phrase is suggested in
// gray; Right Arrow (or Tab) accepts it. Purely client-side, matched by prefix.
const SUGGESTIONS = [
  "How am I doing?",
  "What should I do if something is red?",
  "What is SpO2?",
  "What is heart rate?",
  "What is blood pressure?",
  "What is glucose?",
  "What is body temperature?",
  "What is mood?",
  "What is the WHO-5?",
  "What is the KSS?",
  "How do I measure blood pressure?",
  "How do I measure SpO2?",
  "How do I measure temperature?",
  "How do I log a measurement?",
  "How does the traffic light work?",
  "What are the 5 hazards?",
  "Tell me about sleep",
  "When should I escalate to the flight surgeon?",
  "Give me a gamification tip",
  "Is this validated?",
];

type Role = "user" | "assistant";
interface Msg {
  role: Role;
  content: string;
  source?: "llm" | "rules";
}
interface Alert {
  indicator: string;
  label: string;
  value: number;
  unit: string;
  status: "attention" | "critical";
  status_en: string;
  recommendation: string | null;
}
interface StatusResp {
  greeting: string;
  alerts: Alert[];
  quick_questions: string[];
  disclaimer: string;
  llm_available: boolean;
}

// Convierte **negritas** y saltos de línea del backend a JSX simple.
function renderText(text: string) {
  return text.split("\n").map((line, i) => {
    const parts = line.split(/(\*\*[^*]+\*\*)/g).map((p, j) =>
      p.startsWith("**") && p.endsWith("**") ? (
        <strong key={j}>{p.slice(2, -2)}</strong>
      ) : (
        <span key={j}>{p}</span>
      )
    );
    return (
      <p key={i} className={line.trim() === "" ? "h-2" : ""}>
        {parts}
      </p>
    );
  });
}

// Identidad del asistente: una traza de ECG (coherente con "monitoreo de salud").
function IconPulse({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor"
      strokeWidth={1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M1.5 12h4.2l1.8-5 3 10 2.1-6 1.3 1h6.6" />
    </svg>
  );
}
function IconClose({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor"
      strokeWidth={2} strokeLinecap="round">
      <path d="M6 6l12 12M18 6L6 18" />
    </svg>
  );
}
function IconSend({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} fill="currentColor">
      <path d="M3.4 20.4l17.4-7.5a1 1 0 000-1.84L3.4 3.6a1 1 0 00-1.38 1.17L4 11l10 1-10 1-1.96 6.23a1 1 0 001.36 1.17z" />
    </svg>
  );
}

// Animaciones del widget (inyectadas una vez). Respetan prefers-reduced-motion.
const WIDGET_CSS = `
@keyframes cw-panel-in { from { opacity:0; transform: translateY(14px) scale(.95); } to { opacity:1; transform: none; } }
@keyframes cw-msg-in { from { opacity:0; transform: translateY(7px); } to { opacity:1; transform: none; } }
@keyframes cw-glow { 0%,100% { box-shadow: 0 6px 20px -6px rgba(14,165,233,.5), 0 0 0 0 rgba(56,189,248,.0); } 50% { box-shadow: 0 6px 24px -4px rgba(14,165,233,.7), 0 0 0 6px rgba(56,189,248,.08); } }
@keyframes cw-trace { 0% { stroke-dashoffset: 46; } 55% { stroke-dashoffset: 0; } 100% { stroke-dashoffset: 0; } }
@keyframes cw-dot { 0%,80%,100% { transform: translateY(0); opacity:.5; } 40% { transform: translateY(-3px); opacity:1; } }
.cw-panel { animation: cw-panel-in .24s cubic-bezier(.16,1,.3,1); transform-origin: bottom right; }
.cw-msg { animation: cw-msg-in .22s ease-out; }
.cw-glow { animation: cw-glow 3.2s ease-in-out infinite; }
.cw-trace path { stroke-dasharray: 46; animation: cw-trace 2.6s ease-in-out infinite; }
.cw-typing span { display:inline-block; width:6px; height:6px; border-radius:9999px; background:#64748b; animation: cw-dot 1.1s ease-in-out infinite; }
.cw-typing span:nth-child(2){ animation-delay:.15s; } .cw-typing span:nth-child(3){ animation-delay:.3s; }
@media (prefers-reduced-motion: reduce) {
  .cw-panel,.cw-msg,.cw-glow,.cw-typing span { animation: none !important; }
  .cw-trace path { animation: none !important; stroke-dashoffset: 0 !important; }
}
`;

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [status, setStatus] = useState<StatusResp | null>(null);
  const [backendDown, setBackendDown] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);

  const alertCount = status?.alerts.length ?? 0;
  const hasCritical = status?.alerts.some((a) => a.status === "critical") ?? false;

  // Ghost-text suggestion for the current input (prefix match, case-insensitive).
  const suggestion =
    input.length >= 2
      ? SUGGESTIONS.find(
          (s) => s.toLowerCase().startsWith(input.toLowerCase()) && s.length > input.length
        )
      : undefined;
  const ghost = suggestion ? suggestion.slice(input.length) : "";

  function handleInputKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (!suggestion) return;
    const atEnd = e.currentTarget.selectionStart === input.length;
    if (e.key === "Tab" || (e.key === "ArrowRight" && atEnd)) {
      e.preventDefault();
      setInput(suggestion);
    }
  }

  async function loadStatus() {
    try {
      const res = await fetch(`/api/chat/status?astronaut_id=${ASTRONAUT_ID}`);
      if (!res.ok) throw new Error();
      setStatus(await res.json());
      setBackendDown(false);
    } catch {
      setBackendDown(true);
    }
  }

  // Al montar y cada 30 s: refresca estado/alertas para avisar proactivamente.
  useEffect(() => {
    loadStatus();
    const id = setInterval(loadStatus, 30000);
    return () => clearInterval(id);
  }, []);

  // On first open, seed the assistant's greeting.
  useEffect(() => {
    if (open && messages.length === 0 && status) {
      setMessages([{ role: "assistant", content: status.greeting, source: "rules" }]);
    }
  }, [open, status]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  async function send(text: string) {
    const content = text.trim();
    if (!content || sending) return;
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((m) => [...m, { role: "user", content }]);
    setInput("");
    setSending(true);
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: content, astronaut_id: ASTRONAUT_ID, history }),
      });
      if (!res.ok) throw new Error();
      const data = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: data.reply, source: data.source }]);
      if (data.alerts) setStatus((s) => (s ? { ...s, alerts: data.alerts } : s));
    } catch {
      setMessages((m) => [
        ...m,
        {
          role: "assistant",
          content:
            "I couldn't reach the assistant. Make sure the backend is running (uvicorn main:app --reload in /backend).",
          source: "rules",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  // Vital sign for the status dot: green when all data is fine, amber/red on alert.
  const signalColor = backendDown
    ? "#64748b"
    : alertCount > 0
    ? hasCritical
      ? "#ef4444"
      : "#f59e0b"
    : "#22c55e";

  return (
    <>
      <style>{WIDGET_CSS}</style>

      {/* Floating launcher: a vitals monitor, not a generic chat bubble. */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Close health assistant" : "Open health assistant"}
        aria-expanded={open}
        className={
          "fixed bottom-5 right-5 z-50 w-14 h-14 rounded-full flex items-center justify-center text-white " +
          "bg-gradient-to-br from-cyan-500 to-sky-600 ring-1 ring-cyan-300/30 transition-transform duration-200 " +
          "hover:scale-105 active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300 " +
          (open ? "" : "cw-glow")
        }
      >
        {open ? (
          <IconClose className="w-6 h-6" />
        ) : (
          <IconPulse className="w-7 h-7 cw-trace drop-shadow" />
        )}
        {!open && alertCount > 0 && (
          <span className="absolute -top-0.5 -right-0.5 flex h-5 w-5">
            <span
              className="absolute inline-flex h-full w-full rounded-full opacity-60 animate-ping"
              style={{ backgroundColor: hasCritical ? "#ef4444" : "#f59e0b" }}
            />
            <span
              className="relative inline-flex h-5 w-5 items-center justify-center rounded-full text-[11px] font-bold text-slate-950 ring-2 ring-slate-900"
              style={{ backgroundColor: hasCritical ? "#ef4444" : "#f59e0b" }}
            >
              {alertCount}
            </span>
          </span>
        )}
      </button>

      {/* Panel */}
      {open && (
        <div className="cw-panel fixed bottom-24 right-5 z-50 w-[92vw] max-w-sm h-[72vh] max-h-[580px] flex flex-col rounded-2xl border border-slate-700/70 bg-slate-900 shadow-[0_24px_60px_-15px_rgba(2,6,23,.8)] overflow-hidden">
          {/* Header */}
          <div className="relative px-4 pt-3.5 pb-3 bg-gradient-to-b from-slate-800 to-slate-900 border-b border-slate-700/70">
            <div className="absolute inset-x-0 top-0 h-0.5 bg-gradient-to-r from-cyan-400/0 via-cyan-400/80 to-sky-500/0" />
            <div className="flex items-center gap-3">
              <div className="relative shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-sky-600 flex items-center justify-center text-white">
                <IconPulse className="w-6 h-6 cw-trace" />
                <span
                  className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full ring-2 ring-slate-900"
                  style={{ backgroundColor: signalColor }}
                />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <h2 className="font-semibold text-slate-100 leading-tight">Health assistant</h2>
                  <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-slate-700/70 text-cyan-200 border border-cyan-400/20">
                    {status?.llm_available ? "AI + offline" : "offline"}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-tight truncate">
                  Here to help you read your vitals.
                </p>
              </div>
              <button
                onClick={() => setOpen(false)}
                aria-label="Close"
                className="shrink-0 p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-700/60 focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
              >
                <IconClose className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Proactive alert banner */}
          {alertCount > 0 && (
            <div
              className="flex items-start gap-2.5 px-4 py-2.5 border-b border-slate-700/70"
              style={{
                background: hasCritical
                  ? "linear-gradient(90deg, rgba(239,68,68,.16), rgba(239,68,68,.04))"
                  : "linear-gradient(90deg, rgba(245,158,11,.16), rgba(245,158,11,.04))",
              }}
            >
              <span
                className="mt-1 shrink-0 w-2 h-2 rounded-full"
                style={{ backgroundColor: hasCritical ? "#ef4444" : "#f59e0b" }}
              />
              <div className="text-xs text-slate-200 leading-snug">
                <span className="font-semibold">
                  {alertCount} indicator{alertCount > 1 ? "s" : ""} outside green:
                </span>{" "}
                {status?.alerts.map((a) => a.label).join(", ")}.{" "}
                <button
                  className="font-medium underline decoration-dotted underline-offset-2 hover:text-white"
                  style={{ color: hasCritical ? "#fca5a5" : "#fcd34d" }}
                  onClick={() => send("What should I do?")}
                >
                  What should I do?
                </button>
              </div>
            </div>
          )}

          {backendDown && (
            <div className="px-4 py-2 text-xs bg-amber-900/30 text-amber-300 border-b border-slate-700/70">
              Backend unavailable. Start uvicorn in /backend to use the assistant.
            </div>
          )}

          {/* Messages */}
          <div ref={listRef} className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
            {messages.map((m, i) => (
              <div
                key={i}
                className={"cw-msg flex items-end gap-2 " + (m.role === "user" ? "justify-end" : "justify-start")}
              >
                {m.role === "assistant" && (
                  <div className="shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-cyan-500 to-sky-600 flex items-center justify-center text-white">
                    <IconPulse className="w-4 h-4" />
                  </div>
                )}
                <div
                  className={
                    "max-w-[82%] px-3.5 py-2 text-sm leading-relaxed " +
                    (m.role === "user"
                      ? "bg-gradient-to-br from-cyan-500 to-sky-600 text-white rounded-2xl rounded-br-md shadow-sm"
                      : "bg-slate-800/90 text-slate-100 rounded-2xl rounded-bl-md border border-slate-700/60")
                  }
                >
                  <div className="space-y-0.5">{renderText(m.content)}</div>
                  {m.role === "assistant" && m.source === "llm" && (
                    <div className="mt-1.5 flex items-center gap-1 text-[10px] text-cyan-300/80">
                      <IconPulse className="w-3 h-3" /> written with AI
                    </div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="cw-msg flex items-end gap-2 justify-start">
                <div className="shrink-0 w-6 h-6 rounded-full bg-gradient-to-br from-cyan-500 to-sky-600 flex items-center justify-center text-white">
                  <IconPulse className="w-4 h-4" />
                </div>
                <div className="cw-typing bg-slate-800/90 border border-slate-700/60 rounded-2xl rounded-bl-md px-3.5 py-3 flex items-center gap-1">
                  <span /><span /><span />
                </div>
              </div>
            )}
          </div>

          {/* Quick questions */}
          {status?.quick_questions && messages.length <= 1 && (
            <div className="px-3 pb-2 flex flex-wrap gap-1.5">
              {status.quick_questions.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-xs px-3 py-1.5 rounded-full bg-slate-800/80 hover:bg-slate-700 hover:border-cyan-400/40 border border-slate-700/70 text-slate-300 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
            className="px-2.5 pt-2 pb-2.5 border-t border-slate-700/70 bg-slate-900"
          >
            <div className="flex items-center gap-2">
              <div className="flex-1 relative bg-slate-800 border border-slate-700 rounded-xl overflow-hidden focus-within:border-cyan-400/60 focus-within:ring-1 focus-within:ring-cyan-400/30 transition-colors">
                {/* Ghost layer: typed text is transparent (reserves width), suffix is gray. */}
                <div
                  aria-hidden
                  className="absolute inset-0 px-3.5 py-2.5 text-sm whitespace-pre overflow-hidden pointer-events-none"
                >
                  <span className="text-transparent">{input}</span>
                  <span className="text-slate-500">{ghost}</span>
                  {ghost && (
                    <span className="ml-1 align-middle text-[9px] text-slate-600 rounded border border-slate-600 px-1">
                      →
                    </span>
                  )}
                </div>
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleInputKeyDown}
                  placeholder="Type your question…"
                  className="relative w-full bg-transparent px-3.5 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 outline-none"
                />
              </div>
              <button
                type="submit"
                disabled={sending || !input.trim()}
                aria-label="Send"
                className="shrink-0 w-10 h-10 rounded-xl flex items-center justify-center text-white bg-gradient-to-br from-cyan-500 to-sky-600 disabled:opacity-40 disabled:cursor-not-allowed hover:brightness-110 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300"
              >
                <IconSend className="w-4 h-4" />
              </button>
            </div>
            <p className="mt-1.5 px-1 text-[10px] text-slate-500">
              Not medical advice. Demo data is synthetic.
            </p>
          </form>
        </div>
      )}
    </>
  );
}
