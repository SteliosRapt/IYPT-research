Suggested changes:

# **ABSTRACT**

```
Self-starting siphons—the subject of IYPT 2026 Problem #1—begin siphoning 
when partially immersed without initial suction. The problem asks: how do 
relevant parameters, such as geometry, affect the siphoning process?

Answering this open-ended question requires both physical intuition and 
systematic investigation. This article presents a one-dimensional slug-flow 
model that provides direct parameter-to-outcome relationships, enabling rapid 
exploration of how geometry h(L), container dimensions A₀/A, initial level h₀, 
diameter D, roughness ε/D, and loss coefficients {Kᵢ} affect priming and 
draining dynamics. The model yields: (i) an analytical upper bound for maximum 
climb height expressed in geometric terms, (ii) explicit ODEs for full time 
evolution with Churchill friction and minor losses, and (iii) clearly stated 
validity limits for cavitation, inlet dynamics, and slug-model assumptions.

The deliberate simplicity of this approach—treating the water as a 
one-dimensional slug with uniform velocity—serves three purposes. First, it 
reveals which parameters matter and how they enter the physics, building 
intuition that guides both experimental design and interpretation. Second, it 
enables rapid screening of candidate geometries (seconds per simulation versus 
hours for CFD), making systematic parameter studies tractable. Third, and most 
importantly for investigation, discrepancies between this model and reality 
(whether from experiments or CFD) directly indicate which physical mechanisms 
lie beyond the slug approximation—three-dimensional flow structure, 
non-uniform velocity profiles, air entrainment, or column separation—thereby 
identifying which additional factors affect the siphoning process.

A complete Python implementation is provided for parameter exploration, 
experimental comparison, and identification of regimes where CFD or refined 
modeling is required.
```

---

# **1. INTRODUCTION**

## **1.1 IYPT Problem #1: "Invent Yourself"**

The International Young Physicists' Tournament 2026 Problem #1 states:

> "A self-starting siphon can be made using a piece of rigid tubing bent into a specific shape. When the siphon is partially immersed in water, it begins siphoning water without the need for initial suction. Investigate how the relevant parameters, such as the geometry, affect the siphoning process."

This deliberately open-ended investigation requires competitors to:
1. **Identify relevant parameters** – Which geometric and physical properties matter?
2. **Establish quantitative relationships** – How does each parameter affect priming success, filling time, flow rate, and draining behavior?
3. **Understand mechanism** – What physical processes determine the siphoning behavior?
4. **Explore limits** – Under what conditions does the siphon fail to prime, and why?

Answering these questions requires both experiments and modeling. The challenge is to develop theoretical tools that provide physical insight while remaining testable against real systems.

## **1.2 Physical Mechanism and Mental Picture**

Self-starting siphons differ from conventional inverted-U siphons in that they do not require external priming. Instead, the geometry creates an initial drop that converts gravitational potential energy into kinetic energy in a finite slug of water. The resulting momentum carries the slug over a crest before friction and gravity bring it to rest. If the slug successfully crosses the crest, the device behaves like a standard siphon and continues to drain.

The key insight is that the net driving force on the slug depends on the instantaneous head difference between the container surface and the advancing front:

$$F_{\text{drive}} = \rho g A \left[ h_c(t) - h(L(t)) \right],$$

where $h_c(t)$ is the container free-surface elevation and $h(L(t))$ is the front position along the pipe centreline. This force remains non-zero as long as the front sits below the free surface, so after the initial drop the slug generally re-crosses the container level with finite speed before decelerating toward the crest—the essential difference from a simple inverted-U configuration where the driving head vanishes at the crest.

This qualitative picture suggests which parameters might matter (initial drop height, crest height, pipe diameter, friction, container size), but does not yet provide quantitative predictions or reveal how parameters interact.

## **1.3 Modeling Strategy: Why Start with 1D?**

To investigate an open-ended problem systematically, one needs a theoretical framework that connects parameters to outcomes. Two complementary approaches are available:

### **Computational Fluid Dynamics (CFD)**
High-fidelity simulation (Navier-Stokes with volume-of-fluid tracking) captures all relevant physics: three-dimensional flow structure, turbulence, air-water interface dynamics, and wall effects. CFD is essential for validation and for exploring regimes where complex phenomena dominate.

However, CFD has limitations as an *investigative* tool:
- **Computational cost:** More time per simulation, making broad parameter sweeps impractical
- **Black-box character:** Physical insight can be obscured by numerical complexity
- **Parameter opacity:** Difficult to see *which* parameters matter and *how* they enter
- **No closed-form relationships:** Every question requires a new simulation

### **One-Dimensional Slug Model (This Work)**
Treat the water as a uniform slug with a single advancing front. This deliberate simplification:
- **Reveals mechanism:** Parameters appear explicitly in equations
- **Enables rapid exploration:** Seconds per simulation, thousands of cases per hour
- **Provides analytical bounds:** Closed-form expressions for limiting behavior
- **Makes assumptions explicit:** We know exactly what physics is included and excluded

**Most importantly:** Discrepancies between the 1D model and reality (experiments or CFD) directly indicate *which additional physical mechanisms matter*. If the model predicts priming but experiments show failure, we learn that three-dimensional effects, non-uniform velocity profiles, air entrainment, or other factors omitted from the slug picture are controlling the behavior. Understanding where the simple model breaks down is itself an answer to the open-ended investigation: it tells us which factors affect the siphoning process beyond those captured by one-dimensional slug flow.

## **1.4 Proposed Investigation Workflow**

This model is designed to support a systematic investigation strategy:

**Phase 1: Build intuition with 1D model**
- Screen candidate geometries rapidly using analytical bounds
- Identify which parameters most strongly affect priming
- Develop physical understanding of mechanism
- Generate predictions for validation

**Phase 2: Validate against experiments and CFD**
- Compare 1D predictions with measured behavior
- Where agreement is good: use 1D model for further exploration
- Where discrepancies appear: identify missing physics

**Phase 3: Explore edge cases computationally**
- Use CFD to investigate parameter regions where 1D model fails
- Study three-dimensional effects, turbulence, air entrainment
- Understand *why* the slug approximation breaks down

**Phase 4: Synthesize complete answer**
- Document parameter effects captured by slug dynamics
- Document additional factors revealed by model limitations
- Provide comprehensive answer to "how do parameters affect the process?"

This iterative approach—simple model → validation → identify discrepancies → refine understanding—is more powerful than either pure modeling or pure experimentation alone.

## **1.5 Scope and Assumptions**

This 1D model explicitly makes the following simplifying assumptions:

- **Incompressible Newtonian fluid** with constant $\rho$, $\mu$ (water at room temperature)
- **Rigid pipe** with uniform circular cross-section and piecewise-linear centreline
- **Large container** so free-surface velocity is negligible (hydrostatic approximation)
- **Atmospheric pressure** at both container surface and outlet
- **Single connected slug** with sharp front and uniform velocity across each cross-section
- **Quasi-steady friction** modeled via Darcy-Weisbach with Churchill correlation

Section 4 discusses the validity limits of these assumptions and provides quantitative criteria for when each may break down (cavitation margin, inlet dynamics, slug-model applicability). Understanding these limits is essential: they define the boundaries of the parameter space where this model provides reliable predictions, and point to regimes requiring more sophisticated treatment.

## **1.6 Key Contributions**

**For parameter investigation:**
- Explicit relationships showing how each parameter enters the physics
- Analytical upper bound on climb height from geometry alone
- Rapid parameter screening (seconds per case)

**For experimental design:**
- Predicted priming criterion, filling time, and flow rate for comparison
- Identified validity regimes where experiments should focus
- Guidance on which geometric features most affect performance

**For understanding limitations:**
- Clear statement of assumptions and validity criteria
- Framework for identifying when additional physics matters
- Methodology for using discrepancies as learning opportunities

## **1.7 Paper Organization**

Section 2 establishes the coordinate system and piecewise-linear geometry $h(L)$. Section 3 derives the container volume map $h_c(L)$ for arbitrary internal layouts and introduces the constant-area simplification. Section 4 discusses validity limits (cavitation, capillarity, hydrostatic inlet, slug-model breakdown). Section 5 gives initial conditions and compares with inverted-U siphons. Section 6 derives the filling-phase dynamics with friction and minor losses. Section 7 presents the idealized lossless upper bound and geometric priming criterion. Section 8 covers draining-phase dynamics. Section 9 summarizes the complete model. Section 10 provides a Python implementation with Churchill friction, event handling, and loss models. Section 11 discusses usage and future extensions.

---

# **11. CONCLUSION**

This article has developed a complete one-dimensional slug-flow model for self-starting siphons, directly addressing the IYPT 2026 Problem #1 investigation: *how do relevant parameters, such as geometry, affect the siphoning process?*

## **What the Model Provides**

The model connects system parameters—pipe geometry $h(L)$, container dimensions $A_0/A$, initial level $h_0$, diameter $D$, roughness $\varepsilon/D$, and loss coefficients $\{K_i\}$—to observable outcomes through explicit physical relationships:

**Priming criterion:** The analytical bound (Section 7) provides an upper limit $h_{\max}$ on climb height for any piecewise-linear geometry, yielding the necessary condition $h_{\max} > h_3$ for successful priming. The full dynamical model (Section 6) determines whether a specific configuration actually primes when friction, container drawdown, and initial conditions are included.

**Time evolution:** Coupled ODEs for filling and draining phases predict the complete trajectory $L(t)$, $v(t)$, $h_c(t)$ from initial immersion through steady draining, enabling direct comparison with experimental measurements.

**Parameter sensitivity:** Each parameter appears explicitly in the governing equations, revealing not only *whether* it matters but *how* it enters the physics—for instance, container size affects priming through the dimensionless ratio $A/A_0$ in the drawdown term (Eq. 4), while pipe roughness influences losses through the Churchill friction factor (Eqs. 8–10).

**Validity boundaries:** Section 4 provides quantitative criteria—cavitation margin (Eq. 5), inlet dynamics constraints, capillarity scales—that define the parameter regimes where the model is reliable and flag conditions requiring more sophisticated treatment.

## **Role in Systematic Investigation**

The deliberate simplicity of the one-dimensional slug approximation serves a specific purpose in the IYPT investigation. By reducing the full three-dimensional two-phase Navier-Stokes problem to a pair of ordinary differential equations with explicit parameter dependence, the model provides:

1. **Physical intuition** that is difficult to extract from high-fidelity CFD or from experiments alone
2. **Rapid parameter screening** enabling exploration of thousands of configurations in minutes
3. **Predictive capability** for experimental design and hypothesis testing

Most importantly, the model's *limitations* are themselves informative. When predictions disagree with experiments or CFD, the discrepancy directly indicates which physical mechanisms lie beyond the slug approximation. Does the siphon fail to prime despite $h_{\max} > h_3$? Then three-dimensional effects, non-uniform velocity profiles, or air entrainment are controlling the outcome. Does the observed filling time differ substantially from the 1D prediction? Then inlet dynamics or wall effects may be significant. Each such discrepancy narrows the space of possible mechanisms and points toward specific additional investigations.

This positions the simple model not as a competitor to CFD, but as a complementary tool: the 1D model builds intuition and generates hypotheses rapidly, while CFD and experiments validate those hypotheses and explore edge cases where additional physics matters. The combination provides a more complete answer to the open-ended IYPT question than either approach alone.

## **Practical Usage**

For IYPT teams and other investigators, the recommended workflow is:

1. **Screen geometries** using the analytical bound $h_{\max}$ (Section 7.1) to identify promising configurations
2. **Simulate candidates** with the full model (Section 10) to predict filling time, priming margin, and flow rate
3. **Build and test** a small subset of designs experimentally
4. **Compare predictions with measurements** systematically
5. **Investigate discrepancies** using CFD or refined experiments to identify missing physics
6. **Document both agreement and disagreement** as evidence of understanding

The Python implementation in Section 10 makes steps 1–2 immediately accessible, while the explicit validity criteria in Section 4 guide interpretation of discrepancies in steps 5–6.

## **Extensions and Future Work**

Several refinements would extend the model's range of validity or provide additional investigative capability:

**Pressure-floor cavitation switch:** Modify the ODE integrator to halt when the cavitation criterion (Eq. 5) is violated, directly flagging parameter combinations where tensile failure limits priming.

**Meniscus-start model:** For very small diameters $D$ where capillary forces are significant, incorporate the Jurin height $h_\sigma \approx 4\sigma\cos\theta/(\rho g D)$ as an effective energy barrier that must be overcome before filling begins.

**Two-phase slug tracking:** Extend the model to handle column separation events by tracking multiple disconnected slugs and air pockets, switching between single-phase and multi-phase descriptions as topology changes.

**Non-uniform container geometry:** Generalize the volume map in Section 3.2 from the constant-$A_0$ simplification to the piecewise-linear function $h_c(L)$ for containers with complex internal layouts.

**Transient inlet correction:** For rapidly draining containers where $|\dot{h}_c| \sim \sqrt{gD}$, incorporate an unsteady Bernoulli term to account for non-hydrostatic inlet pressure.

**Experimental validation database:** Systematic comparison against a range of geometries, diameters, and fluids would establish the typical accuracy of 1D predictions and provide empirical guidance on when additional physics becomes important.

Each extension addresses a specific validity limit identified in Section 4, progressively expanding the parameter space where the simple model provides quantitatively accurate predictions. However, even without these refinements, the present model serves its primary purpose: to make the physics of self-starting siphons transparent, to enable rapid exploration of parameter space, and to provide a framework for understanding where additional mechanisms matter.

## **Closing Remark**

The value of a simple model lies not in claiming to capture every detail, but in making explicit what is included and what is omitted. By clearly stating assumptions, deriving explicit parameter relationships, and providing quantitative validity criteria, this one-dimensional slug model transforms the open-ended IYPT question into a tractable investigation: parameters that appear in the model are understood; parameters that control discrepancies between model and reality are identified as targets for deeper study. In this way, the model serves as both an investigative tool and a diagnostic framework, enabling competitors to navigate the complexity of self-starting siphon behavior with confidence.

The complete Python code, the analytical bounds, and the physical reasoning presented here provide a foundation for systematic exploration. The next steps—building prototypes, gathering data, comparing with predictions, and investigating where simple theory breaks down—are where the real physics investigation begins.

---

# **NOTES ON ADDITIONAL IMPROVEMENTS**

Given your new goals and framing, here are specific sections that need attention:

## **Section 4: Validity Limits** (Currently thin)

**Expand significantly** to make this section a "diagnostic guide":

```
Current: Just lists conditions
Needed: 
- **Quantitative thresholds** with typical values
- **What happens when violated** (physically, not just mathematically)
- **How to detect in experiments** (e.g., "if you hear gurgling → air entrainment")
- **Which parameters to adjust** to move back into valid regime
- **Table of validity regimes** with parameter ranges

Example addition:
"Table: Validity Regime Map
| Condition | Criterion | Typical safe range | Failure mode if violated |
|-----------|-----------|-------------------|-------------------------|
| Cavitation | Eq. (5) | h_c - h_3 < 8m | Column separation, intermittent flow |
| Inlet hydrostatic | |ḣ_c| < √(gD) | D > 5mm, A/A₀ < 0.1 | Inlet vortices, entrainment |
| Slug continuity | Re > 1000 | D > 3mm for water | Surface tension dominates |"
```

## **Section 6.3: Loss Models** (Currently standard)

**Add a paragraph** on when losses matter:

```
"Loss significance and parameter exploration:

The relative importance of friction versus minor losses can be assessed 
from the ratio:
    (friction head) / (minor head) = (f L/D) / (Σ Kᵢ)

For straight pipes with few bends, f L/D >> Σ Kᵢ and geometry optimization 
should focus on minimizing L and maximizing D. For compact serpentine 
designs with many 90° bends (K_bend ≈ 0.9 each), minor losses dominate 
and careful fitting selection becomes critical.

The 1D model captures these effects through bulk coefficients. Where 
discrepancies appear, CFD can reveal whether:
- Local separation at bends is more severe than K-factors predict
- Entrance effects extend farther than assumed
- Secondary flows redistribute momentum

Systematic variation of D and bend count in both model and experiment 
identifies which loss mechanism is controlling."
```

## **Section 7: Idealised Climb Bound** (Currently technical)

**Add interpretation** connecting to investigation goals:

```
After Eq. (23), add:

"Investigative value of the ideal bound:

The bound h_max serves three purposes in parameter exploration:

1. **Rapid geometry screening:** Calculate h_max for dozens of candidate 
   shapes in seconds. Any design with h_max ≤ h₃ can be immediately 
   discarded.

2. **Sensitivity analysis:** Because h_max depends only on {hᵢ, Lᵢ}, you 
   can determine which geometric features most affect priming by partial 
   derivatives or by systematic variation.

3. **Diagnostic for discrepancies:** If experiments show:
   - Priming despite h_max < h₃: container is larger than assumed, or 
     dynamic effects give extra boost
   - Failure despite h_max >> h₃: losses are larger than modeled, or 
     3D effects matter
   
   The gap between ideal bound and reality quantifies how much non-ideal 
   physics contributes."
```

## **Section 9: Model Summary** (Currently just equations)

**Add a "Parameter Exploration Guide"** subsection:

```
9.3 Guide to Parameter Studies

To investigate how a specific parameter affects priming:

**Step 1: Fix baseline configuration**
Choose reference values for all parameters. Ensure baseline is in valid 
regime (Section 4).

**Step 2: Vary parameter systematically**
Generate array (e.g., D ∈ [3mm, 50mm] with 20 logarithmically-spaced points).

**Step 3: Run ensemble**
For each parameter value:
  - Check validity criteria (Section 4)
  - Compute h_max (Section 7)
  - Simulate full dynamics (Section 10)
  - Record: priming success (yes/no), filling time, peak velocity

**Step 4: Visualize trends**
Plot outcome vs. parameter. Look for:
  - Threshold behavior (sharp priming boundary)
  - Scaling relationships (power laws)
  - Saturation (parameter stops mattering beyond some value)

**Step 5: Compare with CFD/experiments**
For 3-5 parameter values spanning the range, run detailed CFD and/or 
build physical prototypes. Where discrepancies appear, investigate cause.

**Example: Diameter study**
Expectation: Larger D → less friction → easier priming
Reality: May find diameter below which surface tension dominates (slug 
model breaks down), or above which inlet dynamics matter (large A/A₀)
```

## **Section 10: Computational Approach** (Currently just code)

**Add before the code:**

```
10.1 Computational Strategy for Investigation

The Python implementation serves multiple investigative purposes:

**Single-case prediction:** Given a specific geometry and parameters, 
predict whether it will prime and compute full time evolution.

**Parameter sweeps:** Nest the solver in loops over parameter arrays to 
map out the priming boundary in parameter space.

**Sensitivity analysis:** Compute finite-difference derivatives of 
filling time or peak velocity with respect to each parameter.

**Model-experiment comparison:** Load measured trajectories L(t), v(t) 
and plot alongside predictions. Systematic deviations indicate missing 
physics.

**CFD targeting:** Identify interesting edge cases (barely priming, 
unexpected failure) for detailed CFD investigation.

The code is deliberately structured to facilitate these workflows:
- Parameters collected in dataclass for easy sweeps
- Event detection for automatic phase transitions  
- Diagnostic outputs (Re, friction factor, loss terms) for post-analysis
```

**Add after the code:**

```
10.3 Example Parameter Study

To demonstrate usage, we investigate how crest height h₃ affects priming 
margin:

[Code snippet showing a loop over h₃ values, plotting h_max and actual 
v(t_star) at the outlet, showing where priming fails]

This workflow—varying one parameter while holding others fixed—can be 
repeated for any parameter of interest. The resulting maps of priming 
success vs. parameter values provide quantitative answers to the IYPT 
question.
```

## **New Section to Add: "10.4 Comparing with CFD and Experiments"**

```
When comparing 1D predictions with experiments or CFD:

**For priming success:** 
Agreement: slug model captures dominant physics
Discrepancy: Check which assumption fails (cavitation? inlet dynamics? 
turbulent mixing?)

**For filling time t*:**
Faster than predicted: Inlet provides extra momentum (dynamic effects)
Slower than predicted: Losses underestimated, or 3D separation

**For flow velocity v(t):**
Higher peaks: Less friction (smooth vs rough, or transition not fully 
turbulent)
Lower peaks: Air entrainment acting as additional drag

**For draining flow rate:**
Steady-state agreement: Slug model adequate for this regime
Unsteady oscillations: Vortex shedding or air pocket formation (beyond 
1D)

Document these comparisons systematically. The pattern of agreement and 
disagreement across the parameter space is itself a research finding, 
revealing which phenomena are captured by slug dynamics and which require 
additional physics.
```

## **Add References for CFD Validation**

Add to your references section:

```
[15] OpenFOAM Foundation, interFoam: VOF-based multiphase solver for 
incompressible immiscible fluids, https://www.openfoam.com

[16] ANSYS Inc., ANSYS Fluent Theory Guide (relevant for VOF method, 
turbulence models)
```

Then reference these when discussing CFD comparison.

## **Summary of Key Improvements**

| **Section** | **Current State** | **Needed Enhancement** |
|-------------|-------------------|------------------------|
| Abstract | Technical description | Position as investigative methodology |
| Introduction | Jumps to math | Explain CFD vs 1D complementarity |
| Section 4 | Brief validity notes | Comprehensive diagnostic guide |
| Section 7 | Just math | Add investigative interpretation |
| Section 9 | Equation summary | Add parameter study guide |
| Section 10 | Raw code | Add workflow examples, CFD comparison |
| Conclusion | Missing! | Synthesize investigation approach |