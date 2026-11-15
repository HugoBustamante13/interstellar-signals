import { Status } from "../data/thresholds";

interface BodyPart {
  id: string;
  label: string;
  indicators: string[];
  cx: number;
  cy: number;
  r: number;
}

const BODY_PARTS: BodyPart[] = [
  { id: "head", label: "Cabeza / Mente", indicators: ["mood", "sleep_hours"], cx: 100, cy: 40, r: 18 },
  { id: "chest", label: "Pecho / Cardiovascular", indicators: ["heart_rate", "systolic_bp", "spo2"], cx: 100, cy: 100, r: 28 },
  { id: "abdomen", label: "Abdomen / Metabolismo", indicators: ["glucose"], cx: 100, cy: 160, r: 22 },
  { id: "core", label: "Temperatura corporal", indicators: ["body_temp"], cx: 100, cy: 200, r: 16 },
];

export default function BodyMap({
  statusByIndicator,
  onSelectPart,
  selectedPart,
}: {
  statusByIndicator: Record<string, Status | null>;
  onSelectPart: (part: BodyPart) => void;
  selectedPart: string | null;
}) {
  function partColor(part: BodyPart) {
    const statuses = part.indicators.map((i) => statusByIndicator[i]).filter(Boolean);
    if (statuses.includes("critical")) return "#ef4444";
    if (statuses.includes("attention")) return "#f59e0b";
    if (statuses.length === 0) return "#475569";
    return "#22c55e";
  }

  return (
    <svg viewBox="0 0 200 260" className="w-full max-w-[220px] mx-auto">
      {BODY_PARTS.map((part) => (
        <g key={part.id} onClick={() => onSelectPart(part)} className="cursor-pointer">
          <circle
            cx={part.cx}
            cy={part.cy}
            r={part.r}
            fill={partColor(part)}
            opacity={selectedPart === part.id ? 1 : 0.75}
            stroke={selectedPart === part.id ? "#fff" : "none"}
            strokeWidth={2}
          />
        </g>
      ))}
    </svg>
  );
}

export { BODY_PARTS };
export type { BodyPart };
