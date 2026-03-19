import type { RunManifest } from "@fixed-geometry/shared-schema";
import { useEffect, useMemo, useState } from "react";

import { ChartPanel } from "@/components/ChartPanel";
import { RunViewer } from "@/components/RunViewer";
import { useAppStore } from "@/app/store";
import type { MeshJson } from "@/lib/meshBuilders";

type ExampleIndex = {
  runs: Array<{
    id: string;
    label: string;
    manifest: string;
  }>;
};

type SeriesPoint = { time: number; value: number };

export function RunsPage() {
  const visibility = useAppStore((state) => ({
    container: state.visibility.container,
    tube: state.visibility.tube,
    holders: state.visibility.holders,
    columns: state.visibility.columns,
  }));
  const [indexData, setIndexData] = useState<ExampleIndex | null>(null);
  const [selectedManifestPath, setSelectedManifestPath] = useState<string | null>(null);
  const [manifest, setManifest] = useState<RunManifest | null>(null);
  const [fixedGeometry, setFixedGeometry] = useState<Record<string, unknown[]> | null>(null);
  const [frames, setFrames] = useState<MeshJson[]>([]);
  const [heightSeries, setHeightSeries] = useState<SeriesPoint[]>([]);
  const [flowSeries, setFlowSeries] = useState<SeriesPoint[]>([]);
  const [dischargedSeries, setDischargedSeries] = useState<SeriesPoint[]>([]);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);

  useEffect(() => {
    fetch("/index.json")
      .then((response) => response.json())
      .then((value: ExampleIndex) => {
        setIndexData(value);
        setSelectedManifestPath(value.runs[0]?.manifest ?? null);
      });
  }, []);

  useEffect(() => {
    if (!selectedManifestPath) {
      return;
    }
    void (async () => {
      const manifestValue = (await fetch(`/${selectedManifestPath}`).then((response) =>
        response.json()
      )) as RunManifest;
      setManifest(manifestValue);

      const [geometryValue, heightValue, flowValue, dischargedValue, frameValues] =
        await Promise.all([
          fetch(`/${selectedManifestPath.replace("manifest.json", manifestValue.geometryAssets.fixedJson)}`).then((response) => response.json()),
          fetch(`/${selectedManifestPath.replace("manifest.json", manifestValue.chartSeries.height)}`).then((response) => response.json()),
          fetch(`/${selectedManifestPath.replace("manifest.json", manifestValue.chartSeries.outletFlow)}`).then((response) => response.json()),
          fetch(`/${selectedManifestPath.replace("manifest.json", manifestValue.chartSeries.dischargedVolume)}`).then((response) => response.json()),
          Promise.all(
            manifestValue.fluidAssets.interfaceFrames.map((framePath) =>
              fetch(`/${selectedManifestPath.replace("manifest.json", framePath)}`).then((response) =>
                response.json()
              )
            )
          ),
        ]);

      setFixedGeometry(geometryValue as Record<string, unknown[]>);
      setHeightSeries(heightValue as SeriesPoint[]);
      setFlowSeries(flowValue as SeriesPoint[]);
      setDischargedSeries(dischargedValue as SeriesPoint[]);
      setFrames(frameValues as MeshJson[]);
      setFrameIndex(0);
      setPlaying(false);
    })();
  }, [selectedManifestPath]);

  useEffect(() => {
    if (!playing || frames.length === 0) {
      return;
    }
    const timer = window.setInterval(() => {
      setFrameIndex((current) => (current + 1) % frames.length);
    }, 120);
    return () => window.clearInterval(timer);
  }, [playing, frames.length]);

  const activeFrame = useMemo(() => frames[frameIndex] ?? null, [frames, frameIndex]);

  if (!manifest || !fixedGeometry || !indexData) {
    return <div className="empty-state">Loading example manifests...</div>;
  }

  return (
    <div className="runs-layout">
      <section className="runs-sidebar">
        <div className="panel">
          <div className="panel-heading">
            <h2>Available runs</h2>
          </div>
          <div className="run-list">
            {indexData.runs.map((run) => (
              <button
                className={run.manifest === selectedManifestPath ? "run-pill active" : "run-pill"}
                key={run.id}
                onClick={() => setSelectedManifestPath(run.manifest)}
              >
                {run.label}
              </button>
            ))}
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

