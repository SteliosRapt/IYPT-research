# Derivation: Time to Empty a Syphon

## Problem Setup

We have a syphon draining a reservoir where:
- Reservoir cross-sectional area: $A_0$
- Tube cross-sectional area: $A_{tube}$
- Area ratio: $k = \frac{A_{tube}}{A_0}$
- Initial water height: $h_0$
- Outlet height: $h_{out}$
- Gravity: $g$

## Step 1: Velocity from Bernoulli's Equation

Applying Bernoulli's equation between the reservoir surface and tube outlet, accounting for the velocity at the reservoir surface:

At reservoir surface:
$$P_{atm} + \frac{1}{2}\rho v_0^2 + \rho g h_0 = H$$

At tube outlet:
$$P_{atm} + \frac{1}{2}\rho v^2 + \rho g h_{out} = H$$

Setting them equal:
$$\frac{1}{2}\rho v_0^2 + \rho g h_0 = \frac{1}{2}\rho v^2 + \rho g h_{out}$$

From continuity equation: $v_0 A_0 = v A_{tube}$, so $v_0 = k v$

Substituting:
$$\frac{1}{2}\rho k^2 v^2 + \rho g h_0 = \frac{1}{2}\rho v^2 + \rho g h_{out}$$

$$\frac{1}{2}v^2(1 - k^2) = g(h_0 - h_{out})$$

$$v = \sqrt{\frac{2g(h_0 - h_{out})}{1 - k^2}}$$

## Step 2: Setting up the Differential Equation

The volumetric flow rate out is:
$$Q = v \cdot A_{tube}$$

The rate of volume change in the reservoir:
$$\frac{dV}{dt} = -Q = -v \cdot A_{tube}$$

Since $V = A_0 \cdot h_0$:
$$A_0 \frac{dh_0}{dt} = -v \cdot A_{tube}$$

$$\frac{dh_0}{dt} = -\frac{A_{tube}}{A_0} v = -k v$$

Substituting the expression for $v$:
$$\frac{dh_0}{dt} = -k \sqrt{\frac{2g(h_0 - h_{out})}{1 - k^2}}$$

## Step 3: Separating Variables

$$\frac{dh_0}{\sqrt{h_0 - h_{out}}} = -k \sqrt{\frac{2g}{1 - k^2}} \, dt$$

## Step 4: Integration

Let $u = h_0 - h_{out}$, then $du = dh_0$

$$\int_{h_{0,initial} - h_{out}}^{0} \frac{du}{\sqrt{u}} = -k \sqrt{\frac{2g}{1 - k^2}} \int_0^t dt$$

$$\left[ 2\sqrt{u} \right]_{h_{0,initial} - h_{out}}^{0} = -k \sqrt{\frac{2g}{1 - k^2}} \cdot t$$

$$0 - 2\sqrt{h_{0,initial} - h_{out}} = -k \sqrt{\frac{2g}{1 - k^2}} \cdot t$$

$$2\sqrt{h_{0,initial} - h_{out}} = k \sqrt{\frac{2g}{1 - k^2}} \cdot t$$

## Step 5: Solving for Time

$$t = \frac{2\sqrt{h_{0,initial} - h_{out}}}{k \sqrt{\frac{2g}{1 - k^2}}}$$

$$t = \frac{2\sqrt{h_{0,initial} - h_{out}}}{k} \cdot \sqrt{\frac{1 - k^2}{2g}}$$

$$\boxed{t = \frac{2\sqrt{1 - k^2}}{k\sqrt{2g}} \sqrt{h_{0,initial} - h_{out}}}$$

## Physical Interpretation

This formula shows:
1. Time increases with $\sqrt{h_{0,initial} - h_{out}}$ - greater height difference takes longer to drain (but not linearly!)
2. Time increases as $k$ decreases (smaller tube relative to reservoir)
3. The factor $\sqrt{1-k^2}$ accounts for the non-negligible velocity at the reservoir surface
4. When $k \to 0$ (very small tube), the formula approaches the standard Torricelli result

## Verification

The units check out:
$$[t] = \frac{\sqrt{dimensionless}}{\sqrt{dimensionless} \cdot \sqrt{m/s^2}} \cdot \sqrt{m} = \sqrt{\frac{s^2 \cdot m}{m}} = s \,\checkmark$$
