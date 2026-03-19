# Assumptions

## Geometry

- `A` is treated as the tube outer cross-sectional area because both source files define `r = sqrt(A / pi)` that way.
- Tube wall thickness is not an exposed source parameter. The MVP uses `wallThickness = 0.2 * r`, matching the original HTML visual tube.
- The bend geometry follows the HTML implementation, which uses a midpoint-constrained quadratic Bezier approximation rather than an exact circular arc construction.

## Measurements

- `A0` is used as the default plan area for `H(t)` because the source files define it as the container footprint and do not provide a separate interior-area formula.
- The mock run uses synthetic water-volume evolution. It is not a CFD result and exists to keep the viewer demonstrably functional when OpenFOAM is unavailable.
- Real solver-backed viewer manifests still render reduced box-and-plume browser frames derived from solver-measured `H(t)` and `Q_out(t)`, not the full CFD free-surface mesh.

## Runtime

- WSL with OpenFOAM on PATH is the preferred local runtime on Windows. Docker remains a manual reference path and is not the primary backend execution environment.
- OpenFOAM is not installed in the current environment, so the committed example run is synthetic.
- The generated OpenFOAM-style case now writes solver-consumable STL patch assets plus `setFields`, but it still needs real OpenFOAM validation before production CFD use.
- The initial real-solver water column is applied with `setFields` over the container volume from `y = 0` to the canonical `H0` height. The tube remains dry at startup.
- Browser-triggered runs use the local HTTP API. The API now serves real solver-backed post-processing when the configured solver binary is on PATH and falls back to mock viewer-data assets otherwise.
- CLI `run-case` does not perform a mock fallback. Only API `mode = "auto"` does.

