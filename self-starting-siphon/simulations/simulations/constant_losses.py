"""Siphon simulation with a constant head-loss coefficient."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np

from .common import (
    ReservoirSetup,
    SimulationConfig,
    SimulationResult,
    TubeGeometry,
    ensure_output_dir,
    format_summary_box,
    mass_flow_rate,
    time_grid,
)


def _validate_area_ratio(k: float) -> None:
    if k <= 0 or k >= 1:
        raise ValueError("The tube-to-reservoir area ratio must lie between 0 and 1.")


def _validate_head(head: float) -> None:
    if head <= 0:
        raise ValueError("The reservoir surface must remain above the outlet height.")


def simulate(
    config: SimulationConfig,
    loss_coefficient: float | None = None,
    num_points: int = 400,
) -> SimulationResult:
    """Analytical solution including a constant loss coefficient."""

    k = config.area_ratio
    _validate_area_ratio(k)

    head0 = config.reservoir.initial_head
    _validate_head(head0)

    if loss_coefficient is None:
        loss_coefficient = config.tube.constant_loss_coefficient()
    if loss_coefficient < 0:
        raise ValueError("The loss coefficient must be non-negative.")

    g = config.fluid.gravity
    denom = 1 - k**2 + loss_coefficient

    t_empty = (2 * np.sqrt(denom)) / (k * np.sqrt(2 * g)) * np.sqrt(head0)
    times = time_grid(t_empty, num_points)

    v0 = np.sqrt(2 * g / denom) * np.sqrt(head0)
    decay_rate = k * g / denom
    velocity = np.maximum(0.0, v0 - decay_rate * times)

    alpha = (k / 2) * np.sqrt(2 * g / denom)
    height = config.reservoir.outlet_height + np.maximum(0.0, np.sqrt(head0) - alpha * times) ** 2

    flow = velocity * config.area
    mass_flow = mass_flow_rate(flow, config.fluid)

    label = f"Constant losses (Λ = {loss_coefficient:.2f})"
    return SimulationResult(
        config=config,
        time=times,
        height=height,
        velocity=velocity,
        flow_rate=flow,
        mass_flow_rate=mass_flow,
        drain_time=float(t_empty),
        label=label,
        summary={"loss_coefficient": float(loss_coefficient)},
    )


def _plot_series(
    x: np.ndarray,
    y: np.ndarray,
    xlabel: str,
    ylabel: str,
    title: str,
    annotation: str,
    output_path: Path,
    color: str = "tab:blue",
    extra_lines: Tuple[Tuple[float, dict], ...] | None = None,
) -> None:
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, color=color, linewidth=2)
    if extra_lines:
        for value, kwargs in extra_lines:
            plt.axhline(value, **kwargs)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.text(
        0.02,
        0.98,
        annotation,
        transform=plt.gca().transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="left",
        bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.85),
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def create_plots(
    config: SimulationConfig,
    output_dir: str | Path,
    loss_coefficient: float | None = None,
) -> SimulationResult:
    """Run the constant-loss simulation and persist plots and metadata."""

    if loss_coefficient is None:
        loss_coefficient = config.tube.constant_loss_coefficient()

    result = simulate(config, loss_coefficient=loss_coefficient)
    directory = ensure_output_dir(output_dir)

    summary_box = format_summary_box(result) + f"\nΛ = {loss_coefficient:.3f}"

    velocity_annotation = summary_box + f"\nInitial velocity: {result.velocity[0]:.3f} m/s"
    _plot_series(
        result.time,
        result.velocity,
        "Time (s)",
        "Velocity (m/s)",
        "Velocity decay with constant losses",
        velocity_annotation,
        directory / "velocity_vs_time.png",
    )

    height_annotation = summary_box + f"\nOutlet height: {config.reservoir.outlet_height:.3f} m"
    _plot_series(
        result.time,
        result.height,
        "Time (s)",
        "Reservoir height (m)",
        "Reservoir level with constant losses",
        height_annotation,
        directory / "height_vs_time.png",
        extra_lines=((config.reservoir.outlet_height, {"color": "tab:red", "linestyle": "--"}),),
    )

    flow_annotation = summary_box + f"\nInitial flow: {result.flow_rate[0]*1e3:.3f} L/s"
    _plot_series(
        result.time,
        result.flow_rate * 1e3,
        "Time (s)",
        "Flow rate (L/s)",
        "Volumetric flow with constant losses",
        flow_annotation,
        directory / "flow_rate_vs_time.png",
        color="tab:green",
    )

    metadata_path = directory / "metadata.json"
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(result.to_metadata(), handle, indent=2)

    return result


if __name__ == "__main__":
    example_config = SimulationConfig(
        tube=TubeGeometry(
            length=1.2,
            diameter=0.02,
            friction_factor=0.02,
            minor_loss_coefficients=(0.5,),
        ),
        reservoir=ReservoirSetup(
            surface_area=0.5,
            initial_height=0.8,
            outlet_height=0.2,
        ),
        label="Constant losses",
    )
    create_plots(example_config, Path("plots/constant_losses"))
