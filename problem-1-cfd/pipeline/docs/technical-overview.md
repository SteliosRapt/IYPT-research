# Technical Overview

## Purpose

This repository implements a fixed-geometry CFD workflow for a single experimental rig:

- canonical parameter normalization from the source files
- derived geometry and constraint checks
- canonical case-file assembly
- OpenFOAM-style case generation
- mock and solver-backed viewer manifests
- browser and ParaView inspection assets

The strongest always-available path is:

`spec -> case.json -> generated case -> mock or real viewer manifest`

## Repository Structure

```text
apps/web/                  React/Vite configurator and run viewer
packages/shared-schema/    TypeScript geometry logic, types, and JSON Schemas
services/api/              Browser-triggered HTTP API
services/geometry/         Python geometry, case identity, descriptors, surfaces
services/orchestrator/     Generated case writing and runtime helpers
services/viewer_data/      Mock and real viewer-manifest assembly
scripts/                   Example regeneration and smoke helpers
examples/                  Public sample assets (catalog, sample-cases, sample-runs)
docs/                      Canonical docs, assumptions, roadmap, and execution log
```

## Current Geometry And Case Stack

Python geometry is now split across focused modules:

- `services/geometry/parameters.py`: parameter metadata and constants
- `services/geometry/derive.py`: normalization, derived values, constraints
- `services/geometry/descriptors.py`: fixed/fluid descriptor builders and refinement boxes
- `services/geometry/case_file.py`: defaults plus full-case identity hashing
- `services/geometry/surfaces.py`: STL surface generation for solver cases
- `services/geometry/core.py`: compatibility re-export layer

TypeScript keeps a matching geometry implementation in `packages/shared-schema/src/geometry.ts`.

## Identity Contract

- `provenance.parameterHash` is geometry-only.
- `caseId` hashes the full canonical simulation identity:
  - parameters
  - transport
  - forcing
  - solver
  - event thresholds
  - meshing preset
  - display name

Python and TypeScript both use the same recursively sorted JSON-style serialization, and shared fixtures enforce parity.

## Generated Solver Case

`services/orchestrator/case.py` writes:

- `system/blockMeshDict`
- `system/snappyHexMeshDict`
- `system/surfaceFeatureExtractDict`
- `system/topoSetDict`
- `system/setFieldsDict`
- `0/alpha.water`, `0/U`, `0/p_rgh`
- `constant/transportProperties`
- `constant/triSurface/*.stl`
- `Allrun`

The solver path now uses real STL patch assets instead of JSON pseudo-surfaces:

- `walls.stl`
- `topAtmosphere.stl`
- `topInflow.stl`
- `tubeOutlet.stl`
- `solidObstructions.stl`

`snappyHexMeshDict` also emits explicit searchable refinement boxes:

- `openingBox`
- `bendBoxP2`
- `bendBoxP3`
- `bendBoxP4`
- `outletBox`
- `freeSurfaceBox`

Initial water is aligned with the mock path via `setFieldsDict`, using the canonical `H0` height inside the container.

## Runtime Behavior

`services/orchestrator/runtime.py` owns solver execution and generated-case directory lifecycle.

- Generated case directories are tool-owned.
- Re-generating a recognized case directory clears old generated outputs before writing new files.
- Re-generating into a non-generated non-empty directory fails loudly instead of merging.

Runtime modes:

- CLI `run-case`: real solver only, no fallback
- API `auto`: real solver when available, mock otherwise
- API `mock`: mock only
- API `real`: real solver only

## Viewer Data

`services/viewer_data/mock.py` and `services/viewer_data/real.py` both feed the same manifest contract.

The browser viewer still renders reduced frame geometry derived from water height and outlet flow, not the full CFD free surface. Real runs improve the measurements, not the browser mesh fidelity.

## Web Application

The web app now consumes the shared schema package through its workspace exports instead of a direct Vite source alias.

Stateful async orchestration is separated from page composition:

- `apps/web/src/hooks/useBackendRun.ts`
- `apps/web/src/hooks/useRunsPageState.ts`
- `apps/web/src/lib/runManifest.ts`

The runs viewer also refreshes fixed geometry correctly when the manifest changes and only resets the camera on initial/run switches, not on every frame update.

## Examples

`examples/` remains the Vite public root.

Internal layout:

- `examples/catalog/index.json`
- `examples/sample-cases/`
- `examples/sample-runs/`

`scripts/build_examples.py` regenerates those assets and also leaves a compatibility `examples/index.json`.

## Verification

Primary commands:

```bash
python -m compileall services tests/python
python -m scripts.build_examples
python -m scripts.smoke_run
python -m pytest
npm run test
npm run build
```

Environment-specific gate:

- real OpenFOAM validation of the default generated case through `blockMesh`, `surfaceFeatureExtract`, `snappyHexMesh -overwrite`, `topoSet`, `setFields`, and a short solver run

## Known Limits

- `pytest` may not be installed in every environment; use the documented command in a dev environment with the dependency available.
- OpenFOAM validation is still environment-dependent and is expected to run from WSL on Windows.
- The STL patch geometry is solver-consumable, but still needs real-solver validation for production confidence.
- The browser viewer remains a reduced visualization path, not a CFD mesh viewer.
