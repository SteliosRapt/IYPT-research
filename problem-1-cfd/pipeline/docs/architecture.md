# Architecture

## Monorepo layout

- `apps/web`: React + TypeScript app for configuration, exports, and run browsing.
- `packages/shared-schema`: JSON Schemas, TypeScript types, parameter metadata, and shared geometry formulas.
- `services/geometry`: canonical parameter normalization, derived geometry, constraint checks, and geometry descriptors.
- `services/orchestrator`: OpenFOAM-style case generation and supervisory run entrypoints.
- `services/viewer_data`: mock and post-processed viewer assets plus manifest assembly.
- `solver/openfoam-template`: Docker and solver runtime reference files; WSL with OpenFOAM on PATH is the preferred local runtime on Windows.
- `examples`: committed sample case, generated OpenFOAM-style case, and mock run assets.

## Data flow

1. The web app or Python CLI creates a canonical case JSON.
2. The geometry service derives coordinates, checks constraints, and emits fixed/fluid geometry descriptors.
3. The orchestrator turns the case into an OpenFOAM-style directory and, in this environment, falls back to mock viewer data because OpenFOAM is absent. The preferred local runtime is WSL with OpenFOAM on PATH; Docker remains a manual reference path.
4. The viewer-data service writes time-series JSON, frame meshes, and legacy VTK files for ParaView.
5. The web viewer loads the example manifest and renders fixed geometry plus time-varying fluid assets.

## Source-of-truth traceability

- The formulas for `h2`, `h4`, `X2..X5`, `S0`, `S2`, `C1`, and `C2` match the source files.
- The bend realization follows the HTML implementation: midpoint-constrained quadratic Bezier sampling.
- Holder and structural placement follow the prose constraints from `experimental_setup.md`.

