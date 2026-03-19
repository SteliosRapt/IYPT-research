# Validation Plan

## Automated checks

- Python unit tests for geometry formulas and constraints.
- Source-parity checks against the default values in `setup_3d (2).html`.
- Event-state tests using the mock time-series generator.
- Schema validation for the committed example case and mock manifest.
- Smoke tests for case generation and mock viewer-data generation.

## Manual checks

- Open the web configurator and verify live constraint updates while adjusting parameters.
- Load the committed mock run in the browser and verify the time scrubber, charts, and event markers.
- Open the legacy VTK frames from `examples/default-mock/vtk` in ParaView.

## Deferred CFD validation

- Install OpenFOAM inside WSL and run the solver/API from that same WSL environment.
- Run the generated case through `blockMesh`, `snappyHexMesh`, and `interFoam`.
- Compare the real solver event summary with the mock fallback expectations and update thresholds as needed.

