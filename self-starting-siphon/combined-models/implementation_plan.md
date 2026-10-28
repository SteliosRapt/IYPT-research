# Implementation Plan for `siphon_models_combined.tex`

This document outlines the planned changes to `siphon_models_combined.tex` so that it becomes a formal reference paper on self-starting siphons and the central theoretical/computational backbone for the IYPT 2026 Problem #1 investigation.

In addition to the items below, we will:
- Update all bibliography entries so that each cited work is referenced in the main text at appropriate locations (and remove or justify any uncited references).
- Ensure citation commands (`\cite{}`) and labels are consistent with the new structure and content.

---

## 1. Global goals and cleanup

- Reframe the paper explicitly as a theoretical and computational framework for self-starting siphons, suitable both as an IYPT reference and as a formal fluid-mechanics/physics-education paper.
- Maintain a formal, research-paper tone throughout (avoid instructional “how-to” phrasing; prefer “we consider”, “we propose”, “we show”).
- Ensure notation consistency across the document:
  - `h(L)`, `h_c(t)`, node heights `h_0, …, h_4`, pipe area `A`, container area `A_0`, length scales `L_i`, and ratios like `A_0/A` are all clearly defined and used consistently.
  - Dimensionless numbers (Reynolds, Bond/Weber, etc.) appear with consistent symbols and definitions.
- Fix encoding artefacts (e.g. `�??`) and replace them with proper LaTeX quoting and symbols.
- Make cross-references and labels consistent with the updated section and subsection structure.
- Review the bibliography:
  - Add new CFD references [15]–[16] and cite them where CFD comparison is discussed.
  - Check that each reference is cited in at least one appropriate location in the text.

## 2. Abstract

- Replace the current abstract with a focused, formal abstract that:
  - Mentions IYPT 2026 Problem #1 explicitly as the motivating context.
  - States the main scientific question: how geometry and other parameters affect priming, climb height, and draining dynamics in self-starting siphons.
  - Enumerates the key contributions:
    - One-dimensional slug-flow model for priming and draining.
    - Analytic upper bound for maximum climb height expressed purely in geometric terms via `h(L)`.
    - Explicit ODEs with Churchill friction and minor-loss coefficients.
    - Clear validity criteria (cavitation, capillarity, inlet dynamics, flow regime).
    - A runnable Python implementation enabling rapid parameter studies.
  - Emphasises the methodological value of the model as a bridge between simple analytical reasoning, experiments, and CFD, without sounding like a user manual.
  - Notes that experimental and CFD comparisons are outlined as future work rather than reported results.

## 3. Section 1 – Introduction and mental model

### 3.1 New subsection: IYPT Problem \#1 and objectives

- Add a subsection introducing the IYPT 2026 Problem #1 statement (quoted formally).
- Clarify the investigative objectives in formal language:
  - Identification of relevant geometric and physical parameters.
  - Establishment of quantitative relationships between parameters and outcomes (priming success, filling time, crest height, steady draining rate, etc.).
  - Understanding of the underlying physical mechanisms and their limitations.
- Position this paper as providing:
  - The theoretical formulation.
  - The analytic tools (e.g. climb-height bound).
  - The computational methods needed to support an IYPT-level investigation.

### 3.2 Revised subsection: Physical mechanism and qualitative picture

- Refactor the existing “Introduction and mental model” content into a subsection that:
  - Describes self-starting siphons in contrast to conventional inverted-U siphons.
  - Emphasises the role of the deliberate drop and the resulting momentum-bearing slug.
  - Highlights the central driving-force relation
    \[
      F_{\text{drive}} = \rho g A\,[h_c(t) - h(L(t))].
    \]
  - Explains qualitatively why the driving head remains non-zero as the slug recrosses the container level, and how this differs from an ordinary siphon.
- Keep tone descriptive but formal, avoiding procedural language.

### 3.3 New subsection: Modelling strategy and scope

- Introduce the one-dimensional slug-flow model as the central theoretical framework.
- Discuss CFD as a complementary, higher-fidelity tool:
  - 1D model: rapid parameter-to-outcome mapping, analytical structure, design and interpretation.
  - CFD: full three-dimensional, free-surface, and multiphase dynamics for regimes where 1D assumptions fail.
- Clearly state the scope:
  - What the paper covers (geometry, volume map, validity criteria, dynamics, analytic bound, ODE solver).
  - What is only outlined as methodology (experiments, CFD validation).
- Add a short “roadmap” paragraph summarising the organisation of the rest of the paper with references to the main sections.

## 4. Sections 2–3 – Geometry and container mapping

### 4.1 Section 2: Geometry and coordinate systems

- Keep the existing mathematical description of the geometry and `h(L)`.
- Add a short paragraph at the end explaining how this geometry:
  - Enters the analytic climb-height bound in the idealised case.
  - Underpins the validity analysis (e.g. where the crest and outlet sit relative to the container).
- Ensure notation for node coordinates, segment lengths, and `h(L)` is fully consistent with later sections and with references to figure(s).

### 4.2 Section 3: Container, volume map, and effective area

- Retain the detailed derivation of the container level and volume map.
- Add a bridging paragraph that:
  - Explains how `h_c(t)` and the effective area couple into the filling and draining dynamics.
  - Identifies key ratios such as `A_0/A` that will serve as control parameters in later parameter studies.

## 5. Section 4 – Validity limits and missing physics

### 5.1 Reorganise into clear subsections

- Introduce subsections along these lines:
  - Governing assumptions.
  - Cavitation and pressure limits.
  - Surface tension and capillarity.
  - Flow regime and friction modelling.
  - Inlet dynamics and non-hydrostatic effects.
  - Summary of validity criteria.

### 5.2 Governing assumptions

- Collect the modelling assumptions in one place:
  - Incompressible Newtonian fluid, single-phase water column.
  - Pipe confined to a vertical plane; fixed circular cross-section.
  - Large, quasi-hydrostatic container with negligible free-surface velocity.
  - Atmospheric pressure at both container free surface and outlet; neglected external air dynamics.
- Link these assumptions to dimensionless numbers (Re, Bond/Weber, cavitation head margin).

### 5.3 Cavitation and pressure limits

- Present the cavitation head margin formula cleanly and define all symbols.
- State conditions for safe operation (pressure everywhere above vapour pressure by a specified margin).
- Explain qualitatively how small cavitation margins may lead to column separation or vapour pockets and thus a breakdown of the slug model.

### 5.4 Surface tension and capillarity

- Introduce the relevant dimensionless numbers (e.g. Bond or Weber number) in terms of diameter, surface tension, gravity, and velocity.
- Specify when capillary effects and meniscus dynamics can be neglected (sufficiently large `D`).
- Discuss expected failure modes at small `D` (meniscus pinning, slug breakup) and note that more detailed models would be needed there.

### 5.5 Flow regime and friction modelling

- Define the Reynolds number for the pipe flow and the turbulent regime in which the Churchill correlation is appropriate.
- Discuss how laminar or transitional regimes would alter the friction model and the reliability of predictions.

### 5.6 Inlet dynamics and non-hydrostatic effects

- Clarify the quasi-hydrostatic approximation for the container and the treatment of inlet losses via loss coefficients.
- Identify conditions where inlet jet dynamics, air entrainment, or free-surface deformation may invalidate these approximations.

### 5.7 Summary of validity criteria

- Summarise the validity checks as a concise, formal list:
  - Thresholds for cavitation margin, capillarity influence, and Reynolds number.
  - Qualitative checks on inlet behaviour and container dynamics.
- Make it explicit that these criteria should be evaluated for any proposed configuration before interpreting slug-model predictions quantitatively.

## 6. Sections 5–6 – Initial conditions and filling dynamics

### 6.1 Section 5: Initial conditions and comparison with an inverted-U siphon

- Preserve current derivations and explanation of initial conditions.
- Sharpen the comparison with an inverted-U siphon:
  - Emphasise that in the inverted-U case the driving head vanishes at the crest, unlike in the self-starting configuration.
  - Explicitly link this difference to the shape of `h(L)` and the drop configuration.
- Add a sentence pointing forward to the analytic climb bound as a more formal way to compare geometries.

### 6.2 Section 6: Dynamics in the filling phase

- Keep the detailed momentum balance and loss terms.
- Add a short interpretive paragraph at the end:
  - Identifying the roles of the driving head, distributed friction, and local losses.
  - Highlighting how key parameters (diameter, roughness, loss coefficients, `A_0/A`, geometry) enter the evolution of `L(t)` and `v(t)`.

## 7. Section 7 – Idealised climb bound and analytical stall height

### 7.1 Clarify purpose and context

- At the start of the section, clearly state that:
  - The analysis considers an idealised limit with fixed `h_c` and no losses.
  - The goal is to obtain an upper bound for the maximum climb height (or crest reachable) based solely on geometry.

### 7.2 Interpretation subsection

- Introduce a new subsection (e.g. “Interpretation and implications”) after the derivation that:
  - Explains how the bound changes with key geometric parameters (drop height, crest height, slopes, segment lengths).
  - Clarifies the relationship between the bound and actual priming behaviour in the lossy model.
  - Discusses how designers can use this bound to:
    - Rule out geometries that cannot prime even ideally.
    - Identify geometries which are close to the bound and thus sensitive to friction and inlet effects.

## 8. Section 8 – Dynamics in the draining phase

- Retain the existing derivation for the draining-phase dynamics.
- Add a brief paragraph interpreting:
  - The draining phase as essentially standard siphon behaviour once the pipe is full.
  - Its value for validating friction models (e.g. steady flow rates, time-to-drain) against experiments.

## 9. Section 9 – Model summary and guide to parameter studies

### 9.1 Model components and parameters

- Restructure the current summary so that:
  - Equations are grouped into geometry, container dynamics, filling-phase dynamics, draining-phase dynamics, and validity criteria.
  - Input parameters are grouped into:
    - Geometric (node heights and positions, segment lengths).
    - Fluid properties (density, viscosity, surface tension if used).
    - Loss/roughness parameters (roughness ratio, minor-loss coefficients).
  - It becomes straightforward to see which parameters are varied in studies and which are fixed material constants.

### 9.2 Guide to parameter studies

- Translate the recommended workflow from `suggested_changes.md` into formal prose:
  - Choose a baseline configuration in a regime where the model is valid.
  - Select a parameter (or small set of parameters) to vary systematically (e.g. `D`, crest height, `A_0/A`).
  - For each parameter value:
    - Check validity criteria (Section 4).
    - Compute the analytic climb-height bound (Section 7).
    - Integrate the full dynamics (Sections 6 and 8).
    - Record outcomes: priming success, filling time, peak velocity, draining behaviour.
  - Visualise and interpret results:
    - Identify thresholds (priming/non-priming boundaries).
    - Look for scaling laws (e.g. power-law dependence).
    - Detect saturation regimes where further parameter changes have little effect.
- Emphasise that these parameter studies form a quantitative answer to the IYPT question about how geometry and other parameters affect siphon behaviour.

## 10. Section 10 – Computational approach

### 10.1 Computational strategy subsection

- Add a subsection describing the computational strategy in formal terms:
  - Single-case predictions: given a geometry and parameter set, determine priming outcome and full time evolution.
  - Parameter sweeps: nest the solver in loops over parameter arrays to map priming boundaries.
  - Sensitivity analysis: approximate derivatives of quantities of interest with respect to parameters by finite differences.
  - Preparation for model–experiment and model–CFD comparisons: define what data will be compared (times, velocities, flow rates) and how.
- Connect these tasks explicitly to the ODE system and event handling described earlier.

### 10.2 Python implementation subsection

- Keep the current Python `lstlisting`, but refactor for clarity and alignment with the narrative:
  - Add minimal docstrings or inline comments at the function level explaining:
    - `churchill_f`: returns the friction factor using Churchill’s correlation.
    - `h_of_L`: evaluates `h(L)` using the piecewise linear geometry.
    - `filling_rhs`, `drain_rhs`: right-hand sides of the filling and draining ODE systems.
    - Event functions: detect arrival at the outlet and end of draining.
  - Factor out the example into a `run_example()` or similar function so that:
    - The solver functions can be reused in parameter sweeps.
  - (Optionally) Add simple diagnostic helpers:
    - To compute Reynolds number, friction factor, and cavitation margin at given states.
  - Clarify with comments that the numerical parameter values are placeholders to be replaced by measured or designed configurations.

### 10.3 Example parameter study subsection

- Add a new subsection describing (and optionally sketching in code) how to:
  - Loop over a set of values for a chosen parameter (e.g. crest height or pipe diameter).
  - Call the solver for each value, capturing:
    - Priming success/failure.
    - Time to reach the outlet (`t_*`).
    - Key diagnostics (peak velocity, draining duration).
  - Post-process results (e.g. plotting priming success vs parameter, or `t_*` vs parameter).
- Keep the presentation methodological; note that no actual numerical results are reported yet.

### 10.4 Comparison with CFD and experiments subsection

- Add a subsection outlining how to compare 1D model predictions with:
  - CFD simulations (e.g. using OpenFOAM `interFoam` or ANSYS Fluent, referencing new citations).
  - Laboratory experiments using physical prototypes.
- Structure the comparison along observables:
  - Priming success/failure.
  - Filling time.
  - Velocity time histories.
  - Draining flow rate and any unsteady features.
- For each observable, describe how:
  - Agreement supports the adequacy of the slug model.
  - Discrepancies point to missing physics (e.g. cavitation, air entrainment, three-dimensional effects).
- Make clear that this section sets out planned methodology; actual comparison results are part of future work.

## 11. Section 11 – Conclusions, usage, and future work

### 11.1 Recast the section as conclusions

- Optionally rename the section to “Conclusions, usage, and future work”.
- Begin with a concise summary of the main contributions:
  - Geometric formulation and volume mapping.
  - Validity limits and diagnostic criteria.
  - Idealised analytic climb-height bound.
  - Two-phase ODE model and computational implementation.

### 11.2 Investigation workflow (“playbook”) subsection

- Add a subsection that formally summarises the recommended investigation workflow:
  1. Geometry specification and constraint checking.
  2. Validity assessment using the criteria from Section 4.
  3. Baseline configuration analysis (analytic bound + numerical simulation).
  4. Parameter studies following Section 9 and Section 10.
  5. Experimental implementation for selected configurations.
  6. Model–experiment–CFD comparison as outlined in Section 10.4.
- Keep the language formal, but ensure the sequence is clear enough to guide future work (and potential IYPT presentation preparation).

### 11.3 Future work

- Refine and expand the existing “future work” paragraph to include:
  - Full experimental campaigns guided by the workflow.
  - Detailed CFD studies of regimes where the model predicts marginal priming or borderline validity.
  - Possible model extensions:
    - Explicit cavitation switches in the ODE system.
    - Meniscus-scale models for very small diameters.
    - Simple two-phase models capturing air entrainment and column separation.

## 12. References and citations

- Add CFD-related references (e.g. OpenFOAM `interFoam`, ANSYS Fluent Theory Guide) with consistent formatting as entries [15] and [16].
- Insert `\cite{}` commands for these references in:
  - The modelling strategy subsection (Section 1) where CFD is discussed.
  - The computational comparison subsection (Section 10.4).
- Review all existing references:
  - Ensure each is cited at least once in an appropriate context (introduction, related work, validity discussion, etc.).
  - Adjust or add citations where needed so the bibliography and text are fully aligned.
