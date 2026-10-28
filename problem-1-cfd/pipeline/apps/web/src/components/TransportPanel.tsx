import type { TransportConfig } from "@fixed-geometry/shared-schema";

type Props = {
  transport: TransportConfig;
  onChange: (key: keyof TransportConfig, value: number) => void;
};

const FIELDS: Array<{
  key: keyof TransportConfig;
  label: string;
  min: number;
  max: number;
  step: number;
}> = [
  { key: "waterRho", label: "Water density ρ (kg/m³)", min: 800, max: 1100, step: 0.1 },
  { key: "waterNu",  label: "Water ν (m²/s)",          min: 1e-7, max: 1e-4, step: 1e-8 },
  { key: "airRho",   label: "Air density ρ (kg/m³)",   min: 0.5,  max: 2.0,  step: 0.01 },
  { key: "airNu",    label: "Air ν (m²/s)",             min: 1e-6, max: 1e-4, step: 1e-7 },
  { key: "sigma",    label: "Surface tension σ (N/m)",  min: 0.0,  max: 0.1,  step: 0.001 },
];

export function TransportPanel({ transport, onChange }: Props) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Transport properties</h2>
      </div>
      <div className="rows">
        {FIELDS.map(({ key, label, min, max, step }) => (
          <label className="param-row" key={key}>
            <span>{label}</span>
            <input
              type="number"
              min={min}
              max={max}
              step={step}
              value={transport[key]}
              onChange={(e) => onChange(key, Number.parseFloat(e.currentTarget.value))}
            />
            <strong>{transport[key].toExponential(3)}</strong>
          </label>
        ))}
      </div>
    </section>
  );
}
