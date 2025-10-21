# Siphon Dynamics with Head Losses

This note extends the inviscid siphon derivation to include distributed and minor losses. It also outlines how to push the model toward higher-fidelity predictions.

---

## 1. Governing Energy Balance with Losses

Consider a reservoir draining through a tube of uniform area \(A_{tube}\) into an outlet at elevation \(h_{out}\). The reservoir surface area is \(A_0\) and the surface elevation at time \(t\) is \(h_0(t)\). Define the area ratio \(k = A_{tube} / A_0\) with \(0 < k < 1\).

Applying Bernoulli between the reservoir surface (point 0) and the tube outlet (point out), and including a head loss term \(h_L\):

\[
\frac{P_{atm}}{\rho g} + h_0 + \frac{k^2 v^2}{2g} = \frac{P_{atm}}{\rho g} + h_{out} + \frac{v^2}{2g} + h_L.
\]

Rearranging yields

\[
\frac{1 - k^2}{2g} v^2 = h_0 - h_{out} - h_L.
\]

Let the loss term be represented with a dimensionless coefficient \(\Lambda\) multiplying \(v^2/(2g)\):

\[
h_L = \Lambda \frac{v^2}{2g}, \qquad \Lambda = f \frac{L}{D} + \sum_i K_i,
\]

where \(f\) is the Darcy friction factor, \(L\) the tube length, \(D\) the hydraulic diameter, and each \(K_i\) a minor-loss coefficient (bends, entrances, exits, etc.). Substituting gives

\[
\left(1 - k^2 + \Lambda\right) \frac{v^2}{2g} = h_0 - h_{out}.
\]

Thus the instantaneous velocity is

\[
\boxed{v(h_0) = \sqrt{\frac{2g\, (h_0 - h_{out})}{1 - k^2 + \Lambda}}}.
\]

Setting \(\Lambda = 0\) recovers the inviscid expression.

---

## 2. Height and Velocity Evolution

The continuity equation still gives

\[
A_0 \frac{dh_0}{dt} = -A_{tube} v \quad \Rightarrow \quad \frac{dh_0}{dt} = -k v.
\]

Insert the loss-adjusted velocity expression:

\[
\frac{dh_0}{dt} = -k \sqrt{\frac{2g}{1 - k^2 + \Lambda}} \sqrt{h_0 - h_{out}}.
\]

Separating and integrating as before yields

\[
\boxed{h_0(t) = h_{out} + \left(\sqrt{h_{0,initial} - h_{out}} - \alpha_{\Lambda} t\right)^2},
\]

with

\[
\alpha_{\Lambda} = \frac{k}{2} \sqrt{\frac{2g}{1 - k^2 + \Lambda}}.
\]

Substituting \(h_0(t)\) back into the velocity formula provides the time-dependent velocity

\[
\boxed{v(t) = v_0 - \frac{k g}{1 - k^2 + \Lambda} t},
\]

where \(v_0 = \sqrt{\tfrac{2g(h_{0,initial} - h_{out})}{1 - k^2 + \Lambda}}\). The reservoir empties when the square-root term vanishes, giving the drainage time

\[
\boxed{t_{empty} = \frac{2 \sqrt{1 - k^2 + \Lambda}}{k \sqrt{2g}} \sqrt{h_{0,initial} - h_{out}}}.
\]

Because \(\Lambda > 0\) adds to the denominator, each loss term slows the drainage and increases the time to empty.

---

## 3. Strategies for Increasing Model Fidelity

1. **Laminar vs. turbulent friction:**
   * Use the Reynolds number \(Re = \rho v D / \mu\) to evaluate the flow regime.
   * For laminar flow (\(Re < 2100\)), set \(f = 64 / Re\) and iterate because \(f\) depends on \(v\).
   * For turbulent flow, employ empirical correlations (Blasius, Colebrook–White) with roughness inputs.

2. **Time-varying loss coefficients:**
   * Recompute \(\Lambda(t)\) each time step using the updated friction factor and any valve positions.
   * Integrate the resulting nonlinear ODE numerically (e.g., Runge–Kutta) rather than relying on the closed-form solution.

3. **Two-phase / cavitation considerations:**
   * When pressures approach vapor pressure, account for vapor cores or air entrainment.
   * Introduce compressibility or free-surface entrainment models to estimate flow interruption.

4. **Geometric complexity:**
   * Model varying tube diameter by discretizing along the length and applying continuity/Bernoulli segment-wise.
   * Incorporate entrance reservoirs or downstream backpressure changes.

5. **Validation and calibration:**
   * Compare predictions to experimental data to calibrate minor-loss coefficients and friction factors.
   * Include uncertainty quantification for roughness, viscosity, and geometry to bound predicted discharge rates.

These steps outline a roadmap for progressing from the analytical constant-loss model derived above to a full numerical siphon simulator that responds to changing operating conditions.

---

## 4. Summary of Key Formulas with Losses

| Quantity | Expression |
| --- | --- |
| Instantaneous velocity | \( v(h_0) = \sqrt{\dfrac{2g (h_0 - h_{out})}{1 - k^2 + \Lambda}} \) |
| Velocity slope | \( \dfrac{dv}{dt} = -\dfrac{k g}{1 - k^2 + \Lambda} \) |
| Height evolution | \( h_0(t) = h_{out} + (\sqrt{h_{0,initial} - h_{out}} - \alpha_{\Lambda} t)^2 \) |
| Drainage time | \( t_{empty} = \dfrac{2 \sqrt{1 - k^2 + \Lambda}}{k \sqrt{2g}} \sqrt{h_{0,initial} - h_{out}} \) |

All formulas reduce to the inviscid counterparts by setting \(\Lambda = 0\).
