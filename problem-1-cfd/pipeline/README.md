# Fixed-Geometry CFD Pipeline

This repo turns the source-of-truth rig description in `experimental_setup.md` and `setup_3d (2).html` into:

- a browser configurator
- canonical case JSON files
- OpenFOAM-style case generation
- mock and solver-backed viewer manifests
- browser and ParaView inspection assets

## Quick Start

Install Python and workspace dependencies:

```bash
python -m pip install -e ".[dev]"
npm install
```

Run the frontend and local API together:

```bash
python -m services.api.server
npm run dev
```

Generate the committed sample assets:

```bash
python -m scripts.build_examples
```

Run a local smoke path:

```bash
python -m scripts.smoke_run
```

## Runtime Notes

- Browser-triggered runs require the local API server.
- API run mode `auto` falls back to mock output when the configured solver is not on `PATH`.
- `python -m services.orchestrator.cli run-case ...` does not fall back to mock output. It requires a real solver runtime.
- On Windows, WSL with OpenFOAM on `PATH` is the preferred real-solver environment.

## Example Layout

- Catalog: `examples/catalog/index.json`
- Sample cases: `examples/sample-cases/`
- Sample runs: `examples/sample-runs/`

## Documentation

- Start here: `docs/start-here.md`
- Deep technical guide: `docs/technical-overview.md`
- Assumptions and solver caveats: `docs/assumptions.md`
- Active remediation roadmap: `docs/remediation-roadmap.md`

## Historical Context

- `code_review_report.md`
- `refactoring_proposal.md`
- `docs/refactoring-proposal.md`

Those files are retained for historical context only. The active issue source is `docs/remediation-roadmap.md`.
