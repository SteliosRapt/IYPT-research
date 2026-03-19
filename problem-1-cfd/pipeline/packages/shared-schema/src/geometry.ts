import { defaultParameters } from "./metadata/parameterMetadata";
import type {
  CanonicalParameters,
  CaseFile,
  ConstraintResult,
  DerivedGeometry,
  EventThresholds,
  FixedGeometryDescriptor,
  ForcingConfig,
  GeometrySnapshot,
  MeshingConfig,
  NormalizedParameters,
  Point2D,
  SolverConfig,
  TransportConfig
} from "./types";

export const SOURCE_FILES = ["experimental_setup.md", "setup_3d (2).html"] as const;
export const TUBE_WALL_THICKNESS_RATIO = 0.2;

export const HTML_TO_CANONICAL_PARAMETER_MAP = {
  A0: "A0",
  h0: "h0",
  h1: "h1",
  h3: "h3",
  h5: "h5",
  Y2: "Y2",
  Y4: "Y4",
  W1p: "W1",
  W2p: "W2",
  L1: "L1",
  L2: "L2",
  L3: "L3",
  L4: "L4",
  A_tube: "A",
  Wc: "W",
  alpha: "alpha",
  Ct: "Ct",
  ht: "ht",
  P24t: "P24t",
  hw: "hw",
  ha: "h_a",
  bendR: "bendR"
} as const;

const CONSTRAINT_LABELS = [
  { id: "S0_negative", label: "S0 < 0" },
  { id: "ordering", label: "0 < S1 < X2 < X3 < X4 < S2 < X5" },
  { id: "tube_heights_below_h0", label: "h1, h2, h3, h5 < h0" },
  { id: "valleys_below_h2", label: "h1, h3 < h2" },
  { id: "h2_below_h4", label: "h2 < h4" },
  { id: "left_clearance", label: "|S0| >= sqrt(A/pi) + Ct/2" },
  { id: "S1_clearance", label: "S1 >= sqrt(A/pi) + alpha/2" },
  { id: "X2_clearance", label: "X2 >= S1 + alpha/2 + Ct/2" },
  { id: "X3_clearance", label: "X3 >= X2 + alpha/2 + Ct/2" },
  { id: "X4_clearance", label: "X4 >= X3 + alpha" },
  { id: "S2_clearance", label: "S2 >= X4 + alpha + sqrt(A/pi)" },
  { id: "X5_clearance", label: "X5 >= alpha/2 + S2" },
  { id: "alpha_vs_Ct", label: "alpha >= Ct" },
  { id: "alpha_vs_radius", label: "alpha >= 2.5 * sqrt(A/pi)" },
  { id: "P24t_vs_alpha", label: "P24t <= alpha" },
  { id: "arg1", label: "L1^2 >= (h2 - h1)^2" },
  { id: "arg2", label: "L2^2 >= (h3 - h2)^2" },
  { id: "arg3", label: "L3^2 >= (h4 - h3)^2" },
  { id: "arg4", label: "L4^2 >= (h5 - h4)^2" }
] as const;

function clampSqrt(value: number): number {
  return value > 0 ? Math.sqrt(value) : 0;
}

function roundValue(value: number): number {
  return Number(value.toFixed(12));
}

function stableJsonValue(value: unknown): string {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") {
    return JSON.stringify(value);
  }

  if (Array.isArray(value)) {
    return `[${value.map((item) => stableJsonValue(item)).join(", ")}]`;
  }

  return `{${Object.entries(value as Record<string, unknown>)
    .sort(([left], [right]) => {
      if (left < right) {
        return -1;
      }
      if (left > right) {
        return 1;
      }
      return 0;
    })
    .map(([key, item]) => `${JSON.stringify(key)}: ${stableJsonValue(item)}`)
    .join(", ")}}`;
}

function subtleCrypto(): SubtleCrypto {
  if (globalThis.crypto?.subtle) {
    return globalThis.crypto.subtle;
  }
  throw new Error("Web Crypto API is unavailable in this environment.");
}

export function normalizeParameters(
  raw: Partial<Record<string, number>>
): NormalizedParameters {
  const merged: Record<string, number> = { ...defaultParameters };

  for (const [key, value] of Object.entries(raw)) {
    if (typeof value !== "number" || Number.isNaN(value)) {
      continue;
    }
    const mapped = key in HTML_TO_CANONICAL_PARAMETER_MAP
      ? HTML_TO_CANONICAL_PARAMETER_MAP[key as keyof typeof HTML_TO_CANONICAL_PARAMETER_MAP]
      : key;
    merged[mapped] = value;
  }

  const canonical = merged as unknown as CanonicalParameters;
  return {
    ...canonical,
    P4t: canonical.alpha,
    wallThicknessRatio: TUBE_WALL_THICKNESS_RATIO
  };
}

export function buildTubePath(points: Point2D[], bendRadius: number): Point2D[] {
  const allPoints: Point2D[] = [];
  const arcSegments = 24;

  for (let index = 0; index < points.length; index += 1) {
    const current = points[index];

    if (index === 0 || index === points.length - 1) {
      allPoints.push({ x: roundValue(current.x), y: roundValue(current.y) });
      continue;
    }

    const previous = points[index - 1];
    const next = points[index + 1];
    const dxA = current.x - previous.x;
    const dyA = current.y - previous.y;
    const dxB = next.x - current.x;
    const dyB = next.y - current.y;
    const lenA = Math.sqrt(dxA * dxA + dyA * dyA);
    const lenB = Math.sqrt(dxB * dxB + dyB * dyB);

    if (lenA < 1e-8 || lenB < 1e-8) {
      allPoints.push({ x: roundValue(current.x), y: roundValue(current.y) });
      continue;
    }

    const uAx = dxA / lenA;
    const uAy = dyA / lenA;
    const uBx = dxB / lenB;
    const uBy = dyB / lenB;
    const dot = Math.max(-1, Math.min(1, uAx * uBx + uAy * uBy));
    const halfAngle = Math.acos(dot) / 2;

    if (Math.abs(halfAngle) < 1e-6 || Math.abs(Math.PI - halfAngle * 2) < 1e-6) {
      allPoints.push({ x: roundValue(current.x), y: roundValue(current.y) });
      continue;
    }

    const offset = Math.min(bendRadius, lenA * 0.45, lenB * 0.45);
    const p0x = current.x - uAx * offset;
    const p0y = current.y - uAy * offset;
    const p1x = current.x + uBx * offset;
    const p1y = current.y + uBy * offset;
    const pcx = 2 * current.x - 0.5 * (p0x + p1x);
    const pcy = 2 * current.y - 0.5 * (p0y + p1y);

    allPoints.push({ x: roundValue(p0x), y: roundValue(p0y) });
    for (let step = 1; step < arcSegments; step += 1) {
      const s = step / arcSegments;
      const oneMinusS = 1 - s;
      const qx = oneMinusS * oneMinusS * p0x + 2 * oneMinusS * s * pcx + s * s * p1x;
      const qy = oneMinusS * oneMinusS * p0y + 2 * oneMinusS * s * pcy + s * s * p1y;
      allPoints.push({ x: roundValue(qx), y: roundValue(qy) });
    }
    allPoints.push({ x: roundValue(p1x), y: roundValue(p1y) });
  }

  return allPoints;
}

export function computeDerived(parameters: NormalizedParameters): DerivedGeometry {
  const r = Math.sqrt(parameters.A / Math.PI);
  const h2 = parameters.h0 - parameters.Y2;
  const h4 = parameters.h0 + parameters.Y4;
  const arg1 = parameters.L1 * parameters.L1 - (h2 - parameters.h1) * (h2 - parameters.h1);
  const X2 = clampSqrt(arg1);
  const arg2 = parameters.L2 * parameters.L2 - (parameters.h3 - h2) * (parameters.h3 - h2);
  const X3 = clampSqrt(arg2) + X2;
  const arg3 = parameters.L3 * parameters.L3 - (h4 - parameters.h3) * (h4 - parameters.h3);
  const X4 = clampSqrt(arg3) + X3;
  const arg4 = parameters.L4 * parameters.L4 - (parameters.h5 - h4) * (parameters.h5 - h4);
  const X5 = clampSqrt(arg4) + X4;
  const S1 = parameters.W1;
  const S2 = X5 - parameters.W2;
  const S0 = X2 - parameters.A0 / parameters.W;
  const C1 = X2 > 0 ? ((h2 - parameters.h1) / X2) * S1 + parameters.h1 : parameters.h1;
  const C2 = X5 > X4 ? ((parameters.h5 - h4) / (X5 - X4)) * (S2 - X4) + h4 : h4;
  const points = {
    W0: { x: roundValue(S0), y: roundValue(parameters.h0) },
    P1: { x: 0, y: roundValue(parameters.h1) },
    W1: { x: roundValue(S1), y: roundValue(C1) },
    P2: { x: roundValue(X2), y: roundValue(h2) },
    P3: { x: roundValue(X3), y: roundValue(parameters.h3) },
    P4: { x: roundValue(X4), y: roundValue(h4) },
    W2: { x: roundValue(S2), y: roundValue(C2) },
    P5: { x: roundValue(X5), y: roundValue(parameters.h5) }
  };
  const tubePolyline = buildTubePath(
    [points.P1, points.P2, points.P3, points.P4, points.P5],
    parameters.bendR
  );
  const sqrtArgs = { arg1, arg2, arg3, arg4 };

  return {
    r: roundValue(r),
    P4t: roundValue(parameters.P4t),
    h2: roundValue(h2),
    h4: roundValue(h4),
    X2: roundValue(X2),
    X3: roundValue(X3),
    X4: roundValue(X4),
    X5: roundValue(X5),
    S0: roundValue(S0),
    S1: roundValue(S1),
    S2: roundValue(S2),
    C1: roundValue(C1),
    C2: roundValue(C2),
    H0: roundValue((4 * h2) / 5),
    planArea: roundValue(parameters.A0),
    points,
    tubePolyline,
    holderBases: [
      { name: "W1", x: roundValue(S1), y: 0 },
      { name: "P3", x: roundValue(X3), y: 0 },
      { name: "W2", x: roundValue(S2), y: 0 },
      { name: "P4", x: roundValue(X4), y: roundValue(parameters.h0) }
    ],
    structure: {
      containerLeft: roundValue(S0),
      containerRight: roundValue(X2),
      totalHeight: roundValue(parameters.h0 + parameters.h_a),
      columnZ: [
        roundValue(parameters.W / 2 - parameters.alpha / 2),
        roundValue(-(parameters.W / 2 - parameters.alpha / 2))
      ],
      centerRail: {
        startX: roundValue(X2),
        endX: roundValue(X5),
        y: 0
      }
    },
    sqrtArgs
  };
}

export function checkConstraints(parameters: NormalizedParameters, derived: DerivedGeometry): ConstraintResult[] {
  const checks = [
    derived.S0 < 0,
    0 < derived.S1 && derived.S1 < derived.X2 && derived.X2 < derived.X3 && derived.X3 < derived.X4 && derived.X4 < derived.S2 && derived.S2 < derived.X5,
    parameters.h1 < parameters.h0 && derived.h2 < parameters.h0 && parameters.h3 < parameters.h0 && parameters.h5 < parameters.h0,
    parameters.h1 < derived.h2 && parameters.h3 < derived.h2,
    derived.h2 < derived.h4,
    Math.abs(derived.S0) >= derived.r + parameters.Ct / 2,
    derived.S1 >= derived.r + parameters.alpha / 2,
    derived.X2 >= derived.S1 + parameters.alpha / 2 + parameters.Ct / 2,
    derived.X3 >= derived.X2 + parameters.alpha / 2 + parameters.Ct / 2,
    derived.X4 >= derived.X3 + parameters.alpha,
    derived.S2 >= derived.X4 + parameters.alpha + derived.r,
    derived.X5 >= parameters.alpha / 2 + derived.S2,
    parameters.alpha >= parameters.Ct,
    parameters.alpha >= 2.5 * derived.r,
    parameters.P24t <= parameters.alpha,
    derived.sqrtArgs.arg1 >= 0,
    derived.sqrtArgs.arg2 >= 0,
    derived.sqrtArgs.arg3 >= 0,
    derived.sqrtArgs.arg4 >= 0
  ];

  return CONSTRAINT_LABELS.map((constraint, index) => ({
    ...constraint,
    ok: checks[index]
  }));
}

export function createGeometrySnapshot(
  raw: Partial<Record<string, number>>
): GeometrySnapshot {
  const parameters = normalizeParameters(raw);
  const derived = computeDerived(parameters);
  return {
    parameters,
    derived,
    constraints: checkConstraints(parameters, derived)
  };
}

export function buildFixedGeometryDescriptors(
  parameters: NormalizedParameters,
  derived: DerivedGeometry
): Record<"container" | "tube" | "holders" | "columns", FixedGeometryDescriptor[]> {
  const containerLength = derived.X2 - derived.S0;
  const centerX = derived.S0 + containerLength / 2;
  const totalHeight = parameters.h0 + parameters.h_a;
  const frontZ = parameters.W / 2 - parameters.alpha / 2;
  const backZ = -frontZ;
  const beamLength = Math.max(derived.X4 - parameters.alpha / 2 - derived.X2, 0);
  const beamCenter = beamLength > 0 ? derived.X2 + beamLength / 2 : derived.X2;
  const innerRadius = Math.max(derived.r * (1 - parameters.wallThicknessRatio), derived.r * 0.1);

  return {
    container: [
      {
        type: "box",
        name: "bottom",
        center: [roundValue(centerX), 0, 0],
        size: [roundValue(containerLength + parameters.Ct), roundValue(parameters.Ct), roundValue(parameters.W)]
      },
      {
        type: "box",
        name: "leftWall",
        center: [roundValue(derived.S0), roundValue(totalHeight / 2), 0],
        size: [roundValue(parameters.Ct), roundValue(totalHeight), roundValue(parameters.W)]
      },
      {
        type: "wallWithHole",
        name: "rightWall",
        center: [roundValue(derived.X2), roundValue(totalHeight / 2), 0],
        size: [roundValue(parameters.Ct), roundValue(totalHeight), roundValue(parameters.W)],
        hole: {
          radius: derived.r,
          centerY: derived.h2
        }
      },
      {
        type: "box",
        name: "frontWall",
        center: [roundValue(centerX), roundValue(totalHeight / 2), roundValue(parameters.W / 2)],
        size: [roundValue(containerLength + parameters.Ct), roundValue(totalHeight), roundValue(parameters.Ct)]
      },
      {
        type: "box",
        name: "backWall",
        center: [roundValue(centerX), roundValue(totalHeight / 2), roundValue(-parameters.W / 2)],
        size: [roundValue(containerLength + parameters.Ct), roundValue(totalHeight), roundValue(parameters.Ct)]
      }
    ],
    tube: [
      {
        type: "tube",
        name: "tubeShell",
        path: derived.tubePolyline.map((point) => [point.x, point.y, 0]),
        outerRadius: derived.r,
        innerRadius,
        wallThickness: roundValue(derived.r - innerRadius)
      }
    ],
    holders: [
      {
        type: "holder",
        name: "W1Holder",
        center: [derived.S1, 0, 0],
        pointHeight: derived.C1,
        baseY: 0,
        alpha: parameters.alpha,
        hw: parameters.hw,
        ht: parameters.ht,
        plateThickness: parameters.Ct,
        tubeRadius: derived.r
      },
      {
        type: "holder",
        name: "P3Holder",
        center: [derived.X3, 0, 0],
        pointHeight: parameters.h3,
        baseY: 0,
        alpha: parameters.alpha,
        hw: parameters.hw,
        ht: parameters.ht,
        plateThickness: parameters.Ct,
        tubeRadius: derived.r
      },
      {
        type: "holder",
        name: "W2Holder",
        center: [derived.S2, 0, 0],
        pointHeight: derived.C2,
        baseY: 0,
        alpha: parameters.alpha,
        hw: parameters.hw,
        ht: parameters.ht,
        plateThickness: parameters.Ct,
        tubeRadius: derived.r
      },
      {
        type: "holder",
        name: "P4Holder",
        center: [derived.X4, parameters.h0, 0],
        pointHeight: parameters.Y4,
        baseY: parameters.h0,
        alpha: parameters.alpha,
        hw: parameters.hw,
        ht: parameters.ht,
        plateThickness: parameters.Ct,
        tubeRadius: derived.r
      }
    ],
    columns: [
      {
        type: "box",
        name: "P4Platform",
        center: [derived.X4, parameters.h0, 0],
        size: [parameters.alpha, parameters.Ct, parameters.W]
      },
      {
        type: "box",
        name: "FrontColumn",
        center: [derived.X4, parameters.h0 / 2, frontZ],
        size: [parameters.alpha, parameters.h0, parameters.alpha]
      },
      {
        type: "box",
        name: "BackColumn",
        center: [derived.X4, parameters.h0 / 2, backZ],
        size: [parameters.alpha, parameters.h0, parameters.alpha]
      },
      {
        type: "box",
        name: "FrontTopBeam",
        center: [beamCenter, parameters.h0, frontZ],
        size: [beamLength, parameters.Ct, parameters.alpha]
      },
      {
        type: "box",
        name: "BackTopBeam",
        center: [beamCenter, parameters.h0, backZ],
        size: [beamLength, parameters.Ct, parameters.alpha]
      },
      {
        type: "box",
        name: "FrontBottomBeam",
        center: [beamCenter, 0, frontZ],
        size: [beamLength, parameters.Ct, parameters.alpha]
      },
      {
        type: "box",
        name: "BackBottomBeam",
        center: [beamCenter, 0, backZ],
        size: [beamLength, parameters.Ct, parameters.alpha]
      },
      {
        type: "box",
        name: "FloorPlatform",
        center: [derived.X4, 0, 0],
        size: [parameters.alpha, parameters.Ct, parameters.W]
      },
      {
        type: "box",
        name: "CenterRail",
        center: [roundValue((derived.X2 + derived.X5) / 2), 0, 0],
        size: [roundValue(Math.max(derived.X5 - derived.X2, 0)), parameters.Ct, parameters.alpha]
      }
    ]
  };
}

export async function stableStringHash(value: string): Promise<string> {
  const bytes = new TextEncoder().encode(value);
  const hashBuffer = await subtleCrypto().digest("SHA-256", bytes);
  return Array.from(
    new Uint8Array(hashBuffer),
    (byte) => byte.toString(16).padStart(2, "0")
  ).join("").slice(0, 10);
}

export function defaultEventThresholds(): EventThresholds {
  return {
    eps_H: 1e-3,
    eps_dHdt: 1e-4,
    eps_Q: 1e-6,
    T_ss: 1.0,
    dwell: 1.0,
    requireQBalance: false
  };
}

export function defaultMeshingConfig(): MeshingConfig {
  return {
    preset: "coarse"
  };
}

export function defaultTransportConfig(): TransportConfig {
  return {
    waterNu: 1e-6,
    waterRho: 998.2,
    airNu: 1.5e-5,
    airRho: 1.2,
    sigma: 0.072,
  };
}

export function defaultForcingConfig(): ForcingConfig {
  return {
    mode: "inflow_patch",
    topPatchFraction: 0.18,
    inflowVelocity: 0.02,
    volumetricSourceRate: 0.0,
    reservoirHead: 0.0
  };
}

export function defaultSolverConfig(): SolverConfig {
  return {
    solver: "interFoam",
    startTime: 0,
    endTime: 15,
    deltaT: 0.02,
    writeInterval: 0.1,
    chunkDuration: 0.5,
    tubeWallThicknessRatio: TUBE_WALL_THICKNESS_RATIO
  };
}

export async function createDefaultCase(
  parameters: Partial<Record<string, number>> = {},
  transport?: TransportConfig,
  meshingPreset: MeshingConfig["preset"] = "coarse"
): Promise<CaseFile> {
  const snapshot = createGeometrySnapshot(parameters);
  const { P4t: _p4t, wallThicknessRatio: _wallThicknessRatio, ...caseParameters } = snapshot.parameters;
  const resolvedTransport = transport ?? defaultTransportConfig();
  const resolvedMeshing = { preset: meshingPreset } satisfies MeshingConfig;
  const resolvedSolver = defaultSolverConfig();
  const resolvedForcing = defaultForcingConfig();
  const resolvedEventThresholds = defaultEventThresholds();
  const parameterHash = await stableStringHash(stableJsonValue(caseParameters));
  const caseId = `case-${await stableStringHash(
    stableJsonValue({
      displayName: "Default fixed-geometry case",
      parameters: caseParameters,
      transport: resolvedTransport,
      forcing: resolvedForcing,
      solver: resolvedSolver,
      eventThresholds: resolvedEventThresholds,
      meshing: { preset: resolvedMeshing.preset }
    })
  )}`;

  return {
    schemaVersion: "1.0.0",
    caseId,
    displayName: "Default fixed-geometry case",
    parameters: caseParameters,
    derived: snapshot.derived,
    geometry: {
      fluidBoundaryPatches: ["walls", "topAtmosphere", "topInflow", "tubeOutlet"],
      fixedGeometryGroups: ["container", "tube", "holders", "columns"]
    },
    meshing: resolvedMeshing,
    transport: resolvedTransport,
    solver: resolvedSolver,
    forcing: resolvedForcing,
    eventThresholds: resolvedEventThresholds,
    outputs: {
      exportRoot: "examples/generated/case-default"
    },
    runStatus: {
      state: "not_started"
    },
    provenance: {
      parameterHash,
      gitCommit: null,
      sourceFiles: [...SOURCE_FILES]
    }
  };
}
