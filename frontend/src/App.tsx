import { useCallback, useEffect, useMemo, useState } from "react";
import BodyMap, { BODY_PARTS, BodyPart } from "./components/BodyMap";
import HistoryChart from "./components/HistoryChart";
import IndicatorCard from "./components/IndicatorCard";
import { api, ApiError, Astronaut, StatusResponse } from "./data/api";
import {
  evaluateAbsolute, IndicatorKey, Indicators, KEYS, LOCAL_INDICATORS, LOCAL_META, Meta, NODATA_COLOR, Status, STATUS_COLOR, STATUS_LABEL,
} from "./data/indicators";

type FormState = Record<IndicatorKey, number | null>;
const EMPTY: FormState = Object.fromEntries(KEYS.map((k) => [k, null])) as FormState;

const MODE_TEXT: Record<StatusResponse["evaluation_mode"], string> = {
  prevuelo: "Prevuelo: solo límites clínicos mientras se construye tu línea base.",
  adaptacion_inicial: "Días 1–14 de vuelo: el cuerpo se adapta, así que solo cuentan los límites clínicos.",
  linea_base: "Cada valor se compara con tu banda personal (28 días) y con los límites clínicos.",
};

function Pill({ status }: { status: Status | null }) {
  return (
    <span className="text-xs px-2 py-0.5 rounded-full font-medium"
      style={{ backgroundColor: status ? STATUS_COLOR[status] : NODATA_COLOR, color: "#0f172a" }}>
      {status ? STATUS_LABEL[status] : "Sin dato"}
    </span>
  );
}

export default function App() {
  const [indicators, setIndicators] = useState<Indicators>(LOCAL_INDICATORS);
  const [meta, setMeta] = useState<Meta>(LOCAL_META);
  const [backendOk, setBackendOk] = useState<boolean | null>(null);
  const [astronauts, setAstronauts] = useState<Astronaut[]>([]);
  const [astronautId, setAstronautId] = useState<string>("default");
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [form, setForm] = useState<FormState>(EMPTY);
  const [selectedPart, setSelectedPart] = useState<BodyPart | null>(null);
  const [chartKey, setChartKey] = useState<IndicatorKey>("bp_sys");
  const [refresh, setRefresh] = useState(0);
  const [message, setMessage] = useState<string | null>(null);
  const [localRecs, setLocalRecs] = useState<string[]>([]);

  // al arrancar: límites desde la config del backend (sobrescriben la copia local) y lista de astronautas
  useEffect(() => {
    Promise.all([api.indicators(), api.astronauts()])
      .then(([ind, list]) => {
        const { _meta, ...rest } = ind;
        setIndicators(rest as Indicators);
        setMeta(_meta);
        setAstronauts(list);
        const sim = list.find((a) => a.astronaut_id.startsWith("SIM-"));
        setAstronautId(sim ? sim.astronaut_id : "default");
        setBackendOk(true);
      })
      .catch(() => setBackendOk(false));
  }, []);

  const loadStatus = useCallback((aid: string) => {
    api.status(aid)
      .then(setStatus)
      .catch((e) => { setStatus(null); if (!(e instanceof ApiError && e.status === 404)) setMessage(e.message); });
  }, []);

  useEffect(() => { if (backendOk) loadStatus(astronautId); }, [backendOk, astronautId, loadStatus]);

  const astro = astronauts.find((a) => a.astronaut_id === astronautId);
  const missionDay = status?.mission_day ?? astro?.current_mission_day ?? 1;

  // color del mapa: el del backend; sin backend, solo límites clínicos de lo que se escribió
  const mapStatus = useMemo(() => Object.fromEntries(KEYS.map((k) => [k,
    backendOk ? status?.indicators[k]?.status ?? null
      : form[k] != null ? evaluateAbsolute(k, form[k] as number, missionDay, indicators, meta.absolute_only_first_days) : null,
  ])) as Record<IndicatorKey, Status | null>, [backendOk, status, form, missionDay, indicators, meta]);

  async function handleSubmit() {
    setMessage(null);
    const values = Object.fromEntries(KEYS.filter((k) => form[k] !== null).map((k) => [k, form[k] as number]));
    if (Object.keys(values).length === 0) { setMessage("Ingresa al menos un indicador antes de registrar."); return; }
    if (!backendOk) {
      setLocalRecs(KEYS.filter((k) => form[k] !== null && mapStatus[k] !== "normal")
        .map((k) => `${indicators[k].label}: ${STATUS_LABEL[mapStatus[k] as Status]} por límite clínico. Repite la medición y sigue la guía.`));
      return;
    }
    try {
      const res = await api.postRecord({ astronaut_id: astronautId, ...values });
      setStatus(res.status);
      setForm(EMPTY);
      setRefresh((n) => n + 1);
      if (!astronauts.some((a) => a.astronaut_id === astronautId)) api.astronauts().then(setAstronauts).catch(() => {});
    } catch (e) {
      setMessage(e instanceof Error ? `No se registró: ${e.message}` : "No se registró.");
    }
  }

  const recommendations = status
    ? KEYS.filter((k) => status.indicators[k]?.recommendation).map((k) => `${indicators[k].label}: ${status.indicators[k].recommendation}`)
    : localRecs;
  const ids = astronauts.map((a) => a.astronaut_id);
  if (!ids.includes("default")) ids.push("default");

  return (
    <div className="min-h-screen p-6 max-w-6xl mx-auto">
      <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Astronaut Health Monitor</h1>
          <p className="text-slate-400 text-sm">Registra tus indicadores y compáralos con tu propia línea base.</p>
        </div>
        <div className="flex items-center gap-3">
          {status?.data_origin === "synthetic" && (
            <span className="text-xs font-semibold tracking-wider px-2 py-1 rounded border border-dashed border-amber-400 text-amber-300">DATOS SINTÉTICOS</span>
          )}
          {backendOk && (
            <label className="text-sm text-slate-300 flex items-center gap-2">
              Astronauta
              <select value={astronautId} onChange={(e) => { setAstronautId(e.target.value); setForm(EMPTY); setMessage(null); }}
                className="bg-slate-800 border border-slate-700 rounded px-2 py-1">
                {ids.map((id) => <option key={id} value={id}>{id === "default" ? "default (registro manual)" : id}</option>)}
              </select>
            </label>
          )}
        </div>
      </header>

      {backendOk === false && (
        <p className="mb-4 text-amber-300 text-sm border border-amber-500/50 rounded-lg p-3">
          Modo local: solo límites clínicos, sin línea base personal. Para el semáforo completo arranca el backend
          (<code>cd backend && venv\Scripts\python -m uvicorn main:app --reload</code>).
        </p>
      )}

      {status && (
        <section className="mb-6 rounded-xl bg-slate-900 p-4 border-l-4" style={{ borderColor: STATUS_COLOR[status.overall.status] }} aria-live="polite">
          <div className="flex flex-wrap items-center gap-3">
            <Pill status={status.overall.status} />
            <h2 className="text-lg font-semibold">{status.astronaut_id} · día {status.mission_day}</h2>
          </div>
          <p className="text-sm text-slate-400 mt-1">{MODE_TEXT[status.evaluation_mode]}</p>
          {status.overall.reasons.map((r) => <p key={r.code} className="text-sm mt-1">{r.text}. Cuenta como rojo.</p>)}
        </section>
      )}

      <div className="grid md:grid-cols-[220px_1fr] gap-8">
        <div>
          <BodyMap statusByIndicator={mapStatus} onSelectPart={setSelectedPart} selectedPart={selectedPart?.id ?? null} indicators={indicators} />
          {selectedPart && (
            <div className="mt-4 text-sm bg-slate-900 rounded-lg p-3">
              <p className="font-medium">{selectedPart.label}</p>
              <ul className="text-slate-400 mt-1 space-y-0.5">
                {selectedPart.indicators.map((k) => <li key={k}>{indicators[k].label}: {mapStatus[k] ? STATUS_LABEL[mapStatus[k] as Status] : "sin dato"}</li>)}
              </ul>
            </div>
          )}
          <div className="mt-4 text-xs text-slate-400 space-y-1">
            {(["normal", "attention", "critical"] as Status[]).map((s) => (
              <p key={s}><span className="inline-block w-3 h-3 rounded-full mr-1 align-middle" style={{ backgroundColor: STATUS_COLOR[s] }} /> {STATUS_LABEL[s]}</p>
            ))}
            <p><span className="inline-block w-3 h-3 rounded-full mr-1 align-middle" style={{ backgroundColor: NODATA_COLOR }} /> Sin dato</p>
          </div>
          <p className="mt-3 text-xs text-slate-500">{BODY_PARTS.length} zonas · toca una para ver sus indicadores.</p>
        </div>

        <div>
          <div className="grid sm:grid-cols-2 gap-3 mb-4">
            {KEYS.map((key) => (
              <IndicatorCard
                key={key}
                indicatorKey={key}
                indicators={indicators}
                value={form[key]}
                onChange={(v) => setForm((f) => ({ ...f, [key]: v }))}
                missionDay={missionDay}
                early={meta.absolute_only_first_days}
                serverStatus={status?.indicators[key]}
                selected={chartKey === key}
                onSelect={() => setChartKey(key)}
              />
            ))}
          </div>

          <button onClick={handleSubmit} className="bg-sky-600 hover:bg-sky-500 text-white px-4 py-2 rounded-lg font-medium">
            Registrar medición
          </button>
          {message && <p className="mt-3 text-sm text-amber-300">{message}</p>}

          {recommendations.length > 0 && (
            <div className="mt-4 bg-slate-900 border border-amber-500 rounded-lg p-3 space-y-1">
              <p className="font-medium text-amber-400">Recomendaciones</p>
              {recommendations.map((r) => <p key={r} className="text-sm text-slate-300">• {r}</p>)}
              <p className="text-xs text-slate-500">Orientativas. No reemplazan el criterio del oficial médico.</p>
            </div>
          )}

          {backendOk && (
            <section className="mt-8">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
                <h2 className="font-semibold">Tendencia: {indicators[chartKey].label}</h2>
                <select value={chartKey} onChange={(e) => setChartKey(e.target.value as IndicatorKey)}
                  className="bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm">
                  {KEYS.map((k) => <option key={k} value={k}>{indicators[k].label}</option>)}
                </select>
              </div>
              <HistoryChart astronautId={astronautId} indicatorKey={chartKey} indicators={indicators} refreshKey={refresh} />
            </section>
          )}
        </div>
      </div>
    </div>
  );
}
