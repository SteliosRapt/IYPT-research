# Complete Syphon Analysis: Velocity, Pressure, and Time

## 1. Velocity as a Function of Time

### Step 1.1: Velocity from Bernoulli (instantaneous)

At any instant when the water height is $h_0(t)$:

$$v(h_0) = \sqrt{\frac{2g(h_0 - h_{out})}{1 - k^2}}$$

where $k = \frac{A_{tube}}{A_0}$

### Step 1.2: Height as a Function of Time

From the differential equation:
$$\frac{dh_0}{dt} = -k \sqrt{\frac{2g(h_0 - h_{out})}{1 - k^2}}$$

Integrating (as shown in the time derivation):
$$h_0(t) - h_{out} = \left(\sqrt{h_{0,initial} - h_{out}} - \frac{k}{2}\sqrt{\frac{2g}{1-k^2}} \cdot t\right)^2$$

Let $\alpha = \frac{k}{2}\sqrt{\frac{2g}{1-k^2}}$, then:

$$h_0(t) = h_{out} + \left(\sqrt{h_{0,initial} - h_{out}} - \alpha t\right)^2$$

### Step 1.3: Velocity as a Function of Time

Substituting $h_0(t)$ into the velocity equation:

$$v(t) = \sqrt{\frac{2g}{1-k^2}} \cdot \left(\sqrt{h_{0,initial} - h_{out}} - \alpha t\right)$$

Simplifying with $\alpha = \frac{k}{2}\sqrt{\frac{2g}{1-k^2}}$:

$$\boxed{v(t) = \sqrt{\frac{2g}{1-k^2}} \cdot \sqrt{h_{0,initial} - h_{out}} - kg}$$

Wait, let me recalculate more carefully:

$$v(t) = \sqrt{\frac{2g(h_0(t) - h_{out})}{1-k^2}}$$

$$v(t) = \sqrt{\frac{2g}{1-k^2}} \cdot \left(\sqrt{h_{0,initial} - h_{out}} - \frac{k}{2}\sqrt{\frac{2g}{1-k^2}} \cdot t\right)$$

$$\boxed{v(t) = \sqrt{\frac{2g}{1-k^2}} \cdot \sqrt{h_{0,initial} - h_{out}} - kg \cdot t}$$

This is a **linear decrease** in velocity over time!

---

## 2. Time to Empty

From the integration in the previous derivation:

$$\boxed{t_{empty} = \frac{2\sqrt{1 - k^2}}{k\sqrt{2g}} \sqrt{h_{0,initial} - h_{out}}}$$

The syphon stops when $v(t) = 0$ or equivalently when $h_0(t) = h_{out}$.

---

## 3. Pressure Distribution Along the Tube

### Step 3.1: General Bernoulli Equation

At any point in the tube at height $h$ with velocity $v_{tube}$:

$$P + \frac{1}{2}\rho v_{tube}^2 + \rho g h = H_{total}$$

Where $H_{total}$ is the total head (constant along streamline).

### Step 3.2: Determining Total Head

At the reservoir surface (height $h_0$, velocity $v_0 = kv$):
$$H_{total} = P_{atm} + \frac{1}{2}\rho k^2 v^2 + \rho g h_0$$

### Step 3.3: Pressure at Height $h$

Assuming the tube has constant cross-section, $v_{tube} = v$ everywhere in the tube:

$$P(h) = P_{atm} + \frac{1}{2}\rho k^2 v^2 + \rho g h_0 - \frac{1}{2}\rho v^2 - \rho g h$$

$$P(h) = P_{atm} + \frac{1}{2}\rho v^2(k^2 - 1) + \rho g(h_0 - h)$$

Since $v^2 = \frac{2g(h_0 - h_{out})}{1 - k^2}$:

$$P(h) = P_{atm} + \frac{1}{2}\rho \cdot \frac{2g(h_0 - h_{out})}{1 - k^2} \cdot (k^2 - 1) + \rho g(h_0 - h)$$

$$P(h) = P_{atm} - \rho g(h_0 - h_{out}) + \rho g(h_0 - h)$$

$$\boxed{P(h) = P_{atm} + \rho g(h_{out} - h)}$$

### Step 3.4: Physical Interpretation

**Key insight**: The pressure at height $h$ depends only on the vertical distance below the outlet!

- At $h = h_{out}$: $P = P_{atm}$ ✓ (atmospheric pressure at outlet)
- At $h > h_{out}$: $P < P_{atm}$ (sub-atmospheric pressure in the upper part of syphon)
- At $h < h_{out}$: $P > P_{atm}$ (above atmospheric in lower part)

The **minimum pressure** occurs at the highest point of the syphon tube. If this pressure drops below water's vapor pressure (~2.3 kPa at 20°C), cavitation occurs and the syphon breaks.

### Step 3.5: Maximum Syphon Height

For the syphon to work without cavitation:
$$P_{min} = P_{atm} + \rho g(h_{out} - h_{max}) > P_{vapor}$$

$$h_{max} < h_{out} + \frac{P_{atm} - P_{vapor}}{\rho g}$$

At 20°C:
$$h_{max} < h_{out} + \frac{101300 - 2300}{998 \cdot 9.81} \approx h_{out} + 10.1 \text{ m}$$

---

## Summary of Key Results

| Quantity | Formula |
|----------|---------|
| Velocity at time $t$ | $v(t) = \sqrt{\frac{2g}{1-k^2}} \cdot \sqrt{h_{0,i} - h_{out}} - kg \cdot t$ |
| Height at time $t$ | $h_0(t) = h_{out} + \left(\sqrt{h_{0,i} - h_{out}} - \frac{k}{2}\sqrt{\frac{2g}{1-k^2}} \cdot t\right)^2$ |
| Time to empty | $t_{empty} = \frac{2\sqrt{1 - k^2}}{k\sqrt{2g}} \sqrt{h_{0,i} - h_{out}}$ |
| Pressure at height $h$ | $P(h) = P_{atm} + \rho g(h_{out} - h)$ |
| Volumetric flow rate | $Q(t) = A_{tube} \cdot v(t)$ |
| Mass flow rate | $\dot{m}(t) = \rho A_{tube} \cdot v(t)$ |

Where $k = \frac{A_{tube}}{A_0}$ and $h_{0,i}$ is the initial height.
