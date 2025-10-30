# Advanced Siphon Configurations Roadmap

This note consolidates the current simulation capabilities and sketches the path
toward modelling complex siphons with multiple crests, self-start behaviour, and
three-dimensional awareness. Use it as the design reference while extending the
new segment-aware solver.

## 1. Current simulation families

| Module | Physics scope | Key assumptions |
| --- | --- | --- |
| `simulations.ideal` | Closed-form Bernoulli solution without losses. | Single crest, uniform tube, incompressible liquid, no viscosity, constant outlet pressure. |
| `simulations.constant_losses` | Analytic extension that adds a single lumped head-loss coefficient \(\Lambda\). | Same geometry as the ideal model, losses do not vary with time or Reynolds number. |
| `simulations.variable_losses` | Time-marching solver with Darcy–Weisbach friction updated from the instantaneous Reynolds number and an ordered list of `SiphonSegment` objects. | Segment elevations are inferred from user input; segments are straight and only track scalar roughness/minor losses. |

The `VariableLossConfig` dataclass already accepts multiple segments with
independent diameters, lengths, roughness, and minor-loss coefficients. This
covers most of the requirements listed in `Attempt/musthaves.md` for variable
cross-sections and distributed losses. The remaining gaps are geometric (angles,
branching) and self-start heuristics.

## 2. Goals for the next extension

1. **Angle-aware geometry.** Extend `SiphonSegment` with orientation data so the
   solver can compute crest elevations directly from segment definitions rather
   than assuming the user provides `TubeGeometry.crest_height`.
2. **Multi-crest diagnostics.** Track hydrostatic pressure at every node to
   evaluate vapor-pressure margins across multiple peaks without yet predicting
   when the siphon will self-start.
3. **Branching support.** Allow multiple inlet/outlet branches by generalising
   the segment list into a graph structure with conservation of mass at each
   junction.
4. **Self-start screening.** Layer air-pocket tracking and priming heuristics on
   top of the segmented geometry to predict when a siphon will fail to sustain a
   liquid column.

## 3. Architecture direction

Rather than introducing entirely new modules, the roadmap augments the existing
`simulations.variable_losses` package:

* Add richer geometric dataclasses (e.g., `OrientedSegment`, `SegmentNetwork`)
  that extend `SiphonSegment` while remaining backward compatible.
* Provide helper routines that convert geometric definitions into vertical
  coordinates, assemble loss budgets per segment, and emit node-by-node pressure
  profiles.
* Keep the high-level API centred on `simulate_variable_losses` so notebooks and
  tests continue to work, exposing advanced outputs through optional fields in
  the returned `VariableLossResult`.

## 4. Calculation outline for multi-crest support

1. **Geometry validation** – ensure each segment has positive length/diameter,
   accumulate vertical changes from segment orientations, and verify the computed
   outlet height matches the supplied datum.
2. **Loss coefficient assembly** – for a trial velocity, compute Reynolds
   numbers per segment, evaluate Darcy–Weisbach friction (laminar or turbulent)
   with the supplied roughness, and combine distributed and minor losses into a
   total coefficient \(\Lambda(v)\).
3. **Velocity solve** – iterate on velocity until the energy balance closes using
   the dynamic \(\Lambda(v)\) assembled above.
4. **Pressure profile** – march along the segment list, applying each loss to
   track the energy grade line and static pressure. Record crest pressures and
   the minimum-pressure location immediately after release.
5. **Reporting** – store velocities, flow rates, mass flow, loss breakdown, node
   elevations, and crest diagnostics in the result structure for downstream
   plotting and comparison scripts.

## 5. Subsequent modelling steps

After multi-crest support ships we can extend the solver with:

* Time integration of reservoir drawdown in branching networks while recomputing
  the loss budget each step.
* Entrained-air or cavitation checks triggered when crest pressures approach
  vapor pressure.
* Coupling to external CFD meshes (OpenFOAM, PyFR) using the segment data as
  boundary conditions for high-resolution studies.

These features build directly on the present simulation suite and keep the code
base cohesive while delivering the advanced analyses promised in the project
outline.
