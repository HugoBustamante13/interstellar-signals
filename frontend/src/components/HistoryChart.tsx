import { useEffect, useState } from "react";
import { CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { api, SeriesPoint } from "../data/api";
import { IndicatorKey, Indicators, STATUS_COLOR, STATUS_LABEL } from "../data/indicators";

interface DotProps { cx?: number; cy?: number; payload?: SeriesPoint; index?: number }

// punto de cada día con el color del semáforo; los verdes, pequeños (función, no componente: Recharts le pasa la key)
function renderDot({ cx, cy, payload, index }: DotProps) {
  if (cx == null || cy == null || !payload || payload.value == null) return <g key={`d${index}`} />;
  const st = payload.status;
  return <circle key={`d${index}`} cx={cx} cy={cy} r={st && st !== "normal" ? 3.5 : 1.6} fill={st ? STATUS_COLOR[st] : "#94a3b8"} />;
}

/** Tendencia de un indicador (GET /series): valor diario, banda personal (lo/hi) y línea base. Eje X = día de misión. */
export default function HistoryChart({
  astronautId, indicatorKey, indicators, refreshKey,
}: {
  astronautId: string;
  indicatorKey: IndicatorKey;
  indicators: Indicators;
  refreshKey: number;
}) {
  const meta = indicators[indicatorKey];
  const [data, setData] = useState<SeriesPoint[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    setError(null);
    api.series(astronautId, indicatorKey)
      .then((d) => { if (alive) setData(d); })
      .catch((e: Error) => { if (alive) { setData(null); setError(e.message); } });
    return () => { alive = false; };
  }, [astronautId, indicatorKey, refreshKey]);

  if (error) return <p className="text-slate-500 text-sm">Sin histórico para {meta.label}: {error}.</p>;
  if (!data) return <p className="text-slate-500 text-sm">Cargando {meta.label}…</p>;
  if (!data.some((p) => p.value != null)) return <p className="text-slate-500 text-sm">Sin lecturas de {meta.label} todavía.</p>;

  const hasBand = data.some((p) => p.lo != null || p.hi != null);
  return (
    <div className="w-full">
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="mission_day" type="number" domain={["dataMin", "dataMax"]} tick={{ fontSize: 11, fill: "#94a3b8" }}
              tickFormatter={(d: number) => (d < 0 ? `L${d}` : `${d}`)} />
            <YAxis tick={{ fontSize: 11, fill: "#94a3b8" }} domain={["auto", "auto"]} width={44} />
            <Tooltip
              contentStyle={{ background: "#0f172a", border: "1px solid #334155", fontSize: 12 }}
              labelFormatter={(d) => `Día ${d}`}
              formatter={(v, name, item) => {
                const p = (item as { payload?: SeriesPoint }).payload;
                return name === "Valor" && p?.status ? [`${v} ${meta.unit} · ${STATUS_LABEL[p.status]}`, name] : [v as number, name];
              }}
            />
            <ReferenceLine x={0.5} stroke="#64748b" strokeDasharray="2 4" label={{ value: "lanzamiento", fill: "#64748b", fontSize: 10, position: "insideTopLeft" }} />
            {hasBand && <Line dataKey="hi" name="Banda (máx.)" stroke="#38bdf8" strokeOpacity={0.6} strokeDasharray="4 4" dot={false} isAnimationActive={false} connectNulls={false} />}
            {hasBand && <Line dataKey="lo" name="Banda (mín.)" stroke="#38bdf8" strokeOpacity={0.6} strokeDasharray="4 4" dot={false} isAnimationActive={false} connectNulls={false} />}
            {hasBand && <Line dataKey="base" name="Línea base" stroke="#64748b" strokeDasharray="1 3" dot={false} isAnimationActive={false} />}
            <Line dataKey="value" name="Valor" stroke="#e2e8f0" strokeWidth={1.5} isAnimationActive={false}
              dot={renderDot} activeDot={{ r: 4 }} connectNulls={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
      <p className="text-xs text-slate-500 mt-1">
        {hasBand ? "Líneas punteadas: tu banda personal (media ± 2,5 DE de 28 días). " : "Sin banda personal para este indicador. "}
        Puntos amarillos y rojos: días en alerta.
      </p>
    </div>
  );
}
