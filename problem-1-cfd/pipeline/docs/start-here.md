# Start Here

## Doc Map

- `README.md`: quick start and top-level repo purpose
- `docs/start-here.md`: contributor workflow and working commands
- `docs/technical-overview.md`: canonical technical guide
- `docs/assumptions.md`: non-source assumptions and runtime caveats
- `docs/remediation-roadmap.md`: active backlog and verification gates

## Source Of Truth

Do not edit these unless the user explicitly wants to revise the source specification:

- `experimental_setup.md`
- `setup_3d (2).html`

Canonical parameter names come from `packages/shared-schema`.

## Working Commands

Install:

```bash
python -m pip install -e ".[dev]"
npm install
```

Frontend and API:

```bash
python -m services.api.server
npm run dev
```

Geometry and case generation:

```bash
python -m services.geometry.cli create-case --output examples/sample-cases/default-case.json
python -m services.geometry.cli export-case examples/sample-cases/default-case.json --output-dir tmp/exported-geometry
python -m services.orchestrator.cli generate-case examples/sample-cases/default-case.json --output-dir tmp/openfoam-case
python -m services.orchestrator.cli run-case tmp/openfoam-case
```

Viewer-data generation:

```bash
python -m services.viewer_data.cli mock-run examples/sample-cases/default-case.json --output-dir tmp/mock-run
python -m services.viewer_data.cli build-manifest tmp/openfoam-case
```

Validation helpers:

```bash
python -m scripts.build_examples
python -m scripts.smoke_run
python -m compileall services tests/python
python -m pytest
npm run test
npm run build
```

## Runtime Modes

| Path | Behavior |
|------|----------|
| `python -m services.orchestrator.cli run-case ...` | Requires the configured solver on `PATH`. No mock fallback. |
| API `mode = "auto"` | Uses the real solver when available; otherwise produces mock viewer data. |
| API `mode = "mock"` | Forces mock viewer data. |
| API `mode = "real"` | Requires the solver on `PATH`; returns an error otherwise. |

Browser-triggered runs require `python -m services.api.server`.

## Examples Layout

- `examples/catalog/index.json`: browser-facing run catalog
- `examples/sample-cases/`: canonical sample case JSON and generated OpenFOAM-style case
- `examples/sample-runs/`: browser viewer manifests and frame/series assets

The Vite app serves `examples/` as its public asset root, so manifests and assets must stay under that directory.

## Parameter Naming

HTML aliases still map to canonical schema names:

| HTML | Canonical |
|------|-----------|
| `W1p` | `W1` |
| `W2p` | `W2` |
| `A_tube` | `A` |
| `Wc` | `W` |
| `ha` | `h_a` |

Notes:

- `bendR` is user-facing and remains an explicit input.
- `P4t` is derived from `alpha`; it is not an independent user input in the canonical case schema.

## Current Development Expectations

- Update `docs/assumptions.md` whenever you add a new geometry, solver, or viewer assumption that is not explicit in the source files.
- Treat `docs/remediation-roadmap.md` as the active issue source.
- Treat `docs/code-review-wave-handoff.md` as the execution log.
