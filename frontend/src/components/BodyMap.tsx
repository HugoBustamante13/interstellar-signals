import { IndicatorKey, Indicators, NODATA_COLOR, STATUS_COLOR, STATUS_LABEL, Status } from "../data/indicators";

interface BodyPart {
  id: string;
  label: string;
  indicators: IndicatorKey[];
  cx: number;
  cy: number;
  r: number;
}

const BODY_PARTS: BodyPart[] = [
  { id: "head", label: "Cabeza / Mente", indicators: ["mood", "sleep"], cx: 100, cy: 40, r: 18 },
  { id: "chest", label: "Pecho / Cardiovascular", indicators: ["hr_rest", "bp_sys", "bp_dia", "spo2"], cx: 100, cy: 100, r: 28 },
  { id: "abdomen", label: "Abdomen / Metabolismo", indicators: ["glucose"], cx: 100, cy: 160, r: 22 },
  { id: "core", label: "Temperatura corporal", indicators: ["temp"], cx: 100, cy: 200, r: 16 },
  { id: "legs", label: "Músculo / Ejercicio", indicators: ["exercise", "fitness"], cx: 100, cy: 240, r: 14 },
];

const RANK: Record<Status, number> = { normal: 0, attention: 1, critical: 2 };

/** Peor estado de la zona; null si ninguno de sus indicadores tiene dato. */
export function partStatus(part: BodyPart, statusByIndicator: Partial<Record<IndicatorKey, Status | null>>): Status | null {
  const sts = part.indicators.map((k) => statusByIndicator[k]).filter((s): s is Status => !!s);
  return sts.length ? sts.reduce((a, b) => (RANK[b] > RANK[a] ? b : a)) : null;
}

export default function BodyMap({
  statusByIndicator,
  onSelectPart,
  selectedPart,
  indicators,
}: {
  statusByIndicator: Partial<Record<IndicatorKey, Status | null>>;
  onSelectPart: (part: BodyPart) => void;
  selectedPart: string | null;
  indicators: Indicators;
}) {
  return (
    <svg viewBox="0 0 200 260" className="w-full max-w-[220px] mx-auto" role="group" aria-label="Mapa corporal">
      {BODY_PARTS.map((part) => {
        const st = partStatus(part, statusByIndicator);
        const name = `${part.label}: ${st ? STATUS_LABEL[st] : "sin dato"} (${part.indicators.map((k) => indicators[k].label).join(", ")})`;
        return (
          <g
            key={part.id}
            onClick={() => onSelectPart(part)}
            onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelectPart(part); } }}
            className="cursor-pointer focus:outline-none"
            role="button"
            tabIndex={0}
            aria-label={name}
          >
            <title>{name}</title>
            <circle
              cx={part.cx}
              cy={part.cy}
              r={part.r}
              fill={st ? STATUS_COLOR[st] : NODATA_COLOR}
              opacity={selectedPart === part.id ? 1 : 0.75}
              stroke={selectedPart === part.id ? "#fff" : "none"}
              strokeWidth={2}
            />
          </g>
        );
      })}
    </svg>
  );
}

export { BODY_PARTS };
export type { BodyPart };
