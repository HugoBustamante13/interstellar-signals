import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { THRESHOLDS } from "../data/thresholds";

interface Record {
  timestamp: string;
  [key: string]: any;
}

export default function HistoryChart({
  records,
  indicatorKey,
}: {
  records: Record[];
  indicatorKey: string;
}) {
  const rule = THRESHOLDS[indicatorKey];
  const data = records
    .filter((r) => r[indicatorKey] !== null && r[indicatorKey] !== undefined)
    .map((r) => ({
      time: new Date(r.timestamp).toLocaleString("en-US"),
      value: r[indicatorKey],
    }));

  if (data.length === 0) {
    return <p className="text-slate-500 text-sm">No history yet for {rule.label}.</p>;
  }

  return (
    <div className="h-48 w-full">
      <p className="text-sm text-slate-400 mb-1">{rule.label} over time</p>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="time" tick={{ fontSize: 10 }} hide />
          <YAxis tick={{ fontSize: 10 }} domain={["auto", "auto"]} />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#38bdf8" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
