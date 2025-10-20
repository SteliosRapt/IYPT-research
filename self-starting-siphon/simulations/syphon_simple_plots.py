from math import sqrt
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import os
import json

P_atm = 101300   # Pa (atmospheric pressure)
P_vapor = 2300   # Pa (vapor pressure of water at 20°C)
rho = 998        # kg/m³ (water density at 20°C)
g = 9.81         # m/s²

def find_velocity(A_tube, A_0, h_0, h_out):
    """Calculate instantaneous velocity at height h_0"""
    k = A_tube/A_0
    head = h_0 - h_out
    v = sqrt(2*g*head/(1 - k**2))
    return v

def find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, t):
    """Calculate velocity as a function of time"""
    k = A_tube/A_0
    v_initial = sqrt(2*g/(1-k**2)) * sqrt(h_0_initial - h_out)
    v_t = v_initial - k*g*t
    return max(0, v_t)

def find_height_at_time(A_tube, A_0, h_0_initial, h_out, t):
    """Calculate reservoir height as a function of time"""
    k = A_tube/A_0
    alpha = (k/2) * sqrt(2*g/(1-k**2))
    term = sqrt(h_0_initial - h_out) - alpha*t
    if term <= 0:
        return h_out
    h_t = h_out + term**2
    return h_t

def find_time_to_empty(A_tube, A_0, h_0_initial, h_out):
    """Calculate total time to empty reservoir"""
    k = A_tube/A_0
    t_empty = (2*sqrt(1 - k**2))/(k*sqrt(2*g)) * sqrt(h_0_initial - h_out)
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

def plot_velocity_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir, filename='velocity_vs_time.png'):
    """Plot velocity as a function of time"""
    k = A_tube/A_0
    t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
    t = np.linspace(0, t_empty, 200)
    v = np.array([find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, ti) for ti in t])
    v_initial = find_velocity(A_tube, A_0, h_0_initial, h_out)

    plt.figure(figsize=(8, 6))
    plt.plot(t, v, 'b-', linewidth=2)
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Velocity (m/s)', fontsize=12)

    # Add equation and parameters as text box
    equation_text = f'$v(t) = v_0 - kg t$\n'
    equation_text += f'$v_0 = \\sqrt{{\\frac{{2g(h_0 - h_{{out}})}}{{1 - k^2}}}}$\n\n'
    equation_text += f'$k = {k:.4f}$\n'
    equation_text += f'$v_0 = {v_initial:.4f}$ m/s\n'
    equation_text += f'$t_{{empty}} = {t_empty:.4f}$ s'

    plt.text(0.98, 0.98, equation_text, transform=plt.gca().transAxes,
             fontsize=9, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

    plt.title('Syphon Velocity vs Time', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def plot_height_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir, filename='height_vs_time.png'):
    """Plot reservoir height as a function of time"""
    k = A_tube/A_0
    t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
    t = np.linspace(0, t_empty, 200)
    h = np.array([find_height_at_time(A_tube, A_0, h_0_initial, h_out, ti) for ti in t])
    alpha = (k/2) * sqrt(2*g/(1-k**2))

    plt.figure(figsize=(8, 6))
    plt.plot(t, h, 'g-', linewidth=2)
    plt.axhline(y=h_out, color='r', linestyle='--', label=f'Outlet height = {h_out} m')
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Reservoir Height (m)', fontsize=12)

    # Add equation and parameters as text box
    equation_text = f'$h_0(t) = h_{{out}} + (\\sqrt{{h_{{0,i}} - h_{{out}}}} - \\alpha t)^2$\n'
    equation_text += f'$\\alpha = \\frac{{k}}{{2}}\\sqrt{{\\frac{{2g}}{{1-k^2}}}}$\n\n'
    equation_text += f'$k = {k:.4f}$\n'
    equation_text += f'$\\alpha = {alpha:.4f}$ m/s$^{{1/2}}$\n'
    equation_text += f'$h_{{0,i}} = {h_0_initial:.4f}$ m\n'
    equation_text += f'$h_{{out}} = {h_out:.4f}$ m'

    plt.text(0.02, 0.98, equation_text, transform=plt.gca().transAxes,
             fontsize=9, verticalalignment='top', horizontalalignment='left',
             bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.8))

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
        h_max = h_out + 0.5

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

    # Add equation and parameters as text box
    equation_text = f'$P(h) = P_{{atm}} + \\rho g (h_{{out}} - h)$\n\n'
    equation_text += f'$P_{{atm}} = {P_atm/1000:.1f}$ kPa\n'
    equation_text += f'$\\rho = {rho}$ kg/m³\n'
    equation_text += f'$g = {g}$ m/s²\n'
    equation_text += f'$h_{{out}} = {h_out:.4f}$ m'

    plt.text(0.02, 0.02, equation_text, transform=plt.gca().transAxes,
             fontsize=9, verticalalignment='bottom', horizontalalignment='left',
             bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))

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
    k = A_tube/A_0
    t_empty = find_time_to_empty(A_tube, A_0, h_0_initial, h_out)
    t = np.linspace(0, t_empty, 200)
    Q = np.array([find_velocity_at_time(A_tube, A_0, h_0_initial, h_out, ti) * A_tube for ti in t])
    Q_initial, _ = find_flow_rates(A_tube, A_0, h_0_initial, h_out)

    plt.figure(figsize=(8, 6))
    plt.plot(t, Q*1000, 'r-', linewidth=2)
    plt.xlabel('Time (s)', fontsize=12)
    plt.ylabel('Flow Rate (L/s)', fontsize=12)

    # Add equation and parameters as text box
    equation_text = f'$Q(t) = A_{{tube}} \\cdot v(t)$\n'
    equation_text += f'$Q(t) = A_{{tube}} (v_0 - kg t)$\n\n'
    equation_text += f'$A_{{tube}} = {A_tube:.4f}$ m²\n'
    equation_text += f'$k = {k:.4f}$\n'
    equation_text += f'$Q_0 = {Q_initial*1000:.4f}$ L/s\n'
    equation_text += f'$t_{{empty}} = {t_empty:.4f}$ s'

    plt.text(0.98, 0.98, equation_text, transform=plt.gca().transAxes,
             fontsize=9, verticalalignment='top', horizontalalignment='right',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

    plt.title('Volumetric Flow Rate vs Time', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    filepath = os.path.join(output_dir, filename)
    plt.savefig(filepath, dpi=150)
    plt.close()
    print(f"Saved: {filepath}")

def create_simple_plots(A_tube, A_0, h_0_initial, h_out, h_max=None):
    """Generate 4 basic plots with metadata"""
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
            "A_tube": {"value": A_tube, "unit": "m²", "description": "Tube cross-sectional area"},
            "A_0": {"value": A_0, "unit": "m²", "description": "Reservoir cross-sectional area"},
            "k": {"value": k, "unit": "dimensionless", "description": "Area ratio (A_tube/A_0)"},
            "h_0_initial": {"value": h_0_initial, "unit": "m", "description": "Initial reservoir height"},
            "h_out": {"value": h_out, "unit": "m", "description": "Outlet height"},
            "head": {"value": h_0_initial - h_out, "unit": "m", "description": "Initial head (h_0 - h_out)"}
        },
        "physical_constants": {
            "P_atm": {"value": P_atm, "unit": "Pa", "description": "Atmospheric pressure"},
            "P_vapor": {"value": P_vapor, "unit": "Pa", "description": "Vapor pressure at 20°C"},
            "rho": {"value": rho, "unit": "kg/m³", "description": "Water density"},
            "g": {"value": g, "unit": "m/s²", "description": "Gravitational acceleration"}
        },
        "calculated_results": {
            "v_initial": {"value": v_initial, "unit": "m/s", "description": "Initial velocity"},
            "Q_initial": {"value": Q_initial, "unit": "m³/s", "description": "Initial volumetric flow rate"},
            "Q_initial_L_per_s": {"value": Q_initial * 1000, "unit": "L/s", "description": "Initial volumetric flow rate"},
            "Q_mass_initial": {"value": Q_mass_initial, "unit": "kg/s", "description": "Initial mass flow rate"},
            "t_empty": {"value": t_empty, "unit": "s", "description": "Time to empty reservoir"}
        }
    }

    # Save metadata as JSON
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"Generating simple plots in: {output_dir}")
    print(f"Metadata saved: {metadata_path}")

    # Generate 4 basic plots
    plot_velocity_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir)
    plot_height_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir)
    plot_pressure_vs_height(h_out, output_dir, h_0_initial, h_max)
    plot_flow_rate_vs_time(A_tube, A_0, h_0_initial, h_out, output_dir)

    print(f"All simple plots generated successfully in: {output_dir}")


if __name__ == "__main__":
    # Initial conditions from ber_syphon.py
    A_tube = 0.01    # m²
    A_0 = 0.1        # m²
    h_0 = 0.1        # m
    h_out = 0.06     # m

    # Create simple plots only
    create_simple_plots(A_tube, A_0, h_0, h_out)
