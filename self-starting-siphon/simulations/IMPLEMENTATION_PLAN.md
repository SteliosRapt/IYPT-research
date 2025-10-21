# Unified Improvement Implementation Plan

This plan merges the actionable items from the refactoring recommendations, the physics improvement proposal, and the existing documentation review. It is organised into seven phases that balance correctness, maintainability, and documentation. Each task lists its dependencies, affected modules, deliverables, and verification steps so no critical detail is skipped.

---

## Phase 0 – Baseline & Infrastructure (1–2 days)

| Goal | Ensure changes are measurable and reproducible before modifying core physics. |
| --- | --- |

1. **Set up project-wide quality gates**
   - **Files**: `pyproject.toml` (or `setup.cfg` if added), `.pre-commit-config.yaml` (new), `requirements.txt`.
   - **Actions**:
     1. Define tooling versions (Black/ruff/mypy/pytest) in a central config.
     2. Add a pre-commit configuration covering formatting, import sorting, type checking, and unit tests.
     3. Update `requirements.txt` or create `requirements-dev.txt` with pinned development dependencies.
   - **Verification**: Run `pre-commit run --all-files`, confirm deterministic formatting, and ensure CI configuration (if present) references the new commands.

2. **Capture baseline performance and coverage**
   - **Files**: `test_simulations.py`, `README.md` (append section), CI workflow (if added later).
   - **Actions**:
     1. Execute `pytest --maxfail=1 --disable-warnings -q` and record runtime plus current failures.
     2. Enable coverage measurement (`coverage run -m pytest`) and document baseline figures in `README.md` for comparison after refactors.
     3. Save plots or metadata from sample runs (one per simulation) into `backup/baseline_runs/` for regression comparison.
   - **Verification**: Commit stored artefacts (or scripts to regenerate them) and include baseline metrics table in `README.md`.

---

## Phase 1 – Physics Correctness Hotfixes (2–3 days, highest priority)

| Goal | Address the two correctness bugs and clarify pressure calculations. |
| --- | --- |

1. **Remove adaptive step-size floor in variable-loss integrator**
   - **Files**: `simulations/variable_losses.py` (`simulate` loop around lines 103–120), `docs/variable_losses.md`.
   - **Actions**:
     1. Replace `dt = max(dt, time_step / 10)` with a logarithmic or tolerance-controlled minimum (e.g., cap only by `np.nextafter` logic). Allow `dt` to shrink to remaining head.
     2. Document the new strategy and rationale in the variable-loss documentation.
   - **Verification**: Add regression test to `test_simulations.py` verifying final height is within `1e-6` of outlet for near-empty reservoirs.

2. **Fix premature termination reporting**
   - **Files**: `simulations/variable_losses.py` (`simulate` exit branch), `simulations/common.py` (`SimulationResult`), `docs/physics_improvement_proposal.md` (append change log).
   - **Actions**:
     1. Preserve the last computed `velocity`, `flow`, and `loss_coeff` when `max_time` triggers termination; expose a status enum (`COMPLETED`, `MAX_TIME_REACHED`).
     2. Update `SimulationResult.summary` to include termination status and ensure metadata JSON stores it.
   - **Verification**: Regression test asserting that runs hitting `max_time` keep the final non-zero velocity and set status appropriately.

3. **Clarify pressure reference in ideal model**
   - **Files**: `simulations/ideal.py` (`pressure` calculation), `docs/ideal_without_losses.md`.
   - **Actions**:
     1. Decide on physical interpretation (crest pressure vs outlet gauge). Implement by computing crest height from tube geometry (`TubeGeometry.entry_height`, see Phase 3) and subtracting dynamic head.
     2. Adjust annotation text in `create_plots` to state reference point explicitly.
   - **Verification**: Unit test verifying pressure decreases with height and never drops below vapor pressure unless crest exceeds safe height.

---

## Phase 2 – Shared Utility Extraction & Code De-duplication (2–4 days)

| Goal | Eliminate duplicated helpers to centralise behaviour changes. |
| --- | --- |

1. **Promote common validation helpers**
   - **Files**: `simulations/common.py`, `simulations/ideal.py`, `simulations/constant_losses.py`, `simulations/variable_losses.py`, `simulations/multi_segment.py`.
   - **Actions**:
     1. Move `_validate_area_ratio` and `_validate_head` into `common.py` as public functions (e.g., `validate_area_ratio`, `validate_head`).
     2. Update all modules to import the shared helpers and remove local duplicates.
   - **Verification**: Parameterised tests covering invalid ratios and heads should live in `test_simulations.py`.

2. **Create shared plotting module**
   - **Files**: new `simulations/plotting.py`, existing modules above.
   - **Actions**:
     1. Extract `_plot_series` into reusable functions that accept style overrides and annotate summary boxes.
     2. Ensure facecolour/style differences are controlled via keyword arguments or theme definitions.
     3. Update documentation in `docs/*` that reference plotting internals.
   - **Verification**: Snapshot tests comparing generated plots (using matplotlib testing utilities) ensure parity.

3. **Centralise friction factor and loss aggregation**
   - **Files**: `simulations/common.py`, `simulations/variable_losses.py`, `simulations/multi_segment_physics.py`.
   - **Actions**:
     1. Introduce a `darcy_friction_factor` utility with optional model selection (Swamee–Jain default).
     2. Replace duplicated `_darcy_friction_factor` and `np.sum(self.minor_loss_coefficients)` patterns with helpers (`sum_loss_coefficients`).
   - **Verification**: Unit tests covering laminar, transitional, and turbulent regimes plus zero/negative Reynolds numbers.

4. **Abstract bisection solver**
   - **Files**: new `simulations/solvers.py`, `variable_losses.py`, `multi_segment_physics.py`.
   - **Actions**:
     1. Implement a reusable `bisection` routine that accepts tolerance, max iterations, and callback for diagnostics.
     2. Integrate into both modules, ensuring return signatures remain unchanged.
     3. Emit warnings (via `logging`) when convergence fails; provide hooks for Phase 4 diagnostics.
   - **Verification**: Tests forcing non-convergent cases should assert warnings; successful cases must match previous velocity solutions within tolerance.

---

## Phase 3 – Geometry Model Enhancements (3–4 days)

| Goal | Extend geometry definitions to cover entry heights and variable cross-sections, unblocking advanced scenarios. |
| --- | --- |

1. **Add `entry_height` to `TubeGeometry`**
   - **Files**: `simulations/common.py` (`TubeGeometry` dataclass), `ideal.py`, `constant_losses.py`, `variable_losses.py`, docs.
   - **Actions**:
     1. Introduce optional `entry_height` with backward-compatible default (`reservoir.initial_height`).
     2. Propagate through simulation configs and use in pressure calculations (Phase 1.3).
   - **Verification**: Update tests to instantiate geometry with entry height; confirm existing behaviour unchanged when omitted.

2. **Relax `SegmentedTube` area constraint**
   - **Files**: `simulations/multi_segment_physics.py`, `multi_segment.py`, docs.
   - **Actions**:
     1. Replace fixed-area check with validation that enforces monotonic transitions or acceptable ratios.
     2. Store per-segment areas and compute hydraulic diameter accordingly.
     3. Update solver to handle varying areas in continuity and loss calculations.
   - **Verification**: New tests for reducers/expanders verifying crest detection and loss breakdown remain stable.

3. **Expose crest metadata consistently**
   - **Files**: `multi_segment_physics.py`, `multi_segment.py`, `simulations/comparison.py`.
   - **Actions**:
     1. Provide API returning crest indices, heights, and pressures for downstream diagnostics.
     2. Include crest summary in metadata JSON and ensure plotting overlays crest markers.
   - **Verification**: Tests checking crest metadata for multi-crest scenario; plot regression verifying markers drawn.

---

## Phase 4 – Solver Robustness & Physics Improvements (3–5 days)

| Goal | Improve numerical stability, capture transitional physics, and surface solver issues early. |
| --- | --- |

1. **Implement smooth Reynolds transition**
   - **Files**: `simulations/common.py` (new utility), `variable_losses.py`, `multi_segment_physics.py`.
   - **Actions**:
     1. Add Churchill or Haaland correlation implementation selectable via configuration.
     2. Replace hard laminar/turbulent switch with blended correlation; keep laminar regression tests for validation.
   - **Verification**: Analytical comparison against reference tables (store fixtures) and tests ensuring monotonic behaviour across Reynolds sweep.

2. **Add convergence diagnostics**
   - **Files**: `simulations/solvers.py`, `variable_losses.py`, `multi_segment_physics.py`.
   - **Actions**:
     1. Extend bisection helper to track iteration count, residual history, and failure modes.
     2. Expose diagnostics via `SimulationResult.metadata` and log warnings when tolerance unmet.
   - **Verification**: Tests simulating intentionally tough cases verifying diagnostic payload and warning emission.

3. **Enhance multi-segment priming solver**
   - **Files**: `multi_segment.py`, `multi_segment_physics.py`.
   - **Actions**:
     1. Review `solve_velocity` and `compute_initial_state` to ensure stability when crest pressures approach vapor pressure.
     2. Introduce cavitation guard rails (e.g., automatic step reduction, user warnings) using new diagnostics.
   - **Verification**: Tests covering borderline cavitation scenarios ensuring solver warns but still returns data.

---

## Phase 5 – Testing Expansion & Automation (4–5 days)

| Goal | Reach >90% coverage on physics modules and add regression suites for future proofs. |
| --- | --- |

1. **Unit tests for geometry and solvers**
   - **Files**: `test_simulations.py` (extend significantly), optional `tests/test_plotting.py` for plotting helpers.
   - **Actions**:
     1. Implement the detailed class-based tests outlined in previous recommendations (TubeSegment, SegmentedTube, MultiSegmentSolver).
     2. Add parameterised tests for new utilities (friction factor, convergence diagnostics, loss summations).
   - **Verification**: `pytest --cov=simulations --cov-report=term-missing` should exceed 90% for `multi_segment*` modules.

2. **Regression tests for termination and integrator changes**
   - **Files**: `test_simulations.py`, `backup/baseline_runs/` (expected metadata JSONs).
   - **Actions**:
     1. Use recorded baseline metadata to assert drain times and termination flags for canonical scenarios.
     2. Include tolerance-based checks for pressure and flow arrays to guard against silent regressions.
   - **Verification**: Tests must fail if status flag regresses or integrator reintroduces oversized final step.

3. **Plot comparison tests**
   - **Files**: `tests/test_plots.py` (new), `simulations/plotting.py`.
   - **Actions**:
     1. Use matplotlib image comparison utilities (with hash-based tolerance) to ensure extracted plotting helper preserves aesthetics.
     2. Store baseline images in `tests/baseline_images/` with README describing update procedure.
   - **Verification**: `pytest --mpl` passes locally and in CI.

---

## Phase 6 – Documentation & Knowledge Sharing (2–3 days)

| Goal | Keep documentation aligned with code and provide onboarding aids. |
| --- | --- |

1. **Update physics documentation**
   - **Files**: `docs/ideal_without_losses.md`, `docs/constant_losses.md`, `docs/variable_losses.md`, `docs/advanced_siphon_configurations.md`.
   - **Actions**:
     1. Document new entry-height parameter, smooth friction factor model, and convergence diagnostics.
     2. Add worked examples showing how reducers/expanders affect loss breakdown.
   - **Verification**: Peer review or scientific validation; include formulas derived from updated utilities.

2. **Create developer-focused architecture guide**
   - **Files**: `docs/architecture.md` (new), `README.md` (link to new guide).
   - **Actions**:
     1. Summarise module responsibilities (`common`, `plotting`, `solvers`, `multi_segment_physics`).
     2. Include sequence diagrams for simulation lifecycle and data flow from configuration to metadata output.
   - **Verification**: Ensure newcomers can rebuild a simulation end-to-end using guide instructions.

3. **Publish documentation site**
   - **Files**: `mkdocs.yml` (new), `docs/`.
   - **Actions**:
     1. Organise documentation for MkDocs with navigation covering physics primers, API docs, and development guide.
     2. Configure GitHub Pages (or similar) deployment workflow.
   - **Verification**: Local `mkdocs serve` works; CI deploy pipeline passes.

---

## Phase 7 – Release & Maintenance (ongoing)

| Goal | Solidify the improvements into regular releases and community practice. |
| --- | --- |

1. **Versioning and changelog**
   - **Files**: `CHANGELOG.md` (new), `simulations/__init__.py` (version constant).
   - **Actions**:
     1. Adopt semantic versioning; document breaking changes (e.g., new status flags, API changes).
     2. Automate changelog updates via commit hooks or release scripts.
   - **Verification**: Tag repository with new release and confirm artefacts uploaded (if distribution exists).

2. **Benchmark suite**
   - **Files**: `benchmarks/` (new), scripts referencing `simulations/*`.
   - **Actions**:
     1. Create performance benchmarks for each solver using `pytest-benchmark` or `asv`.
     2. Track runtime impact of physics enhancements (smooth friction factor, geometry generalisation).
   - **Verification**: Benchmark reports stored under `plots/benchmarks/` with README instructions.

3. **Community feedback loop**
   - **Files**: `README.md`, issue templates under `.github/ISSUE_TEMPLATE/`.
   - **Actions**:
     1. Provide template for bug reports capturing geometry, fluid props, and solver status flags.
     2. Add “how to contribute” guidelines referencing the architecture guide and testing requirements.
   - **Verification**: Templates render correctly on hosting platform; contributor onboarding steps validated by dry run.

---

## Dependencies Overview

- Phase 1 depends on baseline tooling from Phase 0 for consistent formatting/testing.
- Phase 3 builds on Phase 2 utilities (shared validation and plotting) to avoid reintroducing duplication.
- Phase 4 relies on the bisection abstraction completed in Phase 2.4.
- Testing (Phase 5) requires prior phases to expose hooks and metadata.
- Documentation (Phase 6) references finalised APIs, so schedule it after core refactors.

---

## Success Metrics

1. **Correctness**: Regression tests confirm no premature termination and accurate end heights; cavitation warnings trigger appropriately.
2. **Maintainability**: Duplicated helper functions reduced to zero occurrences (verified via `rg`), and cyclomatic complexity per module decreases (measure via `radon`).
3. **Coverage**: `pytest --cov=simulations` ≥ 90%; multi-segment modules ≥ 95%.
4. **Documentation**: MkDocs site published with complete navigation; README includes updated quickstart and troubleshooting informed by new diagnostics.
5. **Performance**: Benchmark suite shows ≤10% slowdown despite smoother friction factor; if exceeded, document trade-offs and optimisation plan.

Following this plan ensures the repository addresses critical physics bugs, consolidates shared infrastructure, and provides a maintainable foundation for future research and educational use.
