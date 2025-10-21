# Siphon Drainage Simulations

This repository contains analytical and numerical models for the International Young Physicists' Tournament (IYPT) siphon problem. The code predicts the transient behaviour of a reservoir draining through a siphon tube under three modelling assumptions, plus a design-stage analyser for complex geometries:

* **Ideal (no losses):** closed-form solution with purely gravitational driving head.
* **Constant losses:** analytical solution including a constant Darcy–Weisbach plus minor-loss head-loss coefficient.
* **Velocity-dependent losses:** time-marching solution that recomputes friction and loss coefficients from the instantaneous Reynolds number.
* **Multi-segment primed state:** a geometry-aware solver that reports the initial discharge and crest pressures once a multi-crest siphon is fully primed.

Each simulation can generate diagnostic plots and machine-readable metadata to support comparison with experiments.

## Repository layout

| Path | Description |
| --- | --- |
| `simulations/` | Python modules implementing the siphon models and the comparison/analysis utilities. |
| `docs/` | Physics derivations and background notes at a range of technical depths. |
| `plots/` | Example figures produced by the scripts (created when you run them). |
| `backup/` | Archived materials preserved from earlier iterations of the project. |

## Requirements

The code relies on Python 3.11+ with the following third-party packages:

```
numpy
matplotlib
```

If you have internet access, install them with:

```bash
python -m pip install -r requirements.txt
```

When working offline, install the wheels from your package cache or system package manager before running the simulations.

> **Note:** In the execution environment used for the latest automated checks we were unable to install `numpy` and `matplotlib` because outbound network access is blocked. All reported test results below reflect that limitation.

## Running the simulations

Each module can be executed directly with Python. The example configuration embedded at the bottom of each script will create plots under `plots/<scenario>`.

```bash
# Ideal, lossless siphon
python -m simulations.ideal

# Constant loss coefficient (Λ provided or inferred from geometry)
python -m simulations.constant_losses

# Velocity-dependent losses with iterative friction updates
python -m simulations.variable_losses

# Primed multi-crest geometry analyser
python -m simulations.multi_segment
```

To run all three scenarios side-by-side and produce comparison figures, create a short driver script that imports `simulations.comparison.run_all`, constructs a shared `SimulationConfig`, and calls `run_all` with your output directory of choice.

## Recommended workflow for experiments

1. **Characterise your setup.** Measure tube length, diameter, roughness, and any fittings to estimate the loss coefficients or friction factor bounds.
2. **Start from the ideal model.** Use `simulations.ideal` to establish an upper bound on draining velocity and a lower bound on drain time.
3. **Introduce constant losses.** Move to `simulations.constant_losses` to include Darcy–Weisbach and minor losses estimated from tables. Compare to data to calibrate Λ.
4. **Activate variable losses.** Switch to `simulations.variable_losses` to recompute friction factors with Reynolds-number awareness and to track how Λ evolves as the reservoir empties.
5. **Validate against measurements.** Use the generated metadata (`metadata.json`) to log run conditions and to overlay plots with experimental traces.

## Physics assessment and suggestions

* The **ideal model** reproduces the textbook Torricelli-based drainage law, delivering linear velocity decay and a square-root fall in water height. It is valid only when viscous and minor losses are negligible (short, wide tubes).
* The **constant-loss model** correctly extends the analytic solution by adding a lumped Λ term. This is appropriate for moderate Reynolds numbers where friction does not change appreciably during the drain. Consider exposing laminar/turbulent friction-factor toggles so users can supply \(f(Re)\) curves directly.
* The **variable-loss model** iteratively solves for velocity using a Darcy–Weisbach correlation that blends laminar and turbulent regimes. Because it enforces a velocity floor when head drops to zero, it avoids negative heights. Adding adaptive time stepping (based on a target Courant number) and tolerance-controlled convergence criteria would improve robustness for very small area ratios.
* Across all models, **cavitation and air-entrainment limits** are only diagnosed qualitatively via plots. Introducing crest-pressure tracking and entrance Froude-number checks would let the simulation flag when a siphon is likely to break.
* For experimental comparison, include hooks to ingest measured height–time curves and compute error metrics (RMSE, drain-time offset). This will highlight which loss model best matches a given setup.

Additional derivations and learning resources for both introductory and advanced readers are collected in `docs/`—see especially `docs/physics_overview.md` for a plain-language summary and roadmap.

## Testing

The repository does not yet include automated unit tests. The development workflow relies on executing the modules directly and inspecting the generated plots. Attempting to run `python -m simulations.ideal` in the current sandbox fails because `numpy` is unavailable and cannot be installed without internet access. Once dependencies are installed locally, rerun the command trio listed above to verify end-to-end behaviour.

