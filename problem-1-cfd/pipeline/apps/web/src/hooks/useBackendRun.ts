import type {
  CanonicalParameters,
  MeshingConfig,
  TransportConfig,
} from "@fixed-geometry/shared-schema";
import { useEffect, useState } from "react";

import {
  createBackendCase,
  getRunStatus,
  startBackendRun,
  type ApiRunStatus,
} from "@/lib/runApi";

export function useBackendRun(
  parameters: CanonicalParameters,
  transport: TransportConfig,
  meshingPreset: MeshingConfig["preset"],
) {
  const [backendRun, setBackendRun] = useState<ApiRunStatus | null>(null);
  const [runError, setRunError] = useState<string | null>(null);
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

  return {
    backendRun,
    runError,
    isRunPending,
    launchBackendRun,
  };
}
