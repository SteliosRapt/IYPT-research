# Advanced Siphon Configurations Roadmap

This note consolidates the current simulation capabilities and sketches the path toward modelling complex siphons with multiple crests, self-start behaviour, and tube-angle awareness. Use it as the design reference while we stand up the dedicated multi-segment solver.

## 1. Current simulation families

| Module | Physics scope | Key assumptions |
| --- | --- | --- |
| `simulations.ideal` | Closed-form Bernoulli solution without losses. | Single crest, uniform tube, incompressible liquid, no viscosity, constant outlet pressure. |
| `simulations.constant_losses` | Analytic extension that adds a single lumped head-loss coefficient \(\Lambda\). | Same geometry as the ideal model, losses do not vary with time or Reynolds number. |
| `simulations.variable_losses` | Time-marching solver with Darcy–Weisbach friction updated from the instantaneous Reynolds number. | Straight tube with one crest, uniform diameter, losses depend only on velocity magnitude. |

Across all three modules the reservoir is represented by `SimulationConfig`, which assumes a single drawdown surface area, one tube area, and a single elevation difference between reservoir surface and outlet. The crest height only enters through the Bernoulli head term, so the models cannot describe geometric features such as:

* Multiple local maxima/minima along the tube
* Angled segments that change the vertical elevation non-linearly
* Self-start constraints driven by trapped air pockets or priming failures
* Segment-specific loss coefficients, bends, or valves

## 2. Goals for the multi-crest extension

1. **Segmented geometry.** Represent the tube as an ordered list of straight segments, each with its own length, diameter, orientation angle, and minor-loss coefficients.
2. **Crest diagnostics.** Track the hydrostatic pressure at every node so we can evaluate vapor-pressure margins at each crest without yet predicting when the siphon will self-start.
3. **Primed initial discharge.** Compute the immediate response (velocity, flow, pressures) assuming the siphon is fully primed and suddenly immersed in the reservoir.
4. **Loss-aware physics.** Include distributed friction and minor losses per segment. Each segment can use its own roughness, allowing laminar or turbulent friction factors to be recomputed from the instantaneous Reynolds number.
5. **Angle-aware elevation changes.** Infer vertical elevation changes directly from the supplied segment angles so arbitrary three-dimensional profiles are supported.

We explicitly defer modelling whether the siphon self-primes. Instead, the new solver will accept that a water-filled tube exists and quantify the flow that follows.

## 3. Proposed architecture additions

To keep the existing modules simple, the multi-crest work will live in separate files:

* **`simulations/multi_segment_physics.py`** – low-level dataclasses (`TubeSegment`, `SegmentedTube`, `LossBreakdown`) plus helper functions to evaluate friction factors, compute the loss budget, and generate node-by-node pressure profiles.
* **`simulations/multi_segment.py`** – high-level orchestration that wraps the physics helpers, validates inputs against `ReservoirSetup`, solves for the initial discharge velocity, and returns a structured summary of the primed state.

Both files reuse `FluidProperties` and `ReservoirSetup` from `simulations.common`, but they intentionally bypass `SimulationConfig` so we can store richer geometric detail without overloading the legacy API.

## 4. Calculation outline for the primed-state solver

1. **Geometry validation** – check that each segment has positive length/diameter, accumulate vertical elevation changes from segment angles, and ensure the computed outlet height matches the reservoir outlet datum.
2. **Loss coefficient assembly** – for a trial velocity, compute Reynolds numbers per segment, evaluate Darcy–Weisbach friction (laminar or turbulent) with the supplied roughness, and combine distributed and minor losses into a total coefficient \(\Lambda(v)\).
3. **Velocity solve** – iterate on velocity until the energy balance \((1 - k^2 + \Lambda(v)) v^2 = 2 g \Delta h\) closes, where \(k = A_{\text{tube}} / A_0\) and \(\Delta h\) is the reservoir head.
4. **Pressure profile** – once the velocity is known, march from the outlet back to the entry point, applying each segment’s loss contribution to track the energy grade line and static pressure at every node. This yields crest pressures and the minimum-pressure location immediately after release.
5. **Reporting** – store velocities, flow rates, mass flow, loss breakdown, node elevations, and crest diagnostics in a structured result that downstream tooling (plots, comparison scripts) can consume.

## 5. Next modelling steps

After the primed-state solver is stable we can extend it with:

* Time integration of reservoir drawdown while recomputing the multi-segment loss budget each step.
* Entrained-air or cavitation checks triggered when crest pressures approach vapor pressure.
* Self-start heuristics (e.g., trapped-air pocket tracking) layered on top of the segmented geometry model.

These features will live alongside the new solver rather than altering the existing ideal or single-crest simulations.
