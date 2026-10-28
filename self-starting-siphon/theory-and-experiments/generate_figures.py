"""
Generate all figures for siphon-theory-5.tex
"""

from __future__ import annotations

from pathlib import Path
import re

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.integrate import solve_ivp, quad
from scipy.optimize import brentq, minimize
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
# PATHS / DATA LOADING
# =============================================================================

ROOT_DIR = Path(__file__).resolve().parent
FIG_DIR = ROOT_DIR / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)
EXCEL_PATH = ROOT_DIR / "Exp-data.xlsx"


def save_figure(basename: str) -> None:
    """Save the current matplotlib figure as PDF+PNG into figures/."""
    plt.savefig(FIG_DIR / f"{basename}.pdf", bbox_inches="tight")
    plt.savefig(FIG_DIR / f"{basename}.png", dpi=150, bbox_inches="tight")


def _parse_first_float(value) -> float | None:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return None
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    if isinstance(value, str):
        match = re.search(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", value.replace(",", "."))
        if match:
            return float(match.group(0))
    return None


def load_setup_from_excel(excel_path: Path = EXCEL_PATH) -> dict:
    """Load geometry + setup parameters from Exp-data.xlsx (second sheet)."""
    if not excel_path.exists():
        raise FileNotFoundError(f"Experimental workbook not found: {excel_path}")

    xl = pd.ExcelFile(excel_path)
    df = xl.parse(xl.sheet_names[1])

    key_col = df.columns[0]
    v1_col = df.columns[1]
    v2_col = df.columns[2]

    nodes: dict[str, tuple[float, float]] = {}
    h_c0_val: float | None = None
    D_mm: float | None = None
    A0_cm2: float | None = None
    eps_D: float | None = None
    K_total: float | None = None

    for _, row in df.iterrows():
        key = row.get(key_col, None)
        if not isinstance(key, str):
            continue
        key_s = key.strip()

        if key_s in {"A", "B", "C", "D", "E", "W", "W'", "W′"}:
            x = _parse_first_float(row.get(v1_col, None))
            h = _parse_first_float(row.get(v2_col, None))
            if x is not None and h is not None:
                nodes[key_s] = (x, h)
                continue
            # A key such as "D" with no height is a pipe parameter, not a node.

        key_norm = key_s.lower().replace(" ", "")

        if key_norm.startswith("initialwaterlevel"):
            h_c0_val = _parse_first_float(row.get(v1_col, None))
            continue

        if key_s == "D":
            D_mm = _parse_first_float(row.get(v1_col, None))
            continue

        if key_s in {"ε/D", "e/D", "eps/D", "ε\\D"}:
            eps_D = _parse_first_float(row.get(v1_col, None))
            continue

        if key_s in {"Σk", "ΣK", "∑K", "∑k", "SumK", "sumK"} or ("k" in key_norm and ("σ" in key_norm or "∑" in key_norm)):
            K_total = _parse_first_float(row.get(v1_col, None))
            continue

        if key_s in {"A_0", "A0"}:
            A0_cm2 = _parse_first_float(row.get(v1_col, None))
            continue

    # Measured setup values must come from the workbook; silently substituting
    # defaults would let the figures drift away from the experiment.
    missing = [
        name
        for name, value in (
            ("geometry nodes A-E", nodes),
            ("initial water level", h_c0_val),
            ("tube diameter D", D_mm),
            ("reservoir area A_0", A0_cm2),
        )
        if not value
    ]
    if missing:
        raise ValueError(
            f"Could not read {', '.join(missing)} from {excel_path.name} (second sheet)."
        )

    return {
        "nodes": nodes,
        "h_c0_cm": float(h_c0_val),
        "D_cm": float(D_mm) / 10.0,  # mm -> cm
        "A0_cm2": float(A0_cm2),
        "epsilon_D_guess": float(eps_D) if eps_D is not None else 0.00035,
        "K_total_guess": float(K_total) if K_total is not None else 4.0,
    }


def load_experimental_timeseries(excel_path: Path = EXCEL_PATH) -> dict:
    """Load experimental time-series (first sheet)."""
    if not excel_path.exists():
        raise FileNotFoundError(f"Experimental workbook not found: {excel_path}")

    xl = pd.ExcelFile(excel_path)
    df = xl.parse(xl.sheet_names[0]).copy()
    df.columns = [str(c).strip() for c in df.columns]

    required = {"t(s)", "V(cm/s)", "L(cm)", "L_biased"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns in experimental sheet: {sorted(missing)}")

    for c in ["t(s)", "V(cm/s)", "L(cm)", "L_biased"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    valid = df["V(cm/s)"].notna() & df["L_biased"].notna()

    return {
        "t_s": df.loc[valid, "t(s)"].to_numpy(dtype=float),
        "v_cm_s": df.loc[valid, "V(cm/s)"].to_numpy(dtype=float),
        "L_raw_cm": df.loc[valid, "L(cm)"].to_numpy(dtype=float),
        "L_biased_cm": df.loc[valid, "L_biased"].to_numpy(dtype=float),
        "df": df,
    }

# =============================================================================
# PARAMETERS (from Experimental Data)
# =============================================================================

# Geometric parameters (cm) - from experimental workbook
setup = load_setup_from_excel()
nodes = setup["nodes"]

nodes_x = np.array([nodes["A"][0], nodes["B"][0], nodes["C"][0], nodes["D"][0], nodes["E"][0]], dtype=float)
nodes_h = np.array([nodes["A"][1], nodes["B"][1], nodes["C"][1], nodes["D"][1], nodes["E"][1]], dtype=float)
h_c0 = float(setup["h_c0_cm"])  # Initial water level (cm)

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
# Point W': where h(L) = h_c0 on segment 3 (index 2, ascending crossing)
S_Wp = (h_c0 - c_seg[2]) / s_seg[2]

# Physical parameters - from experimental setup
D_pipe = float(setup["D_cm"])  # Pipe diameter (cm)
A_pipe = np.pi * D_pipe**2 / 4  # Pipe cross-sectional area (cm^2)
A_container = float(setup["A0_cm2"])  # Container area (cm^2)
A_ratio = A_pipe / A_container  # Area ratio

epsilon_D_guess = float(setup["epsilon_D_guess"])  # Relative roughness (initial estimate)
K_total_guess = float(setup["K_total_guess"])  # Total minor loss coefficient (initial estimate)

# These get calibrated to the experiment below.
epsilon_D = epsilon_D_guess
K_total = K_total_guess
f0 = 0.035  # Representative friction factor for I_f (updated after calibration)

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

# Experimental time-series (video tracking) is loaded from Exp-data.xlsx.
# Use the biased arclength L_biased for all v(L) plots.

# Load experimental time-series from workbook
exp = load_experimental_timeseries()
exp_t_valid = exp["t_s"]
exp_v_valid = exp["v_cm_s"]
exp_L_raw_valid = exp["L_raw_cm"]
exp_L_biased_valid = exp["L_biased_cm"]

# Measurement range info (use biased L for all plots, per experimental note)
L_measurement_start = float(np.nanmin(exp_L_biased_valid))
L_measurement_end = float(np.nanmax(exp_L_biased_valid))


def print_setup_summary() -> None:
    print("=" * 60)
    print("SETUP SUMMARY (from Exp-data.xlsx)")
    print("=" * 60)
    print(f"h_c0 = {h_c0:.2f} cm")
    print(f"L_max = {L_max:.2f} cm")
    print(f"S = {np.array2string(S, precision=2)} cm")
    print(f"S_W' = {S_Wp:.2f} cm, S_W = {S_W:.2f} cm")
    print(f"D = {D_pipe:.3f} cm, A/A0 = {A_ratio:.6f}")
    print(f"epsilon/D guess = {epsilon_D_guess:g}, sum K guess = {K_total_guess:g}")
    print(f"Experimental points = {exp_L_biased_valid.size} (L_biased {L_measurement_start:.2f}..{L_measurement_end:.2f} cm)")
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

def integrating_factor(L, f=None, K=None):
    """Integrating factor mu(L) for friction-corrected integral."""
    if f is None:
        f = f0
    if K is None:
        K = K_total
    if L <= S1:
        return 1.0
    return (L / S1)**K * np.exp(f * (L - S1) / D_pipe)

def I_friction(L, f=None, K=None):
    """Friction-corrected energy integral I_f(L) using numerical integration."""
    if f is None:
        f = f0
    if K is None:
        K = K_total
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

def churchill_f(Re, eps_D=None):
    """Churchill correlation for Darcy friction factor."""
    if eps_D is None:
        eps_D = epsilon_D
    if Re < 1e-10:
        return 64.0 / 1e-10  # Avoid division by zero

    A_c = (2.457 * np.log(1.0 / ((7.0/Re)**0.9 + 0.27 * eps_D)))**16
    B_c = (37530.0 / Re)**16

    f = 8 * ((8.0/Re)**12 + 1.0/(A_c + B_c)**1.5)**(1.0/12.0)
    return f

def colebrook_f(Re, eps_D=None, tol=1e-8, max_iter=50):
    """Colebrook-White equation (implicit, solved iteratively)."""
    if eps_D is None:
        eps_D = epsilon_D
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

def solve_filling(t_max=20.0, max_step=0.01):
    """Solve the filling ODE from S1 to S4."""
    # Initial conditions
    y0 = [S1 + 0.01, 0.01]  # Small perturbation to start

    # Event: front reaches outlet
    def event_outlet(t, y):
        return y[0] - S4
    event_outlet.terminal = True
    event_outlet.direction = 1

    # Solve
    sol = solve_ivp(filling_ode, [0, t_max], y0,
                    events=event_outlet,
                    dense_output=True,
                    max_step=max_step)

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
# CALIBRATION: fit (epsilon/D, sum K) to experiment
# =============================================================================

def fit_loss_params():
    """
    Fit epsilon/D and sum K so the model v(L) matches the measured v(L_biased).

    Notes:
      - If the flow is mostly laminar (Re < ~2000), epsilon/D is weakly identifiable
        because f ≈ 64/Re is roughness-independent.
      - The objective enforces successful priming (front reaches outlet).
    """
    global epsilon_D, K_total, f0

    mask = np.isfinite(exp_L_biased_valid) & np.isfinite(exp_v_valid)
    mask &= (exp_L_biased_valid >= S1) & (exp_L_biased_valid <= L_max)

    exp_L = exp_L_biased_valid[mask]
    exp_v = exp_v_valid[mask]

    if exp_L.size < 6:
        raise ValueError("Not enough experimental points to fit loss parameters.")

    def transform(x):
        eps = float(np.clip(10 ** float(x[0]), 1e-6, 1e-2))
        K = float(np.clip(10 ** float(x[1]) - 1.0, 0.0, 20.0))
        return eps, K

    def objective(x):
        global epsilon_D, K_total
        eps, K = transform(x)

        # Set globals used by filling_ode/churchill_f
        epsilon_D = eps
        K_total = K

        sol = solve_filling(t_max=20.0, max_step=0.02)

        # Enforce priming (reach outlet)
        reached_outlet = sol.status == 1 and sol.y[0][-1] >= (L_max - 1e-3)
        if not reached_outlet:
            # Penalise non-priming parameter sets heavily.
            return 1e9 + (L_max - sol.y[0][-1]) * 1e7

        L_model = sol.y[0]
        v_model = sol.y[1]

        # Interpolate v(L) onto experimental biased L positions.
        if exp_L.max() > L_model.max():
            return 1e8 + (exp_L.max() - L_model.max()) * 1e6

        v_pred = np.interp(exp_L, L_model, v_model)
        mse = float(np.mean((v_pred - exp_v) ** 2))

        # Light regularisation to avoid unphysical drift (esp. epsilon/D in laminar regime).
        reg_eps = float(np.log10(eps / epsilon_D_guess) ** 2)
        reg_K = float(((K - K_total_guess) / max(K_total_guess, 1.0)) ** 2)
        return mse + 1.0 * reg_eps + 0.05 * reg_K

    x0 = np.array([np.log10(epsilon_D_guess), np.log10(K_total_guess + 1.0)], dtype=float)
    res = minimize(objective, x0, method="Nelder-Mead", options={"maxiter": 120, "xatol": 1e-4, "fatol": 1e-3})

    eps_fit, K_fit = transform(res.x)
    epsilon_D = eps_fit
    K_total = K_fit

    # Update representative f0 for constant-friction integral (median during filling, ignore tiny Re).
    sol = solve_filling(t_max=20.0, max_step=0.01)
    Re = np.abs(sol.y[1]) * D_pipe / nu
    f_arr = np.array([churchill_f(r) for r in Re])
    mask_f = Re > 200
    f0 = float(np.nanmedian(f_arr[mask_f])) if mask_f.any() else float(np.nanmedian(f_arr))

    return res

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
    ax.axhline(h_c0, color='gray', linestyle='--', linewidth=1.5,
               label=rf"$h_c^{{(0)}} = {h_c0:.1f}\,$cm")

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

    # Mark waterline crossings
    ax.plot(S_Wp, h_c0, marker='s', markersize=9, color='purple')
    ax.annotate(r"$W'$", (S_Wp, h_c0), textcoords='offset points',
               xytext=(8, -14), fontsize=12, fontweight='bold', color='purple')

    ax.plot(S_W, h_c0, marker='s', markersize=9, color='red')
    ax.annotate(r"$W$", (S_W, h_c0), textcoords='offset points',
               xytext=(8, 5), fontsize=12, fontweight='bold', color='red')

    ax.set_xlabel('Arclength $L$ (cm)')
    ax.set_ylabel('Elevation $h$ (cm)')
    ax.set_xlim(0, L_max + 2)
    y_min = min(nodes_h.min(), h_c0) - 2
    y_max = max(nodes_h.max(), h_c0) + 2
    ax.set_ylim(y_min, y_max)
    ax.legend(loc='upper right')
    ax.set_title('Centreline Elevation Profile')

    plt.tight_layout()
    save_figure('figure2_centreline')
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
    for s, label in [(S[2], 'C'), (S_Wp, "W'"), (S[3], 'D'), (S_W, 'W')]:
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
    for s, label in [(S[2], 'C'), (S_Wp, "W'"), (S[3], 'D'), (S_W, 'W')]:
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
    save_figure('figure3_force_acceleration')
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
    I_at_Wp = I_frictionless(S_Wp)
    I_at_W = I_frictionless(S_W)
    I_at_crest = I_frictionless(S[3])

    ax.plot(S_Wp, I_at_Wp, marker='s', markersize=8, color='purple',
            label=rf"$I(S_{{W'}}) = {I_at_Wp:.2f}\,$cm")
    ax.plot(S_W, I_at_W, marker='s', markersize=9, color='red',
            label=rf"$I(S_W) = {I_at_W:.2f}\,$cm")
    ax.plot(S[3], I_at_crest, 'go', markersize=8, label=rf"$I(S_3) = {I_at_crest:.2f}\,$cm")

    # Vertical lines at key positions
    for s, label in [(S[1], 'B'), (S[2], 'C'), (S_Wp, "W'"), (S[3], 'D'), (S_W, 'W')]:
        ax.axvline(s, color='gray', linestyle=':', alpha=0.5)
        ax.annotate(f'${label}$', (s, ax.get_ylim()[1] * 0.95), fontsize=10, ha='center')

    # Shade where h > h_c (above waterline)
    ax.axvspan(S_Wp, S_W, alpha=0.12, color='red', label='Front above waterline')

    ax.set_xlabel('Arclength $L$ (cm)')
    ax.set_ylabel('Energy Integral $I(L)$ (cm)')
    ax.set_title('Frictionless Energy Integral')
    ax.legend(loc='upper left')
    ax.set_xlim(S1 - 2, L_max + 2)

    plt.tight_layout()
    save_figure('figure4_energy_integral')
    plt.close()
    print("Figure 4 saved.")

# =============================================================================
# FIGURE 5: Container drawdown h_c(L)
# =============================================================================

def figure5_drawdown():
    """Generate Figure 5: Container level h_c(L) for different area ratios."""
    fig, ax = plt.subplots(figsize=(9, 5))

    L_arr = np.linspace(S1, L_max, 500)

    # Two area ratios: experiment + a deliberately larger one to illustrate the effect
    ratios = [A_ratio, 0.05]
    labels = [rf"$A/A_0 = {A_ratio:.4f}$ (experiment)", r"$A/A_0 = 0.05$ (smaller container)"]
    styles = ['-', '--']

    for ratio, label, style in zip(ratios, labels, styles):
        h_c_arr = h_c0 - ratio * (L_arr - S1)
        ax.plot(L_arr, h_c_arr, style, linewidth=2, label=label)

    # Initial level
    ax.axhline(h_c0, color='gray', linestyle=':', alpha=0.5,
               label=rf"$h_c^{{(0)}} = {h_c0:.1f}\,$cm")

    # Mark S_W and S_4
    ax.axvline(S_W, color='red', linestyle=':', alpha=0.7)
    ax.axvline(S4, color='green', linestyle=':', alpha=0.7)
    y_annot = h_c0 + 0.4
    ax.annotate('$S_W$', (S_W, y_annot), fontsize=10, ha='center', color='red')
    ax.annotate('$S_4$', (S4, y_annot), fontsize=10, ha='center', color='green')

    # Drawdown amounts
    dd_exp = A_ratio * (S4 - S1)
    dd_large = 0.05 * (S4 - S1)
    ax.annotate(rf"$\Delta h_c = {dd_exp:.3f}\,$cm", (S4 + 0.8, h_c0 - dd_exp), fontsize=9)
    ax.annotate(rf"$\Delta h_c = {dd_large:.2f}\,$cm", (S4 + 0.8, h_c0 - dd_large), fontsize=9)

    ax.set_xlabel('Slug Position $L$ (cm)')
    ax.set_ylabel('Container Level $h_c$ (cm)')
    ax.set_title('Container Drawdown')
    ax.legend(loc='lower left')
    ax.set_xlim(S1 - 2, L_max + 10)
    y_min = h_c0 - dd_large - 0.6
    y_max = h_c0 + 0.6
    ax.set_ylim(y_min, y_max)

    plt.tight_layout()
    save_figure('figure5_drawdown')
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

    # Shade experimental and model Re ranges during filling
    Re_exp = np.abs(exp_v_valid) * D_pipe / nu
    if np.isfinite(Re_exp).any():
        ax.axvspan(np.nanmin(Re_exp), np.nanmax(Re_exp), alpha=0.12, color='orange',
                   label='Experimental Re range')

    sol = solve_filling(t_max=20.0, max_step=0.01)
    Re_model = np.abs(sol.y[1]) * D_pipe / nu
    mask_model = Re_model > 50
    if mask_model.any():
        ax.axvspan(np.nanmin(Re_model[mask_model]), np.nanmax(Re_model[mask_model]),
                   alpha=0.08, color='gray', label='Model Re range')

    # Constant f0
    ax.axhline(f0, color='red', linestyle=':', linewidth=1.5,
               label=rf"$f_0 = {f0:.3f}$ (constant approx.)")

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
    save_figure('figure6_friction')
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

    # Experimental "kinetic head" for comparison: v^2/(2g)
    I_exp = (exp_v_valid ** 2) / (2 * g)
    ax.scatter(exp_L_biased_valid, I_exp, s=18, color='k', alpha=0.65,
               label=r'Experiment: $v^2/(2g)$')

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
    ax.annotate(rf"$I(S_W) = {I_W:.2f}\,$cm", (S_W + 0.8, I_W + 0.25), fontsize=9, color='blue')
    ax.annotate(rf"$I_{{\mathrm{{dd}}}}(S_W) = {I_dd_W:.2f}\,$cm", (S_W + 0.8, I_dd_W - 0.25), fontsize=9, color='green')
    ax.annotate(rf"$I_f(S_W) = {I_f_W:.3f}\,$cm", (S_W + 0.8, I_f_W + 0.08), fontsize=9, color='red')

    # Mark key positions
    for s, label in [(S[2], 'C'), (S_Wp, "W'"), (S[3], 'D'), (S_W, 'W')]:
        ax.axvline(s, color='lightgray', linestyle=':', alpha=0.5)

    ax.set_xlabel('Arclength $L$ (cm)')
    ax.set_ylabel('Energy Integral (cm)')
    ax.set_title('Comparison of Energy Integrals: Hierarchy of Bounds')
    ax.legend(loc='upper left')
    ax.set_xlim(S1 - 2, L_max + 5)

    plt.tight_layout()
    save_figure('figure7_comparison')
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

    ax.plot(L_arr, v_frictionless, 'b-', linewidth=2, label=r'Frictionless: $\sqrt{2gI}$')
    ax.plot(L_arr, v_drawdown, 'g--', linewidth=2, label=r'With drawdown: $\sqrt{2gI_{\mathrm{dd}}}$')
    ax.plot(L_arr, v_friction, 'r-.', linewidth=2, label=r'Constant friction: $\sqrt{2gI_f}$')
    ax.plot(L_arr, v_ode, 'k-', linewidth=2.5, label='Full ODE (numerical)')

    # Experimental velocity points (use biased L)
    ax.scatter(exp_L_biased_valid, exp_v_valid, s=24, color='black', alpha=0.75,
               label='Experiment (biased $L$)')

    # Mark crossings
    ax.axvline(S_Wp, color='purple', linestyle=':', alpha=0.6)
    ax.axvline(S_W, color='red', linestyle=':', alpha=0.6)

    ax.set_xlabel('Arclength $L$ (cm)')
    ax.set_ylabel('Velocity $v$ (cm/s)')
    ax.set_title('Velocity Comparison: Analytical Bounds vs. Numerical Solution')
    ax.legend(loc='upper left')
    ax.set_xlim(S1, L_max)
    v_max = max(np.nanmax(exp_v_valid), np.nanmax(v_ode), np.nanmax(v_frictionless))
    ax.set_ylim(0, v_max * 1.15 + 2)

    plt.tight_layout()
    save_figure('figure8_velocity')
    plt.close()
    print("Figure 8 saved.")

# =============================================================================
# FIGURE 9: Time evolution L(t) and v(t)
# =============================================================================

def figure9_time():
    """Generate Figure 9: Position and velocity vs time."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 7), sharex=True)

    # Solve filling
    sol_filling = solve_filling(t_max=20.0, max_step=0.01)
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

    # Align model time axis to the first experimental point (to account for video tracking start)
    t_shift = 0.0
    if exp_t_valid.size > 0:
        L_align = float(exp_L_biased_valid[0])
        if L_align <= float(L_fill.max()):
            t_model_align = float(np.interp(L_align, L_fill, t_fill))
            t_shift = float(exp_t_valid[0] - t_model_align)

    t_fill_plot = t_fill + t_shift
    t_drain_plot = t_drain + t_shift
    t_fill_end_plot = t_fill_end + t_shift

    # TOP PANEL: Position L(t)
    ax1.plot(t_fill_plot, L_fill, 'b-', linewidth=2, label='Model: filling')
    ax1.plot(t_drain_plot, L_drain, 'b--', linewidth=2, label='Model: draining (pipe full)')
    ax1.scatter(exp_t_valid, exp_L_biased_valid, s=18, color='black', alpha=0.75,
                label='Experiment (biased $L$)')
    ax1.set_ylabel('Position $L$ (cm)')
    ax1.set_ylim(0, L_max + 5)

    # Mark key positions on L axis
    key_positions = [(S[1], 'B'), (S[2], 'C'), (S_Wp, "W'"), (S[3], 'D'), (S_W, 'W'), (S4, 'E (outlet)')]
    t_left = min(float(t_fill_plot.min()), float(exp_t_valid.min())) if exp_t_valid.size else float(t_fill_plot.min())
    t_left += 0.02
    for pos, label in key_positions:
        ax1.axhline(pos, color='gray', linestyle=':', alpha=0.4, linewidth=0.8)
        ax1.annotate(label, (t_left, pos + 0.6), fontsize=8, color='gray')

    # Mark transition
    ax1.axvline(t_fill_end_plot, color='green', linestyle='-', alpha=0.7, linewidth=1.5)
    ax1.legend(loc='lower right')
    ax1.set_title('Time Evolution: Filling and Draining Phases')

    # BOTTOM PANEL: Velocity v(t)
    ax2.plot(t_fill_plot, v_fill, 'r-', linewidth=2, label='Model: filling')
    ax2.plot(t_drain_plot, v_drain, 'r--', linewidth=2, label='Model: draining')
    ax2.scatter(exp_t_valid, exp_v_valid, s=18, color='black', alpha=0.75,
                label='Experiment')
    ax2.set_xlabel('Time $t$ (s)')
    ax2.set_ylabel('Velocity $v$ (cm/s)')
    ax2.set_ylim(0, max(v_all) * 1.15)

    # Mark transition
    ax2.axvline(t_fill_end_plot, color='green', linestyle='-', alpha=0.7, linewidth=1.5)
    ax2.annotate('Pipe fills\ncompletely', (t_fill_end_plot + 0.03, max(v_all) * 0.8),
                fontsize=9, color='green')

    # Find and mark key events
    # Find time when slug reaches C (low point, max velocity during filling)
    idx_C = np.argmin(np.abs(L_fill - S[2]))
    t_C = t_fill_plot[idx_C]
    v_C = v_fill[idx_C]
    ax2.plot(t_C, v_C, 'ko', markersize=6)
    ax2.annotate(f'C: v={v_C:.0f} cm/s', (t_C + 0.02, v_C), fontsize=8)

    # Find time when slug reaches D (crest)
    idx_D = np.argmin(np.abs(L_fill - S[3]))
    t_D = t_fill_plot[idx_D]
    v_D = v_fill[idx_D]
    ax2.plot(t_D, v_D, 'ko', markersize=6)
    ax2.annotate(f'D: v={v_D:.0f} cm/s', (t_D + 0.02, v_D - 5), fontsize=8)

    # Find time when slug reaches W
    idx_W = np.argmin(np.abs(L_fill - S_W))
    t_W = t_fill_plot[idx_W]
    v_W = v_fill[idx_W]
    ax2.plot(t_W, v_W, 'rs', markersize=7)
    ax2.annotate(f'W: v={v_W:.0f} cm/s', (t_W + 0.02, v_W + 3), fontsize=8, color='red')

    ax2.legend(loc='upper right')

    x_max = max(float(t_drain_plot[-1]), float(exp_t_valid.max()) if exp_t_valid.size else 0.0) + 0.05
    ax2.set_xlim(t_left - 0.02, x_max)

    plt.tight_layout()
    save_figure('figure9_time')
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

    # Mark experiment
    D_mm_exp = D_pipe * 10.0
    crest_height_exp = nodes_h[3] - h_c0
    ax.plot(D_mm_exp, crest_height_exp, 'ko', markersize=10, markerfacecolor='yellow',
            markeredgewidth=2, label='Experiment')

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

    # Mark experiment (filling) as a trajectory of (Re, Ca)
    Re_exp = np.abs(exp_v_valid) * D_pipe / nu
    Ca_exp = (mu * np.abs(exp_v_valid)) / gamma
    ax.scatter(Re_exp, Ca_exp, s=18, color='black', alpha=0.65, label='Experiment (filling)')

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

    # Mark experiment at (L/D, Re_max)
    LD_exp = L_max / D_pipe
    Re_max_exp = float(np.nanmax(Re_exp)) if np.isfinite(Re_exp).any() else 1000.0
    ax.plot(LD_exp, Re_max_exp, 'ko', markersize=10, markerfacecolor='yellow',
            markeredgewidth=2, label='Experiment')

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
    save_figure('figure10_validity')
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
    save_figure('figureA1_friction_comparison')
    plt.close()
    print("Figure A1 saved.")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    print("Generating all figures for siphon-theory-5.tex")
    print("=" * 60)

    print_setup_summary()

    print("Calibrating (epsilon/D, sum K) to match v(L_biased)...")
    fit_res = fit_loss_params()
    print(f"Fit success: {bool(fit_res.success)} ({fit_res.message})")
    print(f"  epsilon/D = {epsilon_D:.6g}")
    print(f"  sum K     = {K_total:.3g}")
    print(f"  f0 (rep.) = {f0:.4f}")
    print()

    # Key values for energy-integral discussion
    print("Key energy-integral values:")
    print(f"  I(S_W')    = {I_frictionless(S_Wp):.3f} cm")
    print(f"  I(S_W)     = {I_frictionless(S_W):.3f} cm")
    print(f"  I_dd(S_W)  = {I_drawdown(S_W):.3f} cm")
    print(f"  I_f(S_W)   = {I_friction(S_W):.3f} cm")
    print(f"  v0(W)      = {np.sqrt(2*g*max(I_frictionless(S_W),0)):.1f} cm/s (frictionless)")
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
