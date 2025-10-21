"""Utilities to run and visualise all siphon simulations together."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path
from typing import Callable, Iterable, Sequence

import matplotlib.pyplot as plt
import numpy as np

from . import constant_losses, ideal, variable_losses
from .common import SimulationConfig, SimulationResult, ensure_output_dir


def _comparison_plot(
    results: Sequence[SimulationResult],
    y_getter: Callable[[SimulationResult], np.ndarray],
    ylabel: str,
    title: str,
    output_path: Path,
    annotation: str,
    colors: Sequence[str],
    y_transform: Callable[[np.ndarray], np.ndarray] | None = None,
    extra_lines: Iterable[tuple[float, dict]] | None = None,
) -> None:
    plt.figure(figsize=(9, 6))
    for result, color in zip(results, colors):
        values = y_getter(result)
        if y_transform is not None:
            values = y_transform(values)
        plt.plot(result.time, values, label=result.label, color=color, linewidth=2)
    if extra_lines:
        for value, kwargs in extra_lines:
            plt.axhline(value, **kwargs)
    plt.xlabel("Time (s)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.text(
        0.02,
        0.98,
        annotation,
        transform=plt.gca().transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="left",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()


def run_all(
    config: SimulationConfig,
    output_dir: str | Path,
    constant_loss: float | None = None,
    time_step: float = 0.05,
) -> dict[str, SimulationResult]:
    """Run all three simulation flavours and build comparison plots."""

    directory = ensure_output_dir(output_dir)

    ideal_config = replace(config, label="Ideal (no losses)")
    constant_config = replace(config, label="Constant losses")
    varying_config = replace(config, label="Varying losses")

    ideal_result = ideal.simulate(ideal_config)
    constant_result = constant_losses.simulate(constant_config, loss_coefficient=constant_loss)
    varying_result, loss_history = variable_losses.simulate(varying_config, time_step=time_step)

    if constant_loss is None:
        constant_loss = constant_config.tube.constant_loss_coefficient()

    summary_lines = [
        f"{ideal_result.label}: t = {ideal_result.drain_time:.2f} s",
        f"{constant_result.label}: t = {constant_result.drain_time:.2f} s",
        f"{varying_result.label}: t = {varying_result.drain_time:.2f} s",
        f"Λ (constant): {constant_loss:.2f}",
        f"Λ (varying mean): {loss_history.mean():.2f}",
    ]
    annotation = "\n".join(summary_lines)

    colors = ("tab:blue", "tab:red", "tab:green")

    _comparison_plot(
        (ideal_result, constant_result, varying_result),
        lambda result: result.velocity,
        "Velocity (m/s)",
        "Velocity comparison across simulations",
        Path(directory) / "velocity_comparison.png",
        annotation,
        colors,
    )

    _comparison_plot(
        (ideal_result, constant_result, varying_result),
        lambda result: result.height,
        "Reservoir height (m)",
        "Reservoir height comparison",
        Path(directory) / "height_comparison.png",
        annotation,
        colors,
        extra_lines=((config.reservoir.outlet_height, {"color": "tab:gray", "linestyle": "--"}),),
    )

    _comparison_plot(
        (ideal_result, constant_result, varying_result),
        lambda result: result.flow_rate,
        "Flow rate (L/s)",
        "Volumetric flow comparison",
        Path(directory) / "flow_comparison.png",
        annotation,
        colors,
        y_transform=lambda values: values * 1e3,
    )

    plt.figure(figsize=(9, 6))
    plt.plot(varying_result.time, loss_history, color="tab:green", label="Varying losses")
    plt.axhline(constant_loss, color="tab:red", linestyle="--", label="Constant Λ")
    plt.xlabel("Time (s)")
    plt.ylabel("Loss coefficient Λ")
    plt.title("Loss coefficient behaviour")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.text(
        0.02,
        0.98,
        annotation,
        transform=plt.gca().transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="left",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85),
    )
    plt.tight_layout()
    plt.savefig(Path(directory) / "loss_comparison.png", dpi=150)
    plt.close()

    metadata = {
        "ideal": ideal_result.to_metadata(),
        "constant": constant_result.to_metadata(),
        "varying": varying_result.to_metadata(),
        "comparison": {
            "constant_loss_coefficient": constant_loss,
            "varying_loss_mean": float(loss_history.mean()),
            "varying_loss_min": float(loss_history.min()),
            "varying_loss_max": float(loss_history.max()),
        },
    }

    metadata_path = Path(directory) / "comparison_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)

    return {
        "ideal": ideal_result,
        "constant": constant_result,
        "varying": varying_result,
    }


if __name__ == "__main__":
    raise SystemExit(
        "Comparison module is intended to be imported and orchestrated from an application script."
    )
