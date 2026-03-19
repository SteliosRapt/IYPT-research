# Code Review Wave Handoff

Last updated: 2026-03-19
Source: `code_review_report.md`

## Current Status

- Wave 1 is complete.
- Wave 2 is complete.
- Wave 3 is complete.
- Wave 4 is complete.
- Wave 5 is complete.
- The example assets were regenerated after the completed waves so `examples/default-case.json`, `examples/default-openfoam-case/case.json`, `examples/default-mock/manifest.json`, and `examples/default-mock/event_states.json` reflect the current outputs.

## Wave 1 Completed

- [x] N-01: `services/orchestrator/case.py` now writes `topInflow` in `0/U` from `forcing.inflowVelocity` instead of the hardcoded `0.02`.
- [x] R-02: `packages/shared-schema/src/geometry.ts` now uses SHA-256 with Python-compatible sorted serialization, and browser-exported case IDs match the Python default case hash (`6cc4e9b9e1`).
- [x] R-03: `generate_case()` now deep-copies the incoming case dict before merging defaults.
- [x] N-02: `services/geometry/core.py` now includes a default `transport` section in `create_case_file()`.
- [x] R-06 / N-04: `TUBE_WALL_THICKNESS_RATIO` is centralized and reused in Python, shared-schema, and the web scene builder.
- [x] R-08: `SOURCE_FILES` is centralized in Python and shared-schema, and the mock manifest now reuses case provenance instead of a duplicate hardcoded list.
- [x] Added focused regression coverage for the Wave 1 fixes in [tests/python/test_case_generation.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_case_generation.py) and [packages/shared-schema/src/index.test.ts](/Users/user/Desktop/Problem_1_CFD_1/packages/shared-schema/src/index.test.ts).

## Wave 2 Completed

- [x] N-03: Canonicalized case `runStatus.state` to `not_started | generated | running | done | failed` across Python defaults, TypeScript types, JSON Schema, and docs.
- [x] N-03: Canonicalized manifest `status` to `mock | running | done | failed` across TypeScript, JSON Schema, and docs.
- [x] N-03: `generate_case()` now writes generated case directories with `runStatus.state = "generated"` while `create_case_file()` still starts at `not_started`.
- [x] R-04: Replaced mock time-series magic numbers in [services/viewer_data/mock.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/mock.py) with named module constants.
- [x] R-07: Moved `stable_hash`, `write_json`, and `write_text` into [services/utils.py](/Users/user/Desktop/Problem_1_CFD_1/services/utils.py) and updated all Python consumers.
- [x] R-05: Added `sqrtArgs` to the TypeScript `DerivedGeometry` contract and made `checkConstraints()` consume `derived.sqrtArgs` instead of recomputing.

## Wave 2 Files Touched

- [services/utils.py](/Users/user/Desktop/Problem_1_CFD_1/services/utils.py)
- [services/geometry/core.py](/Users/user/Desktop/Problem_1_CFD_1/services/geometry/core.py)
- [services/orchestrator/case.py](/Users/user/Desktop/Problem_1_CFD_1/services/orchestrator/case.py)
- [services/viewer_data/mock.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/mock.py)
- [packages/shared-schema/src/types/index.ts](/Users/user/Desktop/Problem_1_CFD_1/packages/shared-schema/src/types/index.ts)
- [packages/shared-schema/src/geometry.ts](/Users/user/Desktop/Problem_1_CFD_1/packages/shared-schema/src/geometry.ts)
- [packages/shared-schema/src/schemas/case.schema.json](/Users/user/Desktop/Problem_1_CFD_1/packages/shared-schema/src/schemas/case.schema.json)
- [packages/shared-schema/src/schemas/run-manifest.schema.json](/Users/user/Desktop/Problem_1_CFD_1/packages/shared-schema/src/schemas/run-manifest.schema.json)
- [packages/shared-schema/src/index.test.ts](/Users/user/Desktop/Problem_1_CFD_1/packages/shared-schema/src/index.test.ts)
- [tests/python/test_case_generation.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_case_generation.py)
- [technical_documentation.md](/Users/user/Desktop/Problem_1_CFD_1/technical_documentation.md)
- [docs/case-format.md](/Users/user/Desktop/Problem_1_CFD_1/docs/case-format.md)
- [docs/technical-overview.md](/Users/user/Desktop/Problem_1_CFD_1/docs/technical-overview.md)

## Wave 3 Completed

- [x] R-09: Expanded Python coverage for case generation, viewer-data generation, and orchestrator runtime behavior.
- [x] R-01: Added a shared geometry contract fixture and assertions in both Python and TypeScript to keep cross-language geometry outputs in sync.
- [x] N-05: Replaced the O(n^2) window scan in [services/orchestrator/events.py](/Users/user/Desktop/Problem_1_CFD_1/services/orchestrator/events.py) with a sliding-window implementation that keeps derivative and height-range tracking incremental.
- [x] N-06: Guarded `analyze_series()` against shorter `q_in` / `q_out` arrays without raising `IndexError`.

## Wave 3 Files Touched

- [services/orchestrator/events.py](/Users/user/Desktop/Problem_1_CFD_1/services/orchestrator/events.py)
- [packages/shared-schema/src/index.test.ts](/Users/user/Desktop/Problem_1_CFD_1/packages/shared-schema/src/index.test.ts)
- [packages/shared-schema/src/fixtures/geometry-contract.json](/Users/user/Desktop/Problem_1_CFD_1/packages/shared-schema/src/fixtures/geometry-contract.json)
- [tests/python/test_case_generation.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_case_generation.py)
- [tests/python/test_events.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_events.py)
- [tests/python/test_cross_language_contract.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_cross_language_contract.py)
- [tests/python/test_viewer_data.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_viewer_data.py)
- [tests/python/test_orchestrator_cli.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_orchestrator_cli.py)
- [examples/default-case.json](/Users/user/Desktop/Problem_1_CFD_1/examples/default-case.json)
- [examples/default-openfoam-case/case.json](/Users/user/Desktop/Problem_1_CFD_1/examples/default-openfoam-case/case.json)
- [examples/default-mock/manifest.json](/Users/user/Desktop/Problem_1_CFD_1/examples/default-mock/manifest.json)
- [examples/default-mock/event_states.json](/Users/user/Desktop/Problem_1_CFD_1/examples/default-mock/event_states.json)

## Verification Already Run

- `npm run build`
- `npm run test`
- `python -m scripts.build_examples`
- Ajv-based schema validation for `examples/default-case.json` and `examples/default-mock/manifest.json`
- Inline Python verification script covering:
  - case-file transport defaults
  - `generate_case()` input non-mutation
  - inflow velocity propagation into `0/U`
  - transport propagation into `transportProperties`
  - mock manifest provenance reuse
- Wave 2 reran:
  - `npm run build`
  - `npm run test`
  - `python -m scripts.build_examples`
  - inline Python assertions for `services.utils`, generated-case status promotion, mock manifest status, and mock-series length
  - Ajv schema validation for `examples/default-case.json`, `examples/default-openfoam-case/case.json`, and `examples/default-mock/manifest.json`
- Wave 3 reran:
  - `npm run build`
  - `npm run test`
  - `python -m scripts.build_examples`
  - `python -m compileall services tests/python`
  - inline Python assertions covering the shared geometry contract fixture, case-generation helpers, shorter `q_in` / `q_out` handling, mock manifest generation, viewer manifest assembly, and orchestrator runtime branches
- Wave 4 reran:
  - `npm run build`
  - `npm run test`
  - `python -m compileall services tests/python`
  - inline Python HTTP verification covering `POST /api/cases`, `POST /api/cases/{id}/run`, `GET /api/runs/{id}/status`, `GET /api/runs/{id}/manifest.json`, and `GET /api/runs/{id}/series/height.json`

## Environment Notes

- `pytest` is not installed in this environment, so the Python assertions above were verified with an inline `python -` script instead of `python -m pytest`.
- OpenFOAM is still optional. Keep the mock viewer-data path working if solver tooling is unavailable.

## Follow-Up

- The original mock-only API follow-up is complete. Browser-triggered runs now support real solver-backed execution plus post-processing when the solver binary is available, while preserving the mock fallback.

## Post-Review Follow-Up Completed

- [x] Added solver measurement function objects and `foamToVTK || true` to generated OpenFOAM cases so real runs emit container-volume and flow series for post-processing.
- [x] Added [services/viewer_data/real.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/real.py) plus shared viewer assembly helpers in [services/viewer_data/common.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/common.py) to build real manifests from `postProcessing/*` outputs.
- [x] Updated [services/api/server.py](/Users/user/Desktop/Problem_1_CFD_1/services/api/server.py) and the web run client to support `auto | mock | real` run requests and return the physical viewer manifest path (`/api/runs/{id}/viewer/manifest.json`).
- [x] Documented the new runtime behavior and the remaining reduced-frame limitation in [docs/assumptions.md](/Users/user/Desktop/Problem_1_CFD_1/docs/assumptions.md), [docs/technical-overview.md](/Users/user/Desktop/Problem_1_CFD_1/docs/technical-overview.md), and [technical_documentation.md](/Users/user/Desktop/Problem_1_CFD_1/technical_documentation.md).

## Post-Review Follow-Up Files Touched

- [services/orchestrator/case.py](/Users/user/Desktop/Problem_1_CFD_1/services/orchestrator/case.py)
- [services/api/server.py](/Users/user/Desktop/Problem_1_CFD_1/services/api/server.py)
- [services/viewer_data/common.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/common.py)
- [services/viewer_data/mock.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/mock.py)
- [services/viewer_data/real.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/real.py)
- [services/viewer_data/cli.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/cli.py)
- [tests/python/test_api_server.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_api_server.py)
- [tests/python/test_case_generation.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_case_generation.py)
- [tests/python/test_viewer_data.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_viewer_data.py)
- [apps/web/src/lib/runApi.ts](/Users/user/Desktop/Problem_1_CFD_1/apps/web/src/lib/runApi.ts)
- [apps/web/src/pages/ConfigurePage.tsx](/Users/user/Desktop/Problem_1_CFD_1/apps/web/src/pages/ConfigurePage.tsx)
- [docs/assumptions.md](/Users/user/Desktop/Problem_1_CFD_1/docs/assumptions.md)
- [docs/technical-overview.md](/Users/user/Desktop/Problem_1_CFD_1/docs/technical-overview.md)
- [technical_documentation.md](/Users/user/Desktop/Problem_1_CFD_1/technical_documentation.md)

## Post-Review Follow-Up Verification

- `python -m compileall services tests/python`
- `python -m scripts.build_examples`
- `npm run build`
- `npm run test`
- Inline Python verification covering:
  - real manifest assembly from fabricated `postProcessing` outputs
  - `build-manifest` auto-detection of real outputs
  - HTTP `POST /api/cases/{id}/run` with `mode = "real"`
  - API manifest fetch via `/api/runs/{id}/viewer/manifest.json`
  - API serving of `openfoam-case/.foam`

## Current Status Notes

All report waves are complete. The browser-facing API now supports backend case creation, `auto | mock | real` run submission, status polling, and manifest/asset delivery. Real solver post-processing is now implemented for API and CLI-backed manifests when the configured solver binary is available.

### Wave 2 Checklist

- [x] N-03: Canonicalize `runStatus.state` and manifest `status` enums across Python, TypeScript, schemas, and docs.
- [x] R-04: Replace mock time-series magic numbers with named constants in `services/viewer_data/mock.py`.
- [x] R-07: Move `write_json`, `write_text`, and `stable_hash` into a shared Python utility module and update imports.
- [x] R-05: Add `sqrtArgs` to the TypeScript `DerivedGeometry` type, populate it in `computeDerived`, and consume it in `checkConstraints`.

## Later Waves

### Wave 3 Checklist

- [x] R-09: Add broader orchestrator and viewer-data tests.
- [x] R-01: Add cross-language contract tests with shared fixtures.
- [x] N-05: Replace the O(n^2) event window scan with a sliding-window implementation.
- [x] N-06: Guard `analyze_series` against shorter `q_in` / `q_out` inputs.

### Wave 4 Checklist

- [x] R-10: Add an API layer for browser-triggered runs.

### Wave 5 Checklist

- [x] D-01: Real viewer manifests now leave `paraview.vtkDir = null` unless solver-generated `openfoam-case/VTK` assets actually exist.

## Wave 4 Completed

- [x] R-10: Added a stdlib HTTP API in [services/api/server.py](/Users/user/Desktop/Problem_1_CFD_1/services/api/server.py) for browser-triggered case creation, run submission, status polling, and manifest/asset serving.
- [x] R-10: Wired the web configurator to submit backend runs and deep-link into the Runs page via the API manifest URL.
- [x] R-10: Updated the Runs page to resolve both static example manifests and API-backed manifests/assets from a single path model.
- [x] Documented the API flow, mock fallback, and later solver-backed follow-up in the technical docs and assumptions.

## Wave 4 Files Touched

- [services/api/server.py](/Users/user/Desktop/Problem_1_CFD_1/services/api/server.py)
- [tests/python/test_api_server.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_api_server.py)
- [apps/web/src/lib/runApi.ts](/Users/user/Desktop/Problem_1_CFD_1/apps/web/src/lib/runApi.ts)
- [apps/web/src/pages/ConfigurePage.tsx](/Users/user/Desktop/Problem_1_CFD_1/apps/web/src/pages/ConfigurePage.tsx)
- [apps/web/src/pages/RunsPage.tsx](/Users/user/Desktop/Problem_1_CFD_1/apps/web/src/pages/RunsPage.tsx)
- [apps/web/vite.config.ts](/Users/user/Desktop/Problem_1_CFD_1/apps/web/vite.config.ts)
- [docs/assumptions.md](/Users/user/Desktop/Problem_1_CFD_1/docs/assumptions.md)
- [docs/technical-overview.md](/Users/user/Desktop/Problem_1_CFD_1/docs/technical-overview.md)
- [technical_documentation.md](/Users/user/Desktop/Problem_1_CFD_1/technical_documentation.md)

## Discovered During Wave 5

- D-01: [services/viewer_data/real.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/real.py) populated `paraview.vtkDir` with `"vtk"` even when solver-generated `openfoam-case/VTK` assets were absent, which incorrectly pointed ParaView consumers at the viewer's derived-frame directory.

## Wave 5 Completed

- [x] D-01: Real viewer manifests now only advertise solver-generated VTK directories when `openfoam-case/VTK` exists.
- [x] Added regression coverage for real manifest assembly both with and without solver-generated VTK assets.

## Wave 5 Files Touched

- [services/viewer_data/real.py](/Users/user/Desktop/Problem_1_CFD_1/services/viewer_data/real.py)
- [tests/python/test_viewer_data.py](/Users/user/Desktop/Problem_1_CFD_1/tests/python/test_viewer_data.py)
- [docs/code-review-wave-handoff.md](/Users/user/Desktop/Problem_1_CFD_1/docs/code-review-wave-handoff.md)

## Wave 5 Verification

- `python -m compileall services tests/python`
- Inline Python verification covering:
  - real manifest assembly with solver-generated `VTK` assets present
  - real manifest assembly with solver-generated `VTK` assets absent

## Wave 5 Follow-Up

- No further Wave 5 follow-up is currently tracked.

## Handoff Rules For The Next Agent

- Update this file as part of the same commit or patch that advances a wave.
- Leave completed checkboxes checked and add short notes rather than replacing prior status.
- If you discover new issues while implementing a wave, add a `Discovered During Wave` section here instead of editing `code_review_report.md` unless the user asks for the report itself to be revised.
- If you introduce a new assumption not explicit in the source-of-truth files, update `docs/assumptions.md` in the same change.
