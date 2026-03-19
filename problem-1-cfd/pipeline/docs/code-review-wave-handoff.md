# Remediation Execution Log

Last updated: 2026-03-19
Source: `docs/remediation-roadmap.md`

## Current status

- Planning baseline and historical cleanup: completed
- Solver path correctness: implemented in code; external OpenFOAM validation is still pending
- Runtime and data integrity: completed
- Documentation and schema hardening: completed
- Organization refactor: completed

## 2026-03-19 remediation pass

Completed:

- Replaced the old issue source with `docs/remediation-roadmap.md`.
- Finalized the Python geometry split and kept `services/geometry/core.py` as a compatibility re-export.
- Switched generated solver cases from JSON pseudo-surfaces to STL assets plus searchable refinement boxes.
- Added `surfaceFeatureExtractDict`, `setFieldsDict`, and a `setFields` step in `Allrun`.
- Made generated case directories tool-owned and cleaned on regeneration.
- Moved API runtime dependencies onto `services/orchestrator/runtime.py`.
- Re-keyed API case persistence around full-case identity hashing.
- Matched Python and TypeScript case-identity hashing with shared fixtures.
- Tightened case/manifest schemas for nested objects.
- Extracted browser run orchestration into hooks/services and fixed stale fixed-geometry rendering in `RunViewer`.
- Reorganized sample assets under `examples/catalog`, `examples/sample-cases`, and `examples/sample-runs`.
- Consolidated docs around the new roadmap, quick start, and technical overview.

Files touched:

- `services/utils.py`
- `services/geometry/`
- `services/orchestrator/case.py`
- `services/orchestrator/cli.py`
- `services/orchestrator/runtime.py`
- `services/api/server.py`
- `services/viewer_data/cli.py`
- `packages/shared-schema/src/geometry.ts`
- `packages/shared-schema/src/index.test.ts`
- `packages/shared-schema/src/fixtures/case-identity-contract.json`
- `packages/shared-schema/src/schemas/case.schema.json`
- `packages/shared-schema/src/schemas/run-manifest.schema.json`
- `apps/web/src/components/RunViewer.tsx`
- `apps/web/src/components/RunViewer.test.tsx`
- `apps/web/src/hooks/`
- `apps/web/src/lib/runManifest.ts`
- `apps/web/src/pages/ConfigurePage.tsx`
- `apps/web/src/pages/RunsPage.tsx`
- `apps/web/vite.config.ts`
- `apps/web/package.json`
- `package.json`
- `scripts/build_examples.py`
- `tests/python/test_api_server.py`
- `tests/python/test_case_generation.py`
- `tests/python/test_cross_language_contract.py`
- `tests/python/test_orchestrator_cli.py`
- `README.md`
- `docs/start-here.md`
- `docs/technical-overview.md`
- `docs/assumptions.md`
- `docs/remediation-roadmap.md`
- `technical_documentation.md`
- `AGENTS.md`

Verification run:

- `python -m compileall services tests/python`
- `npm run test --workspace @fixed-geometry/shared-schema`
- `npm run build --workspace @fixed-geometry/shared-schema`
- `npm run test --workspace @fixed-geometry/web`
- `npm run build --workspace @fixed-geometry/web`

Pending external follow-up:

- `python -m pytest` in an environment with `pytest` installed
- `python -m scripts.build_examples`
- `python -m scripts.smoke_run`
- WSL/OpenFOAM validation of the default generated case

## Historical context

- Review Waves 1-5 are complete and superseded by the remediation roadmap.
- Historical review details remain in the archived review documents and git history.
