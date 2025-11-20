# Review TODO and order
- Geometry and notation: check consistency of points A–E, piecewise elevation \(h(L)\), and the container reference level.
- Volume–height relation: verify that the text correctly accounts for pipe volume, meandering legs inside the tank, and the invertible map \(h_c(L)\).
- Modelling limits: confirm that cavitation, capillarity/surface tension, rapidly moving free surface (non-hydrostatic inlet), and slug-model breakdown conditions are stated with quantitative bounds.
- Initial conditions and start-up narrative: ensure the two practical priming setups collapse to \(L(0)=L_1,~\dot L(0)=0,~h_c(0)=h_0\) and are contrasted with a simple inverted-U siphon.
- Dynamics: re-derive/check filling and draining ODEs, friction/minor-loss terms, and the lossless upper-bound model; provide an analytic stall-height condition for the constant-\(h_c\) case.
- Summary/clarity: provide an end-of-paper model summary (variables, key equations) and remove redundancies.
- Computation: outline a numerical strategy (events for \(L=L_{\max}\)), and provide runnable code.
- Citations/value: check that references support cavitation and friction claims and that each section adds distinct value.

# Detailed proposal for the paper

## Structure and exposition
- Begin with a short contribution list: clarified initial conditions; explicit validity limits (cavitation, capillarity, non-hydrostatic inlet); full geometry–volume map; analytic upper bound for climb height; and a computational recipe.
- Place geometry and notation up front, followed by the general \(h_c(L)\) relation (exact piecewise formulation for variable pipe footprints inside the tank, then the constant-area simplification used in the ODEs).
- Add a dedicated “Validity limits” section: hydrostatic-assumption bounds, cavitation criterion, capillary/meniscus threshold, and constraints from rapid container drawdown.
- Introduce a dedicated “Initial conditions and comparison with an inverted-U siphon” subsection that explicitly states the two experimental setups that collapse to the same \(L(0),\dot L(0)\) and highlights the nonzero drive while \(h(L)<h_c\).
- Keep the filling and draining dynamics, but highlight the driving head term \(\rho g A(h_c-h(L))\) early and trace how losses enter.
- Provide an analytic expression for the stall height \(h_{\max}\) in the constant-\(h_c\), lossless case using the piecewise-linear \(h(L)=c_i+s_i L\) form, giving a closed-form root condition (log + linear terms) for \(L_{\text{stall}}\).
- Add a compact end-of-paper model digest: variables, parameters, and equation references for both phases.

## Modelling limits and missing physics
- Cavitation: include a head-margin condition \(p_{\min}\ge p_{\mathrm{vap}}\) (or tensile limit) at the crest; link to the height-limit papers (Boatwright; Vera; Tyree). Note that the loss model already subtracts head, so the safety margin is expressed in metres of water column.
- Capillarity/surface tension: capture the meniscus threshold \(h_{\sigma}\approx 4\sigma \cos\theta/(\rho g D)\) for small \(D\); mention the possible slip resistance until \(v>0\).
- Rapid drawdown / non-hydrostatic inlet: specify that the hydrostatic inlet pressure is valid if \(|\dot h_c|\ll \sqrt{gD}\) and \(|\ddot h_c|\ll g\); otherwise unsteady Bernoulli adds an extra head term of size \(\mathcal{O}\bigl((A/A_0)\dot h_c \dot L/g\bigr)\).
- Model breakdowns: note when air entrainment, column separation, turbulent slug breakup, or strongly curved 3D paths invalidate the 1D slug approach.

## Volume–height map
- Retain the exact expression \(F(h)=\int_0^h A_{\mathrm{eff}}(\eta)\,d\eta\) and \(F(h_c)+AL=F(h_0)+AL_1\), but explicitly state \(n(\eta)\) for the prototype and show the resulting piecewise-linear \(h_c(L)\) with slope changes. Then specialise to \(A_0=\text{const}\).
- Emphasise that \(F(h)\) is the container water volume excluding the pipe interior, because \(A_{\mathrm{eff}}\) subtracts the cross-sectional area of each leg that intersects the slice.

## Initial conditions and comparison
- Explicitly describe the two start-up methods (pre-filling to \(B\) or dipping until \(B\) is wet) and show they both yield \(L(0)=L_1,~\dot L(0)=0,~t_0=0,~h_c(0)=h_0\).
- Contrast with an inverted-U: after the initial drop the driving head vanishes at the crest; here the head remains nonzero for \(h(L)<h_c\), so the slug typically reaches the next crossing with finite momentum.

## Dynamics and analytics
- Keep the extended filling ODE with \(h_c(L)=h_0-(A/A_0)(L-L_1)\) and losses.
- Derive the constant-\(h_c\), lossless climb bound explicitly: for each segment \(h(L)=c_i+s_i L\), the integral \(\int (h_0-h(L))/L\,dL = (h_0-c_i)\ln L - s_i L\) yields a closed-form contribution; assemble segments to obtain the stall condition.
- Provide the necessary priming condition \(h_{\max}=h(L_{\text{stall}})>h_3\) and observe how losses/drawdown shrink the attainable height relative to this bound.

## Computation
- Recommend solving the filling ODE with an event at \(L=L_{\max}\); switch to the draining system \((h_c,v)\) thereafter.
- Include a short Python script using `solve_ivp`, Churchill friction evaluation, and minor-loss aggregation; comment on tolerances and possible stiffness when losses are large.

## Citations and value
- Keep Churchill, Colebrook/Moody (losses), and White (Torricelli/unsteady Bernoulli) as core fluid-mechanics references, and explicitly cite the cavitation-height papers already in the bibliography (Boatwright; Vera; Tyree).
- Trim redundant prose around the effective area so that the exact map and constant-area specialisation appear once in a single coherent section.
- Add a brief “What this model gives” paragraph: geometry-to-priming test, upper-bound climb height, and simulation-ready ODEs.

## Findings for the current `archive/siphon_final.tex`
- The document already implements almost all items above: it includes a general volume–height map, explicit modelling limits (cavitation, capillarity, non-hydrostatic inlet), a clear initial-condition section, a loss-inclusive slug model, an analytic stall-height bound, and a runnable Python solver.
- Small improvements worth making are: (i) emphasising the driving force \(\rho gA(h_c-h(L))\) and initial conditions directly in the introduction, (ii) tightening the wording and scaling of the non-hydrostatic inlet correction, and (iii) adding a compact variable glossary in the model-summary section.

## Concrete changes implemented / planned in the new TeX version
- Update the introduction to state the driving term and initial conditions early, explicitly linking the geometry to the non-zero drive while \(h(L)<h_c\).
- Clarify in the volume-map section that \(F(h)\) is the container volume excluding the pipe interior, and describe how to construct \(n(\eta)\) and thus \(h_c(L)\) piecewise for any given geometry.
- Refine the hydrostatic-inlet validity bullet so the unsteady correction appears as a head term of order \((A/A_0)\dot h_c\dot L/g\), rather than as an unscaled pressure term.
- Add a brief remark that the linear slopes \(s_i\) equal \(\sin\theta_i\) for segment angle \(\theta_i\), making the dependence on geometry more transparent.
- Extend the “Model summary” section with a short description list of the main variables and parameters to serve as a quick-reference glossary at the end of the paper.
