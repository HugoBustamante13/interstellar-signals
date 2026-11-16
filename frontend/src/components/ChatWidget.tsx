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

  return (
    <>
      {/* Botón flotante */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Open health assistant"
        className="fixed bottom-5 right-5 z-50 w-14 h-14 rounded-full bg-sky-600 hover:bg-sky-500 shadow-lg flex items-center justify-center text-2xl"
      >
        {open ? "✕" : "💬"}
        {!open && alertCount > 0 && (
          <span
            className="absolute -top-1 -right-1 min-w-5 h-5 px-1 rounded-full text-xs font-bold flex items-center justify-center text-slate-900"
            style={{ backgroundColor: hasCritical ? "#ef4444" : "#f59e0b" }}
          >
            {alertCount}
          </span>
        )}
      </button>

      {/* Panel */}
      {open && (
        <div className="fixed bottom-24 right-5 z-50 w-[92vw] max-w-sm h-[70vh] max-h-[560px] flex flex-col rounded-2xl border border-slate-700 bg-slate-900 shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="px-4 py-3 bg-slate-800 border-b border-slate-700">
            <div className="flex items-center justify-between">
              <span className="font-semibold">🩺 Health assistant</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700 text-slate-300">
                {status?.llm_available ? "AI + offline" : "offline"}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Helps you self-assess. Not medical advice.
            </p>
          </div>

          {/* Proactive alert banner */}
          {alertCount > 0 && (
            <div
              className="px-4 py-2 text-xs border-b border-slate-700"
              style={{ backgroundColor: hasCritical ? "#7f1d1d" : "#78350f" }}
            >
              <span className="font-semibold">
                {hasCritical ? "🔴" : "🟡"} {alertCount} indicator(s) outside green:
              </span>{" "}
              {status?.alerts.map((a) => a.label).join(", ")}.{" "}
              <button className="underline" onClick={() => send("What should I do?")}>
                What should I do?
              </button>
            </div>
          )}

          {backendDown && (
            <div className="px-4 py-2 text-xs bg-amber-900/40 text-amber-300 border-b border-slate-700">
              Backend unavailable. Start uvicorn in /backend to use the assistant.
            </div>
          )}

          {/* Mensajes */}
          <div ref={listRef} className="flex-1 overflow-y-auto px-3 py-3 space-y-3">
            {messages.map((m, i) => (
              <div key={i} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
                <div
                  className={
                    "max-w-[85%] rounded-2xl px-3 py-2 text-sm " +
                    (m.role === "user"
                      ? "bg-sky-600 text-white rounded-br-sm"
                      : "bg-slate-800 text-slate-200 rounded-bl-sm")
                  }
                >
                  <div className="space-y-0.5">{renderText(m.content)}</div>
                  {m.role === "assistant" && m.source === "llm" && (
                    <div className="mt-1 text-[10px] text-slate-500">written with AI</div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-slate-800 text-slate-400 rounded-2xl rounded-bl-sm px-3 py-2 text-sm">
                  typing…
                </div>
              </div>
            )}
          </div>

          {/* Preguntas rápidas */}
          {status?.quick_questions && messages.length <= 1 && (
            <div className="px-3 pb-2 flex flex-wrap gap-1.5">
              {status.quick_questions.map((q) => (
                <button
                  key={q}
                  onClick={() => send(q)}
                  className="text-xs px-2.5 py-1 rounded-full bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300"
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
            className="p-2 border-t border-slate-700 flex gap-2"
          >
            <div className="flex-1 relative bg-slate-800 border border-slate-700 rounded-lg overflow-hidden focus-within:border-sky-500">
              {/* Ghost layer: typed text is transparent (reserves width), suffix is gray. */}
              <div
                aria-hidden
                className="absolute inset-0 px-3 py-2 text-sm whitespace-pre overflow-hidden pointer-events-none"
              >
                <span className="text-transparent">{input}</span>
                <span className="text-slate-500">{ghost}</span>
              </div>
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleInputKeyDown}
                placeholder="Type your question…"
                className="relative w-full bg-transparent px-3 py-2 text-sm outline-none"
              />
            </div>
            {ghost && (
              <span className="self-center text-[10px] text-slate-500 whitespace-nowrap">
                → to complete
              </span>
            )}
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white px-3 py-2 rounded-lg text-sm font-medium"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </>
  );
}
