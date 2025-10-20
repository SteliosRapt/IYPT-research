from math import sqrt

# Bernoulli's equation: P/(ρg) + v²/(2g) + h = H = const

A_tube = 0.01    # m²
A_0 = 0.1        # m²
k = A_tube/A_0

h_0 = 0.1        # m
h_out = 0.06     # m
head = h_0 - h_out

P_atm = 101300   # Pa (atmospheric pressure)
rho = 998        # kg/m³ (water density at 20°C)
g = 9.81         # m/s²

v = sqrt(2*g*head/(1 - k**2))
Q = v*A_tube              # Volumetric flow rate (m³/s)
Q_mass = rho * Q          # Mass flow rate (kg/s)

# Time to empty calculation
# From integrating dh_0/dt = -k * sqrt(2*g*(h_0 - h_out)/(1 - k²))
t_empty = (2 * sqrt(1 - k**2)) / (k * sqrt(2*g)) * sqrt(h_0 - h_out)

print(f"Velocity: {v:.3f} m/s")
print(f"Volumetric flow rate: {Q:.6f} m³/s ({Q*1000:.2f} L/s)")
print(f"Mass flow rate: {Q_mass:.3f} kg/s")
print(f"Time to empty: {t_empty:.3f} s")