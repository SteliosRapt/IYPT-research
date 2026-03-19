import type { DerivedGeometry } from "@fixed-geometry/shared-schema";

export function DerivedPanel({ derived }: { derived: DerivedGeometry }) {
  const entries = [
    ["S0", derived.S0],
    ["S1", derived.S1],
    ["S2", derived.S2],
    ["h2", derived.h2],
    ["h4", derived.h4],
    ["r", derived.r],
    ["X2", derived.X2],
    ["X3", derived.X3],
    ["X4", derived.X4],
    ["X5", derived.X5],
    ["C1", derived.C1],
    ["C2", derived.C2],
    ["H0", derived.H0],
  ];

  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Derived values</h2>
      </div>
      <div className="metric-grid">
        {entries.map(([label, value]) => (
          <div key={label} className="metric">
            <span>{label}</span>
            <strong>{value.toFixed(4)}</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

