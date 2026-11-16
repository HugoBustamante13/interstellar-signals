// Espejo de simulador/sim/semaforo_config.json, tal como lo entrega GET /indicators.
// Al arrancar, App pide /indicators y sobrescribe esta copia: la copia local solo manda sin conexión con el backend.
// El color real (con línea base personal) lo calcula el backend; aquí solo hay límites clínicos absolutos,
// para la vista previa mientras se escribe y para el modo sin backend.

export type Status = "normal" | "attention" | "critical";

export const KEYS = ["hr_rest", "bp_sys", "bp_dia", "spo2", "temp", "glucose", "sleep", "mood", "exercise", "fitness"] as const;
export type IndicatorKey = (typeof KEYS)[number];

export interface AbsoluteLimits {
  red_gt?: number | null;
  red_lt?: number | null;
  yellow_lt?: number | null;
  yellow_gt?: number | null;
  red_gt_inflight?: number | null;
  inflight_consecutive_days?: number | null;
}

export interface IndicatorMeta {
  label: string;
  unit: string;
  input_range: [number, number];
  body_part: string;
  in_semaforo: boolean;
  absolute: AbsoluteLimits;
}

export interface Meta {
  absolute_only_first_days: number;
  min_window_points: number;
  baseline_window_days: number;
}

export type Indicators = Record<IndicatorKey, IndicatorMeta>;

export const LOCAL_INDICATORS: Indicators = {
  hr_rest: { label: "FC en reposo", unit: "lpm", input_range: [20, 250], body_part: "chest", in_semaforo: true, absolute: { red_gt: 100, red_lt: null, yellow_lt: 50, red_gt_inflight: null } },
  bp_sys: { label: "Presión sistólica", unit: "mmHg", input_range: [50, 260], body_part: "chest", in_semaforo: true, absolute: { red_gt: 180, red_lt: null, yellow_lt: null, red_gt_inflight: null } },
  bp_dia: { label: "Presión diastólica", unit: "mmHg", input_range: [30, 160], body_part: "chest", in_semaforo: true, absolute: { red_gt: 120, red_lt: null, yellow_lt: null, red_gt_inflight: null } },
  spo2: { label: "SpO2", unit: "%", input_range: [50, 100], body_part: "chest", in_semaforo: true, absolute: { red_gt: null, red_lt: 90, yellow_lt: null, red_gt_inflight: null } },
  temp: { label: "Temperatura", unit: "°C", input_range: [30, 45], body_part: "core", in_semaforo: true, absolute: { red_gt: 38.0, red_lt: null, yellow_lt: null, red_gt_inflight: 38.5, inflight_consecutive_days: 2 } },
  glucose: { label: "Glucosa en ayunas", unit: "mg/dL", input_range: [20, 600], body_part: "abdomen", in_semaforo: false, absolute: { red_gt: 126, red_lt: 54, yellow_gt: 100, yellow_lt: 70 } },
  sleep: { label: "Horas de sueño", unit: "h", input_range: [0, 24], body_part: "head", in_semaforo: true, absolute: { red_gt: null, red_lt: null, yellow_lt: null, red_gt_inflight: null } },
  mood: { label: "Estado de ánimo", unit: "1-5", input_range: [1, 5], body_part: "head", in_semaforo: true, absolute: { red_gt: null, red_lt: null, yellow_lt: null, red_gt_inflight: null } },
  exercise: { label: "Ejercicio", unit: "min", input_range: [0, 600], body_part: "legs", in_semaforo: true, absolute: { red_gt: null, red_lt: null, yellow_lt: null, red_gt_inflight: null } },
  fitness: { label: "Aptitud física", unit: "% previa", input_range: [0, 150], body_part: "legs", in_semaforo: true, absolute: { red_gt: null, red_lt: 80, yellow_lt: null, red_gt_inflight: null } },
};

export const LOCAL_META: Meta = { absolute_only_first_days: 14, min_window_points: 14, baseline_window_days: 28 };

/** Solo límites clínicos absolutos (sin línea base). Igual que absolute_code() en backend/semaforo_bridge.py:
 *  temperatura con 38,0 °C en prevuelo y días 1–14 y el límite de vuelo después; FC < 50 solo en vuelo. */
export function evaluateAbsolute(
  key: IndicatorKey, value: number, missionDay: number, indicators: Indicators = LOCAL_INDICATORS, early = LOCAL_META.absolute_only_first_days,
): Status {
  const a = indicators[key].absolute;
  if (key === "glucose") {
    if ((a.red_lt != null && value < a.red_lt) || (a.red_gt != null && value >= a.red_gt)) return "critical";
    if ((a.yellow_lt != null && value < a.yellow_lt) || (a.yellow_gt != null && value >= a.yellow_gt)) return "attention";
    return "normal";
  }
  const gt = key === "temp" && missionDay > early ? a.red_gt_inflight : a.red_gt;
  if (gt != null && value > gt) return "critical";
  if (a.red_lt != null && value < a.red_lt) return "critical";
  if (a.yellow_lt != null && missionDay > 0 && value < a.yellow_lt) return "attention";
  return "normal";
}

export const STATUS_COLOR: Record<Status, string> = { normal: "#22c55e", attention: "#f59e0b", critical: "#ef4444" };
export const NODATA_COLOR = "#475569";
export const STATUS_LABEL: Record<Status, string> = { normal: "Verde", attention: "Amarillo", critical: "Rojo" };
