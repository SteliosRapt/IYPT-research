"""
Generate all figures for siphon-theory-5.tex
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp, quad
from scipy.optimize import brentq
import matplotlib.patches as mpatches

# Set up matplotlib style
plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 12,
    'legend.fontsize': 10,
    'figure.figsize': (8, 5),
    'lines.linewidth': 1.5,
    'axes.grid': True,
    'grid.alpha': 0.3,
})

# =============================================================================
# PARAMETERS (from Experimental Data)
# =============================================================================

# Geometric parameters (cm) - from experimental measurements
nodes_x = np.array([0, 7.5, 13.5, 21.4, 30.3])  # x coordinates
nodes_h = np.array([1, 11, 5, 13, -1.7])  # h coordinates (elevations)
h_c0 = 12.5  # Initial water level (cm)

# Compute segment lengths and slopes
n_segments = 4
L_seg = np.zeros(n_segments)  # Segment lengths
s_seg = np.zeros(n_segments)  # Slopes
c_seg = np.zeros(n_segments)  # Intercepts

for i in range(n_segments):
    dx = nodes_x[i+1] - nodes_x[i]
    dh = nodes_h[i+1] - nodes_h[i]
    L_seg[i] = np.sqrt(dx**2 + dh**2)
    s_seg[i] = dh / L_seg[i]

# Cumulative arclengths S_i
S = np.zeros(n_segments + 1)
for i in range(n_segments):
    S[i+1] = S[i] + L_seg[i]

# Compute intercepts for h(L) = c_i + s_i * L
for i in range(n_segments):
    c_seg[i] = nodes_h[i] - s_seg[i] * S[i]

# Point W: where h(L) = h_c0 on segment 4 (index 3)
S_W = (h_c0 - c_seg[3]) / s_seg[3]

# Physical parameters - from experimental setup
D_pipe = 0.5  # Pipe diameter (cm) = 5 mm
A_pipe = np.pi * D_pipe**2 / 4  # Pipe cross-sectional area (cm^2) ≈ 0.196 cm^2
A_container = 340.0  # Container area (cm^2)
A_ratio = A_pipe / A_container  # Area ratio ≈ 0.0006

epsilon_D = 0.00035  # Relative roughness (from experimental estimate)
K_total = 4.0  # Total minor loss coefficient (4 bends, experimental estimate)
f0 = 0.035  # Constant friction factor approximation (adjusted for smaller diameter)

# Fluid parameters (CGS units for consistency)
rho = 0.998  # g/cm^3
g = 981.0  # cm/s^2
nu = 0.01  # cm^2/s (kinematic viscosity)
gamma = 73.0  # dyn/cm (surface tension)
mu = rho * nu  # dynamic viscosity g/(cm*s)

S1 = S[1]  # Starting position (node B)
S4 = S[4]  # Outlet position (node E)
L_max = S4

# =============================================================================
# EXPERIMENTAL DATA
# =============================================================================

# Experimental velocity measurements with biased L values
# Note: Velocity only measured from L ≈ 18.6 cm to L ≈ 49.4 cm due to measurement difficulties
# L_biased applies exponential correction to better match actual L_max = 49.4 cm

exp_t = np.array([0.433, 0.467, 0.500, 0.533, 0.567, 0.600, 0.633, 0.667, 0.700, 0.733,
                  0.767, 0.800, 0.833, 0.867, 0.900, 0.933, 0.967, 1.000, 1.233, 1.267,
                  1.367, 1.433, 1.467, 1.533, 1.567, 1.600, 1.667, 1.700, 1.733, 1.800,
                  1.867, 1.900, 1.933, 1.967, 2.000, 2.033, 2.133, 2.167, 2.233, 2.267,
                  2.533, 2.567, 2.600, 2.633, 2.667, 2.700, 2.733, 2.767, 2.800, 2.833,
                  2.867, 2.900, 2.933, 2.967, 3.000, 3.033, 3.067, 3.200, 3.233, 3.267])

exp_v = np.array([np.nan, 14.8, 14.0, 13.0, 13.1, 16.5, 19.5, 19.9, 16.9, 15.9,
                  16.6, 17.1, 17.1, 15.8, 14.2, 13.5, 12.8, 10.7, 5.9, 5.0,
                  4.8, 4.5, 4.3, 4.1, 3.6, 3.2, 2.9, 3.0, 3.2, 3.1,
                  3.7, 3.6, 3.3, 3.4, 3.2, 3.8, 4.4, 4.9, 5.5, 5.8,
                  6.2, 7.1, 7.6, 8.3, 8.6, 8.7, 8.8, 9.4, 10.2, 10.7,
                  10.9, 10.8, 11.1, 11.7, 12.9, 13.5, 13.9, 14.7, 14.8, np.nan])

exp_L_raw = np.array([18.90000, 19.15160, 19.62680, 20.07230, 20.51600, 21.00440, 21.59840, 22.26820,
                      22.87540, 23.41660, 23.96910, 24.52515, 25.08945, 25.64875, 26.14375, 26.60080,
                      27.04790, 27.43565, 29.36955, 29.55485, 30.04485, 30.35175, 30.50135, 30.77855,
                      30.90945, 31.02165, 31.22600, 31.32335, 31.42565, 31.63670, 31.86450, 31.98495,
                      32.09880, 32.21270, 32.32160, 32.43710, 32.84710, 33.00520, 33.34840, 33.54050,
                      35.13650, 35.36260, 35.60515, 35.86750, 36.15480, 36.44025, 36.72900, 37.03840,
                      37.36180, 37.70665, 38.07385, 38.43190, 38.79325, 39.18085, 39.58675, 40.02235,
                      40.48815, 42.39005, 42.87680, 43.12840])

exp_L_biased = np.array([18.900000, 19.195936, 19.717777, 20.212025, 20.706639, 21.248655, 21.900144,
                         22.631573, 23.302502, 23.909028, 24.529802, 25.156964, 25.795380, 26.431464,
                         27.003940, 27.539635, 28.067340, 28.535612, 30.617764, 30.882266, 31.466952,
                         31.861969, 32.093136, 32.459774, 32.673288, 32.867804, 33.160906, 33.341295,
                         33.527623, 33.830927, 34.153409, 34.361876, 34.564017, 34.766965, 34.965258,
                         35.171439, 35.698452, 35.953316, 36.411269, 36.705790, 38.541425, 38.879233,
                         39.236527, 39.617136, 40.026919, 40.436335, 40.851101, 41.290592, 41.747543,
                         42.230411, 42.740381, 43.242190, 43.749815, 44.289231, 44.851644, 45.450152,
                         46.085565, 48.362099, 49.030668, 49.432551])

# Filter out NaN values for velocity data
valid_mask = ~np.isnan(exp_v)
exp_t_valid = exp_t[valid_mask]
exp_v_valid = exp_v[valid_mask]
exp_L_biased_valid = exp_L_biased[valid_mask]

# Measurement range info
L_measurement_start = 18.6  # cm - where velocity measurement started
L_measurement_end = L_max   # cm - end of measurements (at outlet)

print("=" * 60)
print("GEOMETRY PARAMETERS")
print("=" * 60)
print(f"Segment lengths: {L_seg}")
print(f"Slopes: {s_seg}")
print(f"Intercepts: {c_seg}")
print(f"Cumulative S: {S}")
print(f"S_W = {S_W:.2f} cm")
print(f"L_max = {L_max:.2f} cm")
print()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_segment(L):
    """Return segment index (0-based) for position L."""
    for i in range(n_segments):
        if S[i] <= L <= S[i+1]:
            return i
    return n_segments - 1

def h_of_L(L):
    """Centreline elevation at position L."""
    i = get_segment(L)
    return c_seg[i] + s_seg[i] * L

def h_of_L_vec(L_arr):
    """Vectorized version of h_of_L."""
    return np.array([h_of_L(L) for L in L_arr])

def driving_head(L, h_c=h_c0):
    """Driving head Delta_h = h_c - h(L)."""
    return h_c - h_of_L(L)

def driving_force(L, h_c=h_c0):
    """Driving force F = rho * g * A * (h_c - h(L))."""
    return rho * g * A_pipe * driving_head(L, h_c)

def acceleration(L, h_c=h_c0):
    """Acceleration a = g * (h_c - h(L)) / L."""
    return g * driving_head(L, h_c) / L

# =============================================================================
# ENERGY INTEGRALS
# =============================================================================

def Phi(a, b, c, s, h_c=h_c0):
    """Contribution to energy integral from interval [a,b] with h(r) = c + s*r."""
    if b <= a:
        return 0.0
    return (h_c - c) * np.log(b / a) - s * (b - a)

def I_frictionless(L):
    """Frictionless energy integral I(L)."""
    if L <= S1:
        return 0.0

    total = 0.0
    k = get_segment(L)

    # Full segments from S1 to S_{k-1}
    for j in range(1, k):  # segments 1 to k-1 (0-indexed: 1, 2, ..., k-1)
        total += Phi(S[j], S[j+1], c_seg[j], s_seg[j])

    # Partial segment k from S[k] to L
    if k >= 1:
        start = max(S[k], S1)
        total += Phi(start, L, c_seg[k], s_seg[k])

    return total

def drawdown_penalty(L):
    """Drawdown penalty integral: (L - S1) - S1 * ln(L/S1)."""
    if L <= S1:
        return 0.0
    return (L - S1) - S1 * np.log(L / S1)

def I_drawdown(L, area_ratio=A_ratio):
    """Energy integral with drawdown: I_dd(L) = I(L) - (A/A0) * penalty."""
    return I_frictionless(L) - area_ratio * drawdown_penalty(L)

def integrating_factor(L, f=f0, K=K_total):
    """Integrating factor mu(L) for friction-corrected integral."""
    if L <= S1:
        return 1.0
    return (L / S1)**K * np.exp(f * (L - S1) / D_pipe)

def I_friction(L, f=f0, K=K_total):
    """Friction-corrected energy integral I_f(L) using numerical integration."""
    if L <= S1:
        return 0.0

    mu_L = integrating_factor(L, f, K)

    def integrand(r):
        mu_r = integrating_factor(r, f, K)
        return mu_r * (h_c0 - h_of_L(r)) / r

    result, _ = quad(integrand, S1, L, limit=100)
    return result / mu_L

# =============================================================================
# CHURCHILL FRICTION CORRELATION
# =============================================================================

def churchill_f(Re, eps_D=epsilon_D):
    """Churchill correlation for Darcy friction factor."""
    if Re < 1e-10:
        return 64.0 / 1e-10  # Avoid division by zero

    A_c = (2.457 * np.log(1.0 / ((7.0/Re)**0.9 + 0.27 * eps_D)))**16
    B_c = (37530.0 / Re)**16

    f = 8 * ((8.0/Re)**12 + 1.0/(A_c + B_c)**1.5)**(1.0/12.0)
    return f

def colebrook_f(Re, eps_D=epsilon_D, tol=1e-8, max_iter=50):
    """Colebrook-White equation (implicit, solved iteratively)."""
    if Re < 4000:
        return np.nan  # Not valid for laminar/transitional

    # Initial guess from Haaland
    f = (1.0 / (-1.8 * np.log10((eps_D/3.7)**1.11 + 6.9/Re)))**2

    for _ in range(max_iter):
        rhs = -2.0 * np.log10(eps_D/3.7 + 2.51/(Re * np.sqrt(f)))
        f_new = 1.0 / rhs**2
        if abs(f_new - f) < tol:
            return f_new
        f = f_new

    return f

# =============================================================================
# ODE SOLVER FOR FULL DYNAMICS
# =============================================================================

def filling_ode(t, y):
    """ODE system for filling phase: y = [L, v]."""
    L, v = y

    if L <= S1:
        L = S1 + 1e-6
    if v < 0:
        v = 0

    # Container level with drawdown
    h_c = h_c0 - A_ratio * (L - S1)

    # Driving head
    dh = h_c - h_of_L(L)

    # Friction factor
    Re = abs(v) * D_pipe / nu
    f = churchill_f(Re)

    # Acceleration
    dv_dt = g * dh / L - (f / D_pipe + K_total / L) * v**2 / 2

    return [v, dv_dt]

def draining_ode(t, y, L_full=L_max):
    """ODE system for draining phase: y = [h_c, v]."""
    h_c, v = y

    if v < 0:
        v = 0

    h_outlet = nodes_h[4]  # h_4 = 0

    # Siphon head
    dh = h_c - h_outlet
    if dh < 0:
        dh = 0

    # Friction factor
    Re = abs(v) * D_pipe / nu
    f = churchill_f(Re)

    # Velocity equation
    friction_term = f * L_full / D_pipe + K_total
    dv_dt = g * dh / L_full - friction_term * v**2 / (2 * L_full)

    # Container level
    dh_c_dt = -A_ratio * v

    return [dh_c_dt, dv_dt]

def solve_filling():
    """Solve the filling ODE from S1 to S4."""
    # Initial conditions
    y0 = [S1 + 0.01, 0.01]  # Small perturbation to start

    # Event: front reaches outlet
    def event_outlet(t, y):
        return y[0] - S4
    event_outlet.terminal = True
    event_outlet.direction = 1

    # Solve
    sol = solve_ivp(filling_ode, [0, 20], y0,
                    events=event_outlet,
                    dense_output=True,
                    max_step=0.01)

    return sol

def solve_draining(h_c_start, v_start, t_max=5.0):
    """Solve the draining ODE."""
    y0 = [h_c_start, v_start]

    # Event: container level reaches inlet or outlet level
    def event_empty(t, y):
        return y[0] - nodes_h[0]  # Stop when h_c = h_0
    event_empty.terminal = True
    event_empty.direction = -1

    sol = solve_ivp(lambda t, y: draining_ode(t, y, L_max),
                    [0, t_max], y0,
                    events=event_empty,
                    dense_output=True,
                    max_step=0.01)

    return sol

# =============================================================================
# FIGURE 2: Centreline elevation h(L)
# =============================================================================

def figure2_centreline():
    """Generate Figure 2: Centreline elevation h(L) vs arclength."""
    fig, ax = plt.subplots(figsize=(9, 5))

    L_arr = np.linspace(0, L_max, 500)
    h_arr = h_of_L_vec(L_arr)

    # Plot centreline
    ax.plot(L_arr, h_arr, 'b-', linewidth=2, label='$h(L)$')

    # Water level
    ax.axhline(h_c0, color='gray', linestyle='--', linewidth=1.5, label='$h_c^{(0)} = 20$ cm')

    # Shade regions
    # Below waterline (blue) - driving force positive
    L_below = L_arr[h_arr <= h_c0]
    h_below = h_arr[h_arr <= h_c0]
    if len(L_below) > 0:
        ax.fill_between(L_arr, h_arr, h_c0, where=(h_arr <= h_c0),
                        alpha=0.2, color='blue', label='$F > 0$ (accelerating)')

    # Above waterline (red) - driving force negative
    ax.fill_between(L_arr, h_arr, h_c0, where=(h_arr > h_c0),
                    alpha=0.2, color='red', label='$F < 0$ (decelerating)')

    # Mark nodes
    for i, (s, h, label) in enumerate(zip(S, nodes_h, ['A', 'B', 'C', 'D', 'E'])):
        ax.plot(s, h, 'ko', markersize=8)
        offset = (5, 10) if label not in ['C', 'E'] else (5, -15)
        ax.annotate(f'${label}$', (s, h), textcoords='offset points',
                   xytext=offset, fontsize=12, fontweight='bold')

    # Mark point W
    ax.plot(S_W, h_c0, 'rs', markersize=10)
    ax.annotate('$W$', (S_W, h_c0), textcoords='offset points',
               xytext=(8, 5), fontsize=12, fontweight='bold', color='red')

    ax.set_xlabel('Arclength $L$ (cm)')
    ax.set_ylabel('Elevation $h$ (cm)')
    ax.set_xlim(0, L_max + 2)
    ax.set_ylim(-2, 28)
    ax.legend(loc='upper right')
    ax.set_title('Centreline Elevation Profile')

    plt.tight_layout()
    plt.savefig('figure2_centreline.pdf', bbox_inches='tight')
    plt.savefig('figure2_centreline.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 2 saved.")

# =============================================================================
# FIGURE 3: Driving force and acceleration (two panels)
# =============================================================================

def figure3_force_acceleration():
    """Generate Figure 3: Two-panel driving force and acceleration."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    L_arr = np.linspace(S1 + 0.1, L_max, 500)

    # Driving force (in dynes, convert to more readable units)
    F_arr = np.array([driving_force(L) for L in L_arr])
    F_arr_N = F_arr / 1e5  # Convert to Newtons (approximately)

    # Acceleration
    a_arr = np.array([acceleration(L) for L in L_arr])

    # Top panel: Force
    ax1.plot(L_arr, F_arr / 1000, 'b-', linewidth=2)  # Convert to reasonable units
    ax1.axhline(0, color='k', linestyle='-', linewidth=0.5)
    ax1.fill_between(L_arr, F_arr/1000, 0, where=(F_arr > 0), alpha=0.3, color='blue')
    ax1.fill_between(L_arr, F_arr/1000, 0, where=(F_arr < 0), alpha=0.3, color='red')

    ax1.set_ylabel('Driving Force $F$ (g$\\cdot$cm/s$^2$ $\\times 10^3$)')
    ax1.set_title('Driving Force: $F = \\rho g A [h_c - h(L)]$')

    # Mark key points
    for s, label in [(S[2], 'C'), (S[3], 'D'), (S_W, 'W')]:
        ax1.axvline(s, color='gray', linestyle=':', alpha=0.5)

    # Bottom panel: Acceleration
    ax2.plot(L_arr, a_arr, 'r-', linewidth=2)
    ax2.axhline(0, color='k', linestyle='-', linewidth=0.5)
    ax2.fill_between(L_arr, a_arr, 0, where=(a_arr > 0), alpha=0.3, color='blue')
    ax2.fill_between(L_arr, a_arr, 0, where=(a_arr < 0), alpha=0.3, color='red')

    ax2.set_xlabel('Arclength $L$ (cm)')
    ax2.set_ylabel('Acceleration $a$ (cm/s$^2$)')
    ax2.set_title('Acceleration: $a = g[h_c - h(L)]/L$ (note $1/L$ suppression)')

    # Mark key points
    for s, label in [(S[2], 'C'), (S[3], 'D'), (S_W, 'W')]:
        ax2.axvline(s, color='gray', linestyle=':', alpha=0.5)
        y_pos = ax2.get_ylim()[1] * 0.9
        ax2.annotate(f'${label}$', (s, y_pos), fontsize=10, ha='center')

    # Add annotation about 1/L effect
    ax2.annotate('Max force at C,\nbut acceleration\nsuppressed by $1/L$',
                xy=(S[2], acceleration(S[2])),
                xytext=(S[2] + 10, acceleration(S[2]) + 100),
                arrowprops=dict(arrowstyle='->', color='gray'),
                fontsize=9)

    plt.tight_layout()
    plt.savefig('figure3_force_acceleration.pdf', bbox_inches='tight')
    plt.savefig('figure3_force_acceleration.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 3 saved.")

# =============================================================================
# FIGURE 4: Energy integral I(L) - frictionless
# =============================================================================

def figure4_energy_integral():
    """Generate Figure 4: Frictionless energy integral I(L)."""
    fig, ax = plt.subplots(figsize=(9, 5))

    L_arr = np.linspace(S1, L_max, 500)
    I_arr = np.array([I_frictionless(L) for L in L_arr])

    ax.plot(L_arr, I_arr, 'b-', linewidth=2, label='$I(L)$ (frictionless)')
    ax.axhline(0, color='k', linestyle='-', linewidth=0.5)

    # Mark key points
    I_at_W = I_frictionless(S_W)
    I_at_crest = I_frictionless(S[3])

    ax.plot(S_W, I_at_W, 'rs', markersize=10, label=f'$I(S_W) = {I_at_W:.2f}$ cm')
    ax.plot(S[3], I_at_crest, 'go', markersize=8, label=f'$I(S_3) = {I_at_crest:.2f}$ cm')

    # Vertical lines at key positions
    for s, label in [(S[1], 'B'), (S[2], 'C'), (S[3], 'D'), (S_W, 'W')]:
        ax.axvline(s, color='gray', linestyle=':', alpha=0.5)
        ax.annotate(f'${label}$', (s, ax.get_ylim()[1] * 0.95), fontsize=10, ha='center')

    # Shade where h > h_c (above waterline)
    # Find crossings
    ax.axvspan(46.5, S_W, alpha=0.1, color='red', label='Front above waterline')

    ax.set_xlabel('Arclength $L$ (cm)')
    ax.set_ylabel('Energy Integral $I(L)$ (cm)')
    ax.set_title('Frictionless Energy Integral')
    ax.legend(loc='upper left')
    ax.set_xlim(S1 - 2, L_max + 2)

    plt.tight_layout()
    plt.savefig('figure4_energy_integral.pdf', bbox_inches='tight')
    plt.savefig('figure4_energy_integral.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 4 saved.")

# =============================================================================
# FIGURE 5: Container drawdown h_c(L)
# =============================================================================

def figure5_drawdown():
    """Generate Figure 5: Container level h_c(L) for different area ratios."""
    fig, ax = plt.subplots(figsize=(9, 5))

    L_arr = np.linspace(S1, L_max, 500)

    # Two area ratios
    ratios = [0.0052, 0.05]
    labels = ['$A/A_0 = 0.0052$ (worked example)', '$A/A_0 = 0.05$ (smaller container)']
    styles = ['-', '--']

    for ratio, label, style in zip(ratios, labels, styles):
        h_c_arr = h_c0 - ratio * (L_arr - S1)
        ax.plot(L_arr, h_c_arr, style, linewidth=2, label=label)

    # Initial level
    ax.axhline(h_c0, color='gray', linestyle=':', alpha=0.5, label='$h_c^{(0)} = 20$ cm')

    # Mark S_W and S_4
    ax.axvline(S_W, color='red', linestyle=':', alpha=0.7)
    ax.axvline(S4, color='green', linestyle=':', alpha=0.7)
    ax.annotate('$S_W$', (S_W, 21), fontsize=10, ha='center', color='red')
    ax.annotate('$S_4$', (S4, 21), fontsize=10, ha='center', color='green')

    # Drawdown amounts
    dd_small = 0.0052 * (S4 - S1)
    dd_large = 0.05 * (S4 - S1)
    ax.annotate(f'$\\Delta h_c = {dd_small:.2f}$ cm', (S4 + 1, h_c0 - dd_small), fontsize=9)
    ax.annotate(f'$\\Delta h_c = {dd_large:.1f}$ cm', (S4 + 1, h_c0 - dd_large), fontsize=9)

    ax.set_xlabel('Slug Position $L$ (cm)')
    ax.set_ylabel('Container Level $h_c$ (cm)')
    ax.set_title('Container Drawdown')
    ax.legend(loc='lower left')
    ax.set_xlim(S1 - 2, L_max + 10)
    ax.set_ylim(15, 21)

    plt.tight_layout()
    plt.savefig('figure5_drawdown.pdf', bbox_inches='tight')
    plt.savefig('figure5_drawdown.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 5 saved.")

# =============================================================================
# FIGURE 6: Friction factor f(Re)
# =============================================================================

def figure6_friction():
    """Generate Figure 6: Friction factor vs Reynolds number."""
    fig, ax = plt.subplots(figsize=(9, 5))

    Re_arr = np.logspace(1, 5, 500)

    # Churchill correlation
    f_churchill = np.array([churchill_f(Re) for Re in Re_arr])
    ax.loglog(Re_arr, f_churchill, 'b-', linewidth=2, label='Churchill correlation')

    # Laminar: f = 64/Re
    Re_lam = Re_arr[Re_arr < 2500]
    f_lam = 64 / Re_lam
    ax.loglog(Re_lam, f_lam, 'g--', linewidth=1.5, label='$f = 64/\\text{Re}$ (laminar)')

    # Shade the Re range for worked example (0 to ~12000)
    ax.axvspan(10, 12000, alpha=0.15, color='orange', label='Filling Re range (worked example)')

    # Constant f0
    ax.axhline(f0, color='red', linestyle=':', linewidth=1.5, label=f'$f_0 = {f0}$ (constant approx.)')

    # Mark regimes
    ax.axvline(2300, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(4000, color='gray', linestyle='--', alpha=0.5)
    ax.annotate('Laminar', (500, 0.15), fontsize=10)
    ax.annotate('Transition', (2800, 0.15), fontsize=9, rotation=90)
    ax.annotate('Turbulent', (20000, 0.015), fontsize=10)

    ax.set_xlabel('Reynolds Number Re')
    ax.set_ylabel('Darcy Friction Factor $f$')
    ax.set_title('Friction Factor: Churchill Correlation')
    ax.legend(loc='upper right')
    ax.set_xlim(10, 1e5)
    ax.set_ylim(0.01, 1)

    plt.tight_layout()
    plt.savefig('figure6_friction.pdf', bbox_inches='tight')
    plt.savefig('figure6_friction.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 6 saved.")

# =============================================================================
# FIGURE 7: Comparison of three energy integrals
# =============================================================================

def figure7_comparison():
    """Generate Figure 7: Comparison of I, I_dd, I_f."""
    fig, ax = plt.subplots(figsize=(9, 5))

    L_arr = np.linspace(S1, L_max, 200)

    I_arr = np.array([I_frictionless(L) for L in L_arr])
    I_dd_arr = np.array([I_drawdown(L) for L in L_arr])
    I_f_arr = np.array([I_friction(L) for L in L_arr])

    ax.plot(L_arr, I_arr, 'b-', linewidth=2, label='$I(L)$ (frictionless)')
    ax.plot(L_arr, I_dd_arr, 'g--', linewidth=2, label='$I_{\\text{dd}}(L)$ (with drawdown)')
    ax.plot(L_arr, I_f_arr, 'r-.', linewidth=2, label='$I_f(L)$ (with friction)')

    ax.axhline(0, color='k', linestyle='-', linewidth=0.5)

    # Mark values at S_W
    I_W = I_frictionless(S_W)
    I_dd_W = I_drawdown(S_W)
    I_f_W = I_friction(S_W)

    ax.axvline(S_W, color='gray', linestyle=':', alpha=0.7)
    ax.plot(S_W, I_W, 'bs', markersize=8)
    ax.plot(S_W, I_dd_W, 'g^', markersize=8)
    ax.plot(S_W, I_f_W, 'ro', markersize=8)

    # Annotations
    ax.annotate(f'$I(S_W) = {I_W:.2f}$ cm', (S_W + 1, I_W + 0.3), fontsize=9, color='blue')
    ax.annotate(f'$I_{{\\text{{dd}}}}(S_W) = {I_dd_W:.2f}$ cm', (S_W + 1, I_dd_W - 0.5), fontsize=9, color='green')
    ax.annotate(f'$I_f(S_W) \\approx {I_f_W:.1f}$ cm', (S_W + 1, I_f_W - 0.5), fontsize=9, color='red')

    ax.annotate('$S_W$', (S_W, -1), fontsize=10, ha='center')

    # Mark key positions
    for s, label in [(S[2], 'C'), (S[3], 'D')]:
        ax.axvline(s, color='lightgray', linestyle=':', alpha=0.5)

    ax.set_xlabel('Arclength $L$ (cm)')
    ax.set_ylabel('Energy Integral (cm)')
    ax.set_title('Comparison of Energy Integrals: Hierarchy of Bounds')
    ax.legend(loc='upper left')
    ax.set_xlim(S1 - 2, L_max + 5)

    plt.tight_layout()
    plt.savefig('figure7_comparison.pdf', bbox_inches='tight')
    plt.savefig('figure7_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 7 saved.")

# =============================================================================
# FIGURE 8: Velocity v(L) comparison
# =============================================================================

def figure8_velocity():
    """Generate Figure 8: Velocity from all models with error analysis."""
    fig, ax = plt.subplots(figsize=(9, 5))

    # Solve ODE
    sol_filling = solve_filling()

    L_arr = np.linspace(S1 + 0.5, min(sol_filling.y[0].max(), S4), 200)

    # Analytical predictions
    v_frictionless = np.array([np.sqrt(2 * g * max(I_frictionless(L), 0)) for L in L_arr])
    v_drawdown = np.array([np.sqrt(2 * g * max(I_drawdown(L), 0)) for L in L_arr])
    v_friction = np.array([np.sqrt(2 * g * max(I_friction(L), 0)) for L in L_arr])

    # ODE solution interpolated
    v_ode = np.array([sol_filling.sol(t)[1] for t in
                      np.interp(L_arr, sol_filling.y[0], sol_filling.t)])

    # For proper interpolation, use position-based
    L_ode = sol_filling.y[0]
    v_ode_raw = sol_filling.y[1]
    v_ode = np.interp(L_arr, L_ode, v_ode_raw)

    ax.plot(L_arr, v_frictionless, 'b-', linewidth=2, label='Frictionless: $\\sqrt{2gI}$')
    ax.plot(L_arr, v_drawdown, 'g--', linewidth=2, label='With drawdown: $\\sqrt{2gI_{\\text{dd}}}$')
    ax.plot(L_arr, v_friction, 'r-.', linewidth=2, label='Constant friction: $\\sqrt{2gI_f}$')
    ax.plot(L_arr, v_ode, 'k-', linewidth=2.5, label='Full ODE (numerical)')

    # Error analysis at key points
    key_positions = [S[2], S[3], S_W]
    key_labels = ['C', 'D', 'W']

    for pos, label in zip(key_positions, key_labels):
        if pos > L_arr.max():
            continue
        idx = np.argmin(np.abs(L_arr - pos))
        v_ode_pt = v_ode[idx]
        v_fric_pt = v_frictionless[idx]

        if v_ode_pt > 0:
            error_pct = (v_fric_pt - v_ode_pt) / v_ode_pt * 100
            ax.annotate(f'{label}: +{error_pct:.0f}%',
                       (pos, v_fric_pt),
                       textcoords='offset points',
                       xytext=(10, 5), fontsize=8, color='blue')

    # Mark S_W
    ax.axvline(S_W, color='gray', linestyle=':', alpha=0.5)
    ax.annotate('$S_W$', (S_W, 10), fontsize=10, ha='center')

    ax.set_xlabel('Arclength $L$ (cm)')
    ax.set_ylabel('Velocity $v$ (cm/s)')
    ax.set_title('Velocity Comparison: Analytical Bounds vs. Numerical Solution')
    ax.legend(loc='upper left')
    ax.set_xlim(S1, L_max)
    ax.set_ylim(0, 150)

    plt.tight_layout()
    plt.savefig('figure8_velocity.pdf', bbox_inches='tight')
    plt.savefig('figure8_velocity.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 8 saved.")

# =============================================================================
# FIGURE 9: Time evolution L(t) and v(t)
# =============================================================================

def figure9_time():
    """Generate Figure 9: Position and velocity vs time."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    # Solve filling
    sol_filling = solve_filling()
    t_fill = sol_filling.t
    L_fill = sol_filling.y[0]
    v_fill = sol_filling.y[1]

    t_fill_end = t_fill[-1]

    # Get final conditions for draining
    h_c_end = h_c0 - A_ratio * (L_fill[-1] - S1)
    v_end = v_fill[-1]

    # Solve draining (show only ~0.5s of draining, less than filling)
    drain_duration = min(0.5, t_fill_end * 0.5)
    sol_drain = solve_draining(h_c_end, v_end, t_max=drain_duration)
    t_drain = sol_drain.t + t_fill_end
    h_c_drain = sol_drain.y[0]
    v_drain = sol_drain.y[1]

    # Position during draining is constant at L_max
    L_drain = np.full_like(t_drain, L_max)

    # Combine
    t_all = np.concatenate([t_fill, t_drain])
    L_all = np.concatenate([L_fill, L_drain])
    v_all = np.concatenate([v_fill, v_drain])

    # TOP PANEL: Position L(t)
    ax1.plot(t_fill, L_fill, 'b-', linewidth=2, label='Filling phase')
    ax1.plot(t_drain, L_drain, 'b--', linewidth=2, label='Draining phase (pipe full)')
    ax1.set_ylabel('Position $L$ (cm)')
    ax1.set_ylim(0, L_max + 5)

    # Mark key positions on L axis
    key_positions = [(S[1], 'B'), (S[2], 'C'), (S[3], 'D'), (S_W, 'W'), (S4, 'E (outlet)')]
    for pos, label in key_positions:
        ax1.axhline(pos, color='gray', linestyle=':', alpha=0.4, linewidth=0.8)
        ax1.annotate(label, (0.02, pos + 1), fontsize=8, color='gray')

    # Mark transition
    ax1.axvline(t_fill_end, color='green', linestyle='-', alpha=0.7, linewidth=1.5)
    ax1.legend(loc='lower right')
    ax1.set_title('Time Evolution: Filling and Draining Phases')

    # BOTTOM PANEL: Velocity v(t)
    ax2.plot(t_fill, v_fill, 'r-', linewidth=2, label='Filling phase')
    ax2.plot(t_drain, v_drain, 'r--', linewidth=2, label='Draining phase')
    ax2.set_xlabel('Time $t$ (s)')
    ax2.set_ylabel('Velocity $v$ (cm/s)')
    ax2.set_ylim(0, max(v_all) * 1.15)

    # Mark transition
    ax2.axvline(t_fill_end, color='green', linestyle='-', alpha=0.7, linewidth=1.5)
    ax2.annotate('Pipe fills\ncompletely', (t_fill_end + 0.03, max(v_all) * 0.8),
                fontsize=9, color='green')

    # Find and mark key events
    # Find time when slug reaches C (low point, max velocity during filling)
    idx_C = np.argmin(np.abs(L_fill - S[2]))
    t_C = t_fill[idx_C]
    v_C = v_fill[idx_C]
    ax2.plot(t_C, v_C, 'ko', markersize=6)
    ax2.annotate(f'C: v={v_C:.0f} cm/s', (t_C + 0.02, v_C), fontsize=8)

    # Find time when slug reaches D (crest)
    idx_D = np.argmin(np.abs(L_fill - S[3]))
    t_D = t_fill[idx_D]
    v_D = v_fill[idx_D]
    ax2.plot(t_D, v_D, 'ko', markersize=6)
    ax2.annotate(f'D: v={v_D:.0f} cm/s', (t_D + 0.02, v_D - 5), fontsize=8)

    # Find time when slug reaches W
    idx_W = np.argmin(np.abs(L_fill - S_W))
    t_W = t_fill[idx_W]
    v_W = v_fill[idx_W]
    ax2.plot(t_W, v_W, 'rs', markersize=7)
    ax2.annotate(f'W: v={v_W:.0f} cm/s', (t_W + 0.02, v_W + 3), fontsize=8, color='red')

    ax2.legend(loc='upper right')

    ax2.set_xlim(0, t_all[-1] + 0.05)

    plt.tight_layout()
    plt.savefig('figure9_time.pdf', bbox_inches='tight')
    plt.savefig('figure9_time.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 9 saved.")

# =============================================================================
# FIGURE 10: Validity regime diagrams (3 panels)
# =============================================================================

def figure10_validity():
    """Generate Figure 10: Validity regime diagrams."""
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))

    # Panel (a): D vs (h_3 - h_c) - cavitation and capillarity
    ax = axes[0]

    D_range = np.linspace(1, 30, 100)  # mm
    h_crest_range = np.linspace(0, 50, 100)  # cm

    D_grid, h_grid = np.meshgrid(D_range, h_crest_range)

    # Cavitation limit: h_crest < 1000 cm (10 m) - v^2/2g
    # Assume v ~ 100 cm/s, so v^2/2g ~ 5 cm
    cavitation_limit = 1000 - 5  # cm

    # Capillarity limit: Bo > 1 means D > sqrt(gamma/(rho*g)) ~ 2.7 mm
    D_cap_limit = np.sqrt(gamma / (rho * g)) * 10  # convert to mm

    # Shade valid region
    valid = (h_grid < cavitation_limit) & (D_grid > D_cap_limit)
    ax.contourf(D_grid, h_grid, valid.astype(int), levels=[0.5, 1.5],
                colors=['lightgreen'], alpha=0.3)

    # Cavitation boundary (way above plot range, so just note it)
    ax.axhline(100, color='red', linestyle='--', label='Cavitation limit (~10 m)')

    # Capillarity boundary
    ax.axvline(D_cap_limit, color='blue', linestyle='--', label=f'Capillarity limit (Bo=1)')
    ax.axvspan(0, D_cap_limit, alpha=0.2, color='blue')

    # Mark worked example
    ax.plot(10, 4, 'ko', markersize=12, markerfacecolor='yellow',
            markeredgewidth=2, label='Worked example')

    ax.set_xlabel('Diameter $D$ (mm)')
    ax.set_ylabel('Crest height $h_3 - h_c$ (cm)')
    ax.set_title('(a) Diameter vs. Crest Height')
    ax.legend(loc='upper right', fontsize=8)
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 50)
    ax.annotate('Capillarity\ndominates', (1.5, 25), fontsize=8, color='blue')
    ax.annotate('Valid\nregion', (15, 25), fontsize=10, color='green')

    # Panel (b): Re vs Ca
    ax = axes[1]

    Re_range = np.logspace(2, 5, 100)
    Ca_range = np.logspace(-4, 0, 100)

    Re_grid, Ca_grid = np.meshgrid(Re_range, Ca_range)

    # Valid: Re > 2000 (turbulent, quasi-steady valid) and Ca < 0.1
    valid = (Re_grid > 2000) & (Ca_grid < 0.1)
    ax.contourf(Re_grid, Ca_grid, valid.astype(int), levels=[0.5, 1.5],
                colors=['lightgreen'], alpha=0.3)

    ax.axvline(2000, color='orange', linestyle='--', label='Re = 2000 (turbulent)')
    ax.axhline(0.1, color='purple', linestyle='--', label='Ca = 0.1')

    # Shade invalid regions
    ax.axvspan(100, 2000, alpha=0.15, color='orange')
    ax.axhspan(0.1, 1, alpha=0.15, color='purple')

    # Mark worked example: Re ~ 10000, Ca ~ 0.01
    ax.plot(10000, 0.01, 'ko', markersize=12, markerfacecolor='yellow',
            markeredgewidth=2, label='Worked example')

    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlabel('Reynolds Number Re')
    ax.set_ylabel('Capillary Number Ca')
    ax.set_title('(b) Re vs. Ca')
    ax.legend(loc='upper left', fontsize=8)
    ax.set_xlim(100, 1e5)
    ax.set_ylim(1e-4, 1)
    ax.annotate('Laminar/\ntransition', (500, 0.001), fontsize=8, color='orange')
    ax.annotate('Capillary\neffects', (10000, 0.3), fontsize=8, color='purple')
    ax.annotate('Valid', (10000, 0.003), fontsize=10, color='green')

    # Panel (c): L/D vs Re
    ax = axes[2]

    LD_range = np.linspace(10, 200, 100)
    Re_range_c = np.logspace(2, 5, 100)

    LD_grid, Re_grid_c = np.meshgrid(LD_range, Re_range_c)

    # Entrance length: L_e/D ~ 10-20 for turbulent
    # Valid if L/D > L_e/D, i.e., L/D > 20 for turbulent
    # And Re > 2000
    valid = (LD_grid > 20) & (Re_grid_c > 2000)
    ax.contourf(LD_grid, Re_grid_c, valid.astype(int), levels=[0.5, 1.5],
                colors=['lightgreen'], alpha=0.3)

    ax.axhline(2000, color='orange', linestyle='--', label='Re = 2000')
    ax.axvline(20, color='brown', linestyle='--', label='$L/D = 20$ (entrance)')

    ax.axhspan(100, 2000, alpha=0.15, color='orange')
    ax.axvspan(10, 20, alpha=0.15, color='brown')

    # Worked example: L/D ~ 76/1 = 76
    ax.plot(76, 10000, 'ko', markersize=12, markerfacecolor='yellow',
            markeredgewidth=2, label='Worked example')

    ax.set_yscale('log')
    ax.set_xlabel('Length/Diameter $L/D$')
    ax.set_ylabel('Reynolds Number Re')
    ax.set_title('(c) $L/D$ vs. Re')
    ax.legend(loc='lower right', fontsize=8)
    ax.set_xlim(10, 200)
    ax.set_ylim(100, 1e5)
    ax.annotate('Entrance\neffects', (12, 20000), fontsize=8, color='brown')
    ax.annotate('Laminar', (100, 500), fontsize=8, color='orange')
    ax.annotate('Valid', (100, 20000), fontsize=10, color='green')

    plt.tight_layout()
    plt.savefig('figure10_validity.pdf', bbox_inches='tight')
    plt.savefig('figure10_validity.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure 10 saved.")

# =============================================================================
# FIGURE A1: Friction correlation comparison
# =============================================================================

def figureA1_friction_comparison():
    """Generate Figure A1: Comparison of friction correlations."""
    fig, ax = plt.subplots(figsize=(9, 5))

    Re_arr = np.logspace(1, 5, 500)

    # Churchill
    f_churchill = np.array([churchill_f(Re) for Re in Re_arr])
    ax.loglog(Re_arr, f_churchill, 'b-', linewidth=2.5, label='Churchill (all regimes)')

    # Laminar: f = 64/Re
    f_laminar = 64 / Re_arr
    ax.loglog(Re_arr, f_laminar, 'g--', linewidth=1.5, label='$f = 64/\\text{Re}$ (laminar)')

    # Colebrook-White (turbulent only)
    Re_turb = Re_arr[Re_arr >= 4000]
    f_colebrook = np.array([colebrook_f(Re) for Re in Re_turb])
    ax.loglog(Re_turb, f_colebrook, 'r:', linewidth=2, label='Colebrook-White (turbulent)')

    # Mark regimes
    ax.axvline(2300, color='gray', linestyle='--', alpha=0.5)
    ax.axvline(4000, color='gray', linestyle='--', alpha=0.5)

    # Annotations
    ax.annotate('Laminar', (300, 0.2), fontsize=11)
    ax.annotate('Transition', (2800, 0.2), fontsize=9, rotation=90)
    ax.annotate('Turbulent', (30000, 0.015), fontsize=11)

    # Show agreement
    ax.annotate('Churchill matches\nlaminar exactly', (200, 0.4), fontsize=9,
               arrowprops=dict(arrowstyle='->', color='green'),
               xytext=(500, 0.6), color='green')
    ax.annotate('Churchill matches\nColebrook to ~1%', (30000, 0.025), fontsize=9,
               arrowprops=dict(arrowstyle='->', color='red'),
               xytext=(8000, 0.06), color='red')

    ax.set_xlabel('Reynolds Number Re')
    ax.set_ylabel('Darcy Friction Factor $f$')
    ax.set_title('Friction Correlation Comparison')
    ax.legend(loc='upper right')
    ax.set_xlim(10, 1e5)
    ax.set_ylim(0.01, 1)

    plt.tight_layout()
    plt.savefig('figureA1_friction_comparison.pdf', bbox_inches='tight')
    plt.savefig('figureA1_friction_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("Figure A1 saved.")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("Generating all figures for siphon-theory-5.tex")
    print("=" * 60)

    # Verify parameters
    print(f"\nKey values:")
    print(f"  I(S_W) = {I_frictionless(S_W):.2f} cm")
    print(f"  I_dd(S_W) = {I_drawdown(S_W):.2f} cm")
    print(f"  I_f(S_W) = {I_friction(S_W):.2f} cm")
    print(f"  v_frictionless at W = {np.sqrt(2*g*I_frictionless(S_W)):.1f} cm/s")
    print()

    # Generate all figures
    figure2_centreline()
    figure3_force_acceleration()
    figure4_energy_integral()
    figure5_drawdown()
    figure6_friction()
    figure7_comparison()
    figure8_velocity()
    figure9_time()
    figure10_validity()
    figureA1_friction_comparison()

    print("\n" + "=" * 60)
    print("All figures generated successfully!")
    print("=" * 60)
