export type ParameterId =
  | "A0"
  | "h0"
  | "h1"
  | "h3"
  | "h5"
  | "Y2"
  | "Y4"
  | "W1"
  | "W2"
  | "L1"
  | "L2"
  | "L3"
  | "L4"
  | "A"
  | "W"
  | "alpha"
  | "Ct"
  | "ht"
  | "P24t"
  | "hw"
  | "h_a"
  | "bendR";

export interface ParameterDefinition {
  id: ParameterId;
  label: string;
  section: "primary" | "structural" | "bend";
  min: number;
  max: number;
  step: number;
  defaultValue: number;
}

export interface CanonicalParameters {
  A0: number;
  h0: number;
  h1: number;
  h3: number;
  h5: number;
  Y2: number;
  Y4: number;
  W1: number;
  W2: number;
  L1: number;
  L2: number;
  L3: number;
  L4: number;
  A: number;
  W: number;
  alpha: number;
  Ct: number;
  ht: number;
  P24t: number;
  hw: number;
  h_a: number;
  bendR: number;
}

export interface NormalizedParameters extends CanonicalParameters {
  P4t: number;
  wallThicknessRatio: number;
}

export interface Point2D {
  x: number;
  y: number;
}

export interface SqrtArgs {
  arg1: number;
  arg2: number;
  arg3: number;
  arg4: number;
}

export type CaseRunStatusState = "not_started" | "generated" | "running" | "done" | "failed";
export type RunManifestStatus = "mock" | "running" | "done" | "failed";

export interface DerivedGeometry {
  r: number;
  P4t: number;
  h2: number;
  h4: number;
  X2: number;
  X3: number;
  X4: number;
  X5: number;
  S0: number;
  S1: number;
  S2: number;
  C1: number;
  C2: number;
  H0: number;
  planArea: number;
  points: Record<"W0" | "P1" | "W1" | "P2" | "P3" | "P4" | "W2" | "P5", Point2D>;
  tubePolyline: Point2D[];
  holderBases: Array<{ name: "W1" | "P3" | "W2" | "P4"; x: number; y: number }>;
  structure: {
    containerLeft: number;
    containerRight: number;
    totalHeight: number;
    columnZ: [number, number];
    centerRail: { startX: number; endX: number; y: number };
  };
  sqrtArgs: SqrtArgs;
}

export interface ConstraintResult {
  id: string;
  label: string;
  ok: boolean;
}

export interface GeometrySnapshot {
  parameters: NormalizedParameters;
  derived: DerivedGeometry;
  constraints: ConstraintResult[];
}

export interface PrimitiveBoxDescriptor {
  type: "box";
  name: string;
  center: [number, number, number];
  size: [number, number, number];
}

export interface PrimitiveWallWithHoleDescriptor {
  type: "wallWithHole";
  name: string;
  center: [number, number, number];
  size: [number, number, number];
  hole: {
    radius: number;
    centerY: number;
  };
}

export interface PrimitiveTubeDescriptor {
  type: "tube";
  name: string;
  path: [number, number, number][];
  outerRadius: number;
  innerRadius: number;
  wallThickness: number;
}

export interface PrimitiveHolderDescriptor {
  type: "holder";
  name: string;
  center: [number, number, number];
  pointHeight: number;
  baseY: number;
  alpha: number;
  hw: number;
  ht: number;
  plateThickness: number;
  tubeRadius: number;
}

export type FixedGeometryDescriptor =
  | PrimitiveBoxDescriptor
  | PrimitiveWallWithHoleDescriptor
  | PrimitiveTubeDescriptor
  | PrimitiveHolderDescriptor;

export interface TransportConfig {
  waterNu: number;
  waterRho: number;
  airNu: number;
  airRho: number;
  sigma: number;
}

export interface EventThresholds {
  eps_H: number;
  eps_dHdt: number;
  eps_Q: number;
  T_ss: number;
  dwell: number;
  requireQBalance: boolean;
}

export interface MeshingConfig {
  preset: "coarse" | "medium" | "fine";
  backgroundCellSize?: number;
  refinementLevels?: {
    opening: number;
    bends: number;
    outlet: number;
    freeSurface: number;
  };
}

export interface ForcingConfig {
  mode: "none" | "inflow_patch" | "volumetric_source" | "reservoir_head";
  topPatchFraction: number;
  inflowVelocity: number;
  volumetricSourceRate: number;
  reservoirHead: number;
}

export interface SolverConfig {
  solver: "interFoam" | "interIsoFoam";
  startTime: number;
  endTime: number;
  deltaT: number;
  writeInterval: number;
  chunkDuration: number;
  tubeWallThicknessRatio: number;
}

export interface ProvenanceMetadata {
  parameterHash: string;
  gitCommit: string | null;
  sourceFiles: string[];
}

export interface CaseFile {
  schemaVersion: "1.0.0";
  caseId: string;
  displayName: string;
  parameters: CanonicalParameters;
  derived: DerivedGeometry;
  geometry: {
    fluidBoundaryPatches: string[];
    fixedGeometryGroups: string[];
  };
  meshing: MeshingConfig;
  transport: TransportConfig;
  solver: SolverConfig;
  forcing: ForcingConfig;
  eventThresholds: EventThresholds;
  outputs: {
    exportRoot: string;
    manifestPath?: string;
  };
  runStatus: {
    state: CaseRunStatusState;
    reason?: string;
  };
  provenance: ProvenanceMetadata;
}

export interface RunManifest {
  schemaVersion: "1.0.0";
  caseId: string;
  displayName: string;
  timeSteps: number[];
  chartSeries: {
    height: string;
    outletFlow: string;
    dischargedVolume: string;
  };
  geometryAssets: {
    fixedGlb: string | null;
    fixedJson: string;
  };
  fluidAssets: {
    interfaceFrames: string[];
  };
  events: {
    t_h0_up: number | null;
    t_steady: number | null;
    terminationReason: string;
    currentState: "PRE_H0" | "POST_H0_MONITORING" | "DONE";
  };
  status: RunManifestStatus;
  paraview: {
    foamFile: string | null;
    vtkDir: string | null;
  };
  metadata: ProvenanceMetadata & {
    meshPreset: "coarse" | "medium" | "fine";
    solverName: "interFoam" | "interIsoFoam";
  };
}
