"""Primed-state solver for multi-segment siphon geometries."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .common import FluidProperties, ReservoirSetup, mass_flow_rate
from .multi_segment_physics import (
    LossBreakdown,
    SegmentedTube,
    TubeSegment,
    crest_pressures,
    solve_velocity,
)


def _validate_area_ratio(k: float) -> None:
    if k <= 0.0 or k >= 1.0:
        raise ValueError("The tube-to-reservoir area ratio must lie between 0 and 1.")


@dataclass(frozen=True)
class MultiSegmentConfig:
    """Configuration container for the segmented siphon solver."""

    reservoir: ReservoirSetup
    tube: SegmentedTube
    fluid: FluidProperties = FluidProperties()
    label: str = "multi-segment"

    def __post_init__(self) -> None:
        self.reservoir.validate()

    @property
    def area_ratio(self) -> float:
        return self.tube.area_ratio(self.reservoir.surface_area)


@dataclass(frozen=True)
class MultiSegmentInitialState:
    """Result of the primed-state calculation for a segmented siphon."""

    config: MultiSegmentConfig
    velocity: float
    flow_rate: float
    mass_flow_rate: float
    loss_breakdown: LossBreakdown
    node_heights: np.ndarray
    node_pressures: np.ndarray
    energy_heads: np.ndarray
    crest_pressures: tuple[tuple[int, float], ...]

    def to_metadata(self) -> dict:
        cfg = self.config
        metadata: dict[str, object] = {
            "label": cfg.label,
            "velocity_m_per_s": float(self.velocity),
            "flow_rate_m3_per_s": float(self.flow_rate),
            "mass_flow_rate_kg_per_s": float(self.mass_flow_rate),
            "reservoir": {
                "surface_area_m2": cfg.reservoir.surface_area,
                "initial_height_m": cfg.reservoir.initial_height,
                "outlet_height_m": cfg.reservoir.outlet_height,
            },
            "tube": {
                "entry_height_m": cfg.tube.entry_height,
                "outlet_height_m": cfg.tube.outlet_height,
                "diameter_m": cfg.tube.diameter,
                "area_m2": cfg.tube.area,
                "segments": [
                    {
                        "length_m": segment.length,
                        "angle_deg": segment.angle_deg,
                        "roughness_m": segment.roughness,
                        "minor_losses": list(segment.minor_loss_coefficients),
                    }
                    for segment in cfg.tube.segments
                ],
            },
            "loss_breakdown": {
                "entry_lambda": self.loss_breakdown.entry_lambda,
                "exit_lambda": self.loss_breakdown.exit_lambda,
                "segments": [
                    {
                        "index": loss.index,
                        "reynolds": loss.reynolds_number,
                        "friction_factor": loss.friction_factor,
                        "major_lambda": loss.major_lambda,
                        "minor_lambda": loss.minor_lambda,
                    }
                    for loss in self.loss_breakdown.segments
                ],
            },
            "node_heights_m": self.node_heights.tolist(),
            "node_pressures_Pa": self.node_pressures.tolist(),
            "crest_pressures_Pa": [
                {"node_index": idx, "pressure_Pa": pressure}
                for idx, pressure in self.crest_pressures
            ],
        }
        return metadata


def compute_initial_state(config: MultiSegmentConfig) -> MultiSegmentInitialState:
    """Compute the instantaneous discharge for a primed multi-crest siphon."""

    k = config.area_ratio
    _validate_area_ratio(k)

    head = config.reservoir.initial_head
    velocity, breakdown = solve_velocity(head, k, config.tube, config.fluid)
    flow = velocity * config.tube.area
    mass_flow = float(mass_flow_rate(np.array([flow]), config.fluid)[0])

    heights, pressures, energy_heads = config.tube.pressure_profile(velocity, config.fluid, breakdown)
    crest_data = crest_pressures(config.tube, heights, pressures)

    return MultiSegmentInitialState(
        config=config,
        velocity=float(velocity),
        flow_rate=float(flow),
        mass_flow_rate=mass_flow,
        loss_breakdown=breakdown,
        node_heights=heights,
        node_pressures=pressures,
        energy_heads=energy_heads,
        crest_pressures=crest_data,
    )


def save_metadata(state: MultiSegmentInitialState, output_path: str | Path) -> Path:
    """Persist the primed-state metadata as JSON."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(state.to_metadata(), handle, indent=2)
    return path


def _format_crest_report(state: MultiSegmentInitialState) -> str:
    lines = ["Crest pressures (Pa):"]
    if not state.crest_pressures:
        lines.append("  <no local maxima>")
    else:
        for idx, pressure in state.crest_pressures:
            lines.append(f"  Node {idx}: {pressure:,.1f}")
    return "\n".join(lines)


def describe_state(state: MultiSegmentInitialState) -> str:
    """Return a human-readable report for console output."""

    cfg = state.config
    lines = [
        f"Scenario: {cfg.label}",
        f"Reservoir head: {cfg.reservoir.initial_head:.4f} m",
        f"Velocity: {state.velocity:.4f} m/s",
        f"Volumetric flow: {state.flow_rate*1e3:.4f} L/s",
        f"Mass flow: {state.mass_flow_rate:.4f} kg/s",
        f"Total lambda: {state.loss_breakdown.total_lambda:.4f}",
        _format_crest_report(state),
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    # Rough demonstration using three segments: up to a crest, down past the outlet,
    # then a short tail toward the discharge reservoir.
    tube = SegmentedTube(
        entry_height=0.05,
        outlet_height=0.0,
        segments=[
            TubeSegment(length=0.4, diameter=0.01, angle_deg=45.0, minor_loss_coefficients=[0.5]),
            TubeSegment(length=0.4, diameter=0.01, angle_deg=-60.0, minor_loss_coefficients=[0.2]),
            TubeSegment(length=0.25, diameter=0.01, angle_deg=-10.0, minor_loss_coefficients=[1.0]),
        ],
        entry_minor_losses=(0.5,),
        exit_minor_losses=(1.0,),
    )

    reservoir = ReservoirSetup(surface_area=0.25, initial_height=0.6, outlet_height=0.0)
    config = MultiSegmentConfig(reservoir=reservoir, tube=tube, label="demo multi-crest")
    state = compute_initial_state(config)
    print(describe_state(state))
