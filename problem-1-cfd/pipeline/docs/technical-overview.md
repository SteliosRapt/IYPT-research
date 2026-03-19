# Technical Overview — Fixed-Geometry CFD Pipeline

## 1. Purpose

This repository implements a parametric pipeline for configuring, generating, and
(optionally) running two-phase CFD simulations on a fixed experimental geometry.
The geometry represents a water-discharge test rig: a rectangular container connected
to an S-shaped tube whose path is defined by a polyline of key points.  When
OpenFOAM/Docker is unavailable the pipeline falls back to a fully synthetic mock run,
so the entire data path from parameter input to browser/ParaView visualisation can be
exercised without a solver.

---

## 2. Repository Layout

```
Problem_1_CFD_1/
├── apps/web/                     React/Vite web configurator
├── packages/shared-schema/       JSON Schemas + TypeScript types
├── services/
│   ├── geometry/                 Canonical geometry computations  ← core library
│   ├── orchestrator/             Case generation & run control
│   └── viewer_data/              Mock synthetic output generation
├── solver/openfoam-template/     Docker / solver reference files
├── scripts/                      build_examples.py, smoke_run.py
├── tests/python/                 pytest suite
├── examples/                     Committed golden assets
├── docs/                         Architecture, assumptions, formats
├── experimental_setup.md         Source-of-truth geometry spec
├── setup_3d (2).html             Interactive 2-D reference implementation
├── pyproject.toml                Python project (setuptools, pytest)
├── package.json                  npm workspaces root
└── Makefile                      Convenience targets
```

---

## 3. Data Flow

```
User / Web UI
     │ raw parameter dict (may use HTML names)
     ▼
services/geometry/core.py
  normalize_parameters()     → applies HTML→canonical map, fills defaults
  compute_derived()          → computes h2, h4, X2-X5, S0-S2, C1-C2, polyline
  check_constraints()        → 19 geometric constraint checks → list[{id,ok}]
  build_fixed_geometry_descriptors()  → container/tube/holders/columns JSON
  build_fluid_geometry_descriptors()  → fluid domain + boundary patches JSON
  create_case_file()         → canonical case.json
     │
     ├─► services/geometry/cli.py   export-case
     │       → fixed_geometry.json, fluid_geometry.json
     │
     └─► services/orchestrator/case.py   generate_case()
             → OpenFOAM directory (0/, constant/, system/, Allrun)
             │
             └─► services/orchestrator/cli.py   run-case
                     [OpenFOAM/Docker present] → execute Allrun
                     [fallback] ──────────────►
                         services/viewer_data/mock.py   create_mock_run()
                             → series/*.json (height, outlet_flow, discharged_volume)
                             → frames/frame_NNNN.json   (triangulated water+plume mesh)
                             → vtk/frame_NNNN.vtk       (legacy VTK polydata)
                             → event_states.json
                             → manifest.json
                             │
                             └─► Browser viewer  /  ParaView
```

---

## 4. Services

### 4.1 `services/geometry/core.py`

The single source of computed geometry truth.  Every other module imports from here.

#### Key types

| Symbol | Kind | Description |
|--------|------|-------------|
| `ParameterDefinition` | frozen dataclass | identifier, label, section, min/max/step/default |
| `PARAMETER_DEFINITIONS` | list[ParameterDefinition] | 22 entries (21 user-facing + bendR) |
| `DEFAULT_PARAMETERS` | dict[str, float] | Identity map from defaults |
| `HTML_TO_CANONICAL_PARAMETER_MAP` | dict[str, str] | Translates HTML slider names |
| `CONSTRAINT_LABELS` | list[tuple[str,str]] | (id, human-readable formula) — 19 entries |

#### Primary parameters (21)

| Group | Parameters |
|-------|-----------|
| Primary geometry | A0, h0, h1, h3, h5, Y2, Y4, W1, W2, L1, L2, L3, L4, A, W |
| Structural (fixed by construction) | alpha, Ct, ht, P24t, hw, h_a |
| Bend | bendR |

#### Derived values (computed in `compute_derived`)

```
r   = sqrt(A / π)            tube inner radius
h2  = h0 − Y2                first valley height
h4  = h0 + Y4                second peak height
X2  = sqrt(L1² − (h2−h1)²)
X3  = sqrt(L2² − (h3−h2)²) + X2
X4  = sqrt(L3² − (h4−h3)²) + X3
X5  = sqrt(L4² − (h5−h4)²) + X4
S0  = X2 − A0/W              container left wall x-coordinate
S1  = W1                     W1 holder x-coordinate
S2  = X5 − W2                W2 holder x-coordinate
C1  = interpolated height at S1 on segment P1→P2
C2  = interpolated height at S2 on segment P4→P5
H0  = 4·h2/5                 initial water level
```

Eight named key points are also produced:

| Point | x | y |
|-------|---|---|
| W0 | S0 | h0 |
| P1 | 0 | h1 |
| W1 | S1 | C1 |
| P2 | X2 | h2 |
| P3 | X3 | h3 |
| P4 | X4 | h4 |
| W2 | S2 | C2 |
| P5 | X5 | h5 |

The tube polyline P1→P2→P3→P4→P5 is passed through `build_tube_path` which
inserts quadratic Bézier arcs (24 segments per bend) at every interior vertex.

#### Constraint checks (19)

The constraints enforce geometric feasibility: left-wall sign, strict ordering of
X-coordinates, tube height limits, height ordering, and minimum clearances between
tube radius, holder width, and structural parameters.  All are evaluated in
`check_constraints` and returned as `{id, label, ok}` records.

#### Key pure functions

| Function | Signature | Notes |
|----------|-----------|-------|
| `normalize_parameters` | `raw → dict[str,float]` | Merges defaults, applies HTML map, appends P4t/wallThicknessRatio |
| `compute_derived` | `parameters → dict` | All derived geometry; calls `build_tube_path` |
| `check_constraints` | `parameters, derived → list` | Returns per-constraint pass/fail |
| `build_fixed_geometry_descriptors` | `parameters, derived → dict` | Container/tube/holders/columns |
| `build_fluid_geometry_descriptors` | `parameters, derived, forcing → dict` | Fluid domain + boundary patches |
| `create_geometry_snapshot` | `raw → dict` | parameters + derived + constraints |
| `create_case_file` | `raw → dict` | Full canonical case JSON |
| `stable_hash` | `parameters → str` | SHA-256 hex prefix (10 chars) |

---

### 4.2 `services/orchestrator/case.py`

Generates an OpenFOAM-style case directory from a case JSON file.

#### Mesh presets

| Preset | Background divisor | Refinement levels |
|--------|--------------------|-------------------|
| coarse | 24 | 2 |
| medium | 36 | 3 |
| fine | 48 | 4 |

`domain_span = min(W, h0+h_a, X5−S0)`.
`backgroundCellSize = domain_span / divisor`.

#### Generated case structure

```
<case_dir>/
├── 0/
│   ├── alpha.water       (uniform 0)
│   ├── U                 (zeroGradient, inlet fixedValue)
│   └── p_rgh             (uniform 0)
├── constant/
│   ├── transportProperties  (water/air viscosity, density, surface tension)
│   ├── g
│   └── triSurface/
│       └── fluid_geometry.json
├── system/
│   ├── blockMeshDict
│   ├── snappyHexMeshDict
│   ├── controlDict
│   ├── fvSchemes
│   ├── fvSolution
│   └── topoSetDict
├── Allrun              (bash script, meshes then runs interFoam)
├── case.json           (copy of canonical case file)
├── fixed_geometry.json
├── fluid_geometry.json
└── run_metadata.json
```

#### Solver settings defaults

| Parameter | Default |
|-----------|---------|
| solver | interFoam |
| startTime | 0 |
| endTime | 15 s |
| deltaT | 0.02 s |
| writeInterval | 0.1 s |
| Time scheme | Euler |
| Divergence | Gauss linear / vanLeer |
| p_rgh solver | PCG + DIC |
| U solver | smoothSolver + symGaussSeidel |
| PIMPLE nCorrectors | 2 |

---

### 4.3 `services/orchestrator/events.py`

A three-state machine that post-processes height time-series to detect the moment the
water level crosses the target `h0` upward and subsequently reaches steady state.

#### States

```
PRE_H0  ──(h crosses h0 upward)──►  POST_H0_MONITORING  ──(dwell satisfied)──►  DONE
```

**Steady-state criteria** (all must hold over a rolling window `T_ss`):

| Criterion | Threshold key | Default |
|-----------|--------------|---------|
| Height span | eps_H | 1 × 10⁻³ m |
| RMS dH/dt | eps_dHdt | 1 × 10⁻⁴ m/s |
| Q balance (optional) | eps_Q | 1 × 10⁻⁶ m³/s |

The dwell counter resets on any non-steady timestep.  After `dwell` seconds (default
1 s) of continuous steady state the machine transitions to DONE and records `t_steady`.

#### `EventSummary` dataclass

| Field | Type | Meaning |
|-------|------|---------|
| t_h0_up | float \| None | Time of upward crossing |
| t_steady | float \| None | Time DONE was entered |
| termination_reason | str | `"steady_state_reached"` or `"max_time_reached"` or `"no_samples"` |
| states | list[dict] | Per-timestep record |

---

### 4.4 `services/viewer_data/mock.py`

Generates fully synthetic run output so the viewer works without OpenFOAM.

#### Synthetic time series (121 points, 0–12 s, Δt = 0.1 s)

```
height(t) = (h0 + 0.0075) − [(h0 + 0.0075) − H0] · exp(−0.8·t)
           + 0.0025 · exp(−1.1·max(t−2,0)) · sin(4·max(t−2,0))   [damped oscillation]

q_out(t)  = max(0, 0.00035 · [1 − exp(−0.7·max(t−1.6,0))] · exp(−0.06·max(t−5,0)))
q_in(t)   = 0.00042  (t < 8 s),   0.00018  (t ≥ 8 s)
discharged = trapezoid integral of q_out
```

#### Frame mesh

Each frame contains two box surfaces combined into one triangle mesh:
- **Water box**: `[S0, X2] × [0, height(t)] × [−W/2, W/2]`
- **Outlet plume**: a small box extending from `X5` proportional to `q_out(t)`

Frames are written as both JSON (`frames/frame_NNNN.json`) and legacy VTK polydata
(`vtk/frame_NNNN.vtk`).

---

## 5. Case JSON Structure

```json
{
  "schemaVersion": "1.0.0",
  "caseId": "case-<hash10>",
  "displayName": "string",
  "parameters": { /* 21 primary parameters */ },
  "derived": {
    "r", "h2", "h4", "X2"–"X5", "S0"–"S2", "C1", "C2", "H0",
    "planArea", "points", "tubePolyline", "holderBases", "structure", "sqrtArgs"
  },
  "geometry": {
    "fluidBoundaryPatches": ["walls", "topAtmosphere", "topInflow", "tubeOutlet"],
    "fixedGeometryGroups":  ["container", "tube", "holders", "columns"]
  },
  "meshing":  { "preset": "coarse|medium|fine" },
  "solver":   { "solver": "interFoam", "startTime": 0, "endTime": 15, ... },
  "forcing":  { "mode": "inflow_patch", "topPatchFraction": 0.18, ... },
  "eventThresholds": { "eps_H": 1e-3, "eps_dHdt": 1e-4, "eps_Q": 1e-6, ... },
  "outputs":  { "exportRoot": "...", "manifestPath": null },
  "runStatus": { "state": "not_started" },
  "provenance": { "parameterHash": "...", "sourceFiles": [...] }
}
```

---

## 6. Manifest JSON Structure

```json
{
  "schemaVersion": "1.0.0",
  "caseId": "case-<hash10>",
  "timeSteps": [0.0, 0.1, ...],
  "chartSeries": {
    "height": "series/height.json",
    "outletFlow": "series/outlet_flow.json",
    "dischargedVolume": "series/discharged_volume.json"
  },
  "geometryAssets": { "fixedGlb": null, "fixedJson": "fixed_geometry.json" },
  "fluidAssets":    { "interfaceFrames": ["frames/frame_0000.json", ...] },
  "events": { "t_h0_up": float|null, "t_steady": float|null, ... },
  "status": "mock",
  "paraview": { "foamFile": null, "vtkDir": "vtk" },
  "metadata": { "parameterHash": "...", "meshPreset": "coarse", ... }
}
```

---

## 7. CLI Reference

All CLIs use `python -m services.<service>.cli`.

### Geometry

```
python -m services.geometry.cli create-case   [--output FILE]
python -m services.geometry.cli export-case   --case FILE [--output-dir DIR]
python -m services.geometry.cli snapshot      [--case FILE] [--output FILE]
```

### Orchestrator

```
python -m services.orchestrator.cli generate-case --case FILE [--output-dir DIR]
python -m services.orchestrator.cli run-case      --case FILE [--output-dir DIR]
```

### Viewer data

```
python -m services.viewer_data.cli mock-run       --case FILE [--output-dir DIR]
python -m services.viewer_data.cli build-manifest --case-dir DIR
```

---

## 8. Testing

```
pytest tests/python/            # full suite
make py-test                    # same via Makefile
make smoke                      # pytest + smoke_run.py + npm build
```

| Test file | What it covers |
|-----------|---------------|
| test_geometry_core.py | Derived values at default parameters; holder layout; constraint all-pass |
| test_events.py | State machine crosses h0, reaches steady state |
| test_schema_and_examples.py | JSON Schema validation for case + manifest |
| test_smoke.py | End-to-end: create case → generate → mock run |
| test_source_truth_parity.py | (contents not shown) presumably cross-checks with HTML reference |

---

## 9. Dependencies

### Python (≥3.11)

| Package | Version | Usage |
|---------|---------|-------|
| numpy | ≥2.2 | Numerical work (mock series, geometry) |
| jsonschema | ≥4.23 | Schema validation in tests |
| meshio | ≥5.3 | Optional — geometry export |
| trimesh | ≥4.6 | Optional — geometry export |
| shapely | ≥2.0 | Optional — boolean ops |
| manifold3d | ≥2.5 | Optional — boolean ops |
| pytest | ≥8.3 | Dev / testing |

### Node (workspaces)

| Workspace | Purpose |
|-----------|---------|
| `@fixed-geometry/web` | Vite + React configurator UI |
| `@fixed-geometry/shared-schema` | JSON Schemas, TypeScript types, parameter metadata |

---

## 10. Known Limitations / Deferred Items

- OpenFOAM execution requires Docker; falls back silently to mock data.
- GLB export (`fixedGlb`) is `null` — not yet implemented.
- `gitCommit` provenance field is always `null`.
- Boolean mesh operations (shapely/manifold3d extras) are not called by any current path.
- The web configurator only reads/writes case JSON; no live solver connection.
- `test_source_truth_parity.py` depends on the HTML file being parseable as a reference implementation; fragile if the HTML changes.
