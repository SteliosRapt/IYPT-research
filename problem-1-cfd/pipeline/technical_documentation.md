# Fixed-Geometry CFD Pipeline — Technical Documentation

**Version 0.1.0 · March 2026 · Repository: Problem\_1\_CFD\_1**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Repository Structure](#2-repository-structure)
3. [Architecture & Data Flow](#3-architecture--data-flow)
4. [Python Backend Services](#4-python-backend-services)
5. [TypeScript & Shared Schema Package](#5-typescript--shared-schema-package)
6. [Key Algorithms](#6-key-algorithms)
7. [Data Schemas](#7-data-schemas)
8. [CLI Reference](#8-cli-reference)
9. [Configuration & Environment](#9-configuration--environment)
10. [Testing](#10-testing)
11. [Known Limitations](#11-known-limitations)

---

## 1. Project Overview

The Fixed-Geometry CFD Pipeline is an MVP monorepo that converts a physical experimental apparatus (described in `experimental_setup.md` and `setup_3d (2).html`) into a complete simulation and visualisation workflow. The pipeline produces:

- A browser-based configurator for adjusting the 22 free parameters of the geometry.
- A canonical case JSON that acts as the single source of truth for one simulation configuration.
- An OpenFOAM-style case directory (`blockMeshDict`, `snappyHexMeshDict`, field files, `Allrun` script).
- Event detection logic (h0 crossing, steady-state detection) operating on time-series data.
- Viewer assets: per-frame JSON meshes, time-series JSON series, and legacy VTK files compatible with ParaView.
- A React/Vite web application for parameter configuration, 3D preview, and run browsing.

The physical experiment models an open-top container fed by an inflow patch on its top face. Water drains through a bent tube that passes through the right wall of the container. The geometry is fixed (no moving parts, no FSI). The CFD solver is OpenFOAM `interFoam` (two-phase incompressible VOF). When OpenFOAM is unavailable, the pipeline generates a synthetic mock run to keep the viewer functional.

---

## 2. Repository Structure

| Path | Purpose |
|------|---------|
| `packages/shared-schema/` | JSON schemas, TypeScript types, parameter metadata, and geometry formulas shared between frontend and any TypeScript consumers. |
| `services/api/` | Python: lightweight HTTP API for browser-triggered case creation, `auto | mock | real` run submission, status polling, and run asset delivery. |
| `services/geometry/` | Python: canonical parameter normalisation, derived geometry computation, constraint checking, and geometry descriptor builders. |
| `services/orchestrator/` | Python: OpenFOAM-style case generation, event detection, and run orchestration CLI. |
| `services/viewer_data/` | Python: synthetic time-series generation, per-frame JSON/VTK output, and run manifest assembly. |
| `services/utils.py` | Python: shared JSON/text output helpers and stable hashing used across services. |
| `apps/web/` | React 18 + Vite SPA. Two pages: Configure (parameter editor + 3D scene) and Runs (manifest browser + chart). |
| `solver/openfoam-template/` | Docker image definition and runtime reference scripts; WSL with OpenFOAM on PATH is the preferred local OpenFOAM environment on Windows. |
| `examples/` | Committed default case JSON, generated OpenFOAM-style case directory, and a full synthetic mock run (121 frames, VTK files, series JSON). |
| `docs/` | Architecture, physics model, case format, assumptions, and validation plan documentation. |
| `tests/python/` | Pytest suite covering geometry computation, constraint validation, schema conformance, event detection, and smoke tests. |
| `scripts/` | `build_examples.py` and `smoke_run.py` for end-to-end validation. |

---

## 3. Architecture & Data Flow

The pipeline proceeds through five numbered stages, each consuming the output of the previous.

### 3.1 Stage 1 — Case Creation

The entry point is either the browser configurator, the browser-facing HTTP API, or the Python CLI. All of them produce a canonical case JSON file (schema version 1.0.0) that captures:

- All 22 free parameters (`A0`, `h0`, `h1`, `h3`, `h5`, `Y2`, `Y4`, `W1`, `W2`, `L1`–`L4`, `A`, `W`, `alpha`, `Ct`, `ht`, `P24t`, `hw`, `h_a`, `bendR`).
- All derived geometric quantities computed from those parameters.
- Solver configuration (`interFoam`, start/end time, time step, write interval).
- Forcing configuration (mode, inflow velocity, patch fraction).
- Transport properties (fluid physical constants for water and air phases).
- Event detection thresholds (`eps_H`, `eps_dHdt`, `eps_Q`, `T_ss`, `dwell`).
- Provenance (parameter hash, source files, git commit).

### 3.2 Stage 2 — Geometry Service

`services/geometry/core.py` is the canonical geometry engine. Given a raw parameter dict, it:

- Normalises inputs through `normalize_parameters()`, merging user values over defaults and mapping any HTML parameter names to canonical names.
- Computes all derived quantities through `compute_derived()` — `h2`, `h4`, `X2`, `X3`, `X4`, `X5`, `S0`, `S1`, `S2`, `C1`, `C2`, `H0`, the tube polyline (Bezier approximation), and holder bases.
- Validates 19 geometric constraints through `check_constraints()` and returns a pass/fail list.
- Emits fixed geometry descriptors (container walls, tube shell, holders, columns) and fluid geometry descriptors (interior bounds, top atmosphere patch, inflow patch, tube outlet, solid obstructions) consumed by the OpenFOAM case generator.

### 3.3 Stage 3 — OpenFOAM Case Generation

`services/orchestrator/case.py` generates a complete OpenFOAM-style directory from the case JSON:

- `system/blockMeshDict` — background hex mesh sized from domain extents with a 25% margin.
- `system/snappyHexMeshDict` — surface snapping referencing both `fluid_geometry.json` (fluid walls) and `fixed_geometry.json` (solid obstructions such as holders and columns).
- `system/controlDict` — solver application, time bounds, and write settings.
- `system/fvSchemes` and `fvSolution` — Euler time scheme, PIMPLE pressure-velocity coupling, PCG/symGaussSeidel solvers.
- `system/topoSetDict` — container region cell set for volume averaging.
- `0/alpha.water`, `0/U`, `0/p_rgh` — initial and boundary conditions.
- `constant/transportProperties` — water/air phases (`nu`, `rho`, `sigma`), populated from the case file's `transport` section.
- `constant/g` — gravitational acceleration vector.
- `Allrun` — `blockMesh`, `snappyHexMesh`, `topoSet`, solver execution, and `foamToVTK || true`.

### 3.4 Stage 4 — Simulation or Mock

`services/orchestrator/cli.py` drives execution. If `interFoam` is found on PATH it runs `Allrun` directly and raises on non-zero exit. On Windows, the intended local setup is to run this from WSL so the solver and Python API share the same environment. If Docker but not OpenFOAM is available it raises an error directing the user to run the solver manually via Docker. When neither is available it raises an error. Mock run generation is now a separate explicit step.

For browser-triggered runs, `services/api/server.py` exposes a lightweight HTTP layer. The API-backed run path now chooses between real solver execution and the mock fallback: `mode = "auto"` uses the configured solver when it is on PATH and otherwise falls back to mock viewer-data generation. Real runs generate the OpenFOAM-style case directory, execute `Allrun`, and post-process solver outputs into the same browser-facing manifest contract.

The mock generator in `services/viewer_data/mock.py` synthesises a physically plausible (but not CFD-accurate) water-height trajectory using an exponential approach to steady state with an oscillatory damping term, then passes it through the event detection state machine.

### 3.5 Stage 5 — Viewer Data & Manifest

`create_mock_run()` (and, in a real run, a post-processor) writes:

- `series/height.json`, `series/outlet_flow.json`, `series/discharged_volume.json` — time-value pairs.
- `frames/frame_NNNN.json` — per-time-step triangulated mesh of the water column and outlet plume.
- `vtk/frame_NNNN.vtk` — same mesh in legacy ASCII VTK POLYDATA format for ParaView.
- `event_states.json` — per-step state machine trace (`state`, `heightSpan`, `rmsDHdt`, `qBalance`).
- `fixed_geometry.json` — descriptor tree for the invariant solid geometry.
- `manifest.json` — index referencing all assets, event times, run status, and metadata.

---

## 4. Python Backend Services

### 4.1 `services/geometry/core.py`

#### Module-level constants

- `PARAMETER_DEFINITIONS` — list of 22 `ParameterDefinition` dataclass instances (`identifier`, `label`, `section`, `min_value`, `max_value`, `step`, `default`). Sections are `'primary'`, `'structural'`, and `'bend'`.
- `DEFAULT_PARAMETERS` — dict built from `PARAMETER_DEFINITIONS` defaults.
- `HTML_TO_CANONICAL_PARAMETER_MAP` — maps legacy HTML parameter names (e.g. `W1p`, `A_tube`) to canonical names (`W1`, `A`).
- `CONSTRAINT_LABELS` — ordered list of `(id, human-readable formula)` tuples that corresponds positionally to the check list built by `check_constraints()`.
- `SOURCE_FILES` — list of source-of-truth filenames used to populate provenance fields.

#### Public functions

| Function | Description |
|----------|-------------|
| `normalize_parameters(raw)` | Merges raw user dict over defaults, maps HTML aliases to canonical names, injects `P4t = alpha` and `wallThicknessRatio = 0.2`. |
| `compute_derived(parameters)` | Computes all derived scalars, named points, tube polyline, holder bases, and structure extents from normalized parameters. |
| `check_constraints(parameters, derived)` | Evaluates 19 geometric constraints and returns a list of `{id, label, ok}` dicts. |
| `create_geometry_snapshot(raw)` | Convenience wrapper: normalize → derive → check. Returns `{parameters, derived, constraints}`. |
| `build_tube_path(points, bend_radius)` | Converts a list of 2D key points into a dense polyline by inserting midpoint-constrained quadratic Bezier arcs at each interior vertex (24 segments per bend). |
| `build_fixed_geometry_descriptors(p, d)` | Returns typed descriptor trees for `container`, `tube`, `holders`, and `columns`. |
| `build_fluid_geometry_descriptors(p, d, f, fg)` | Returns wall bounds, top atmosphere, inflow patch, tube outlet, and solid obstruction list (holders + columns from fixed geometry) used by OpenFOAM. |
| `create_case_file(raw)` | Creates a full case JSON dict with all fields including provenance and run status. |

Shared cross-service helpers now live in `services/utils.py`: `stable_hash()`, `write_json()`, and `write_text()`.

### 4.2 `services/orchestrator/case.py`

Generates a complete OpenFOAM-style case directory. Key function:

**`generate_case(case_file, output_dir)`** — accepts the case JSON dict and output `Path`. Computes mesh preset (coarse / medium / fine), creates the directory tree, writes all solver files, and promotes `runStatus.state` from `not_started` to `generated` in the written case file. Returns the output `Path`.

Mesh preset logic: `backgroundCellSize = domain_span / divisor` where `divisor` is 24, 36, or 48 for coarse, medium, fine respectively. Refinement levels follow 2 / 3 / 4.

`build_snappy_hex_mesh_dict()` now accepts the geometry snapshot and computes a guaranteed-interior `locationInMesh` point at the horizontal centre of the container at half `h0` height. It also references both `fluid_geometry.json` (fluid walls) and `fixed_geometry.json` (solid obstructions to carve out).

`build_transport_properties()` now reads fluid physical constants from `case_file["transport"]` rather than using hardcoded values, making them user-configurable.

### 4.3 `services/orchestrator/events.py`

Implements the steady-state detection state machine operating on time-series data from the solver.

#### State machine

- **`PRE_H0`** — waiting for the first upward crossing of the `h0` target water height.
- **`POST_H0_MONITORING`** — computing rolling-window height span, RMS of `dH/dt`, and optionally flow balance.
- **`DONE`** — steady state confirmed after `dwell` seconds of continuous satisfaction.

**`analyze_series(times, heights, h0_target, thresholds, q_in, q_out)`** — main entry point. Returns an `EventSummary` dataclass with `t_h0_up`, `t_steady`, `termination_reason` (`'steady_state_reached'` or `'max_time_reached'`), and per-step `states` list.

Thresholds: `eps_H` (height span < 1 mm default), `eps_dHdt` (RMS derivative < 0.1 mm/s default), `eps_Q` (flow imbalance, optional), `T_ss` (rolling window = 1 s default), `dwell` (confirmation window = 1 s default).

#### State output fields per step

| Field | Description |
|-------|-------------|
| `time` | Simulation time (s). |
| `state` | Current state machine state. |
| `height` | Water height H(t) (m). |
| `heightSpan` | Max − min height within rolling window (m). |
| `rmsDHdt` | RMS of finite-difference dH/dt within rolling window (m/s). |
| `qBalance` | Max `|Q_in − Q_out|` within window; `null` if not checked. |
| `steady` | Whether steady-state conditions were met at this step. |

### 4.4 `services/orchestrator/cli.py`

**`run_case(case_dir)`** — attempts to run the case with `interFoam` (if available). Raises `RuntimeError` on non-zero exit, on Docker-only environments, or when neither solver nor Docker is found. The generated `Allrun` script now also calls `foamToVTK || true` after the solver so real API/CLI runs can expose ParaView assets when that tool is available.

### 4.5 `services/viewer_data/mock.py`

**`create_mock_run(case_json, output_dir)`** — orchestrates synthetic run creation. Calls `create_time_series()` then `analyze_series()`, writes all viewer assets, and returns the output directory `Path`.

**`create_time_series(case_file, snapshot)`** — generates 121 time steps (t = 0…12 s, Δt = 0.1 s). Water height follows an exponential approach to `h0 + 7.5 mm` with an oscillatory damping transient. Outlet flow uses a delayed exponential rise with a slow decay. `Q_in` is a step function. Cumulative discharged volume is computed by trapezoidal integration.

### 4.6 `services/viewer_data/real.py`

**`create_real_run(case_dir, output_dir)`** — loads the generated case's `postProcessing/containerWaterVolume`, `postProcessing/tubeOutletFlow`, and optional `postProcessing/topInflowFlow` outputs, converts them into `H(t)`, `Q_out(t)`, discharged-volume, and event-state series, and writes the same viewer asset bundle used by mock runs.

Real manifests keep the same browser contract as mock runs but set `status = "done"` and populate `paraview.foamFile` / `paraview.vtkDir` from the generated OpenFOAM case when those assets exist.

### 4.7 `services/api/server.py`

**`python -m services.api.server`** starts a stdlib `ThreadingHTTPServer` that the Vite app can reach through `/api`.

Supported endpoints:

| Endpoint | Action |
|----------|--------|
| `GET /api/health` | Liveness probe for the local API. |
| `POST /api/cases` | Accept `parameters`, `transport`, and `meshingPreset`; create and persist a canonical case JSON. |
| `GET /api/cases/{id}` | Return a previously created canonical case JSON. |
| `POST /api/cases/{id}/run` | Queue a browser-triggered run for that case. Accepts `mode = "auto" | "mock" | "real"`. |
| `GET /api/runs/{id}/status` | Return `queued` / `running` / `done` / `failed` state with timestamps and error details. |
| `GET /api/runs/{id}/viewer/manifest.json` | Return the completed run manifest when available. |
| `GET /api/runs/{id}/...` | Serve run assets such as `series/*.json`, `frames/*.json`, and `fixed_geometry.json`. |

Run assets are stored under `tmp/api/runs/<run-id>/viewer` with the generated case under `tmp/api/runs/<run-id>/openfoam-case`. They are served through API-relative URLs so the browser can resolve them the same way it resolves static example manifests.

---

## 5. TypeScript & Shared Schema Package

### 5.1 `packages/shared-schema`

The shared-schema package is the frontend's authoritative source of geometry logic and type definitions.

- `src/schemas/` — JSON Schema files for `case`, `parameters`, and `run-manifest`.
- `src/types/index.ts` — TypeScript interfaces: `CanonicalParameters`, `NormalizedParameters`, `DerivedGeometry`, `ConstraintResult`, `GeometrySnapshot`, `CaseFile`, `RunManifest`, `ForcingConfig`, `SolverConfig`, `MeshingConfig`, `TransportConfig`, `EventThresholds`, `FixedGeometryDescriptor`, `Point2D`.
- `src/metadata/parameterMetadata.ts` — parameter definitions (min, max, step, default, section) mirroring Python's `PARAMETER_DEFINITIONS` and `HTML_TO_CANONICAL_PARAMETER_MAP`.
- `src/geometry.ts` — TypeScript reimplementation of the full geometry pipeline: `normalizeParameters`, `buildTubePath`, `computeDerived`, `checkConstraints`, `createGeometrySnapshot`, `buildFixedGeometryDescriptors`, `stableStringHash`, `defaultTransportConfig`, and all other default config factories.

> **Note:** The geometry logic is independently implemented in both Python and TypeScript. They share a contract via JSON Schemas and must be kept in sync manually. See `refactoring_proposal.md` for discussion of this risk.

### 5.2 `apps/web` — React Application

#### Technology stack

- React 18 with hooks (`useMemo`, `useTransition`).
- Zustand for global state (parameters, visibility toggles, transport config, meshing preset, mesh-domain and fluid-interior visibility flags).
- Vite as the build tool / dev server.
- Three.js for 3D scene rendering in `Scene3D.tsx`.
- Recharts for time-series chart rendering in `ChartPanel.tsx`.

#### Application structure

| File | Responsibility |
|------|---------------|
| `src/app/App.tsx` | Root component. Defines the topbar and react-router-dom routes: `/` → `ConfigurePage`, `/runs` → `RunsPage`. |
| `src/app/store.ts` | Zustand store. Holds `parameters`, `visibility`, `transport`, `meshingPreset`, `showMeshDomain`, `showFluidInterior`. Actions: `setParameter`, `resetParameters`, `toggleVisibility`, `setTransport`, `setMeshingPreset`, `toggleMeshDomain`, `toggleFluidInterior`. |
| `src/pages/ConfigurePage.tsx` | Parameter editing page. Renders `ParameterPanel` (×3 sections), `VisibilityToggles`, `MeshingPanel`, `TransportPanel`, `DerivedPanel`, `ConstraintList`, `Scene3D`, and export buttons. |
| `src/pages/RunsPage.tsx` | Run browsing page. Loads `examples/index.json`, fetches the selected manifest, renders `ChartPanel` and run metadata. |
| `src/components/Scene3D.tsx` | Three.js canvas. Builds the 3D scene from `buildFixedGeometryDescriptors()` output. Supports container, tube, holders, columns, label, mesh domain, and fluid interior visibility. |
| `src/components/MeshingPanel.tsx` | UI for selecting mesh preset (coarse / medium / fine) and toggling mesh domain / fluid interior overlays in the 3D view. |
| `src/components/TransportPanel.tsx` | UI for editing fluid physical constants (`waterNu`, `waterRho`, `airNu`, `airRho`, `sigma`). |
| `src/lib/sceneBuilder.ts` | Export utilities: `exportCaseJson` (now accepts `transport` and `meshingPreset`), `exportStl`, `exportGlb`. |
| `src/lib/meshBuilders.ts` | Three.js mesh construction helpers for each geometry descriptor type. |

---

## 6. Key Algorithms

### 6.1 Derived Geometry Computation

All derived quantities flow from the 22 primary parameters:

| Symbol | Formula | Meaning |
|--------|---------|---------|
| `h2` | `h0 − Y2` | Height of tube entry through container right wall. |
| `h4` | `h0 + Y4` | Height of peak (P4) above the water line. |
| `X2` | `√(L1² − (h2−h1)²)` | Horizontal position of tube entry (right wall x-coord). |
| `X3` | `√(L2² − (h3−h2)²) + X2` | Horizontal position of valley (P3). |
| `X4` | `√(L3² − (h4−h3)²) + X3` | Horizontal position of peak (P4). |
| `X5` | `√(L4² − (h5−h4)²) + X4` | Horizontal position of tube outlet (P5). |
| `S0` | `X2 − A0/W` | Left-wall x-coordinate (negative = container extends left of origin). |
| `S1` | `W1` | x-position of first holder (`W1` is a primary parameter). |
| `S2` | `X5 − W2` | x-position of last holder. |
| `C1` | `h1 + (h2−h1)/X2 · S1` | Height of tube at first holder (linear interpolation on P1→P2 segment). |
| `C2` | `h4 + (h5−h4)/(X5−X4) · (S2−X4)` | Height of tube at last holder (linear interpolation on P4→P5 segment). |
| `H0` | `4·h2 / 5` | Initial water height (80% of tube entry height). |

If any argument under a square root is negative (geometry violation), the clamped square-root helper returns 0 and the corresponding constraint check will fail.

### 6.2 Tube Path (Bezier Bends)

The tube is represented as a 2D polyline through key points P1 → P2 → P3 → P4 → P5. At each interior vertex the path is replaced by a midpoint-constrained quadratic Bezier arc:

1. Compute unit tangents `uA` (incoming) and `uB` (outgoing).
2. Clamp the offset to `min(bendR, 0.45 · len_A, 0.45 · len_B)` to avoid overshooting adjacent segments.
3. Compute control point `pC = 2·corner − 0.5·(p0 + p1)` (ensures the Bezier passes through the geometric midpoint near the corner).
4. Sample 24 intermediate points along the Bezier using De Casteljau evaluation.

This replicates the HTML source-of-truth visual exactly.

### 6.3 Geometric Constraint Checks

19 constraints are evaluated in order. Each maps to a `(id, label, ok)` dict:

| ID | Formula |
|----|---------|
| `S0_negative` | `S0 < 0` |
| `ordering` | `0 < S1 < X2 < X3 < X4 < S2 < X5` |
| `tube_heights_below_h0` | `h1, h2, h3, h5 < h0` |
| `valleys_below_h2` | `h1, h3 < h2` |
| `h2_below_h4` | `h2 < h4` |
| `left_clearance` | `\|S0\| ≥ r + Ct/2` |
| `S1_clearance` | `S1 ≥ r + alpha/2` |
| `X2_clearance` | `X2 ≥ S1 + alpha/2 + Ct/2` |
| `X3_clearance` | `X3 ≥ X2 + alpha/2 + Ct/2` |
| `X4_clearance` | `X4 ≥ X3 + alpha` |
| `S2_clearance` | `S2 ≥ X4 + alpha + r` |
| `X5_clearance` | `X5 ≥ alpha/2 + S2` |
| `alpha_vs_Ct` | `alpha ≥ Ct` |
| `alpha_vs_radius` | `alpha ≥ 2.5 · r` |
| `P24t_vs_alpha` | `P24t ≤ alpha` |
| `arg1`–`arg4` | `L1²−(h2−h1)² ≥ 0`, etc. |

### 6.4 Event Detection State Machine

The state machine processes a time series of measured water height H(t):

- **PRE_H0:** scan for the first upward crossing of `h0`. On crossing, linearly interpolate the precise crossing time `t_h0_up` and transition to `POST_H0_MONITORING`.
- **POST_H0_MONITORING:** at each step, gather all samples within the last `T_ss` seconds. Compute height span (max − min) and RMS of finite-difference `dH/dt`. If `span < eps_H` and `RMS < eps_dHdt` (and optionally `|Q_in − Q_out| < eps_Q`), set `dwell_start` if not set. After the condition holds for `dwell` continuous seconds, record `t_steady` and transition to `DONE`.
- **DONE:** terminate iteration.

---

## 7. Data Schemas

### 7.1 Case JSON (`case.schema.json`)

| Field | Type | Description |
|-------|------|-------------|
| `schemaVersion` | string | Schema version string. Currently `"1.0.0"`. |
| `caseId` | string | `"case-"` + 10-char SHA-256 prefix of sorted parameter JSON. |
| `displayName` | string | Human-readable label. |
| `parameters` | object | The 22 canonical free parameters as numeric key-value pairs. |
| `derived` | object | All derived scalars and structures computed from parameters. |
| `geometry` | object | Lists of fluid boundary patch names and fixed geometry group names. |
| `meshing` | object | `preset`, `backgroundCellSize`, `refinementLevels` per zone. |
| `transport` | object | `waterNu`, `waterRho`, `airNu`, `airRho`, `sigma` — fluid physical constants. |
| `solver` | object | `solver`, `startTime`, `endTime`, `deltaT`, `writeInterval`, `chunkDuration`. |
| `forcing` | object | `mode`, `topPatchFraction`, `inflowVelocity`, `volumetricSourceRate`, `reservoirHead`. |
| `eventThresholds` | object | `eps_H`, `eps_dHdt`, `eps_Q`, `T_ss`, `dwell`, `requireQBalance`. |
| `outputs` | object | `exportRoot` path, optional `manifestPath`. |
| `runStatus` | object | `state`: `'not_started'` \| `'generated'` \| `'running'` \| `'done'` \| `'failed'`. |
| `provenance` | object | `parameterHash`, `gitCommit`, `sourceFiles` list. |

### 7.2 Run Manifest (`run-manifest.schema.json`)

| Field | Type | Description |
|-------|------|-------------|
| `schemaVersion` | string | `"1.0.0"`. |
| `caseId` | string | Links manifest back to the originating case. |
| `timeSteps` | number[] | Ordered list of simulation times corresponding to frames. |
| `chartSeries` | object | Relative paths to `height`, `outletFlow`, and `dischargedVolume` series JSON. |
| `geometryAssets` | object | Optional `fixedGlb` path and `fixedJson` path for the static geometry. |
| `fluidAssets` | object | `interfaceFrames`: array of relative paths to per-step frame JSON. |
| `events` | object | `t_h0_up`, `t_steady`, `terminationReason`, `currentState`. |
| `status` | string | `'mock'` \| `'running'` \| `'done'` \| `'failed'`. `mock` is reserved for synthetic viewer-data output. |
| `paraview` | object | Optional `foamFile` path and `vtkDir` path for ParaView integration. |
| `metadata` | object | `parameterHash`, `gitCommit`, `sourceFiles`, `meshPreset`, `solverName`. |

---

## 8. CLI Reference

### 8.1 Geometry CLI

```bash
python3 -m services.geometry.cli create-case [--output PATH]
```

Creates a canonical case JSON with default parameters. `--output` defaults to stdout.

```bash
python3 -m services.geometry.cli export-case CASE_JSON [--output-dir DIR]
```

Computes geometry snapshot and writes geometry descriptors to the output directory.

### 8.2 Orchestrator CLI

```bash
python3 -m services.orchestrator.cli generate-case CASE_JSON --output-dir DIR
```

Generates a complete OpenFOAM-style case directory from the case JSON.

```bash
python3 -m services.orchestrator.cli run-case CASE_DIR
```

Attempts to run the case with `interFoam` (if available on PATH). Raises on failure. Does **not** generate mock data — use the viewer-data CLI for that.

### 8.3 Viewer-Data CLI

```bash
python3 -m services.viewer_data.cli mock-run CASE_JSON --output-dir DIR
```

Generates a complete synthetic mock run without requiring OpenFOAM.

```bash
python3 -m services.viewer_data.cli build-manifest CASE_DIR
```

Builds or refreshes a viewer manifest from a generated case directory. If real solver `postProcessing/*` outputs exist it emits a real manifest; otherwise it falls back to the mock manifest path.

### 8.4 API Server

```bash
python -m services.api.server --host 127.0.0.1 --port 8000
```

Starts the local HTTP API used by the web app for browser-triggered runs. In development the Vite app proxies `/api/*` to `http://127.0.0.1:8000` by default.

### 8.4 Makefile Targets

| Target | Action |
|--------|--------|
| `make web-dev` | Start the Vite development server. |
| `make web-build` | Production build of the web application. |
| `make case-generate CASE=… CASE_DIR=…` | Generate an OpenFOAM-style case directory from a case JSON file. |
| `make viewer-data CASE=… VIEWER_DIR=…` | Generate mock viewer data from a case JSON file. |

---

## 9. Configuration & Environment

### 9.1 Python

The Python project is defined in `pyproject.toml`. Install with:

```bash
python3 -m pip install -e '.[dev]'
```

Requires Python ≥ 3.11. Core dependencies: `numpy ≥ 2.2`, `jsonschema ≥ 4.23`. Optional extras:

- `[geometry]` — `meshio`, `trimesh` for STL/GLB export.
- `[boolean]` — `shapely`, `manifold3d` for watertight boolean cutouts (not used in MVP).
- `[dev]` — `pytest`.

### 9.2 Node / TypeScript

Root `package.json` defines a workspace with `packages/shared-schema` and `apps/web`. Install with:

```bash
npm install
```

### 9.3 WSL / OpenFOAM

WSL with OpenFOAM on PATH is the preferred local runtime on Windows because the backend API and CLI expect to see `interFoam` in the same execution environment as Python. `solver/openfoam-template/Dockerfile` and `compose.yaml` remain available as manual/reference assets, but Docker is not the primary local execution path for the backend.

---

## 10. Testing

### 10.1 Python Test Suite

```bash
pytest
```

| Test file | Coverage |
|-----------|---------|
| `test_geometry_core.py` | Default derived values (`h2`, `h4`, `X2`, `X5`, `H0`), constraint pass/fail, holder layout, structure extents. |
| `test_events.py` | State machine transitions, `h0` crossing interpolation, steady-state detection with and without flow balance. |
| `test_schema_and_examples.py` | JSON Schema validation of `examples/default-case.json`, `manifest.json`, and parameter sets. |
| `test_smoke.py` | End-to-end: create case → generate OpenFOAM dir → generate mock run → validate manifest. |
| `test_source_truth_parity.py` | Verifies that Python-derived values match values from the HTML source-of-truth. |

### 10.2 TypeScript Tests

`packages/shared-schema/src/index.test.ts` covers TypeScript geometry computation parity with Python defaults.

### 10.3 Validation Scripts

- `scripts/build_examples.py` — regenerates all example files and validates them against schemas.
- `scripts/smoke_run.py` — full pipeline smoke test (case creation → OpenFOAM case generation → mock run → viewer asset validation).

---

## 11. Known Limitations

- The committed example run is synthetic. Real CFD results require OpenFOAM and a valid mesh.
- The geometry service produces a scaffold OpenFOAM case that has not been validated for mesh quality or boundary condition correctness in production.
- Boolean holder cutouts in exported solid meshes (STL/GLB) are not yet implemented.
- The browser viewer uses simplified polydata (box + plume approximations), not the actual CFD mesh.
- The browser viewer still uses reduced box-and-plume frame meshes derived from solver measurements, not the full CFD free-surface geometry.
- Only the `'coarse'` mesh preset has been exercised. Medium and fine presets are defined but untested.
- The `inflow_patch` forcing mode is the only tested boundary condition configuration.
- `run_case()` in the orchestrator CLI no longer auto-generates mock data — this must now be done explicitly via `services.viewer_data.cli`.
