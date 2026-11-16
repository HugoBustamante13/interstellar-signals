import { useEffect, useRef, useState } from "react";

// Asistente de salud a bordo. Widget flotante que habla con el backend (/api/chat).
// El backend responde en modo híbrido: núcleo offline por reglas + capa LLM opcional.
// Nota de honestidad (regla de SI del reto): se avisa en la UI que hay IA y que no
// es consejo médico.

const ASTRONAUT_ID = "default";

type Role = "user" | "assistant";
interface Msg {
  role: Role;
  content: string;
  source?: "llm" | "reglas";
}
interface Alert {
  indicator: string;
  label: string;
  value: number;
  unit: string;
  status: "attention" | "critical";
  status_es: string;
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

  // Al abrir por primera vez, siembra el saludo del asistente.
  useEffect(() => {
    if (open && messages.length === 0 && status) {
      setMessages([{ role: "assistant", content: status.greeting, source: "reglas" }]);
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
            "No pude conectar con el asistente. Revisa que el backend esté corriendo (uvicorn main:app --reload en /backend).",
          source: "reglas",
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
        aria-label="Abrir asistente de salud"
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
              <span className="font-semibold">🩺 Asistente de salud</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-700 text-slate-300">
                {status?.llm_available ? "IA + offline" : "offline"}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Te ayuda a autoevaluarte. No es consejo médico.
            </p>
          </div>

          {/* Banner de alerta proactivo */}
          {alertCount > 0 && (
            <div
              className="px-4 py-2 text-xs border-b border-slate-700"
              style={{ backgroundColor: hasCritical ? "#7f1d1d" : "#78350f" }}
            >
              <span className="font-semibold">
                {hasCritical ? "🔴" : "🟡"} {alertCount} indicador(es) fuera de verde:
              </span>{" "}
              {status?.alerts.map((a) => a.label).join(", ")}.{" "}
              <button className="underline" onClick={() => send("¿Qué hago?")}>
                ¿Qué hago?
              </button>
            </div>
          )}

          {backendDown && (
            <div className="px-4 py-2 text-xs bg-amber-900/40 text-amber-300 border-b border-slate-700">
              Backend no disponible. Inicia uvicorn en /backend para usar el asistente.
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
                    <div className="mt-1 text-[10px] text-slate-500">redactado con IA</div>
                  )}
                </div>
              </div>
            ))}
            {sending && (
              <div className="flex justify-start">
                <div className="bg-slate-800 text-slate-400 rounded-2xl rounded-bl-sm px-3 py-2 text-sm">
                  escribiendo…
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
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Escribe tu pregunta…"
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-sky-500"
            />
            <button
              type="submit"
              disabled={sending || !input.trim()}
              className="bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white px-3 py-2 rounded-lg text-sm font-medium"
            >
              Enviar
            </button>
          </form>
        </div>
      )}
    </>
  );
}
