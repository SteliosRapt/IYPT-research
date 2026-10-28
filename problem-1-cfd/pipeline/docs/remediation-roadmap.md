# Remediation Roadmap

## Historical completions

- Review Waves 1-5 and the earlier post-review follow-up are complete and remain available in git history plus the historical review documents.
- The current remediation pass completed the planned code changes for:
  - full-case `caseId` hashing with shared Python/TypeScript contract fixtures
  - geometry module split plus compatibility re-export
  - solver-consumable STL surface generation and searchable refinement boxes
  - `setFields` initialization from canonical `H0`
  - tool-owned generated case directories with cleanup on regeneration
  - API persistence keyed by the new `caseId`
  - runs viewer fixed-geometry refresh and page-hook extraction
  - schema hardening for nested case/manifest objects
  - examples reorganization under `examples/catalog`, `examples/sample-cases`, and `examples/sample-runs`
  - documentation consolidation around `README.md`, `docs/start-here.md`, and `docs/technical-overview.md`

## Open issues

- Real OpenFOAM acceptance for the default generated case still needs to be executed in an environment where the solver toolchain is available.
- `python -m pytest` still depends on a dev environment with `pytest` installed.
- The browser viewer continues to use reduced box-and-plume frame meshes derived from measurements rather than the full CFD free-surface mesh.

## Execution phases

- Phase 1: planning baseline and historical cleanup — completed
- Phase 2: solver path correctness — implemented in code, pending external OpenFOAM validation
- Phase 3: runtime and data integrity — completed
- Phase 4: documentation and schema hardening — completed
- Phase 5: organization refactor and example reorganization — completed

## Verification gates

- Completed:
  - `python -m compileall services tests/python`
  - `npm run test --workspace @fixed-geometry/shared-schema`
  - `npm run test --workspace @fixed-geometry/web`
  - `npm run build --workspace @fixed-geometry/shared-schema`
  - `npm run build --workspace @fixed-geometry/web`
- Pending in a suitable environment:
  - `python -m pytest`
  - `python -m scripts.build_examples`
  - `python -m scripts.smoke_run`
  - WSL/OpenFOAM validation of the default generated case through `blockMesh`, `surfaceFeatureExtract`, `snappyHexMesh -overwrite`, `topoSet`, `setFields`, and a short solver run
