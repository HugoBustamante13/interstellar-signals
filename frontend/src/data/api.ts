// Cliente de la API del backend (contrato: docs/decision_integracion_semaforo.md, sección 5).
// Vite reenvía /api/* al backend en http://localhost:8000 (vite.config.ts).
import type { IndicatorKey, Indicators, Meta, Status } from "./indicators";

export interface Reason { code: string; text: string; [extra: string]: unknown }
export interface Baseline { ready: boolean; mean: number | null; lo: number | null; hi: number | null }
export interface IndicatorStatus {
  value: number | null;
  value_day: number | null;
  carried: boolean;
  status: Status | null;
  reason: Reason | null;
  baseline: Baseline | null;
  recommendation: string | null;
}
export interface StatusResponse {
  astronaut_id: string;
  mission_day: number;
  phase: "preflight" | "inflight";
  evaluation_mode: "prevuelo" | "adaptacion_inicial" | "linea_base";
  data_origin: "synthetic" | "manual";
  overall: { status: Status; reasons: Reason[] };
  indicators: Record<IndicatorKey, IndicatorStatus>;
}
export interface Astronaut { astronaut_id: string; launch_date: string; source: string; current_mission_day: number }
export interface SeriesPoint { mission_day: number; value: number | null; status: Status | null; base: number | null; lo: number | null; hi: number | null }
export type RecordInput = { astronaut_id: string } & Partial<Record<IndicatorKey, number>>;

export class ApiError extends Error {
  constructor(public status: number, message: string) { super(message); }
}

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, init);
  if (!res.ok) {
    let detail = `Error ${res.status}`;
    try {
      const j = await res.json();
      detail = typeof j.detail === "string" ? j.detail : Array.isArray(j.detail) ? j.detail.map((d: { msg: string }) => d.msg).join(" · ") : detail;
    } catch { /* respuesta sin JSON */ }
    throw new ApiError(res.status, detail);
  }
  return res.json() as Promise<T>;
}

export const api = {
  indicators: () => call<Indicators & { _meta: Meta }>("/indicators"),
  astronauts: () => call<Astronaut[]>("/astronauts"),
  status: (aid: string) => call<StatusResponse>(`/status?astronaut_id=${encodeURIComponent(aid)}`),
  series: (aid: string, k: IndicatorKey) => call<SeriesPoint[]>(`/series?astronaut_id=${encodeURIComponent(aid)}&indicator=${k}`),
  postRecord: (body: RecordInput) =>
    call<{ record: unknown; status: StatusResponse }>("/records", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    }),
};
