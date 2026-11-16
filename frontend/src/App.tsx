import { useEffect, useState } from "react";
import IndicatorCard from "./components/IndicatorCard";
import HistoryChart from "./components/HistoryChart";
import BodyMap, { BODY_PARTS, BodyPart } from "./components/BodyMap";
import ChatWidget from "./components/ChatWidget";
import { THRESHOLDS, evaluate, Status } from "./data/thresholds";

const INDICATOR_KEYS = Object.keys(THRESHOLDS);

type FormState = Record<string, number | null>;

export default function App() {
  const [form, setForm] = useState<FormState>(
    Object.fromEntries(INDICATOR_KEYS.map((k) => [k, null]))
  );
  const [records, setRecords] = useState<any[]>([]);
  const [selectedPart, setSelectedPart] = useState<BodyPart | null>(null);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);

  async function loadRecords() {
    try {
      const res = await fetch("/api/records");
      if (!res.ok) throw new Error("API no disponible");
      setRecords(await res.json());
      setApiError(null);
    } catch (e) {
      setApiError(
        "No se pudo conectar al backend (¿está corriendo `uvicorn main:app --reload` en /backend?). Trabajando solo en modo local."
      );
    }
  }

  useEffect(() => {
    loadRecords();
  }, []);

  const statusByIndicator: Record<string, Status | null> = Object.fromEntries(
    INDICATOR_KEYS.map((k) => [k, form[k] !== null ? evaluate(k, form[k] as number) : null])
  );

  async function handleSubmit() {
    // Solo se envían los indicadores con dato; los vacíos se omiten.
    const payload = Object.fromEntries(
      INDICATOR_KEYS.filter((k) => form[k] !== null).map((k) => [k, form[k]])
    );
    if (Object.keys(payload).length === 0) {
      setRecommendations(["Ingresa al menos un indicador antes de registrar."]);
      return;
    }
    try {
      const res = await fetch("/api/records", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error();
      const result = await res.json();
      const recs = Object.values(result.assessment || {})
        .map((a: any) => a.recommendation)
        .filter(Boolean);
      setRecommendations(recs);
      loadRecords();
    } catch {
      // Modo sin backend: solo evaluamos localmente
      const recs = INDICATOR_KEYS.filter((k) => form[k] !== null && statusByIndicator[k] !== "normal")
        .map((k) => `${THRESHOLDS[k].label}: fuera de rango, considera reposo y volver a medir.`);
      setRecommendations(recs);
    }
  }

  return (
    <div className="min-h-screen p-6 max-w-5xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">🚀 Astronaut Health Monitor</h1>
        <p className="text-slate-400 text-sm">
          Registra tus indicadores de salud y evalúa tu estado a simple vista.
        </p>
        {apiError && (
          <p className="text-amber-400 text-xs mt-2">{apiError}</p>
        )}
      </header>

      <div className="grid md:grid-cols-[220px_1fr] gap-8">
        <div>
          <BodyMap
            statusByIndicator={statusByIndicator}
            onSelectPart={setSelectedPart}
            selectedPart={selectedPart?.id ?? null}
          />
          {selectedPart && (
            <div className="mt-4 text-sm bg-slate-900 rounded-lg p-3">
              <p className="font-medium">{selectedPart.label}</p>
              <p className="text-slate-400">
                Indicadores: {selectedPart.indicators.map((i) => THRESHOLDS[i].label).join(", ")}
              </p>
            </div>
          )}
          <div className="mt-4 text-xs text-slate-500 space-y-1">
            <p><span className="inline-block w-3 h-3 rounded-full bg-[#22c55e] mr-1" /> Normal</p>
            <p><span className="inline-block w-3 h-3 rounded-full bg-[#f59e0b] mr-1" /> Atención</p>
            <p><span className="inline-block w-3 h-3 rounded-full bg-[#ef4444] mr-1" /> Crítico</p>
          </div>
        </div>

        <div>
          <div className="grid sm:grid-cols-2 gap-3 mb-4">
            {INDICATOR_KEYS.map((key) => (
              <IndicatorCard
                key={key}
                indicatorKey={key}
                value={form[key]}
                onChange={(v) => setForm((f) => ({ ...f, [key]: v }))}
              />
            ))}
          </div>

          <button
            onClick={handleSubmit}
            className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg font-medium"
          >
            Registrar medición
          </button>

          {recommendations.length > 0 && (
            <div className="mt-4 bg-slate-900 border border-amber-500 rounded-lg p-3 space-y-1">
              <p className="font-medium text-amber-400">Recomendaciones</p>
              {recommendations.map((r, i) => (
                <p key={i} className="text-sm text-slate-300">• {r}</p>
              ))}
            </div>
          )}

          <div className="mt-8 grid sm:grid-cols-2 gap-6">
            {INDICATOR_KEYS.map((key) => (
              <HistoryChart key={key} records={records} indicatorKey={key} />
            ))}
          </div>
        </div>
      </div>

      <ChatWidget />
    </div>
  );
}
