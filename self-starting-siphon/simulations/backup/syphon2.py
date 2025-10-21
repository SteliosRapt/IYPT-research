from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import animation
from mpl_toolkits.mplot3d import Axes3D
from datetime import datetime
import os
import json

P_atm = 101300   # Pa (atmospheric pressure)
P_vapor = 2300   # Pa (vapor pressure of water at 20°C)
rho = 998        # kg/m³ (water density at 20°C)
g = 9.81         # m/s²
mu = 0.001       # Pa·s (dynamic viscosity of water at 20°C)

def _validate_area_ratio(A_tube, A_0):
    """Validate geometry inputs and return the area ratio k."""
    if A_tube <= 0 or A_0 <= 0:
        raise ValueError("Cross-sectional areas must be positive.")

    k = A_tube / A_0
    if not 0 < k < 1:
        raise ValueError(
            "Area ratio k = A_tube/A_0 must lie between 0 and 1 for the inviscid siphon model."
        )
    return k


def _validate_head(head):
    """Ensure the hydraulic head difference is positive."""
    if head <= 0:
        raise ValueError("Reservoir surface must be above the outlet (h_0 > h_out).")


def find_velocity(A_tube, A_0, h_0, h_out):
    """Calculate instantaneous velocity at height h_0."""
    k = _validate_area_ratio(A_tube, A_0)
    head = h_0 - h_out
    _validate_head(head)
    v = sqrt(2 * g * head / (1 - k**2))
    return v

def find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, t):
    """Calculate velocity as a function of time."""
    if t < 0:
        raise ValueError("Time must be non-negative.")

    k = _validate_area_ratio(A_tube, A_0)
    head_initial = h_0_initial - h_out
    _validate_head(head_initial)

    v_initial = sqrt(2 * g / (1 - k**2)) * sqrt(head_initial)
    decay_rate = k * g / (1 - k**2)
    v_t = v_initial - decay_rate * t
    return max(0.0, v_t)  # velocity cannot be negative

def find_height_at_time(A_tube, A_0, h_0_initial, h_out, t):
    """Calculate reservoir height as a function of time."""
    if t < 0:
        raise ValueError("Time must be non-negative.")

    k = _validate_area_ratio(A_tube, A_0)
    head_initial = h_0_initial - h_out
    _validate_head(head_initial)

    alpha = (k / 2) * sqrt(2 * g / (1 - k**2))
    term = sqrt(head_initial) - alpha * t
    if term <= 0:
        return h_out
    h_t = h_out + term**2
    return h_t

def find_time_to_empty(A_tube, A_0, h_0_initial, h_out):
    """Calculate total time to empty reservoir."""
    k = _validate_area_ratio(A_tube, A_0)
    head_initial = h_0_initial - h_out
    _validate_head(head_initial)

    t_empty = (2 * sqrt(1 - k**2)) / (k * sqrt(2 * g)) * sqrt(head_initial)
    return t_empty

def find_pressure_at_height(h, h_out):
    """Calculate pressure at height h in the tube"""
    P = P_atm + rho*g*(h_out - h)
    return P

def find_flow_rates(A_tube, A_0, h_0, h_out):
    """Calculate volumetric and mass flow rates"""
    v = find_velocity(A_tube, A_0, h_0, h_out)
    Q = v * A_tube  # m³/s
    Q_mass = rho * Q  # kg/s
    return Q, Q_mass

def calculate_reynolds_number(v, D):
    """Calculate Reynolds number for flow in tube

    Args:
        v: velocity (m/s)
        D: tube diameter (m)

    Returns:
        Re: Reynolds number (dimensionless)
    """
    Re = rho * v * D / mu
    return Re

def get_tube_diameter(A_tube):
    """Get tube diameter from cross-sectional area (assuming circular tube)"""
    D = sqrt(4 * A_tube / np.pi)
    return D

def plot_velocity_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir, filename='velocity_vs_time.png'):
    """Plot velocity as a function of time"""
    t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
    t = np.linspace(0, t_empty, 200)
    v = np.array([find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, ti) for ti in t])

    plt.figure(figsize=(8, 6))
    plt.plot(t, v, 'b-', linewidth=2)
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Velocity (m/s)', fontsize=12)
    plt.title('Syphon Velocity vs Time', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def plot_height_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir, filename='height_vs_time.png'):
    """Plot reservoir height as a function of time"""
    t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
    t = np.linspace(0, t_empty, 200)
    h = np.array([find_height_at_time(A_tube, A_0, h_0_initial, h_out, ti) for ti in t])

    plt.figure(figsize=(8, 6))
    plt.plot(t, h, 'g-', linewidth=2)
    plt.axhline(y=h_out, color='r', linestyle='--', label=f'Outlet height = {h_out} m')
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Reservoir Height (m)', fontsize=12)
    plt.title('Reservoir Height vs Time', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def plot_pressure_vs_height(h_out, output_dir, h_0_initial=None, h_max=None, filename='pressure_vs_height.png'):
    """Plot pressure distribution along the tube with cavitation limit"""
    if h_max is None:
        # Don't extend above initial reservoir height
        h_max = h_0_initial if h_0_initial is not None else h_out + 0.5

    # Only show physical heights (outlet and above)
    h_min = h_out
    h = np.linspace(h_min, h_max, 200)
    P = np.array([find_pressure_at_height(hi, h_out) for hi in h])

    plt.figure(figsize=(8, 6))
    plt.plot(P/1000, h, 'b-', linewidth=2.5, label='Pressure in tube')
    plt.axvline(x=P_atm/1000, color='k', linestyle='--', linewidth=1.5, label=f'Atmospheric ({P_atm/1000:.1f} kPa)')

    # Only show vapor pressure line if minimum pressure drops below it
    P_min = np.min(P)
    if P_min < P_vapor:
        plt.axvline(x=P_vapor/1000, color='r', linestyle='--', linewidth=1.5, label=f'Vapor pressure ({P_vapor/1000:.1f} kPa)')

    plt.axhline(y=h_out, color='g', linestyle=':', linewidth=1.5, alpha=0.7, label=f'Outlet height ({h_out} m)')

    if h_0_initial is not None:
        plt.axhline(y=h_0_initial, color='orange', linestyle='-.', linewidth=1.5, alpha=0.7, label=f'Initial reservoir ({h_0_initial} m)')

    plt.xlabel('Pressure (kPa)', fontsize=12)
    plt.ylabel('Height (m)', fontsize=12)
    plt.title('Pressure Distribution in Syphon Tube', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def plot_flow_rate_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir, filename='flow_rate_vs_time.png'):
    """Plot volumetric flow rate as a function of time"""
    t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
    t = np.linspace(0, t_empty, 200)
    Q = np.array([find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, ti) * A_tube for ti in t])

    plt.figure(figsize=(8, 6))
    plt.plot(t, Q*1000, 'r-', linewidth=2)  # Convert to L/s
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Flow Rate (L/s)', fontsize=12)
    plt.title('Volumetric Flow Rate vs Time', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

# ============================================================================
# ADVANCED PLOTS: 3D and Contour Plots
# ============================================================================

def plot_drainage_time_3d(h_out, output_dir, filename='drainage_time_3d.png'):
    """3D surface plot: drainage time as function of A_tube and h_0"""
    A_tube_range = np.linspace(0.001, 0.05, 30)
    h_0_range = np.linspace(h_out + 0.01, h_out + 0.5, 30)
    A_0 = 0.1  # Fixed reservoir area

    A_tube_grid, h_0_grid = np.meshgrid(A_tube_range, h_0_range)
    t_empty_grid = np.zeros_like(A_tube_grid)

    for i in range(len(h_0_range)):
        for j in range(len(A_tube_range)):
            t_empty_grid[i, j] = find_time_to_empty(A_tube_range[j], A_0, h_0_range[i], h_out)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(A_tube_grid, h_0_grid, t_empty_grid, cmap='viridis', alpha=0.8)
    ax.set_xlabel('Tube Area (m²)', fontsize=10)
    ax.set_ylabel('Initial Height (m)', fontsize=10)
    ax.set_zlabel('Drainage Time (s)', fontsize=10)
    ax.set_title(f'Drainage Time vs A_tube and h_0\n(A_0 = {A_0} m², h_out = {h_out} m)', fontsize=12)
    fig.colorbar(surf, shrink=0.5, aspect=5, label='Time (s)')
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def plot_drainage_time_contour(h_out, output_dir, filename='drainage_time_contour.png'):
    """2D contour plot: drainage time as function of A_tube and h_0"""
    A_tube_range = np.linspace(0.001, 0.05, 50)
    h_0_range = np.linspace(h_out + 0.01, h_out + 0.5, 50)
    A_0 = 0.1  # Fixed reservoir area

    A_tube_grid, h_0_grid = np.meshgrid(A_tube_range, h_0_range)
    t_empty_grid = np.zeros_like(A_tube_grid)

    for i in range(len(h_0_range)):
        for j in range(len(A_tube_range)):
            t_empty_grid[i, j] = find_time_to_empty(A_tube_range[j], A_0, h_0_range[i], h_out)

    plt.figure(figsize=(10, 8))
    contour = plt.contourf(A_tube_grid, h_0_grid, t_empty_grid, levels=20, cmap='plasma')
    plt.colorbar(contour, label='Drainage Time (s)')
    contour_lines = plt.contour(A_tube_grid, h_0_grid, t_empty_grid, levels=10, colors='white', linewidths=0.5, alpha=0.5)
    plt.clabel(contour_lines, inline=True, fontsize=8)
    plt.xlabel('Tube Area (m²)', fontsize=12)
    plt.ylabel('Initial Height (m)', fontsize=12)
    plt.title(f'Drainage Time Contour Map\n(A_0 = {A_0} m², h_out = {h_out} m)', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def plot_velocity_3d_parametric(A_0, h_out, output_dir, filename='velocity_3d_parametric.png'):
    """3D scatter: multiple scenarios in (k, h_0, v_initial) space"""
    k_values = np.linspace(0.01, 0.3, 15)
    h_0_values = np.linspace(h_out + 0.02, h_out + 0.3, 15)

    k_list = []
    h_0_list = []
    v_list = []

    for k in k_values:
        for h_0 in h_0_values:
            A_tube = k * A_0
            v = find_velocity(A_tube, A_0, h_0, h_out)
            k_list.append(k)
            h_0_list.append(h_0)
            v_list.append(v)

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')
    scatter = ax.scatter(k_list, h_0_list, v_list, c=v_list, cmap='coolwarm', s=30)
    ax.set_xlabel('Area Ratio k', fontsize=10)
    ax.set_ylabel('Initial Height h_0 (m)', fontsize=10)
    ax.set_zlabel('Initial Velocity (m/s)', fontsize=10)
    ax.set_title(f'Initial Velocity in Parameter Space\n(A_0 = {A_0} m², h_out = {h_out} m)', fontsize=12)
    fig.colorbar(scatter, shrink=0.5, aspect=5, label='Velocity (m/s)')
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

# ============================================================================
# ADVANCED PLOTS: Multiple Scenario Overlays
# ============================================================================

def plot_velocity_comparison(A_0, h_0_initial, h_out, output_dir, filename='velocity_comparison.png'):
    """Overlay velocity vs time for different k values"""
    k_values = [0.05, 0.1, 0.15, 0.2]
    colors = ['blue', 'green', 'orange', 'red']

    plt.figure(figsize=(10, 7))
    for k, color in zip(k_values, colors):
        A_tube = k * A_0
        t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
        t = np.linspace(0, t_empty, 200)
        v = np.array([find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, ti) for ti in t])
        plt.plot(t, v, color=color, linewidth=2, label=f'k = {k}')

    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Velocity (m/s)', fontsize=12)
    plt.title(f'Velocity Comparison for Different Area Ratios\n(A_0 = {A_0} m², h_0 = {h_0_initial} m, h_out = {h_out} m)', fontsize=13)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def plot_height_comparison(A_0, h_out, output_dir, filename='height_comparison.png'):
    """Overlay height vs time for different initial heights"""
    h_0_values = [h_out + 0.05, h_out + 0.1, h_out + 0.15, h_out + 0.2]
    colors = ['purple', 'blue', 'green', 'orange']
    A_tube = 0.01  # Fixed tube area

    plt.figure(figsize=(10, 7))
    for h_0, color in zip(h_0_values, colors):
        t_empty = find_time_to_empty(A_tube, A_0, h_0, h_out)
        t = np.linspace(0, t_empty, 200)
        h = np.array([find_height_at_time(A_tube, A_0, h_0, h_out, ti) for ti in t])
        plt.plot(t, h, color=color, linewidth=2, label=f'h_0 = {h_0:.2f} m')

    plt.axhline(y=h_out, color='red', linestyle='--', linewidth=1.5, label=f'Outlet (h_out = {h_out} m)')
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Height (m)', fontsize=12)
    plt.title(f'Height Comparison for Different Initial Heights\n(A_tube = {A_tube} m², A_0 = {A_0} m²)', fontsize=13)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def plot_flow_rate_comparison(A_0, h_0_initial, h_out, output_dir, filename='flow_rate_comparison.png'):
    """Overlay flow rate vs time for different k values"""
    k_values = [0.05, 0.1, 0.15, 0.2]
    colors = ['blue', 'green', 'orange', 'red']

    plt.figure(figsize=(10, 7))
    for k, color in zip(k_values, colors):
        A_tube = k * A_0
        t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
        t = np.linspace(0, t_empty, 200)
        Q = np.array([find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, ti) * A_tube for ti in t])
        plt.plot(t, Q*1000, color=color, linewidth=2, label=f'k = {k}')

    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Flow Rate (L/s)', fontsize=12)
    plt.title(f'Flow Rate Comparison for Different Area Ratios\n(A_0 = {A_0} m², h_0 = {h_0_initial} m, h_out = {h_out} m)', fontsize=13)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

# ============================================================================
# ADVANCED PLOTS: Animations
# ============================================================================

def animate_drainage(A_tube, A_0, h_0_initial, h_out, output_dir, filename='drainage_animation.gif'):
    """Animated visualization of syphon drainage with live plots"""
    t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
    frames = 100
    t_vals = np.linspace(0, t_empty, frames)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    fig.suptitle(f'Syphon Drainage Animation (k={A_tube/A_0:.2f})', fontsize=14)

    # Setup axes
    ax1.set_xlim(0, t_empty)
    ax1.set_ylim(0, find_velocity(A_tube, A_0, h_0_initial, h_out) * 1.1)
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Velocity (m/s)')
    ax1.set_title('Velocity vs Time')
    ax1.grid(True, alpha=0.3)

    ax2.set_xlim(0, t_empty)
    ax2.set_ylim(h_out * 0.95, h_0_initial * 1.05)
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('Height (m)')
    ax2.set_title('Reservoir Height vs Time')
    ax2.axhline(y=h_out, color='red', linestyle='--', alpha=0.5)
    ax2.grid(True, alpha=0.3)

    ax3.set_xlim(0, t_empty)
    Q_max = find_velocity(A_tube, A_0, h_0_initial, h_out) * A_tube * 1000
    ax3.set_ylim(0, Q_max * 1.1)
    ax3.set_xlabel('Time (s)')
    ax3.set_ylabel('Flow Rate (L/s)')
    ax3.set_title('Flow Rate vs Time')
    ax3.grid(True, alpha=0.3)

    ax4.set_xlim(-0.5, 1)
    ax4.set_ylim(0, h_0_initial * 1.2)
    ax4.set_xlabel('Width')
    ax4.set_ylabel('Height (m)')
    ax4.set_title('Syphon Schematic')
    ax4.set_xticks([])

    # Initialize plot elements
    line1, = ax1.plot([], [], 'b-', linewidth=2)
    line2, = ax2.plot([], [], 'g-', linewidth=2)
    line3, = ax3.plot([], [], 'r-', linewidth=2)
    water_rect = plt.Rectangle((0, 0), 0.4, 0, color='cyan', alpha=0.6)
    ax4.add_patch(water_rect)

    def init():
        line1.set_data([], [])
        line2.set_data([], [])
        line3.set_data([], [])
        water_rect.set_height(0)
        return line1, line2, line3, water_rect

    def animate(frame):
        t_current = t_vals[:frame+1]
        v_current = [find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, t) for t in t_current]
        h_current = [find_height_at_time(A_tube, A_0, h_0_initial, h_out, t) for t in t_current]
        Q_current = [v * A_tube * 1000 for v in v_current]

        line1.set_data(t_current, v_current)
        line2.set_data(t_current, h_current)
        line3.set_data(t_current, Q_current)

        water_rect.set_height(h_current[-1])

        return line1, line2, line3, water_rect

    anim = animation.FuncAnimation(fig, animate, init_func=init, frames=frames, interval=50, blit=True)
    filepath = os.path.join(output_dir, filename)
    anim.save(filepath, writer='pillow', fps=20)
    plt.close()
    print(f"Saved: {filepath}")

def animate_parameter_sweep(A_0, h_0_initial, h_out, output_dir, filename='parameter_sweep_animation.gif'):
    """Animate how velocity curve changes as k varies"""
    k_values = np.linspace(0.05, 0.25, 50)

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.set_xlabel('Time (s)', fontsize=12)
    ax.set_ylabel('Velocity (m/s)', fontsize=12)
    ax.set_title('Velocity vs Time: Parameter Sweep Animation', fontsize=14)
    ax.grid(True, alpha=0.3)

    # Find max time and velocity for axis limits
    max_t = max([find_time_to_empty(k*A_0, A_0, h_0_initial, h_out) for k in k_values])
    max_v = max([find_velocity(k*A_0, A_0, h_0_initial, h_out) for k in k_values])
    ax.set_xlim(0, max_t)
    ax.set_ylim(0, max_v * 1.1)

    line, = ax.plot([], [], 'b-', linewidth=2.5)
    text = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12, verticalalignment='top',
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

    def init():
        line.set_data([], [])
        text.set_text('')
        return line, text

    def animate(frame):
        k = k_values[frame]
        A_tube = k * A_0
        t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
        t = np.linspace(0, t_empty, 200)
        v = np.array([find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, ti) for ti in t])

        line.set_data(t, v)
        text.set_text(f'k = {k:.3f}\nA_tube = {A_tube:.4f} m²\nt_empty = {t_empty:.2f} s')
        return line, text

    anim = animation.FuncAnimation(fig, animate, init_func=init, frames=len(k_values), interval=100, blit=True)
    filepath = os.path.join(output_dir, filename)
    anim.save(filepath, writer='pillow', fps=10)
    plt.close()
    print(f"Saved: {filepath}")

# ============================================================================
# ADVANCED PLOTS: Reynolds Number Analysis
# ============================================================================

def plot_reynolds_number_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir, filename='reynolds_vs_time.png'):
    """Plot Reynolds number vs time with flow regime indicators"""
    D = get_tube_diameter(A_tube)
    t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
    t = np.linspace(0, t_empty, 200)

    Re_vals = []
    for ti in t:
        v = find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, ti)
        Re = calculate_reynolds_number(v, D)
        Re_vals.append(Re)

    Re_vals = np.array(Re_vals)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))

    # Plot 1: Reynolds number vs time
    ax1.plot(t, Re_vals, 'b-', linewidth=2)
    ax1.axhline(y=2300, color='orange', linestyle='--', linewidth=1.5, label='Laminar/Transitional (Re=2300)')
    ax1.axhline(y=4000, color='red', linestyle='--', linewidth=1.5, label='Transitional/Turbulent (Re=4000)')

    # Color-coded regions
    ax1.fill_between([0, t_empty], 0, 2300, color='green', alpha=0.1, label='Laminar')
    ax1.fill_between([0, t_empty], 2300, 4000, color='yellow', alpha=0.1, label='Transitional')
    ax1.fill_between([0, t_empty], 4000, max(Re_vals)*1.1, color='red', alpha=0.1, label='Turbulent')

    ax1.set_xlabel('Time (s)', fontsize=12)
    ax1.set_ylabel('Reynolds Number', fontsize=12)
    ax1.set_title(f'Reynolds Number vs Time\n(D = {D*1000:.2f} mm, μ = {mu*1000:.2f} mPa·s)', fontsize=13)
    ax1.legend(fontsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(0, max(Re_vals) * 1.1)

    # Plot 2: Flow regime percentage
    laminar_pct = np.sum(Re_vals < 2300) / len(Re_vals) * 100
    transitional_pct = np.sum((Re_vals >= 2300) & (Re_vals < 4000)) / len(Re_vals) * 100
    turbulent_pct = np.sum(Re_vals >= 4000) / len(Re_vals) * 100

    regimes = ['Laminar', 'Transitional', 'Turbulent']
    percentages = [laminar_pct, transitional_pct, turbulent_pct]
    colors_pie = ['green', 'yellow', 'red']

    ax2.pie(percentages, labels=regimes, colors=colors_pie, autopct='%1.1f%%', startangle=90)
    ax2.set_title('Flow Regime Distribution During Drainage', fontsize=13)

    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def plot_reynolds_vs_velocity(A_tube, output_dir, filename='reynolds_vs_velocity.png'):
    """Plot Reynolds number as function of velocity for different tube diameters"""
    v_range = np.linspace(0.1, 3, 100)
    D_values = [0.005, 0.01, 0.02, 0.05]  # Different diameters in meters
    colors = ['blue', 'green', 'orange', 'red']

    plt.figure(figsize=(10, 7))

    for D, color in zip(D_values, colors):
        Re_vals = [calculate_reynolds_number(v, D) for v in v_range]
        plt.plot(v_range, Re_vals, color=color, linewidth=2, label=f'D = {D*1000:.1f} mm')

    plt.axhline(y=2300, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='Laminar limit (Re=2300)')
    plt.axhline(y=4000, color='red', linestyle='--', linewidth=1.5, alpha=0.7, label='Turbulent limit (Re=4000)')

    plt.xlabel('Velocity (m/s)', fontsize=12)
    plt.ylabel('Reynolds Number', fontsize=12)
    plt.title(f'Reynolds Number vs Velocity\n(ρ = {rho} kg/m³, μ = {mu*1000:.2f} mPa·s)', fontsize=13)
    plt.legend(fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def create_all_plots(A_tube, A_0, h_0_initial, h_out, h_max=None):
    """Generate all four minimal plots in folder named by initial conditions"""
    # Create output directory based on initial conditions
    k = A_tube/A_0
    folder_name = f"Atube{A_tube}_A0{A_0}_h0{h_0_initial}_hout{h_out}"
    output_dir = os.path.join("plots", folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # Calculate results
    t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
    v_initial = find_velocity(A_tube, A_0, h_0_initial, h_out)
    Q_initial, Q_mass_initial = find_flow_rates(A_tube, A_0, h_0_initial, h_out)

    # Create metadata dictionary
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata = {
        "timestamp": timestamp,
        "initial_conditions": {
            "A_tube": {
                "value": A_tube,
                "unit": "m²",
                "description": "Tube cross-sectional area"
            },
            "A_0": {
                "value": A_0,
                "unit": "m²",
                "description": "Reservoir cross-sectional area"
            },
            "k": {
                "value": k,
                "unit": "dimensionless",
                "description": "Area ratio (A_tube/A_0)"
            },
            "h_0_initial": {
                "value": h_0_initial,
                "unit": "m",
                "description": "Initial reservoir height"
            },
            "h_out": {
                "value": h_out,
                "unit": "m",
                "description": "Outlet height"
            },
            "head": {
                "value": h_0_initial - h_out,
                "unit": "m",
                "description": "Initial head (h_0 - h_out)"
            }
        },
        "physical_constants": {
            "P_atm": {
                "value": P_atm,
                "unit": "Pa",
                "description": "Atmospheric pressure"
            },
            "P_vapor": {
                "value": P_vapor,
                "unit": "Pa",
                "description": "Vapor pressure at 20°C"
            },
            "rho": {
                "value": rho,
                "unit": "kg/m³",
                "description": "Water density"
            },
            "g": {
                "value": g,
                "unit": "m/s²",
                "description": "Gravitational acceleration"
            }
        },
        "calculated_results": {
            "v_initial": {
                "value": v_initial,
                "unit": "m/s",
                "description": "Initial velocity"
            },
            "Q_initial": {
                "value": Q_initial,
                "unit": "m³/s",
                "description": "Initial volumetric flow rate"
            },
            "Q_initial_L_per_s": {
                "value": Q_initial * 1000,
                "unit": "L/s",
                "description": "Initial volumetric flow rate"
            },
            "Q_mass_initial": {
                "value": Q_mass_initial,
                "unit": "kg/s",
                "description": "Initial mass flow rate"
            },
            "t_empty": {
                "value": t_empty,
                "unit": "s",
                "description": "Time to empty reservoir"
            }
        }
    }

    # Save metadata as JSON
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Generating plots in: {output_dir}")
    print(f"Metadata saved: {metadata_path}")

    plot_velocity_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir)
    plot_height_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir)
    plot_pressure_vs_height(h_out, output_dir, h_0_initial, h_max)
    plot_flow_rate_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir)
    print(f"All basic plots generated successfully in: {output_dir}")

def create_advanced_plots(A_tube, A_0, h_0_initial, h_out):
    """Generate all advanced plots in the same folder"""
    k = A_tube/A_0
    folder_name = f"Atube{A_tube}_A0{A_0}_h0{h_0_initial}_hout{h_out}"
    output_dir = os.path.join("plots", folder_name)
    os.makedirs(output_dir, exist_ok=True)

    print(f"\nGenerating advanced plots in: {output_dir}")

    # 3D and Contour plots
    print("Creating 3D/Contour plots...")
    plot_drainage_time_3d(h_out, output_dir)
    plot_drainage_time_contour(h_out, output_dir)
    plot_velocity_3d_parametric(A_0, h_out, output_dir)

    # Multiple scenario overlays
    print("Creating comparison plots...")
    plot_velocity_comparison(A_0, h_0_initial, h_out, output_dir)
    plot_height_comparison(A_0, h_out, output_dir)
    plot_flow_rate_comparison(A_0, h_0_initial, h_out, output_dir)

    # Reynolds number analysis
    print("Creating Reynolds number plots...")
    plot_reynolds_number_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir)
    plot_reynolds_vs_velocity(A_tube, output_dir)

    # Animations (these take longer)
    print("Creating animations (this may take a while)...")
    animate_drainage(A_tube, A_0, h_0_initial, h_out, output_dir)
    animate_parameter_sweep(A_0, h_0_initial, h_out, output_dir)

    print(f"\nAll advanced plots generated successfully in: {output_dir}")


if __name__ == "__main__":
    # Initial conditions from ber_syphon.py
    A_tube = 0.01    # m²
    A_0 = 0.1        # m²
    h_0 = 0.1        # m
    h_out = 0.06     # m

    # Create basic plots
    create_all_plots(A_tube, A_0, h_0, h_out)

    # Create advanced plots
    create_advanced_plots(A_tube, A_0, h_0, h_out)
