# Physics Roadmap for the Siphon Simulations

This guide summarises the modelling approach behind the three siphon simulations and suggests how readers with different backgrounds can use the materials in `docs/`.

## 1. Quick intuition (for science-fair and high-school audiences)

* A siphon drains because gravity pulls water down the outlet leg faster than the inlet leg can refill, creating a pressure drop at the crest that drags the liquid over the top.
* The wider the tube compared with the reservoir, the faster the water level falls. We encode this ratio as \(k = A_{tube} / A_{reservoir}\).
* Real tubes waste energy on friction (rubbed walls, bends, valves). Engineers summarise those effects with a **loss coefficient** \(\Lambda\). Bigger \(\Lambda\) means more energy wasted and a slower siphon.
* Cavitation (vaporization due to low pressure) and air entrainment (vortex at the inlet) can break the siphon even if water remains above the outlet. Keep the crest below roughly 10 m above the outlet and submerge the inlet deeply to stay safe.

**Suggested reading order:**

1. `docs/ideal_without_losses.md` — shows how height and velocity change with time when losses are zero.
2. `docs/constant_losses.md` — introduces the idea of a fixed \(\Lambda\) that slows everything down uniformly.
3. Skim the plots produced by `simulations/ideal.py` and `simulations/constant_losses.py` to see the theory in action.

## 2. Intermediate depth (for undergraduates)

* Treat the reservoir surface and outlet as two stations connected by Bernoulli's equation. The only unknown is the tube velocity.
* **Constant-loss model:** write \(\Lambda = f L/D + \sum K_i\). Tables for \(f\) (Darcy friction factor) and \(K_i\) (minor losses) give decent first estimates. Drain time grows with \(\sqrt{1 - k^2 + \Lambda}\).
* **Variable-loss model:** recompute \(f\) from the Reynolds number at each time step. Laminar flow uses \(f = 64/Re\); turbulent flow uses a Colebrook–White approximation. This creates a nonlinear algebraic equation for velocity that the code solves by bisection.
* Monitor the crest pressure to ensure \(P > P_{vapour}\) and the inlet Froude number \(Fr < 0.3\) to avoid entrainment.

**Suggested reading order:**

1. Review Sections 1–2 of `docs/constant_losses.md` for the analytical solution with \(\Lambda\).
2. Study Sections 3–6 of `docs/variable_losses.md` to understand how losses evolve with Reynolds number and how the numerical integrator advances the tank height.
3. Experiment with `simulations.variable_losses.create_plots` to see how \(\Lambda(t)\) responds to geometry changes.

## 3. Advanced exploration (for research projects)

* Replace the plug-flow assumption with kinetic-energy correction factors \(\alpha\) to capture non-uniform velocity profiles.
* Segment the tube into varying diameters and roughness to assemble distributed losses from handbook data.
* Extend the solver with adaptive time stepping and Newton iterations for the implicit energy balance as outlined in Section 5 of `docs/variable_losses.md`.
* Incorporate a two-phase model (slug flow or homogeneous mixture) once cavitation or air entrainment triggers. This demands tracking pressure waves and compressibility.
* Validate against experiments by logging measured drain curves and comparing them to the metadata emitted by each simulation.

## 4. Suggested next steps for the codebase

1. **Testing:** add regression tests that call each simulation with a small time/point grid and assert drain times against known benchmarks.
2. **Cavitation warnings:** extend `SimulationResult.summary` with minimum crest pressure and inlet Froude number to provide automatic warnings.
3. **Data assimilation:** create utilities to read CSV height–time data and fit \(\Lambda\) or roughness, closing the loop between experiment and model.
4. **Documentation website:** publish the `docs/` materials with a static site generator (e.g., MkDocs) to make the derivations searchable and easier to navigate.

These steps will make the project more approachable for competitors preparing IYPT presentations and for mentors seeking to validate experimental results.
