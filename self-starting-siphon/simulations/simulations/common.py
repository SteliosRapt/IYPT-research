"""Common data structures and helpers for siphon simulations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Sequence

import numpy as np


@dataclass(frozen=True)
class FluidProperties:
    """Physical properties of the working fluid."""

    density: float = 998.0  # kg/m^3
    viscosity: float = 1.0e-3  # Pa·s
    gravity: float = 9.81  # m/s^2
    atmospheric_pressure: float = 101300.0  # Pa
    vapor_pressure: float = 2300.0  # Pa


@dataclass(frozen=True)
class TubeGeometry:
    """Geometric description of the siphon tube."""

    length: float  # m
    diameter: float  # m
    minor_loss_coefficients: Sequence[float] = field(default_factory=tuple)
    friction_factor: float | None = None
    roughness: float | None = None  # m, absolute roughness for turbulent models

    @property
    def area(self) -> float:
        radius = self.diameter / 2
        return np.pi * radius**2

    @property
    def relative_roughness(self) -> float:
        if self.roughness is None:
            return 0.0
        return max(self.roughness / self.diameter, 0.0)

    @property
    def minor_losses(self) -> float:
        return float(np.sum(self.minor_loss_coefficients)) if self.minor_loss_coefficients else 0.0

    def constant_loss_coefficient(self, friction_factor: float | None = None) -> float:
        """Return Λ = f L/D + ΣK for a supplied or stored friction factor."""

        f = friction_factor if friction_factor is not None else self.friction_factor
        if f is None:
            raise ValueError("A friction factor must be provided to compute constant losses.")
        return f * (self.length / self.diameter) + self.minor_losses


@dataclass(frozen=True)
class ReservoirSetup:
    """Reservoir geometry and reference elevations."""

    surface_area: float  # m^2
    initial_height: float  # m
    outlet_height: float  # m

    @property
    def initial_head(self) -> float:
        return self.initial_height - self.outlet_height

    def validate(self) -> None:
        if self.surface_area <= 0:
            raise ValueError("Reservoir surface area must be positive.")
        if self.initial_height <= self.outlet_height:
            raise ValueError("The reservoir surface must sit above the outlet height.")


@dataclass(frozen=True)
class SimulationConfig:
    """Container for all configuration required to run a simulation."""

    tube: TubeGeometry
    reservoir: ReservoirSetup
    fluid: FluidProperties = FluidProperties()
    label: str = "ideal"

    def __post_init__(self) -> None:
        self.reservoir.validate()
        if self.tube.diameter <= 0:
            raise ValueError("Tube diameter must be positive.")
        if self.tube.length <= 0:
            raise ValueError("Tube length must be positive.")

    @property
    def area_ratio(self) -> float:
        return self.tube.area / self.reservoir.surface_area

    @property
    def area(self) -> float:
        return self.tube.area


@dataclass
class SimulationResult:
    """Container for the outputs of a siphon simulation."""

    config: SimulationConfig
    time: np.ndarray
    height: np.ndarray
    velocity: np.ndarray
    flow_rate: np.ndarray
    mass_flow_rate: np.ndarray
    drain_time: float
    label: str
    summary: dict[str, float] | None = None

    def to_metadata(self) -> dict:
        """Return a JSON-serialisable payload describing the simulation."""

        cfg = self.config
        timestamp = datetime.utcnow().isoformat(timespec="seconds")
        metadata: dict[str, object] = {
            "timestamp": timestamp,
            "label": self.label,
            "drain_time_s": float(self.drain_time),
            "config": {
                "tube": {
                    "length_m": cfg.tube.length,
                    "diameter_m": cfg.tube.diameter,
                    "area_m2": cfg.tube.area,
                    "minor_losses": list(cfg.tube.minor_loss_coefficients),
                    "roughness_m": cfg.tube.roughness,
                    "friction_factor": cfg.tube.friction_factor,
                },
                "reservoir": {
                    "surface_area_m2": cfg.reservoir.surface_area,
                    "initial_height_m": cfg.reservoir.initial_height,
                    "outlet_height_m": cfg.reservoir.outlet_height,
                },
                "fluid": {
                    "density_kg_per_m3": cfg.fluid.density,
                    "viscosity_Pa_s": cfg.fluid.viscosity,
                    "gravity_m_per_s2": cfg.fluid.gravity,
                    "atmospheric_pressure_Pa": cfg.fluid.atmospheric_pressure,
                    "vapor_pressure_Pa": cfg.fluid.vapor_pressure,
                },
            },
        }
        if self.summary:
            metadata["summary"] = self.summary
        return metadata


def ensure_output_dir(path: str | Path) -> Path:
    """Create an output directory if it does not already exist."""

    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def mass_flow_rate(flow_rate: np.ndarray, fluid: FluidProperties) -> np.ndarray:
    return flow_rate * fluid.density


def format_summary_box(result: SimulationResult) -> str:
    cfg = result.config
    head = cfg.reservoir.initial_head
    return (
        f"Scenario: {result.label}\n"
        f"Drain time: {result.drain_time:.2f} s\n"
        f"Initial head: {head:.3f} m\n"
        f"Tube L/D: {cfg.tube.length / cfg.tube.diameter:.1f}\n"
        f"Area ratio k: {cfg.area_ratio:.4f}"
    )


def time_grid(duration: float, num_points: int) -> np.ndarray:
    if duration <= 0:
        return np.array([0.0])
    return np.linspace(0.0, duration, num_points)
