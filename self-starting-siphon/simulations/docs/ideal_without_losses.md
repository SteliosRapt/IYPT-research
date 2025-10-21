# Complete Siphon Analysis: Velocity, Pressure, and Time

This document provides a comprehensive mathematical analysis of siphon drainage, including derivations for velocity, height as functions of time, drainage time, and pressure distribution. The numerical implementation that mirrors these equations lives in `simulations/ideal.py`, which exposes the ideal (lossless) scenario.

---

## 1. Velocity from Bernoulli's Equation (Instantaneous)

### Step 1.1: Bernoulli Between Reservoir Surface and Outlet

Applying Bernoulli's equation between the reservoir surface and tube outlet:

At reservoir surface (height $h_0$, velocity $v_0$):
$$P_{atm} + \frac{1}{2}\rho v_0^2 + \rho g h_0 = H$$

At tube outlet (height $h_{out}$, velocity $v$):
$$P_{atm} + \frac{1}{2}\rho v^2 + \rho g h_{out} = H$$

Setting them equal:
$$\frac{1}{2}\rho v_0^2 + \rho g h_0 = \frac{1}{2}\rho v^2 + \rho g h_{out}$$

### Step 1.2: Apply Continuity Equation

From continuity: $v_0 A_0 = v A_{tube}$

Let $k = \frac{A_{tube}}{A_0}$, then $v_0 = k v$

Substituting into Bernoulli:
$$\frac{1}{2}\rho k^2 v^2 + \rho g h_0 = \frac{1}{2}\rho v^2 + \rho g h_{out}$$

$$\frac{1}{2}v^2(1 - k^2) = g(h_0 - h_{out})$$

$$\boxed{v(h_0) = \sqrt{\frac{2g(h_0 - h_{out})}{1 - k^2}}}$$

This gives the instantaneous velocity when the reservoir height is $h_0$.

> **Validity requirements:** the derivation assumes a positive head difference $(h_0 > h_{out})$ and an area ratio $0 < k < 1$. Values of $k$ at or above unity invalidate the inviscid siphon model because the velocity at the reservoir surface would exceed that in the tube.
>
> **⚠️ CRITICAL:** As $k \to 1$, the denominator $(1 - k^2) \to 0$, causing velocity, acceleration, and drain time to diverge. In practice, $k > 0.3$ already produces significant errors because the assumption of negligible reservoir surface velocity breaks down. Always verify $k \ll 1$ before applying these formulas.

---

## 2. Time to Empty the Reservoir

### Step 2.1: Differential Equation Setup

The volumetric flow rate out is:
$$Q = v \cdot A_{tube}$$

The rate of volume change in the reservoir:
$$\frac{dV}{dt} = -Q = -v \cdot A_{tube}$$

Since $V = A_0 \cdot h_0$:
$$A_0 \frac{dh_0}{dt} = -v \cdot A_{tube}$$

$$\frac{dh_0}{dt} = -\frac{A_{tube}}{A_0} v = -k v$$

Substituting the expression for $v$:
$$\frac{dh_0}{dt} = -k \sqrt{\frac{2g(h_0 - h_{out})}{1 - k^2}}$$

### Step 2.2: Separating Variables

$$\frac{dh_0}{\sqrt{h_0 - h_{out}}} = -k \sqrt{\frac{2g}{1 - k^2}} \, dt$$

### Step 2.3: Integration

Let $u = h_0 - h_{out}$, then $du = dh_0$

$$\int_{h_{0,initial} - h_{out}}^{0} \frac{du}{\sqrt{u}} = -k \sqrt{\frac{2g}{1 - k^2}} \int_0^t dt$$

$$\left[ 2\sqrt{u} \right]_{h_{0,initial} - h_{out}}^{0} = -k \sqrt{\frac{2g}{1 - k^2}} \cdot t$$

$$0 - 2\sqrt{h_{0,initial} - h_{out}} = -k \sqrt{\frac{2g}{1 - k^2}} \cdot t$$

$$2\sqrt{h_{0,initial} - h_{out}} = k \sqrt{\frac{2g}{1 - k^2}} \cdot t$$

### Step 2.4: Solving for Time to Empty

$$t = \frac{2\sqrt{h_{0,initial} - h_{out}}}{k \sqrt{\frac{2g}{1 - k^2}}}$$

$$t = \frac{2\sqrt{h_{0,initial} - h_{out}}}{k} \cdot \sqrt{\frac{1 - k^2}{2g}}$$

$$\boxed{t_{empty} = \frac{2\sqrt{1 - k^2}}{k\sqrt{2g}} \sqrt{h_{0,initial} - h_{out}}}$$

**Physical interpretation:**
1. Time increases with $\sqrt{h_{0,initial} - h_{out}}$ - greater height difference takes longer (non-linear scaling)
2. Time increases as $k$ decreases (smaller tube relative to reservoir drains slower)
3. The factor $\sqrt{1-k^2}$ accounts for non-negligible velocity at the reservoir surface
4. When $k \to 0$ (very small tube), approaches the standard Torricelli result

---

## 3. Height as a Function of Time

### Step 3.1: Deriving $h_0(t)$

From the separated differential equation in Step 2.2, integrating from 0 to time $t$:

$$\int_{h_{0,initial}}^{h_0(t)} \frac{dh_0}{\sqrt{h_0 - h_{out}}} = -k \sqrt{\frac{2g}{1 - k^2}} \int_0^t dt$$

$$2\sqrt{h_0(t) - h_{out}} - 2\sqrt{h_{0,initial} - h_{out}} = -k \sqrt{\frac{2g}{1 - k^2}} \cdot t$$

$$\sqrt{h_0(t) - h_{out}} = \sqrt{h_{0,initial} - h_{out}} - \frac{k}{2}\sqrt{\frac{2g}{1-k^2}} \cdot t$$

Let $\alpha = \frac{k}{2}\sqrt{\frac{2g}{1-k^2}}$, then:

$$\boxed{h_0(t) = h_{out} + \left(\sqrt{h_{0,initial} - h_{out}} - \alpha t\right)^2}$$

where $\alpha = \frac{k}{2}\sqrt{\frac{2g}{1-k^2}}$

---

## 4. Velocity as a Function of Time

### Step 4.1: Substituting $h_0(t)$ into Velocity Formula

Substituting the expression for $h_0(t)$ into the instantaneous velocity equation:

$$v(t) = \sqrt{\frac{2g(h_0(t) - h_{out})}{1-k^2}}$$

$$v(t) = \sqrt{\frac{2g}{1-k^2}} \cdot \sqrt{h_0(t) - h_{out}}$$

$$v(t) = \sqrt{\frac{2g}{1-k^2}} \cdot \left(\sqrt{h_{0,initial} - h_{out}} - \frac{k}{2}\sqrt{\frac{2g}{1-k^2}} \cdot t\right)$$

Expanding:

$$v(t) = \sqrt{\frac{2g}{1-k^2}} \cdot \sqrt{h_{0,initial} - h_{out}} - \sqrt{\frac{2g}{1-k^2}} \cdot \frac{k}{2}\sqrt{\frac{2g}{1-k^2}} \cdot t$$

$$v(t) = \sqrt{\frac{2g}{1-k^2}} \cdot \sqrt{h_{0,initial} - h_{out}} - \frac{k g}{1-k^2} \cdot t$$

$$\boxed{v(t) = v_0 - \frac{k g}{1-k^2} \cdot t}$$

where $v_0 = \sqrt{\frac{2g(h_{0,initial} - h_{out})}{1-k^2}}$ is the initial velocity.

**Key insight**: Velocity decreases **linearly** with time, with slope $\frac{k g}{1-k^2}$.

---

## 5. Pressure Distribution Along the Tube

### Step 5.1: General Bernoulli Equation

At any point in the tube at height $h$ with velocity $v_{tube}$:

$$P + \frac{1}{2}\rho v_{tube}^2 + \rho g h = H_{total}$$

Where $H_{total}$ is the total head (constant along streamline).

### Step 5.2: Determining Total Head

At the reservoir surface (height $h_0$, velocity $v_0 = kv$):
$$H_{total} = P_{atm} + \frac{1}{2}\rho k^2 v^2 + \rho g h_0$$

### Step 5.3: Pressure at Height $h$

Assuming the tube has constant cross-section, $v_{tube} = v$ everywhere in the tube:

$$P(h) = P_{atm} + \frac{1}{2}\rho k^2 v^2 + \rho g h_0 - \frac{1}{2}\rho v^2 - \rho g h$$

$$P(h) = P_{atm} + \frac{1}{2}\rho v^2(k^2 - 1) + \rho g(h_0 - h)$$

Since $v^2 = \frac{2g(h_0 - h_{out})}{1 - k^2}$:

$$P(h) = P_{atm} + \frac{1}{2}\rho \cdot \frac{2g(h_0 - h_{out})}{1 - k^2} \cdot (k^2 - 1) + \rho g(h_0 - h)$$

Note that $(k^2 - 1) = -(1 - k^2)$, so the dynamic pressure term simplifies:

$$P(h) = P_{atm} + \frac{1}{2}\rho \cdot \frac{2g(h_0 - h_{out})}{1 - k^2} \cdot [-(1 - k^2)] + \rho g(h_0 - h)$$

$$P(h) = P_{atm} - \rho g(h_0 - h_{out}) + \rho g(h_0 - h)$$

$$\boxed{P(h) = P_{atm} + \rho g(h_{out} - h)}$$

### Step 5.4: Physical Interpretation

**Key insight**: The pressure at height $h$ depends only on the vertical distance below the outlet!

- At $h = h_{out}$: $P = P_{atm}$ ✓ (atmospheric pressure at outlet)
- At $h > h_{out}$: $P < P_{atm}$ (sub-atmospheric pressure in the upper part of siphon)
- At $h < h_{out}$: $P > P_{atm}$ (above atmospheric in lower part)

For crest diagnostics the implementation now references the explicit crest elevation $h_c$. It is configurable through `TubeGeometry.entry_height` (defaulting to the initial reservoir height so existing scripts remain valid). The plotted crest pressure therefore becomes

$$
P_{crest}(t) = P_{atm} + \rho g (h_0(t) - h_c) - \tfrac{1}{2}\rho v^2(t),
$$

which makes the dynamic head subtraction explicit and clarifies that the reported pressure is relative to the crest rather than the outlet gauge.

### Step 5.5: Maximum Siphon Height (Cavitation Limit)

The **minimum pressure** occurs at the highest point of the siphon tube. If this pressure drops below water's vapor pressure (~2.3 kPa at 20°C), cavitation occurs and the siphon breaks.

For the siphon to work without cavitation:
$$P_{min} = P_{atm} + \rho g(h_{out} - h_{max}) > P_{vapor}$$

$$h_{max} < h_{out} + \frac{P_{atm} - P_{vapor}}{\rho g}$$

At 20°C with standard atmospheric pressure:
$$h_{max} < h_{out} + \frac{101300 - 2300}{998 \cdot 9.81} \approx h_{out} + 10.1 \text{ m}$$

---

## 6. Flow Rates

### Volumetric Flow Rate
$$Q(t) = A_{tube} \cdot v(t) = A_{tube}\left(v_0 - \frac{kg}{1-k^2} \cdot t\right)$$

### Mass Flow Rate
$$\dot{m}(t) = \rho A_{tube} \cdot v(t) = \rho A_{tube}\left(v_0 - \frac{kg}{1-k^2} \cdot t\right)$$

---

## Summary of Key Results

| Quantity | Formula |
|----------|---------|
| **Instantaneous velocity** | $v(h_0) = \sqrt{\frac{2g(h_0 - h_{out})}{1 - k^2}}$ |
| **Velocity vs time** | $v(t) = v_0 - kg \cdot t$ |
| **Height vs time** | $h_0(t) = h_{out} + \left(\sqrt{h_{0,i} - h_{out}} - \alpha t\right)^2$ |
| **Time to empty** | $t_{empty} = \frac{2\sqrt{1 - k^2}}{k\sqrt{2g}} \sqrt{h_{0,i} - h_{out}}$ |
| **Pressure at height** | $P(h) = P_{atm} + \rho g(h_{out} - h)$ |
| **Volumetric flow rate** | $Q(t) = A_{tube} \cdot v(t)$ |
| **Mass flow rate** | $\dot{m}(t) = \rho A_{tube} \cdot v(t)$ |

Where:
- $k = \frac{A_{tube}}{A_0}$ (area ratio)
- $\alpha = \frac{k}{2}\sqrt{\frac{2g}{1-k^2}}$
- $v_0 = \sqrt{\frac{2g(h_{0,i} - h_{out})}{1-k^2}}$ (initial velocity)
- $h_{0,i}$ is the initial reservoir height

---

## Unit Verification

Time to empty:
$$[t] = \frac{\sqrt{dimensionless}}{\sqrt{dimensionless} \cdot \sqrt{m/s^2}} \cdot \sqrt{m} = \sqrt{\frac{s^2 \cdot m}{m}} = s \,\checkmark$$

Velocity:
$$[v] = \sqrt{\frac{m/s^2 \cdot m}{dimensionless}} = \sqrt{m^2/s^2} = m/s \,\checkmark$$

Pressure:
$$[P] = Pa + \frac{kg}{m^3} \cdot \frac{m}{s^2} \cdot m = Pa + \frac{kg}{m \cdot s^2} = Pa + Pa = Pa \,\checkmark$$
