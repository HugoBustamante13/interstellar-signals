// Mantener sincronizado con backend/thresholds.py
export type Status = "normal" | "attention" | "critical";

export interface IndicatorRule {
  label: string;
  unit: string;
  normal: [number, number];
  attention: [number, number];
}

export const THRESHOLDS: Record<string, IndicatorRule> = {
  heart_rate: { label: "Frecuencia cardíaca", unit: "bpm", normal: [60, 100], attention: [50, 120] },
  systolic_bp: { label: "Presión sistólica", unit: "mmHg", normal: [90, 120], attention: [85, 140] },
  spo2: { label: "SpO2", unit: "%", normal: [95, 100], attention: [90, 100] },
  body_temp: { label: "Temperatura corporal", unit: "°C", normal: [36.1, 37.2], attention: [35.5, 38.0] },
  glucose: { label: "Glucosa", unit: "mg/dL", normal: [70, 140], attention: [60, 180] },
  sleep_hours: { label: "Horas de sueño", unit: "h", normal: [7, 9], attention: [5, 12] },
  mood: { label: "Estado de ánimo", unit: "1-5", normal: [4, 5], attention: [2, 5] },
};

export function evaluate(indicator: string, value: number): Status {
  const rule = THRESHOLDS[indicator];
  if (!rule) return "normal";
  const [nLo, nHi] = rule.normal;
  const [aLo, aHi] = rule.attention;
  if (value >= nLo && value <= nHi) return "normal";
  if (value >= aLo && value <= aHi) return "attention";
  return "critical";
}

export const STATUS_COLOR: Record<Status, string> = {
  normal: "#22c55e",
  attention: "#f59e0b",
  critical: "#ef4444",
};
