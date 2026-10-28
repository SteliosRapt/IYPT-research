import type { RunManifest } from "@fixed-geometry/shared-schema";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import type { MeshJson } from "@/lib/meshBuilders";
import {
  loadExampleIndex,
  loadRunBundle,
  type ExampleIndex,
  type SeriesPoint,
} from "@/lib/runManifest";

export function useRunsPageState() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [indexData, setIndexData] = useState<ExampleIndex | null>(null);
  const [selectedManifestPath, setSelectedManifestPath] = useState<string | null>(null);
  const [customPath, setCustomPath] = useState("");
  const [manifest, setManifest] = useState<RunManifest | null>(null);
  const [fixedGeometry, setFixedGeometry] = useState<Record<string, unknown[]> | null>(null);
  const [frames, setFrames] = useState<MeshJson[]>([]);
  const [heightSeries, setHeightSeries] = useState<SeriesPoint[]>([]);
  const [flowSeries, setFlowSeries] = useState<SeriesPoint[]>([]);
  const [dischargedSeries, setDischargedSeries] = useState<SeriesPoint[]>([]);
  const [frameIndex, setFrameIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const manifestQuery = searchParams.get("manifest");

  const selectManifest = (manifestPath: string) => {
    setSelectedManifestPath(manifestPath);
    setSearchParams({ manifest: manifestPath });
  };

  const reloadIndex = async () => {
    const nextIndex = await loadExampleIndex();
    setIndexData(nextIndex);
    if (!manifestQuery && !selectedManifestPath) {
      setSelectedManifestPath(nextIndex.runs[0]?.manifest ?? null);
    }
  };

  useEffect(() => {
    void reloadIndex();
  }, []);

  useEffect(() => {
    if (manifestQuery) {
      setSelectedManifestPath(manifestQuery);
    }
  }, [manifestQuery]);

  useEffect(() => {
    if (!selectedManifestPath) {
      return;
    }
    let cancelled = false;

    void (async () => {
      const bundle = await loadRunBundle(selectedManifestPath);
      if (cancelled) {
        return;
      }
      setManifest(bundle.manifest);
      setFixedGeometry(bundle.fixedGeometry);
      setHeightSeries(bundle.heightSeries);
      setFlowSeries(bundle.flowSeries);
      setDischargedSeries(bundle.dischargedSeries);
      setFrames(bundle.frames);
      setFrameIndex(0);
      setPlaying(false);
    })();

    return () => {
      cancelled = true;
    };
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

  return {
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
  };
}
