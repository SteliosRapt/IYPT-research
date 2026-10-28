"""Siphon simulation with velocity-dependent head losses."""

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
    TerminationStatus,
    TubeGeometry,
    ensure_output_dir,
    format_summary_box,
    mass_flow_rate,
)


def _validate_area_ratio(k: float) -> None:
    if k <= 0 or np.isclose(k, 0.0) or k >= 1 or np.isclose(k, 1.0):
        raise ValueError("The tube-to-reservoir area ratio must lie between 0 and 1.")


def _validate_head(head: float) -> None:
    if head <= 0:
        raise ValueError("The reservoir surface must remain above the outlet height.")


def _darcy_friction_factor(reynolds: float, relative_roughness: float) -> float:
    if reynolds <= 0:
        return 0.0
    if reynolds < 2000:
        return 64.0 / reynolds
    return 0.25 / (
        np.log10(relative_roughness / 3.7 + 5.74 / reynolds**0.9) ** 2
    )


def _loss_coefficient(config: SimulationConfig, velocity: float) -> float:
    if velocity <= 0:
        return config.tube.minor_losses

    fluid = config.fluid
    diameter = config.tube.diameter
    reynolds = fluid.density * velocity * diameter / fluid.viscosity
    reynolds = max(reynolds, 1.0)
    friction_factor = _darcy_friction_factor(reynolds, config.tube.relative_roughness)
    return friction_factor * (config.tube.length / diameter) + config.tube.minor_losses


def _solve_velocity(config: SimulationConfig, head: float) -> Tuple[float, float]:
    if head <= 0:
        return 0.0, config.tube.minor_losses

    g = config.fluid.gravity
    k = config.area_ratio
    ideal_velocity = np.sqrt(2 * g * head / max(1e-12, 1 - k**2))

    lower = 0.0
    upper = ideal_velocity
    for _ in range(80):
        mid = 0.5 * (lower + upper)
        loss_coeff = _loss_coefficient(config, mid)
        residual = mid**2 * (1 - k**2 + loss_coeff) - 2 * g * head
        if abs(residual) < 1e-8:
            return mid, loss_coeff
        if residual > 0:
            upper = mid
        else:
            lower = mid
    velocity = 0.5 * (lower + upper)
    return velocity, _loss_coefficient(config, velocity)


def simulate(
    config: SimulationConfig,
    time_step: float = 0.05,
    max_time: float = 3600.0,
) -> Tuple[SimulationResult, np.ndarray]:
    """Numerically integrate the siphon with velocity-dependent losses."""

    if not np.isfinite(time_step) or time_step <= 0:
        raise ValueError("time_step must be a positive, finite number.")
    if not np.isfinite(max_time) or max_time <= 0:
        raise ValueError("max_time must be a positive, finite number.")

    k = config.area_ratio
    _validate_area_ratio(k)

    head0 = config.reservoir.initial_head
    _validate_head(head0)

    time = 0.0
    height = config.reservoir.initial_height
    outlet_height = config.reservoir.outlet_height
    min_dt = np.nextafter(0.0, 1.0)

    times = [time]
    heights = [height]
    velocities = [0.0]
    flows = [0.0]
    loss_coeffs = [config.tube.minor_losses]

    while height > outlet_height and time < max_time:
        head = height - outlet_height
        velocity, loss_coeff = _solve_velocity(config, head)
        flow = velocity * config.area

        if velocity <= 0:
            dt = min(time_step, max(max_time - time, min_dt))
        else:
            remaining_head = max(head, 0.0)
            dt_limit = remaining_head / (k * max(velocity, min_dt))
            dt = min(time_step, 0.5 * dt_limit)
            dt = max(dt, min_dt)
            if time + dt > max_time:
                dt = max(max_time - time, min_dt)

        height = max(
            outlet_height,
            height - k * velocity * dt,
        )
        if time + dt == time:
            raise RuntimeError(
                f"Time step {dt!r} no longer advances time at t={time!r}; "
                "the integration has stalled."
            )
        time += dt

        times.append(time)
        heights.append(height)
        velocities.append(velocity)
        flows.append(flow)
        loss_coeffs.append(loss_coeff)

        if np.isclose(height, outlet_height, atol=1e-6):
            break

    drained = height <= outlet_height or np.isclose(height, outlet_height, atol=1e-6)
    status = TerminationStatus.COMPLETED if drained else TerminationStatus.MAX_TIME_REACHED

    if status is TerminationStatus.COMPLETED:
        velocities[-1] = 0.0
        flows[-1] = 0.0
    if len(velocities) > 1:
        velocities[0] = velocities[1]
        flows[0] = flows[1]
        loss_coeffs[0] = loss_coeffs[1]

    time_array = np.array(times)
    height_array = np.array(heights)
    velocity_array = np.array(velocities)
    flow_array = np.array(flows)
    loss_array = np.array(loss_coeffs)

    result = SimulationResult(
        config=config,
        time=time_array,
        height=height_array,
        velocity=velocity_array,
        flow_rate=flow_array,
        mass_flow_rate=mass_flow_rate(flow_array, config.fluid),
        drain_time=float(time_array[-1]),
        label="Varying losses",
        summary={
            "loss_coefficient_min": float(np.min(loss_array)),
            "loss_coefficient_max": float(np.max(loss_array)),
            "loss_coefficient_mean": float(np.mean(loss_array)),
            "termination_status": status.name,
        },
        termination_status=status,
    )
    return result, loss_array


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
        bbox=dict(boxstyle="round", facecolor="lavender", alpha=0.85),
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def create_plots(
    config: SimulationConfig,
    output_dir: str | Path,
    time_step: float = 0.05,
) -> SimulationResult:
    """Run the varying-loss simulation and persist plots and metadata."""

    result, loss_history = simulate(config, time_step=time_step)
    directory = ensure_output_dir(output_dir)

    summary_box = format_summary_box(result)
    summary_box += (
        f"\nΛ range: {loss_history.min():.2f} – {loss_history.max():.2f}"
        f"\nΛ mean: {loss_history.mean():.2f}"
    )

    initial_velocity = result.velocity[1] if result.velocity.size > 1 else result.velocity[0]
    velocity_annotation = summary_box + f"\nInitial velocity: {initial_velocity:.3f} m/s"
    _plot_series(
        result.time,
        result.velocity,
        "Time (s)",
        "Velocity (m/s)",
        "Velocity with varying losses",
        velocity_annotation,
        directory / "velocity_vs_time.png",
    )

    height_annotation = summary_box + f"\nOutlet height: {config.reservoir.outlet_height:.3f} m"
    _plot_series(
        result.time,
        result.height,
        "Time (s)",
        "Reservoir height (m)",
        "Reservoir level with varying losses",
        height_annotation,
        directory / "height_vs_time.png",
        extra_lines=((config.reservoir.outlet_height, {"color": "tab:red", "linestyle": "--"}),),
    )

    initial_flow = result.flow_rate[1] if result.flow_rate.size > 1 else result.flow_rate[0]
    flow_annotation = summary_box + f"\nInitial flow: {initial_flow*1e3:.3f} L/s"
    _plot_series(
        result.time,
        result.flow_rate * 1e3,
        "Time (s)",
        "Flow rate (L/s)",
        "Volumetric flow with varying losses",
        flow_annotation,
        directory / "flow_rate_vs_time.png",
        color="tab:green",
    )

    loss_annotation = summary_box + "\nDynamic Λ shown over drain interval"
    _plot_series(
        result.time,
        loss_history,
        "Time (s)",
        "Loss coefficient Λ",
        "Loss coefficient evolution",
        loss_annotation,
        directory / "loss_coefficient_vs_time.png",
        color="tab:orange",
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
            roughness=1.5e-4,
            minor_loss_coefficients=(0.5,),
        ),
        reservoir=ReservoirSetup(
            surface_area=0.5,
            initial_height=0.8,
            outlet_height=0.2,
        ),
        label="Varying losses",
    )
    create_plots(example_config, Path("plots/varying_losses"))
