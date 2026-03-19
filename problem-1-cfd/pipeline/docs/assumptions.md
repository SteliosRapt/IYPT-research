# Assumptions

## Geometry

- `A` is treated as the tube outer cross-sectional area because both source files define `r = sqrt(A / pi)` that way.
- Tube wall thickness is not an exposed source parameter. The MVP uses `wallThickness = 0.2 * r`, matching the original HTML visual tube.
- The bend geometry follows the HTML implementation, which uses a midpoint-constrained quadratic Bezier approximation rather than an exact circular arc construction.

## Measurements

- `A0` is used as the default plan area for `H(t)` because the source files define it as the container footprint and do not provide a separate interior-area formula.
- The mock run uses synthetic water-volume evolution. It is not a CFD result and exists to keep the viewer demonstrably functional when OpenFOAM is unavailable.

## Runtime

- Docker and OpenFOAM are not installed in the current environment, so the committed example run is synthetic.
- The generated OpenFOAM-style case is intended as a coarse starting point and needs mesh and boundary-condition validation before production CFD use.

