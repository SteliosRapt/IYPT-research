"""Ideal siphon simulation without head losses."""

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


def simulate(config: SimulationConfig, num_points: int = 400) -> SimulationResult:
    """Analytical solution for an ideal siphon without losses."""

    k = config.area_ratio
    _validate_area_ratio(k)

    g = config.fluid.gravity
    head0 = config.reservoir.initial_head

    t_empty = (2 * np.sqrt(1 - k**2)) / (k * np.sqrt(2 * g)) * np.sqrt(head0)
    times = time_grid(t_empty, num_points)

    v0 = np.sqrt(2 * g / (1 - k**2)) * np.sqrt(head0)
    velocity = np.maximum(0.0, v0 - k * g * times)

    alpha = (k / 2) * np.sqrt(2 * g / (1 - k**2))
    height = config.reservoir.outlet_height + np.maximum(0.0, np.sqrt(head0) - alpha * times) ** 2

    flow = velocity * config.area
    mass_flow = mass_flow_rate(flow, config.fluid)

    return SimulationResult(
        config=config,
        time=times,
        height=height,
        velocity=velocity,
        flow_rate=flow,
        mass_flow_rate=mass_flow,
        drain_time=float(t_empty),
        label="Ideal (no losses)",
        summary={"loss_coefficient": 0.0},
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
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.85),
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def create_plots(config: SimulationConfig, output_dir: str | Path) -> SimulationResult:
    """Run the ideal simulation and persist diagnostic plots and metadata."""

    result = simulate(config)
    directory = ensure_output_dir(output_dir)

    summary_box = format_summary_box(result)

    velocity_annotation = summary_box + f"\nInitial velocity: {result.velocity[0]:.3f} m/s"
    _plot_series(
        result.time,
        result.velocity,
        "Time (s)",
        "Velocity (m/s)",
        "Siphon velocity without losses",
        velocity_annotation,
        directory / "velocity_vs_time.png",
    )

    height_annotation = summary_box + f"\nOutlet height: {config.reservoir.outlet_height:.3f} m"
    _plot_series(
        result.time,
        result.height,
        "Time (s)",
        "Reservoir height (m)",
        "Reservoir level over time (ideal)",
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
        "Volumetric flow without losses",
        flow_annotation,
        directory / "flow_rate_vs_time.png",
        color="tab:green",
    )

    pressure = config.fluid.atmospheric_pressure + config.fluid.density * config.fluid.gravity * (
        config.reservoir.outlet_height - result.height
    )
    pressure_annotation = (
        summary_box
        + f"\nMin pressure: {pressure.min() / 1000:.1f} kPa\nVapour limit: {config.fluid.vapor_pressure / 1000:.1f} kPa"
    )
    _plot_series(
        pressure / 1000.0,
        result.height,
        "Pressure (kPa)",
        "Height (m)",
        "Pressure distribution along the tube",
        pressure_annotation,
        directory / "pressure_vs_height.png",
        color="tab:purple",
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
            minor_loss_coefficients=(0.5, 0.5),
        ),
        reservoir=ReservoirSetup(
            surface_area=0.5,
            initial_height=0.8,
            outlet_height=0.2,
        ),
        label="Ideal (no losses)",
    )
    create_plots(example_config, Path("plots/ideal"))
