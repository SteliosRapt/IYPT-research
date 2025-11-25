#!/usr/bin/env python3
"""
One-Dimensional Slug-Flow Model for Self-Starting Siphons
==========================================================

IYPT 2026 Problem #1

Notation:
- h_0 = h_A = inlet elevation
- h_1 = h_B = initial water level (container surface)

Geometry Constraints:
1. x_A = 0
2. x_A < x_B < x_C < x_D < x_E
3. h_D is maximum (crest)
4. h_B = h_1 (water level)
5. Two lowest among {A, C, E}, second lowest is C or E
   (E CAN be lower than A)
"""

import numpy as np
from dataclasses import dataclass, field
from typing import Tuple, Optional, Dict, Any, List
from scipy.integrate import solve_ivp
from scipy.optimize import brentq


def churchill_friction(Re: float, eps_D: float) -> float:
    """Churchill friction factor for all flow regimes."""
    Re = max(abs(Re), 1e-10)
    if Re < 1.0:
        return 64.0 / Re
    
    inner = (7.0 / Re)**0.9 + 0.27 * eps_D
    A1 = min((-2.457 * np.log(inner))**16, 1e100)
    A2 = min((37530.0 / Re)**16, 1e100)
    
    return 8.0 * ((8.0 / Re)**12 + 1.0 / max(A1 + A2, 1e-100)**1.5)**(1.0/12.0)


def validate_geometry_constraints(nodes: np.ndarray, h1: float) -> List[str]:
    """
    Validate geometry constraints.
    
    Constraints:
    1. x_A = 0
    2. x strictly increasing
    3. h_D is maximum
    4. h_B = h_1
    5. Two lowest among {A,C,E}, second lowest is C or E
    """
    errors = []
    if len(nodes) != 5:
        errors.append(f"Need 5 nodes, got {len(nodes)}")
        return errors
    
    x, h = nodes[:, 0], nodes[:, 1]
    names = ['A', 'B', 'C', 'D', 'E']
    
    # 1. x_A = 0
    if abs(x[0]) > 1e-10:
        errors.append(f"x_A must be 0, got {x[0]}")
    
    # 2. x strictly increasing
    for i in range(4):
        if x[i+1] <= x[i]:
            errors.append(f"x_{names[i]} >= x_{names[i+1]}")
    
    # 3. h_D maximum
    if h[3] < np.max(h) - 1e-10:
        errors.append(f"h_D must be maximum, but h_{names[np.argmax(h)]} is higher")
    
    # 4. h_B = h_1
    if abs(h[1] - h1) > 1e-10:
        errors.append(f"h_B={h[1]:.4f} must equal h_1={h1:.4f}")
    
    # 5. Two lowest among {A,C,E}, second lowest is C or E
    sorted_idx = np.argsort(h)
    if sorted_idx[0] not in [0, 2, 4]:
        errors.append(f"Lowest must be A, C, or E (got {names[sorted_idx[0]]})")
    if sorted_idx[1] not in [2, 4]:
        errors.append(f"Second lowest must be C or E (got {names[sorted_idx[1]]})")
    
    return errors


def create_valid_geometry(h1: float, h_crest: float, h_outlet: float, 
                          h_inlet: float, h_ubend: float,
                          x_positions: np.ndarray = None) -> Tuple[np.ndarray, List[str]]:
    """Create geometry satisfying all constraints."""
    if x_positions is None:
        x_positions = np.array([0.0, 0.02, 0.04, 0.06, 0.10])
    
    nodes = np.array([
        [x_positions[0], h_inlet],   # A: h_0
        [x_positions[1], h1],        # B: h_1
        [x_positions[2], h_ubend],   # C
        [x_positions[3], h_crest],   # D
        [x_positions[4], h_outlet]   # E
    ])
    
    errors = validate_geometry_constraints(nodes, h1)
    if errors:
        raise ValueError("Geometry violates constraints:\n" + "\n".join(errors))
    
    warnings = []
    if h_crest >= h1:
        warnings.append(f"Crest ({h_crest*100:.1f}cm) >= water level ({h1*100:.1f}cm)")
    
    return nodes, warnings


@dataclass
class PipeGeometry:
    """Piecewise-linear pipe geometry."""
    nodes: np.ndarray
    h1_for_validation: float = None
    S: np.ndarray = field(init=False)
    L_segments: np.ndarray = field(init=False)
    slopes: np.ndarray = field(init=False)
    intercepts: np.ndarray = field(init=False)
    crest_index: int = field(init=False)
    
    def __post_init__(self):
        self.nodes = np.asarray(self.nodes, dtype=float)
        
        if self.h1_for_validation is not None and len(self.nodes) == 5:
            errors = validate_geometry_constraints(self.nodes, self.h1_for_validation)
            if errors:
                raise ValueError("Constraints violated:\n  " + "\n  ".join(errors))
        
        x, h = self.nodes[:, 0], self.nodes[:, 1]
        dx, dh = np.diff(x), np.diff(h)
        self.L_segments = np.sqrt(dx**2 + dh**2)
        self.S = np.concatenate([[0], np.cumsum(self.L_segments)])
        self.slopes = dh / self.L_segments
        self.intercepts = h[:-1] - self.slopes * self.S[:-1]
        self.crest_index = np.argmax(h)
    
    @property
    def n_segments(self): return len(self.L_segments)
    @property
    def L_total(self): return self.S[-1]
    @property
    def h0(self): return self.nodes[0, 1]  # Inlet elevation
    @property
    def h_outlet(self): return self.nodes[-1, 1]
    @property
    def h_crest(self): return self.nodes[self.crest_index, 1]
    @property
    def L_crest(self): return self.S[self.crest_index]
    
    def h_of_L(self, L: float) -> float:
        idx = np.clip(np.searchsorted(self.S, L, side='right') - 1, 0, self.n_segments - 1)
        return self.intercepts[idx] + self.slopes[idx] * L
    
    def h_of_L_vec(self, L_arr: np.ndarray) -> np.ndarray:
        idx = np.clip(np.searchsorted(self.S, L_arr, side='right') - 1, 0, self.n_segments - 1)
        return self.intercepts[idx] + self.slopes[idx] * L_arr
    
    def segment_of_L(self, L: float) -> int:
        return np.clip(np.searchsorted(self.S, L, side='right') - 1, 0, self.n_segments - 1)


@dataclass
class SiphonParams:
    """Complete parameter set. h_0=inlet elevation, h_1=water level."""
    geometry: PipeGeometry
    g: float = 9.81
    rho: float = 1000.0
    mu: float = 1.0e-3
    D: float = 0.010
    A0: float = 0.02
    eps_D: float = 1.0e-4
    K_minor: float = 1.0
    K_drain: float = 1.5
    h1: float = None  # Water level (h_B)
    L1: float = None  # Initial wetted length
    
    def __post_init__(self):
        if self.h1 is None:
            self.h1 = self.geometry.nodes[1, 1]
        if self.L1 is None:
            self.L1 = self.geometry.S[1]
    
    @property
    def A(self): return np.pi * self.D**2 / 4.0
    @property
    def Lmax(self): return self.geometry.L_total
    @property
    def h0(self): return self.geometry.h0  # Inlet elevation
    @property
    def h_outlet(self): return self.geometry.h_outlet
    @property
    def h_crest(self): return self.geometry.h_crest
    @property
    def area_ratio(self): return self.A / self.A0
    
    def h_of_L(self, L): return self.geometry.h_of_L(L)
    def hc_of_L(self, L): return self.h1 - self.area_ratio * (L - self.L1)
    def reynolds(self, v): return self.rho * abs(v) * self.D / self.mu
    def friction_factor(self, v): return churchill_friction(self.reynolds(v), self.eps_D)
    def bond_number(self, sigma=0.072): return self.rho * self.g * self.D**2 / sigma


def filling_rhs(t, y, p):
    """Filling phase ODE: dy/dt = [v, dv/dt]"""
    L, v = max(y[0], 1e-10), y[1]
    hc, h_front = p.hc_of_L(L), p.h_of_L(L)
    f = p.friction_factor(v)
    loss = f * L / p.D + p.K_minor
    dvdt = (p.g / L) * (hc - h_front) - (0.5 / L) * loss * abs(v) * v
    return [v, dvdt]


def draining_rhs(t, y, p):
    """Draining phase ODE: dy/dt = [dhc/dt, dv/dt]"""
    hc, v = y
    f = p.friction_factor(v)
    loss = f * p.Lmax / p.D + p.K_drain
    dhc_dt = -p.area_ratio * v
    dv_dt = (p.g / p.Lmax) * (hc - p.h_outlet) - (0.5 / p.Lmax) * loss * abs(v) * v
    return [dhc_dt, dv_dt]


@dataclass
class SimulationResult:
    primed: bool
    t_fill: np.ndarray
    L_fill: np.ndarray
    v_fill: np.ndarray
    hc_fill: np.ndarray
    h_front_fill: np.ndarray
    t_prime: Optional[float] = None
    v_prime: Optional[float] = None
    hc_prime: Optional[float] = None
    t_drain: Optional[np.ndarray] = None
    hc_drain: Optional[np.ndarray] = None
    v_drain: Optional[np.ndarray] = None
    t_total: Optional[float] = None
    h_max_reached: Optional[float] = None
    L_max_reached: Optional[float] = None
    stall_reason: Optional[str] = None


def simulate(p: SiphonParams, t_max_fill=100.0, t_max_drain=500.0) -> SimulationResult:
    """Run complete simulation."""
    Lmax = p.Lmax
    
    def ev_filled(t, y): return y[0] - Lmax
    ev_filled.terminal, ev_filled.direction = True, 1
    
    def ev_stall(t, y): return y[1]
    ev_stall.terminal, ev_stall.direction = True, -1
    
    def ev_head(t, y): return p.hc_of_L(y[0]) - p.h_of_L(y[0])
    ev_head.terminal, ev_head.direction = True, -1
    
    sol = solve_ivp(lambda t, y: filling_rhs(t, y, p), [0, t_max_fill], [p.L1, 0.0],
                    events=[ev_filled, ev_stall, ev_head], rtol=1e-8, atol=1e-10, max_step=0.1)
    
    t_fill, L_fill, v_fill = sol.t, sol.y[0], sol.y[1]
    hc_fill = np.array([p.hc_of_L(L) for L in L_fill])
    h_front_fill = np.array([p.h_of_L(L) for L in L_fill])
    
    primed, stall_reason = False, None
    if sol.t_events[0].size > 0:
        primed, t_prime = True, sol.t_events[0][0]
    elif sol.t_events[1].size > 0:
        stall_reason = "velocity_reversal"
    elif sol.t_events[2].size > 0:
        stall_reason = "head_exhausted"
    else:
        stall_reason = "timeout"
    
    if not primed:
        return SimulationResult(False, t_fill, L_fill, v_fill, hc_fill, h_front_fill,
                                h_max_reached=np.max(h_front_fill), L_max_reached=np.max(L_fill),
                                stall_reason=stall_reason)
    
    v_prime, hc_prime = sol.y[1, -1], p.hc_of_L(Lmax)
    
    def ev_empty(t, y): return y[0] - p.h_outlet
    ev_empty.terminal, ev_empty.direction = True, -1
    
    sol2 = solve_ivp(lambda t, y: draining_rhs(t, y, p), [t_prime, t_prime + t_max_drain],
                     [hc_prime, v_prime], events=[ev_empty], rtol=1e-8, atol=1e-10, max_step=0.1)
    
    return SimulationResult(True, t_fill, L_fill, v_fill, hc_fill, h_front_fill,
                            t_prime, v_prime, hc_prime, sol2.t, sol2.y[0], sol2.y[1],
                            sol2.t[-1], np.max(h_front_fill), np.max(L_fill))


def segment_energy(h1, c, s, a, b):
    """Energy integral for segment."""
    if b <= a or a <= 0: return 0.0
    return (h1 - c) * np.log(b / a) - s * (b - a)


def compute_ideal_bound(p: SiphonParams) -> Tuple[float, float, bool]:
    """Ideal (lossless) maximum climb height."""
    geom, h1 = p.geometry, p.h1
    S, c, s = geom.S, geom.intercepts, geom.slopes
    
    start_seg = geom.segment_of_L(p.L1)
    cumulative = 0.0
    
    if p.L1 > S[start_seg]:
        contrib = segment_energy(h1, c[start_seg], s[start_seg], p.L1, S[start_seg + 1])
        if cumulative + contrib < 0:
            def fn(L): return cumulative + segment_energy(h1, c[start_seg], s[start_seg], p.L1, L)
            L_stall = brentq(fn, p.L1, S[start_seg + 1])
            return geom.h_of_L(L_stall), L_stall, geom.h_of_L(L_stall) > geom.h_crest
        cumulative += contrib
        start_seg += 1
    
    for i in range(start_seg, geom.n_segments):
        a = S[i] if i > start_seg or p.L1 <= S[start_seg] else p.L1
        b = S[i + 1]
        contrib = segment_energy(h1, c[i], s[i], a, b)
        
        if cumulative + contrib < 0:
            def fn(L, cum=cumulative, ci=c[i], si=s[i], ai=a):
                return cum + segment_energy(h1, ci, si, ai, L)
            try:
                L_stall = brentq(fn, a + 1e-10, b)
            except ValueError:
                L_stall = b
            return geom.h_of_L(L_stall), L_stall, geom.h_of_L(L_stall) > geom.h_crest
        cumulative += contrib
    
    return np.max(geom.h_of_L_vec(np.linspace(p.L1, geom.L_total, 1000))), geom.L_total, True


def validate_setup(p: SiphonParams) -> List[str]:
    """Run validity checks."""
    w = []
    Bo = p.bond_number()
    if Bo < 1: w.append(f"CAPILLARITY: Bo={Bo:.2f}")
    elif Bo < 10: w.append(f"Moderate Bond: Bo={Bo:.2f}")
    
    h_L1 = p.h_of_L(p.L1)
    if h_L1 > p.h1: w.append(f"Front ({h_L1*100:.1f}cm) above water ({p.h1*100:.1f}cm)")
    return w


def plot_results(result: SimulationResult, p: SiphonParams, save_path: str = None):
    """Plot simulation results."""
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not available")
        return
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Geometry
    ax = axes[0, 0]
    nodes = p.geometry.nodes
    ax.plot(nodes[:, 0]*100, nodes[:, 1]*100, 'ko-', lw=2, ms=8)
    for i, (x, h) in enumerate(nodes):
        ax.annotate(['A(h₀)', 'B(h₁)', 'C', 'D', 'E'][i], (x*100, h*100), 
                   xytext=(5, 5), textcoords='offset points', fontsize=9)
    ax.axhline(p.h1*100, color='b', ls='--', alpha=0.5, label=f'h₁={p.h1*100:.1f}cm')
    ax.axhline(p.h0*100, color='g', ls=':', alpha=0.5, label=f'h₀={p.h0*100:.1f}cm')
    ax.set_xlabel('x [cm]'); ax.set_ylabel('h [cm]')
    ax.set_title('Geometry'); ax.legend(fontsize=8); ax.grid(alpha=0.3)
    ax.set_aspect('equal')
    
    # Wetted length
    ax = axes[0, 1]
    ax.plot(result.t_fill, result.L_fill*100, 'b-')
    ax.axhline(p.Lmax*100, color='g', ls='--', alpha=0.5)
    if result.primed:
        ax.axvline(result.t_prime, color='r', ls=':', alpha=0.5)
    ax.set_xlabel('t [s]'); ax.set_ylabel('L [cm]')
    ax.set_title('Filling'); ax.grid(alpha=0.3)
    
    # Velocity
    ax = axes[1, 0]
    ax.plot(result.t_fill, result.v_fill*100, 'b-', label='Fill')
    if result.primed and result.t_drain is not None:
        ax.plot(result.t_drain, result.v_drain*100, 'r-', label='Drain')
    ax.axhline(0, color='k', alpha=0.3)
    ax.set_xlabel('t [s]'); ax.set_ylabel('v [cm/s]')
    ax.set_title('Velocity'); ax.legend(); ax.grid(alpha=0.3)
    
    # Elevations
    ax = axes[1, 1]
    ax.plot(result.t_fill, result.hc_fill*100, 'b-', label='h_c')
    ax.plot(result.t_fill, result.h_front_fill*100, 'g-', label='Front')
    ax.axhline(p.h_crest*100, color='r', ls='--', alpha=0.5, label='Crest')
    if result.primed and result.t_drain is not None:
        ax.plot(result.t_drain, result.hc_drain*100, 'b--', alpha=0.7)
    ax.set_xlabel('t [s]'); ax.set_ylabel('h [cm]')
    ax.set_title('Water Levels'); ax.legend(); ax.grid(alpha=0.3)
    
    plt.tight_layout()
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Saved: {save_path}")
    plt.show()


def print_summary(p: SiphonParams, result: SimulationResult = None):
    """Print parameter and result summary."""
    print("=" * 60)
    print("SIPHON SIMULATION SUMMARY")
    print("=" * 60)
    print(f"\nGeometry (h₀=inlet, h₁=water level):")
    print(f"  A (inlet):  h₀ = {p.h0*100:6.2f} cm")
    print(f"  B (water):  h₁ = {p.h1*100:6.2f} cm")
    print(f"  C (U-bend):      {p.geometry.nodes[2,1]*100:6.2f} cm")
    print(f"  D (crest):       {p.h_crest*100:6.2f} cm")
    print(f"  E (outlet):      {p.h_outlet*100:6.2f} cm")
    print(f"  Pipe length:     {p.Lmax*100:6.2f} cm")
    
    print(f"\nParameters:")
    print(f"  D={p.D*1000:.1f}mm, A₀={p.A0*1e4:.1f}cm², Bond={p.bond_number():.1f}")
    
    h_max, L_stall, can_prime = compute_ideal_bound(p)
    print(f"\nIdeal bound:")
    print(f"  h_max={h_max*100:.2f}cm, crest={p.h_crest*100:.2f}cm, margin={(h_max-p.h_crest)*100:.2f}cm")
    
    if result:
        print(f"\nResult: {'PRIMED' if result.primed else 'FAILED'}")
        if result.primed:
            print(f"  t_prime={result.t_prime:.3f}s, v={result.v_prime*100:.1f}cm/s")
        else:
            print(f"  Reason: {result.stall_reason}")
            print(f"  Max h: {result.h_max_reached*100:.2f}cm")
    print("=" * 60)


def main():
    """Example with outlet below inlet (E lowest)."""
    print("Self-Starting Siphon Simulation - IYPT 2026")
    print("-" * 50)
    
    h1 = 0.20  # Water level (h_1 = h_B)
    
    # E is lowest, C is second lowest, A is above both
    nodes, warnings = create_valid_geometry(
        h1=h1,
        h_crest=0.22,    # D (highest)
        h_outlet=-0.30,  # E (lowest!)
        h_inlet=0.05,    # A = h_0
        h_ubend=-0.15,   # C (second lowest)
        x_positions=np.array([0.0, 0.03, 0.06, 0.09, 0.15])
    )
    
    print("\nGeometry created:")
    print(f"  A: h₀ = {nodes[0,1]*100:6.1f} cm (inlet)")
    print(f"  B: h₁ = {nodes[1,1]*100:6.1f} cm (water level)")
    print(f"  C:      {nodes[2,1]*100:6.1f} cm (2nd lowest)")
    print(f"  D:      {nodes[3,1]*100:6.1f} cm (crest, max)")
    print(f"  E:      {nodes[4,1]*100:6.1f} cm (outlet, lowest)")
    
    for w in warnings:
        print(f"  Note: {w}")
    
    geometry = PipeGeometry(nodes, h1_for_validation=h1)
    
    params = SiphonParams(
        geometry=geometry,
        D=0.012,
        A0=0.05,
        h1=h1,
        L1=geometry.S[1],
        K_minor=0.5,
        K_drain=1.0
    )
    
    # Validate
    print("\nValidation:")
    for w in validate_setup(params):
        print(f"  ⚠ {w}")
    
    # Ideal bound
    h_max, _, can_prime = compute_ideal_bound(params)
    print(f"\nIdeal bound: h_max={h_max*100:.2f}cm, crest={params.h_crest*100:.2f}cm")
    print(f"  Margin: {(h_max - params.h_crest)*100:.2f}cm")
    
    # Simulate
    print("\nSimulating...")
    result = simulate(params)
    
    if result.primed:
        print(f"  ✓ PRIMED at t={result.t_prime:.3f}s, v={result.v_prime*100:.1f}cm/s")
    else:
        print(f"  ✗ FAILED: {result.stall_reason}")
        print(f"    Max height: {result.h_max_reached*100:.2f}cm")
    
    print("\n")
    print_summary(params, result)
    
    try:
        plot_results(result, params, '/mnt/user-data/outputs/siphon_simulation.png')
    except Exception as e:
        print(f"Plot error: {e}")
    
    return params, result


if __name__ == "__main__":
    params, result = main()
