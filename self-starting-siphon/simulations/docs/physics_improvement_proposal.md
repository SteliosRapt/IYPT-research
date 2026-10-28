# Physics Solver Improvement and Refactoring Proposal

## Overview
This document consolidates recent findings about the siphon simulators and outlines a set of corrective actions and refactoring steps. The focus is on eliminating the two critical bugs uncovered during the code review, strengthening the architecture shared by the physics modules, and expanding automated coverage so regressions are caught early.

## Bug Fix Priorities
1. **Variable-loss integrator step floor**
   The adaptive integrator in the variable-loss solver enforces a minimum step equal to one tenth of the nominal step size. When the reservoir is nearly empty this lower bound overshoots the remaining head, which in turn inflates the predicted drain time. Removing the hard floor (or switching to a logarithmic step contraction capped only by the tolerance) will let the final integration step shrink to the physically correct scale.
   *Update:* The production solver now drives the step size down to machine precision when required, eliminating the spurious tail in the drainage curve.

2. **Premature termination reporting**
   If the solver exits because `max_time` is reached while the fluid level is still above the outlet, the routine still zeros the terminal velocity and flow. That masks incomplete drains as if they finished successfully. Preserve the last computed velocity/head pair in this branch and expose a status flag so callers can tell when a run hit the cap.
   *Update:* Runs that hit `max_time` now keep their terminal kinematics and surface a `MAX_TIME_REACHED` status flag in the metadata.

## Refactoring Opportunities
- **Unify plot formatting helpers**  
  The plotting routines in the ideal, constant-loss, and variable-loss modules all clone `_plot_series`. Extract a shared helper (e.g., `simulations.plotting.format_series`) that accepts stylistic overrides. Tests should ensure identical defaults so module-specific plots remain visually consistent.

- **Surface convergence issues**  
  The solvers currently return the last midpoint when bisection cannot satisfy the tolerance. Wrapping these fallbacks in a structured warning (or exception for strict modes) will help practitioners notice when inputs lead to non-convergent states.

- **Generalise multi-segment geometry validation**  
  `SegmentedTube._validate_geometry` forbids cross-sectional area changes, preventing reducer/expander sections that appear in experiments. Refactor the geometry model so each segment can optionally supply its own area computation, allowing tees, bulbs, or reducers while retaining safety checks for impossible transitions.

## Testing Enhancements
- Add regression tests that target the multi-segment solver, verifying crest detection logic and the primed-state solver under representative geometries.
- Extend the existing single-tube tests to cover the corrected termination semantics and the removal of the minimum step floor.

## Fluid Dynamics Model Improvements
Replace the stepwise Reynolds-number switch with a smoother blended correlation (e.g., Churchill or Haaland). Implement this as a standalone utility so the different solvers can share the same laminar–turbulent transition function, reducing the chance of divergent behaviour across modules.

## Suggested Implementation Order
1. Patch the two correctness bugs and add regression tests for them.
2. Refactor shared plotting utilities and convergence reporting, keeping behaviour parity verified via tests.
3. Relax the geometry validation and add multi-segment coverage.
4. Introduce the smoother Reynolds transition model and update dependent modules, accompanied by validation plots.

Following this order addresses the most urgent accuracy issues first while building the scaffolding needed for broader architectural improvements.
