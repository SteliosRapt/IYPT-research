import { ChartPanel } from "@/components/ChartPanel";
import { RunViewer } from "@/components/RunViewer";
import { useAppStore } from "@/app/store";
import { useRunsPageState } from "@/hooks/useRunsPageState";

export function RunsPage() {
  const visibility = useAppStore((state) => state.visibility);
  const {
    indexData,
    selectedManifestPath,
    customPath,
    setCustomPath,
    manifest,
    fixedGeometry,
    heightSeries,
    flowSeries,
    dischargedSeries,
    frameIndex,
    setFrameIndex,
    playing,
    setPlaying,
    activeFrame,
    reloadIndex,
    selectManifest,
  } = useRunsPageState();

  if (!manifest || !fixedGeometry || !indexData) {
    return <div className="empty-state">Loading example manifests...</div>;
  }

  return (
    <div className="runs-layout">
      <section className="runs-sidebar">
        <div className="panel">
          <div className="panel-heading">
            <h2>Available runs</h2>
            <button className="secondary-button" style={{ fontSize: "0.75rem", padding: "0.2rem 0.6rem" }} onClick={reloadIndex}>
              Refresh
            </button>
          </div>
          <div className="run-list">
            {indexData.runs.map((run) => (
              <button
                className={run.manifest === selectedManifestPath ? "run-pill active" : "run-pill"}
                key={run.id}
                onClick={() => selectManifest(run.manifest)}
              >
                {run.label}
              </button>
            ))}
          </div>
          <div style={{ marginTop: "0.75rem" }}>
            <p className="body-copy muted" style={{ marginBottom: "0.35rem", fontSize: "0.72rem" }}>
              Load by path (relative to examples/, e.g. sample-runs/default-mock/manifest.json)
            </p>
            <div style={{ display: "flex", gap: "0.4rem" }}>
              <input
                style={{ flex: 1, fontSize: "0.75rem", padding: "0.25rem 0.4rem", background: "#12121c", border: "1px solid #303050", color: "#d0d8e8", borderRadius: "4px" }}
                placeholder="run-name/manifest.json"
                value={customPath}
                onChange={(e) => setCustomPath(e.currentTarget.value)}
                onKeyDown={(e) => { if (e.key === "Enter" && customPath) selectManifest(customPath); }}
              />
              <button
                className="secondary-button"
                style={{ fontSize: "0.75rem", padding: "0.2rem 0.6rem", whiteSpace: "nowrap" }}
                onClick={() => { if (customPath) selectManifest(customPath); }}
              >
                Load
              </button>
            </div>
          </div>
        </div>
        <div className="panel">
          <div className="panel-heading">
            <h2>Playback</h2>
          </div>
          <p className="body-copy">
            Time {manifest.timeSteps[frameIndex]?.toFixed(2)} s
          </p>
          <input
            className="scrubber"
            type="range"
            min={0}
            max={Math.max(frames.length - 1, 0)}
            value={frameIndex}
            onChange={(event) => setFrameIndex(Number.parseInt(event.currentTarget.value, 10))}
          />
          <div className="button-row">
            <button className="primary-button" onClick={() => setPlaying((value) => !value)}>
              {playing ? "Pause" : "Play"}
            </button>
          </div>
          <div className="status-block">
            <span>h0 crossing</span>
            <strong>{manifest.events.t_h0_up?.toFixed(2) ?? "n/a"} s</strong>
          </div>
          <div className="status-block">
            <span>steady stop</span>
            <strong>{manifest.events.t_steady?.toFixed(2) ?? "n/a"} s</strong>
          </div>
          <div className="status-block">
            <span>termination</span>
            <strong>{manifest.events.terminationReason}</strong>
          </div>
        </div>
      </section>
      <section className="runs-content">
        <RunViewer
          manifest={manifest}
          fixedGeometry={fixedGeometry}
          frame={activeFrame}
          visibility={visibility}
        />
        <ChartPanel
          manifest={manifest}
          heightSeries={heightSeries}
          flowSeries={flowSeries}
          dischargedSeries={dischargedSeries}
        />
      </section>
    </div>
  );
}

