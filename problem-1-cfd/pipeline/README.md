# Fixed-Geometry CFD Pipeline MVP

This repo turns the source-of-truth geometry in `experimental_setup.md` and `setup_3d (2).html` into a local pipeline with:

- a browser configurator
- canonical case JSON export
- OpenFOAM-style case generation
- event logic and mock run generation
- browser viewer assets and ParaView-compatible legacy VTK frames

## Status

Implemented now:

- canonical parameter schema and shared formulas
- Python geometry, orchestrator, and viewer-data CLIs
- React/Vite web app scaffold for configuration and run browsing
- committed default example case and mock run
- tests, docs, and smoke scripts

Not fully executed here:

- real OpenFOAM meshing and solving
- WSL-based coarse CFD run
- exact watertight boolean holder cutouts in exported solid meshes

## Install

For local OpenFOAM work on Windows, use WSL Ubuntu and run the solver/API from the same WSL environment. The Docker image in `solver/openfoam-template` remains a manual reference path and is not the primary local runtime.

Python:

```bash
python3 -m pip install -e '.[dev]'
```

Node:

```bash
npm install
```

## Run the web app

```bash
make web-dev
```

## Export a case

Browser:

- open the configurator
- adjust parameters
- use `Export case JSON`, `Export STL`, or `Export GLB`

CLI:

```bash
python3 -m services.geometry.cli create-case --output examples/default-case.json
python3 -m services.geometry.cli export-case examples/default-case.json --output-dir examples/exported-geometry
```

## Run a coarse simulation

Generate the OpenFOAM-style case:

```bash
make case-generate CASE=examples/default-case.json CASE_DIR=examples/default-openfoam-case
```

Preferred on Windows: run this from WSL after OpenFOAM is installed there, so `interFoam` is on the same `PATH` as the Python API/CLI.

If OpenFOAM is available on the current runtime:

```bash
python3 -m services.orchestrator.cli run-case examples/default-openfoam-case
```

If it is not available, use the mock viewer-data path instead.

## Generate viewer data

```bash
make viewer-data CASE=examples/default-case.json VIEWER_DIR=examples/default-mock
```

## Load a run in the browser

Run the app, then open the `Runs` page. The committed example index points at:

- `examples/default-mock/manifest.json`

## Inspect the same run in ParaView

Open any legacy VTK frame under:

- `examples/default-mock/vtk/`

For example:

```bash
paraview examples/default-mock/vtk/frame_0000.vtk
```

## Validation commands

```bash
pytest
python3 scripts/build_examples.py
python3 scripts/smoke_run.py
make web-build
```

## Main entry points

- web app: `apps/web`
- geometry service: `services/geometry/core.py`
- case generator: `services/orchestrator/case.py`
- solver runner: `services/orchestrator/cli.py`
- viewer-data builder: `services/viewer_data/mock.py`

## Known limitations

- The committed example run is synthetic because OpenFOAM is not installed in this environment.
- The generated OpenFOAM-style case is a baseline scaffold and needs runtime validation before production use.
- The browser viewer uses simplified fixed-geometry polydata derived from geometry descriptors, not a full CFD mesh.
