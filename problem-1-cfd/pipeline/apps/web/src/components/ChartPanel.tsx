import type { RunManifest } from "@fixed-geometry/shared-schema";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Point = { time: number; value: number };

export function ChartPanel({
  manifest,
  heightSeries,
  flowSeries,
  dischargedSeries,
}: {
  manifest: RunManifest;
  heightSeries: Point[];
  flowSeries: Point[];
  dischargedSeries: Point[];
}) {
  const merged = heightSeries.map((point, index) => ({
    time: point.time,
    height: point.value,
    qOut: flowSeries[index]?.value ?? 0,
    discharged: dischargedSeries[index]?.value ?? 0,
  }));

  return (
    <section className="panel chart-panel">
      <div className="panel-heading">
        <h2>Run metrics</h2>
      </div>
      <div className="chart-stack">
        <div className="chart-card">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={merged}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2c3342" />
              <XAxis dataKey="time" stroke="#8d98aa" />
              <YAxis stroke="#8d98aa" />
              <Tooltip />
              <Legend />
              {manifest.events.t_h0_up !== null ? (
                <ReferenceLine x={manifest.events.t_h0_up} stroke="#f59e0b" />
              ) : null}
              {manifest.events.t_steady !== null ? (
                <ReferenceLine x={manifest.events.t_steady} stroke="#22c55e" />
              ) : null}
              <Line type="monotone" dataKey="height" stroke="#7eb8ff" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <div className="chart-card">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={merged}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2c3342" />
              <XAxis dataKey="time" stroke="#8d98aa" />
              <YAxis stroke="#8d98aa" />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="qOut" stroke="#34d399" dot={false} />
              <Line type="monotone" dataKey="discharged" stroke="#f472b6" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  );
}

