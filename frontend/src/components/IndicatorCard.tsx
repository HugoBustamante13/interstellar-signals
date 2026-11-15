import { THRESHOLDS, evaluate, STATUS_COLOR } from "../data/thresholds";

interface Props {
  indicatorKey: string;
  value: number | null;
  onChange: (value: number | null) => void;
}

export default function IndicatorCard({ indicatorKey, value, onChange }: Props) {
  const rule = THRESHOLDS[indicatorKey];
  const status = value !== null && Number.isFinite(value) ? evaluate(indicatorKey, value) : null;
  const color = status ? STATUS_COLOR[status] : "#475569";

  return (
    <div
      className="rounded-xl border p-4 bg-slate-900 flex flex-col gap-2"
      style={{ borderColor: color }}
    >
      <div className="flex justify-between items-center">
        <span className="font-medium">{rule.label}</span>
        <span
          className="text-xs px-2 py-0.5 rounded-full"
          style={{ backgroundColor: color, color: "#0f172a" }}
        >
          {status ?? "sin dato"}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="number"
          step="any"
          value={value ?? ""}
          placeholder={`${rule.normal[0]}–${rule.normal[1]} ${rule.unit}`}
          onChange={(e) => {
            const n = parseFloat(e.target.value);
            onChange(Number.isFinite(n) ? n : null);
          }}
          className="bg-slate-800 border border-slate-700 rounded px-2 py-1 w-full text-sm"
        />
        <span className="text-xs text-slate-400">{rule.unit}</span>
      </div>
    </div>
  );
}
