import {
  createGeometrySnapshot,
  type CanonicalParameters,
} from "@fixed-geometry/shared-schema";
import { useMemo, useTransition } from "react";

import { ChartPanel } from "@/components/ChartPanel";
import { ConstraintList } from "@/components/ConstraintList";
import { DerivedPanel } from "@/components/DerivedPanel";
import { MeshingPanel } from "@/components/MeshingPanel";
import { ParameterPanel } from "@/components/ParameterPanel";
import { Scene3D } from "@/components/Scene3D";
import { TransportPanel } from "@/components/TransportPanel";
import { VisibilityToggles } from "@/components/VisibilityToggles";
import {
  exportCaseJson,
  exportGlb,
  exportStl,
} from "@/lib/sceneBuilder";
import { parameterSections, useAppStore } from "@/app/store";

export function ConfigurePage() {
  const parameters = useAppStore((state) => state.parameters);
  const visibility = useAppStore((state) => state.visibility);
  const transport = useAppStore((state) => state.transport);
  const meshingPreset = useAppStore((state) => state.meshingPreset);
  const showMeshDomain = useAppStore((state) => state.showMeshDomain);
  const showFluidInterior = useAppStore((state) => state.showFluidInterior);
  const toggleFluidInterior = useAppStore((state) => state.toggleFluidInterior);
  const setParameter = useAppStore((state) => state.setParameter);
  const resetParameters = useAppStore((state) => state.resetParameters);
  const toggleVisibility = useAppStore((state) => state.toggleVisibility);
  const setTransport = useAppStore((state) => state.setTransport);
  const setMeshingPreset = useAppStore((state) => state.setMeshingPreset);
  const toggleMeshDomain = useAppStore((state) => state.toggleMeshDomain);
  const snapshot = useMemo(() => createGeometrySnapshot(parameters), [parameters]);
  const [isPending, startTransition] = useTransition();

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="sidebar-scroll">
          <div className="button-row">
            <button className="primary-button" onClick={() => resetParameters()}>
              Reset defaults
            </button>
            <button
              className="secondary-button"
              onClick={() =>
                startTransition(() => {
                  void exportCaseJson(parameters, transport, meshingPreset);
                })
              }
            >
              Export case JSON
            </button>
          </div>
          <div className="button-row">
            <button
              className="secondary-button"
              onClick={() =>
                startTransition(() => {
                  void exportStl(parameters, visibility);
                })
              }
            >
              Export STL
            </button>
            <button
              className="secondary-button"
              onClick={() =>
                startTransition(() => {
                  void exportGlb(parameters, visibility);
                })
              }
            >
              Export GLB
            </button>
          </div>
          <ParameterPanel
            title="Primary geometry"
            definitions={parameterSections.primary}
            values={parameters}
            onChange={(key, value) => setParameter(key as keyof CanonicalParameters, value)}
          />
          <ParameterPanel
            title="Structural constants"
            definitions={parameterSections.structural}
            values={parameters}
            onChange={(key, value) => setParameter(key as keyof CanonicalParameters, value)}
          />
          <ParameterPanel
            title="Bend radius"
            definitions={parameterSections.bend}
            values={parameters}
            onChange={(key, value) => setParameter(key as keyof CanonicalParameters, value)}
          />
          <VisibilityToggles visibility={visibility} toggle={toggleVisibility} />
          <MeshingPanel
            parameters={snapshot.parameters}
            derived={snapshot.derived}
            preset={meshingPreset}
            showMeshDomain={showMeshDomain}
            showFluidInterior={showFluidInterior}
            onPresetChange={setMeshingPreset}
            onToggleMeshDomain={toggleMeshDomain}
            onToggleFluidInterior={toggleFluidInterior}
          />
          <TransportPanel transport={transport} onChange={setTransport} />
          <DerivedPanel derived={snapshot.derived} />
          <ConstraintList constraints={snapshot.constraints} />
          <section className="panel">
            <div className="panel-heading">
              <h2>Export notes</h2>
            </div>
            <p className="body-copy">
              Browser exports preserve the current parameter set, the fixed geometry
              group visibility, and the canonical case schema used by the backend.
            </p>
            {isPending ? <p className="body-copy muted">Preparing export...</p> : null}
          </section>
        </div>
      </aside>
      <main className="content">
        <Scene3D
          parameters={parameters}
          visibility={visibility}
          meshingPreset={meshingPreset}
          showMeshDomain={showMeshDomain}
          showFluidInterior={showFluidInterior}
        />
      </main>
    </div>
  );
}

