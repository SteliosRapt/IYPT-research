import type {
  CanonicalParameters,
  MeshingConfig,
  TransportConfig,
} from "@fixed-geometry/shared-schema";

export type ApiCaseResponse = {
  caseId: string;
  caseUrl: string;
  caseFile: unknown;
};

export type ApiRunStatus = {
  runId: string;
  caseId: string;
  mode: "mock" | "real";
  state: "queued" | "running" | "done" | "failed";
  createdAt: string;
  updatedAt: string;
  startedAt: string | null;
  completedAt: string | null;
  statusUrl: string;
  manifestUrl: string;
  error: string | null;
};

async function readJson<T>(response: Response): Promise<T> {
  const payload = (await response.json()) as T | { error?: string };
  if (!response.ok) {
    const message =
      typeof payload === "object" && payload !== null && "error" in payload && typeof payload.error === "string"
        ? payload.error
        : `${response.status} ${response.statusText}`;
    throw new Error(message);
  }
  return payload as T;
}

export async function createBackendCase(
  parameters: CanonicalParameters,
  transport: TransportConfig,
  meshingPreset: MeshingConfig["preset"]
): Promise<ApiCaseResponse> {
  const response = await fetch("/api/cases", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      parameters,
      transport,
      meshingPreset,
    }),
  });
  return readJson<ApiCaseResponse>(response);
}

export async function startBackendRun(caseId: string, mode: "auto" | "mock" | "real" = "auto"): Promise<ApiRunStatus> {
  const response = await fetch(`/api/cases/${caseId}/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mode }),
  });
  return readJson<ApiRunStatus>(response);
}

export async function getRunStatus(runId: string): Promise<ApiRunStatus> {
  const response = await fetch(`/api/runs/${runId}/status`);
  return readJson<ApiRunStatus>(response);
}

export function resolveManifestUrl(manifestPath: string): string {
  return new URL(manifestPath, window.location.origin).toString();
}

export function resolveAssetUrl(manifestPath: string, assetPath: string): string {
  return new URL(assetPath, resolveManifestUrl(manifestPath)).toString();
}
