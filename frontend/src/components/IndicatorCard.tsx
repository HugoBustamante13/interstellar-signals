import type { IndicatorStatus } from "../data/api";
import { IndicatorKey, Indicators, NODATA_COLOR, STATUS_COLOR, STATUS_LABEL, evaluateAbsolute } from "../data/indicators";

interface Props {
  indicatorKey: IndicatorKey;
  indicators: Indicators;
  value: number | null;
  onChange: (value: number | null) => void;
  missionDay: number;
  early: number;
  /** Estado calculado por el backend (con línea base). Manda mientras no se esté escribiendo un valor nuevo. */
  serverStatus?: IndicatorStatus;
  selected?: boolean;
  onSelect?: () => void;
}

const fmt = (v: number | null | undefined) => (v == null ? "—" : v.toLocaleString("es-CO", { maximumFractionDigits: 1 }));

export default function IndicatorCard({ indicatorKey, indicators, value, onChange, missionDay, early, serverStatus, selected, onSelect }: Props) {
  const meta = indicators[indicatorKey];
  const typing = value !== null && Number.isFinite(value);
  // vista previa mientras se escribe: solo límite clínico; el color con línea base llega del backend al registrar
  const status = typing ? evaluateAbsolute(indicatorKey, value as number, missionDay, indicators, early) : serverStatus?.status ?? null;
  const color = status ? STATUS_COLOR[status] : NODATA_COLOR;
  const b = serverStatus?.baseline;
  const band = b?.ready ? (b.lo != null && b.hi != null ? `banda ${fmt(b.lo)}–${fmt(b.hi)}` : b.lo != null ? `mínimo ${fmt(b.lo)}` : `máximo ${fmt(b.hi)}`) : null;

  return (
    <div
      className={`rounded-xl border p-4 bg-slate-900 flex flex-col gap-2 ${selected ? "ring-2 ring-sky-400" : ""}`}
      style={{ borderColor: color }}
    >
      <div className="flex justify-between items-center gap-2">
        <button type="button" onClick={onSelect} className="font-medium text-left hover:text-sky-300" title="Ver su tendencia">
          {meta.label}
        </button>
        <span className="text-xs px-2 py-0.5 rounded-full whitespace-nowrap" style={{ backgroundColor: color, color: "#0f172a" }}>
          {status ? STATUS_LABEL[status] : "sin dato"}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="number"
          step="any"
          min={meta.input_range[0]}
          max={meta.input_range[1]}
          value={value ?? ""}
          placeholder={serverStatus?.value != null ? `último: ${fmt(serverStatus.value)}` : `${meta.input_range[0]}–${meta.input_range[1]}`}
          aria-label={`${meta.label} (${meta.unit})`}
          onChange={(e) => {
            const n = parseFloat(e.target.value);
            onChange(Number.isFinite(n) ? n : null);
          }}
          className="bg-slate-800 border border-slate-700 rounded px-2 py-1 w-full text-sm"
        />
        <span className="text-xs text-slate-400 whitespace-nowrap">{meta.unit}</span>
      </div>
      {typing ? (
        <p className="text-xs text-slate-400">Vista previa: solo límite clínico.</p>
      ) : serverStatus?.reason || band ? (
        <p className="text-xs text-slate-400">
          {serverStatus?.reason?.text}
          {serverStatus?.reason && band ? " · " : ""}
          {band}
          {serverStatus?.carried && serverStatus.value_day != null ? ` · última lectura del día ${serverStatus.value_day}` : ""}
        </p>
      ) : null}
    </div>
  );
}
