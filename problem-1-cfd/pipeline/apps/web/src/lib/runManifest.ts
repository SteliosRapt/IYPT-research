import type { RunManifest } from "@fixed-geometry/shared-schema";

import type { MeshJson } from "@/lib/meshBuilders";
import { resolveAssetUrl, resolveManifestUrl } from "@/lib/runApi";

export const EXAMPLE_CATALOG_PATH = "/catalog/index.json";

export type ExampleIndex = {
  runs: Array<{
    id: string;
    label: string;
    manifest: string;
  }>;
};

export type SeriesPoint = { time: number; value: number };

export type LoadedRunBundle = {
  manifest: RunManifest;
  fixedGeometry: Record<string, unknown[]>;
  heightSeries: SeriesPoint[];
  flowSeries: SeriesPoint[];
  dischargedSeries: SeriesPoint[];
  frames: MeshJson[];
};

async function readJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  return response.json() as Promise<T>;
}

export async function loadExampleIndex(): Promise<ExampleIndex> {
  return readJson<ExampleIndex>(`${EXAMPLE_CATALOG_PATH}?${Date.now()}`);
}

export async function loadRunBundle(manifestPath: string): Promise<LoadedRunBundle> {
  const manifestUrl = resolveManifestUrl(manifestPath);
  const manifest = await readJson<RunManifest>(manifestUrl);
  const [fixedGeometry, heightSeries, flowSeries, dischargedSeries, frames] = await Promise.all([
    readJson<Record<string, unknown[]>>(resolveAssetUrl(manifestUrl, manifest.geometryAssets.fixedJson)),
    readJson<SeriesPoint[]>(resolveAssetUrl(manifestUrl, manifest.chartSeries.height)),
    readJson<SeriesPoint[]>(resolveAssetUrl(manifestUrl, manifest.chartSeries.outletFlow)),
    readJson<SeriesPoint[]>(resolveAssetUrl(manifestUrl, manifest.chartSeries.dischargedVolume)),
    Promise.all(
      manifest.fluidAssets.interfaceFrames.map((framePath) =>
        readJson<MeshJson>(resolveAssetUrl(manifestUrl, framePath))
      )
    ),
  ]);

  return {
    manifest,
    fixedGeometry,
    heightSeries,
    flowSeries,
    dischargedSeries,
    frames,
  };
}
