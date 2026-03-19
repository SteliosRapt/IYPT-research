import type { DerivedGeometry, MeshingConfig, NormalizedParameters } from "@fixed-geometry/shared-schema";

const PRESETS: MeshingConfig["preset"][] = ["coarse", "medium", "fine"];
const DIVISORS: Record<MeshingConfig["preset"], number> = {
  coarse: 24,
  medium: 36,
  fine: 48,
};
const REFINEMENT_LEVELS: Record<MeshingConfig["preset"], number> = {
  coarse: 2,
  medium: 3,
  fine: 4,
};

function computeCellSize(parameters: NormalizedParameters, derived: DerivedGeometry, preset: MeshingConfig["preset"]): number {
  const domainSpan = Math.min(
    parameters.W,
    parameters.h0 + parameters.h_a,
    derived.X5 - derived.S0
  );
  return domainSpan / DIVISORS[preset];
}

type Props = {
  parameters: NormalizedParameters;
  derived: DerivedGeometry;
  preset: MeshingConfig["preset"];
  showMeshDomain: boolean;
  showFluidInterior: boolean;
  onPresetChange: (preset: MeshingConfig["preset"]) => void;
  onToggleMeshDomain: () => void;
  onToggleFluidInterior: () => void;
};

export function MeshingPanel({ parameters, derived, preset, showMeshDomain, showFluidInterior, onPresetChange, onToggleMeshDomain, onToggleFluidInterior }: Props) {
  const cellSize = computeCellSize(parameters, derived, preset);
  const level = REFINEMENT_LEVELS[preset];
  const tubeRadiusCells = derived.r / cellSize;

  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Meshing</h2>
      </div>
      <div className="rows">
        <div className="param-row">
          <span>Preset</span>
          <span style={{ display: "flex", gap: "0.5rem" }}>
            {PRESETS.map((p) => (
              <label key={p} style={{ display: "flex", alignItems: "center", gap: "0.25rem", cursor: "pointer" }}>
                <input
                  type="radio"
                  name="meshingPreset"
                  value={p}
                  checked={preset === p}
                  onChange={() => onPresetChange(p)}
                />
                {p}
              </label>
            ))}
          </span>
        </div>
        <div className="param-row">
          <span>Background cell size</span>
          <strong>{cellSize.toFixed(5)} m</strong>
        </div>
        <div className="param-row">
          <span>Refinement levels</span>
          <strong>{level}</strong>
        </div>
        <div className="param-row">
          <span>Tube radius / cell size</span>
          <strong style={{ color: tubeRadiusCells < 3 ? "#ff6644" : "inherit" }}>
            {tubeRadiusCells.toFixed(1)}×
            {tubeRadiusCells < 3 ? " ⚠ too coarse" : ""}
          </strong>
        </div>
        <label className="param-row" style={{ cursor: "pointer" }}>
          <span>Show fluid interior</span>
          <input type="checkbox" checked={showFluidInterior} onChange={onToggleFluidInterior} />
        </label>
        <label className="param-row" style={{ cursor: "pointer" }}>
          <span>Show mesh domain</span>
          <input type="checkbox" checked={showMeshDomain} onChange={onToggleMeshDomain} />
        </label>
      </div>
    </section>
  );
}
