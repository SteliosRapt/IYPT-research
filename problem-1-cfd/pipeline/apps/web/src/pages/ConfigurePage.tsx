import {
  createGeometrySnapshot,
  type CanonicalParameters,
} from "@fixed-geometry/shared-schema";
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

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
import {
  createBackendCase,
  getRunStatus,
  startBackendRun,
  type ApiRunStatus as BackendRunStatus,
} from "@/lib/runApi";

export function ConfigurePage() {
  const navigate = useNavigate();
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
  const [backendRun, setBackendRun] = useState<BackendRunStatus | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
  const [isExportPending, setIsExportPending] = useState(false);
  const [isRunPending, setIsRunPending] = useState(false);

  useEffect(() => {
    if (!backendRun || !["queued", "running"].includes(backendRun.state)) {
      return;
    }

    let cancelled = false;
    let timer: number | null = null;

    const pollStatus = async () => {
      try {
        const nextStatus = await getRunStatus(backendRun.runId);
        if (cancelled) {
          return;
        }
        setBackendRun(nextStatus);
        if (["queued", "running"].includes(nextStatus.state)) {
          timer = window.setTimeout(() => {
            void pollStatus();
          }, 1000);
        }
      } catch (error) {
        if (cancelled) {
          return;
        }
        setRunError(error instanceof Error ? error.message : "Failed to poll API run status.");
      }
    };

    void pollStatus();
    return () => {
      cancelled = true;
      if (timer !== null) {
        window.clearTimeout(timer);
      }
    };
  }, [backendRun]);

  const exportCurrentCase = async () => {
    setIsExportPending(true);
    try {
      await exportCaseJson(parameters, transport, meshingPreset);
    } finally {
      setIsExportPending(false);
    }
  };

  const launchBackendRun = async () => {
    setIsRunPending(true);
    setRunError(null);
    setBackendRun(null);
    try {
      const caseResponse = await createBackendCase(parameters, transport, meshingPreset);
      const runStatus = await startBackendRun(caseResponse.caseId, "auto");
      setBackendRun(runStatus);
    } catch (error) {
      setRunError(error instanceof Error ? error.message : "Failed to start backend run.");
    } finally {
      setIsRunPending(false);
    }
  };

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
              onClick={() => {
                void exportCurrentCase();
              }}
            >
              Export case JSON
            </button>
          </div>
          <div className="button-row">
            <button
              className="primary-button"
              disabled={isRunPending || backendRun?.state === "queued" || backendRun?.state === "running"}
              onClick={() => {
                void launchBackendRun();
              }}
            >
              Run via API
            </button>
            {backendRun?.state === "done" ? (
              <button
                className="secondary-button"
                onClick={() => navigate(`/runs?manifest=${encodeURIComponent(backendRun.manifestUrl)}`)}
              >
                Open run
              </button>
            ) : null}
          </div>
          <div className="button-row">
            <button
              className="secondary-button"
              onClick={() => {
                void exportStl(parameters, visibility);
              }}
            >
              Export STL
            </button>
            <button
              className="secondary-button"
              onClick={() => {
                void exportGlb(parameters, visibility);
              }}
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
              <h2>Export and API</h2>
            </div>
            <p className="body-copy">
              Browser exports preserve the current parameter set, the fixed geometry
              group visibility, and the canonical case schema used by the backend.
            </p>
            <p className="body-copy muted">
              Start the local API with <code>python -m services.api.server</code> to enable
              browser-triggered runs. If the configured solver is on PATH, the API uses real
              solver-backed post-processing; otherwise it falls back to the mock path.
            </p>
            {isExportPending ? <p className="body-copy muted">Preparing export...</p> : null}
            {isRunPending ? <p className="body-copy muted">Submitting browser run...</p> : null}
            {backendRun ? (
              <div className="status-block">
                <span>API run state</span>
                <strong>
                  {backendRun.state} ({backendRun.mode})
                </strong>
              </div>
            ) : null}
            {backendRun?.state === "done" ? (
              <p className="body-copy muted">
                The backend run is ready. Open it in the Runs page to inspect the generated
                manifest and viewer assets.
              </p>
            ) : null}
            {runError ? <p className="body-copy">{runError}</p> : null}
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

