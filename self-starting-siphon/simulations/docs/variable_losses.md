# Siphon Dynamics with Dynamic Losses, Regime Transitions, and Cavitation Limits

This document extends the classical inviscid siphon derivation to cover friction that evolves with the instantaneous flow, regime transitions between laminar and turbulent states, geometric minor losses, and limits imposed by vapor pressure and air entrainment. The goal is to give both the governing mathematics **and** the intuition required to implement a high-fidelity simulation. The corresponding numerical model is implemented in `simulations/variable_losses.py`.

---

## 1. Control Volumes and Notation

We consider a reservoir of planform area $A_0$ draining through a siphon tube of circular diameter $D(s)$ and local cross-sectional area $A(s)$ into an outlet at elevation $h_{out}$. The reservoir free surface is at elevation $h_0(t)$, and the highest point (crest) of the siphon is at elevation $h_c$ with coordinate $s = s_c$ along the centerline. The tube roughness is $\varepsilon(s)$, the local wall shear stress is $\tau_w(s,t)$, and the fluid has density $\rho$, dynamic viscosity $\mu$, and vapor pressure $P_v$.

We assume the flow is single-valued along the tube (no recirculation) and initially fully filled. Later sections describe when this assumption fails and how to extend the model.

The local velocity magnitude is $v(s,t)$ and is related to the volumetric flow rate $Q(t)$ via
\[
Q(t) = v(s,t) A(s) \quad \Rightarrow \quad v(s,t) = \frac{Q(t)}{A(s)}.
\]
Because $Q$ is constant along a 1-D incompressible stream, all head-loss expressions can be written in terms of $Q(t)$.

---

## 2. Unsteady Bernoulli Equation with Distributed and Minor Losses

Apply the extended Bernoulli equation between the reservoir surface (state 0) and the outlet (state out), keeping the loss terms explicit:
\[
\frac{P_{atm}}{\rho g} + h_0(t) + \frac{\alpha_0 Q^2}{2 g A_0^2} = \frac{P_{atm}}{\rho g} + h_{out} + \frac{\alpha_{out} Q^2}{2 g A_{out}^2} + h_{L,\text{dist}}(Q) + h_{L,\text{minor}}(Q).
\]
Here $\alpha$ are kinetic-energy correction factors that account for non-uniform velocity profiles. Typical values:
- $\alpha = 1.0$ for uniform (plug) flow or fully turbulent pipe flow
- $\alpha = 2.0$ for fully developed laminar flow in circular pipes
- $\alpha \approx 1.05-1.15$ for turbulent flow in practice due to boundary layer effects

For a reservoir, $\alpha_0 \approx 1$ and $A_0 \gg A_{out}$, so the surface kinetic term is negligible. Rearranging gives
\[
\frac{Q^2}{2g A_{out}^2} = h_0(t) - h_{out} - h_{L,\text{dist}}(Q) - h_{L,\text{minor}}(Q).
\]
The distributed head loss in a duct of varying diameter uses the Darcy–Weisbach integral
\[
h_{L,\text{dist}}(Q) = \int_{0}^{L} f(s,t) \frac{Q^2}{2 g D_h^2(s) A^2(s)} \; ds,
\]
with local hydraulic diameter $D_h(s)$ and friction factor $f(s,t)$. For a uniform tube of length $L$ and diameter $D$, this collapses to $f L/D \cdot Q^2 / (2 g A_{out}^2)$.

Minor losses accumulate from geometric discontinuities:
\[
h_{L,\text{minor}}(Q) = \sum_j K_j(Q) \frac{Q^2}{2 g A_j^2}.
\]
Many coefficients $K_j$ depend weakly on Reynolds number or valve position; capturing that dependence avoids under/over-estimating the dissipation when regimes change.

**Intuition:** The left-hand side is the kinetic head at the outlet. The right-hand side is the gravitational head minus the energy eaten by viscous friction and local turbulence. When losses grow, the same elevation drop drives less flow.

---

## 3. Continuity: Evolution of the Reservoir Head

The reservoir volume obeys $V(t) = A_0 h_0(t)$ (assuming a vertical-walled tank). Conservation of mass gives
\[
A_0 \frac{dh_0}{dt} = -Q(t) \quad \Rightarrow \quad \frac{dh_0}{dt} = -\frac{Q(t)}{A_0}.
\]
The challenge is that $Q(t)$ is no longer an explicit function of $h_0$ because the losses themselves depend on $Q$ through the friction factor and Reynolds number. Instead, we solve an implicit algebraic equation for $Q$ at each time:
\[
\Phi(Q, h_0) \equiv \frac{Q^2}{2g A_{out}^2} + h_{L,\text{dist}}(Q) + h_{L,\text{minor}}(Q) - (h_0 - h_{out}) = 0.
\]
Once $Q$ is found, the ODE $dh_0/dt = -Q/A_0$ advances the free surface.

**Algorithmic intuition:** Every time step is a negotiation between inertia and friction. Guess $Q$, compute losses, check whether the total head drop matches the elevation difference, and iterate until balance is achieved.

**Implementation note:** The numerical integrator now allows the time step to contract all the way down to machine precision (via `np.nextafter`) instead of imposing a hard `Δt` floor. This prevents the final updates from overshooting the remaining head when the reservoir is almost empty, keeping the predicted drain time and terminal height consistent with the physics.

---

## 4. Reynolds Number and Friction Factor Models

### 4.1 Reynolds Number
For circular pipes the Reynolds number is
\[
\mathrm{Re}(t) = \frac{\rho v D}{\mu} = \frac{4 \rho Q}{\pi D \mu}.
\]
In a variable-diameter tube use local $D(s)$ and integrate the distributed losses piecewise, evaluating $\mathrm{Re}(s,t) = \rho Q / (\mu A(s)) \cdot D_h(s)$ for each segment.

### 4.2 Laminar Regime
If $\mathrm{Re} < 2100$, laminar flow yields an exact friction factor
\[
f = \frac{64}{\mathrm{Re}}.
\]
Substituting this into the distributed loss integral maintains the correct $f \propto 1/Q$ scaling, leading to a linear dependence of $h_{L,\text{dist}}$ on $Q$ rather than quadratic. The implicit equation $\Phi(Q,h_0)=0$ remains nonlinear because $f$ still multiplies $Q^2$ inside the integral, but the effective exponent drops to unity.

### 4.3 Transition Zone
For $2100 < \mathrm{Re} < 4000$, the flow is in a **transition zone** where neither laminar nor fully turbulent correlations are strictly valid. Flow becomes intermittently turbulent with unpredictable friction factors that can vary significantly with pipe roughness, entrance conditions, and vibrations. Practical approaches include:

* **Conservative estimate:** Use the higher of the laminar and turbulent predictions to bound the uncertainty.
* **Interpolation:** Linearly blend $f_{\text{lam}} = 64/\mathrm{Re}$ and $f_{\text{turb}}$ based on position within the transition band.
* **Avoid steady operation:** In experimental setups, design to keep $\mathrm{Re}$ either below 2100 or above 4000 throughout the drain to maintain predictable behavior.

During siphon drainage, the Reynolds number typically decreases monotonically, so the flow may start turbulent and transition to laminar. The simulation should detect and handle this regime change automatically.

### 4.4 Fully Turbulent Regime
For $\mathrm{Re} \gtrsim 4000$, turbulent correlations are required. Two common choices are:

* **Blasius correlation (smooth pipe, $\mathrm{Re} < 10^5$):**
  \[
  f = 0.3164 \; \mathrm{Re}^{-1/4}.
  \]
  This captures the $f \sim Q^{-1/4}$ weak dependence characteristic of smooth turbulent flow.

* **Colebrook–White equation (rough pipes, all turbulent regimes):**
  \[
  \frac{1}{\sqrt{f}} = -2 \log_{10} \left( \frac{\varepsilon/D}{3.7} + \frac{2.51}{\mathrm{Re} \sqrt{f}} \right).
  \]
  Because $f$ appears on both sides, solve using Newton iteration. Define $\phi(f) = \frac{1}{\sqrt{f}} + 2 \log_{10} \left( \frac{\varepsilon/D}{3.7} + \frac{2.51}{\mathrm{Re} \sqrt{f}} \right) = 0$. The derivative is
  \[
  \frac{d\phi}{df} = -\frac{1}{2f^{3/2}} - \frac{2}{\ln(10)} \cdot \frac{2.51/(2\mathrm{Re} f^{3/2})}{\varepsilon/D/3.7 + 2.51/(\mathrm{Re}\sqrt{f})}.
  \]
  Alternatively, use the explicit Swamee–Jain approximation (accurate to ±1% for $10^{-6} < \varepsilon/D < 10^{-2}$ and $5 \times 10^3 < \mathrm{Re} < 10^8$):
  \[
  f \approx \frac{0.25}{\left[ \log_{10}\left( \frac{\varepsilon/D}{3.7} + \frac{5.74}{\mathrm{Re}^{0.9}} \right) \right]^2}.
  \]

**Intuition:** In laminar flow the fluid shears in orderly layers, so doubling $Q$ doubles the wall stress and the head loss grows linearly with flow. In turbulent flow the velocity profile flattens and wall eddies dominate, causing a weaker-than-linear rise of friction with $Q$ but making the loss sensitive to roughness. Transition is detected automatically via $\mathrm{Re}(t)$.

---

## 5. Time Integration Strategy

Because $Q$ feeds back into the loss terms, analytic solutions like the linear velocity decay in the inviscid case are no longer valid. A practical time-marching scheme is:

1. **Given** $h_0^n$ at time $t_n$, set an initial guess $Q^{(0)}$ (e.g., previous time step value).
2. **Iterate** on $Q$ until convergence:
   1. Compute $\mathrm{Re}$ and select the appropriate $f$ correlation for each segment.
   2. Evaluate $h_{L,\text{dist}}(Q)$ and $h_{L,\text{minor}}(Q)$.
   3. Update $Q$ with Newton's method:
      \[
      Q^{(k+1)} = Q^{(k)} - \frac{\Phi(Q^{(k)}, h_0^n)}{\partial \Phi / \partial Q},
      \]
      where
      \[
      \frac{\partial \Phi}{\partial Q} = \frac{Q}{g A_{out}^2} + \int_0^L \left[ \frac{\partial}{\partial Q} \left( f \frac{Q^2}{2 g D_h^2 A^2} \right) \right] ds + \sum_j \frac{\partial}{\partial Q}\left( K_j \frac{Q^2}{2 g A_j^2} \right).
      \]
      The derivatives include terms from $f(Q)$ and $K_j(Q)$, which require $df/dQ = (df/d\mathrm{Re}) (d\mathrm{Re}/dQ)$.
3. **Advance** the reservoir height using an ODE integrator (Forward Euler shown for clarity):
   \[
   h_0^{n+1} = h_0^{n} - \Delta t \; \frac{Q^{n}}{A_0}.
   \]
   Higher-order schemes (Runge–Kutta) reduce numerical diffusion.

**Physical insight:** When friction rises rapidly (laminar $f \propto 1/Q$), the implicit solve stabilizes the flow—large $Q$ guesses quickly get damped. In turbulent flow, $f$ varies slowly, so the implicit Jacobian keeps the iteration efficient.

---

## 6. Pressure Distribution and Cavitation Margin

The piezometric head at any position $s$ obeys the mechanical-energy balance from state 0 to $s$:
\[
\frac{P(s,t)}{\rho g} + z(s) + \frac{\alpha(s) Q^2}{2 g A^2(s)} = h_0(t) - \int_{0}^{s} \frac{\tau_w(\xi,t)}{\rho g R_h(\xi)} \, d\xi - \sum_{j \in [0,s]} K_j(Q) \frac{Q^2}{2 g A_j^2},
\]
where $R_h$ is the hydraulic radius. For a uniform circular pipe this simplifies to
\[
P(s,t) = P_{atm} + \rho g \left[ h_0(t) - z(s) - f \frac{s}{D} \frac{Q^2}{2 g A_{out}^2} - \sum_{j \in [0,s]} K_j(Q) \frac{Q^2}{2 g A_j^2} - \frac{Q^2}{2 g A_{out}^2} \right].
\]
The minimum pressure usually occurs at the crest $s_c$. Ensuring $P(s_c,t) > P_v$ defines a cavitation constraint:
\[
 h_0(t) - z(s_c) > \frac{Q^2}{2 g A_{out}^2} \left[ 1 + f \frac{s_c}{D} + \sum_{j \in [0,s_c]} K_j(Q) \frac{A_{out}^2}{A_j^2} \right] + \frac{P_v - P_{atm}}{\rho g}.
\]
**Intuition:** As the reservoir drains, both $h_0$ and $Q$ fall. Friction suppresses velocity, which relaxes the dynamic pressure drop, but the hydrostatic head shrinks faster. Once the hydrostatic head can no longer offset the kinetic and frictional losses plus the vapor margin, the siphon pulls a vapor core and breaks.

To assist post-processing, the solver records a `termination_status` flag alongside the time histories. It reports whether the run naturally completed (`COMPLETED`) or whether it terminated after reaching the configured `max_time` cap, preserving the terminal velocity and loss coefficient in the latter case for diagnostics.

---

## 7. Accounting for Variable Geometry

For tubes with piecewise diameters $D_i$ and lengths $L_i$, evaluate the distributed loss segment by segment:
\[
h_{L,\text{dist}} = \sum_i f_i \frac{L_i}{D_i} \frac{Q^2}{2 g A_i^2}.
\]
Each segment has its own Reynolds number $\mathrm{Re}_i = 4 \rho Q/(\pi D_i \mu)$ and roughness ratio $\varepsilon_i/D_i$ that feed into $f_i$. Bends, contractions, and valves in each segment contribute additional $K_j$. This modular structure mirrors how commercial piping handbooks tabulate head losses and allows you to assemble an arbitrary siphon path.

**Geometric intuition:** Contractions accelerate the flow and increase local head loss, elbows create secondary flows that raise $K$, and rough sections amplify the turbulent dissipation. Explicitly tracking them prevents optimistic runtime estimates.

---

## 8. Free-Surface and Air-Entrainment Effects

Even before vapor pressure is reached, the siphon can ingest air if the inlet forms a vortex or if the crest pressure drops enough to pull bubbles out of solution. A simple screening uses the Froude number at the reservoir entrance:
\[
\mathrm{Fr} = \frac{v_{entrance}}{\sqrt{g h_{sub}}},
\]
where $h_{sub}$ is the submergence depth of the intake below the free surface. Experiments show that maintaining $\mathrm{Fr} < 0.3$ (rough guideline) suppresses vortex formation. Expressed in flow rate,
\[
Q < 0.3 \; A_{entrance} \sqrt{g h_{sub}}.
\]
If this inequality is violated, introduce an entrainment loss term or cap $Q$ to represent intermittent slug flow. The kinetic-energy correction factor $\alpha_0$ may also rise above unity due to the non-uniform approach velocity.

**Intuition:** A siphon survives only if a continuous liquid column spans crest to outlet. Air ingestion breaks that column long before vapor pressure is hit. Controlling entrance velocity is the practical knob to avoid it.

---

## 9. Multiphase Extensions

When cavitation initiates or air is entrained, the flow becomes two-phase. A minimal extension is to treat the mixture as a homogeneous bubbly fluid with void fraction $\beta(t)$. Replace $\rho$ with the mixture density $\rho_m = (1-\beta) \rho_{\ell} + \beta \rho_g$ and adjust the momentum equation with a slip correction. The sound speed drops, so compressibility effects can no longer be ignored.

A more detailed slug-flow model discretizes the siphon into alternating liquid plugs and gas pockets. Each plug obeys a momentum balance
\[
M_i \frac{d v_i}{dt} = (P_{i-1} - P_i) A_i - F_{f,i}(v_i) - W_i,
\]
where $F_{f,i}$ is the friction force and $W_i$ the weight component. Coupling these plugs captures oscillations and rapid siphon breakage.

**Intuition:** Two-phase flow introduces inertia mismatches and compressibility that make the siphon behave like a spring–mass system. Capturing it requires time-resolved pressure states rather than a single Bernoulli equation.

---

## 10. Summary and Implementation Roadmap

* **Implicit energy balance:** Solve $\Phi(Q, h_0) = 0$ every step to determine $Q$ under time-varying friction and minor losses.
* **Regime-aware friction:** Update $f$ from the instantaneous Reynolds number using laminar $64/\mathrm{Re}$, turbulent (Blasius or Colebrook), and smooth transition handling.
* **Segmented geometry:** Sum losses over piecewise diameters, roughness, and fittings to reflect the actual siphon layout.
* **Cavitation safety check:** Evaluate crest pressure to ensure $P > P_v$ and include entrance Froude limits to avoid air entrainment.
* **Multiphase preparedness:** When limits are violated, switch to mixture or slug models that evolve pressure and mass in each phase.

With these components the siphon model migrates from a closed-form analytic solution to a physics-rich numerical simulator capable of predicting drain time, crest pressure, and failure modes across a wide range of operating conditions.
