"""Siphon model including distributed and minor losses."""

from math import sqrt
import os
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np

# Physical constants for water at 20 °C
P_ATM = 101300  # Pa
RHO = 998       # kg/m³
G = 9.81        # m/s²
MU = 0.001      # Pa·s


def _validate_area_ratio(A_tube: float, A_reservoir: float) -> float:
    if A_tube <= 0 or A_reservoir <= 0:
        raise ValueError("Cross-sectional areas must be positive.")

    k = A_tube / A_reservoir
    if not 0 < k < 1:
        raise ValueError("Area ratio k = A_tube/A_reservoir must lie between 0 and 1.")
    return k


def _validate_head(head: float) -> None:
    if head <= 0:
        raise ValueError("Reservoir surface must sit above the outlet (h_reservoir > h_outlet).")


def compute_velocity_with_losses(
    A_tube: float,
    A_reservoir: float,
    h_reservoir: float,
    h_outlet: float,
    loss_coefficient: float,
) -> float:
    """Return the instantaneous velocity including head losses.

    Args:
        A_tube: Tube cross-sectional area (m²).
        A_reservoir: Reservoir surface area (m²).
        h_reservoir: Current reservoir surface elevation (m).
        h_outlet: Outlet elevation (m).
        loss_coefficient: Dimensionless loss coefficient (fL/D + ΣK).
    """
    if loss_coefficient < 0:
        raise ValueError("Loss coefficient must be non-negative.")

    k = _validate_area_ratio(A_tube, A_reservoir)
    head = h_reservoir - h_outlet
    _validate_head(head)

    denominator = 1 - k**2 + loss_coefficient
    return sqrt(2 * G * head / denominator)


def compute_velocity_decay_rate(k: float, loss_coefficient: float) -> float:
    """Slope of the velocity-time relationship with losses."""
    return k * G / (1 - k**2 + loss_coefficient)


def height_over_time_with_losses(
    A_tube: float,
    A_reservoir: float,
    h_initial: float,
    h_outlet: float,
    loss_coefficient: float,
    t: np.ndarray,
) -> np.ndarray:
    """Analytical height evolution in the presence of a constant loss coefficient."""
    if np.any(t < 0):
        raise ValueError("Time values must be non-negative.")

    k = _validate_area_ratio(A_tube, A_reservoir)
    head_initial = h_initial - h_outlet
    _validate_head(head_initial)

    alpha = (k / 2) * sqrt(2 * G / (1 - k**2 + loss_coefficient))
    term = np.maximum(0.0, sqrt(head_initial) - alpha * t)
    return h_outlet + term**2


def velocity_over_time_with_losses(
    A_tube: float,
    A_reservoir: float,
    h_initial: float,
    h_outlet: float,
    loss_coefficient: float,
    t: np.ndarray,
) -> np.ndarray:
    """Linear velocity decay with constant losses."""
    if np.any(t < 0):
        raise ValueError("Time values must be non-negative.")

    k = _validate_area_ratio(A_tube, A_reservoir)
    head_initial = h_initial - h_outlet
    _validate_head(head_initial)

    v0 = sqrt(2 * G / (1 - k**2 + loss_coefficient)) * sqrt(head_initial)
    decay_rate = compute_velocity_decay_rate(k, loss_coefficient)
    v = v0 - decay_rate * t
    return np.clip(v, 0.0, None)


def time_to_empty_with_losses(
    A_tube: float,
    A_reservoir: float,
    h_initial: float,
    h_outlet: float,
    loss_coefficient: float,
) -> float:
    """Total drain time accounting for a constant loss coefficient."""
    k = _validate_area_ratio(A_tube, A_reservoir)
    head_initial = h_initial - h_outlet
    _validate_head(head_initial)

    return (2 * sqrt(1 - k**2 + loss_coefficient)) / (k * sqrt(2 * G)) * sqrt(head_initial)


def _ensure_output_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def plot_velocity_scenarios(
    A_tube: float,
    A_reservoir: float,
    h_initial: float,
    h_outlet: float,
    loss_coefficients: Iterable[float],
    output_dir: str,
    filename: str = "velocity_with_losses.png",
) -> str:
    """Plot velocity decay curves for multiple loss coefficients."""
    _ensure_output_dir(output_dir)

    times = np.linspace(0, max(
        time_to_empty_with_losses(A_tube, A_reservoir, h_initial, h_outlet, lc)
        for lc in loss_coefficients
    ), 250)

    plt.figure(figsize=(8, 6))
    for lc in loss_coefficients:
        t_empty = time_to_empty_with_losses(A_tube, A_reservoir, h_initial, h_outlet, lc)
        v = velocity_over_time_with_losses(
            A_tube, A_reservoir, h_initial, h_outlet, lc, times
        )
        plt.plot(times, v, label=f"Λ = {lc:.2f}, t_empty = {t_empty:.1f} s")

    plt.xlabel("Time (s)")
    plt.ylabel("Velocity (m/s)")
    plt.title("Siphon Velocity Decay with Head Losses")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


def plot_height_scenario(
    A_tube: float,
    A_reservoir: float,
    h_initial: float,
    h_outlet: float,
    loss_coefficient: float,
    output_dir: str,
    filename: str = "height_with_losses.png",
) -> str:
    """Plot reservoir height trajectory for a single loss coefficient."""
    _ensure_output_dir(output_dir)

    t_empty = time_to_empty_with_losses(A_tube, A_reservoir, h_initial, h_outlet, loss_coefficient)
    times = np.linspace(0, t_empty, 250)
    heights = height_over_time_with_losses(
        A_tube, A_reservoir, h_initial, h_outlet, loss_coefficient, times
    )

    plt.figure(figsize=(8, 6))
    plt.plot(times, heights, color="tab:green", label="Reservoir height")
    plt.axhline(h_outlet, color="tab:red", linestyle="--", label="Outlet elevation")
    plt.xlabel("Time (s)")
    plt.ylabel("Height (m)")
    plt.title(f"Reservoir Height with Loss Coefficient Λ = {loss_coefficient:.2f}")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path


if __name__ == "__main__":
    # Example scenario
    A_TUBE = 3.0e-4        # m² (~20 mm diameter)
    A_RESERVOIR = 0.04     # m²
    H_INITIAL = 0.75       # m
    H_OUTLET = 0.15        # m
    LOSS_CASES = [0.0, 1.5, 3.0]

    out_dir = os.path.join(os.path.dirname(__file__), "plots")
    velocity_path = plot_velocity_scenarios(
        A_TUBE, A_RESERVOIR, H_INITIAL, H_OUTLET, LOSS_CASES, out_dir
    )
    height_path = plot_height_scenario(
        A_TUBE, A_RESERVOIR, H_INITIAL, H_OUTLET, LOSS_CASES[-1], out_dir
    )

    print(f"Saved velocity comparison plot to {velocity_path}")
    print(f"Saved height trajectory plot to {height_path}")
