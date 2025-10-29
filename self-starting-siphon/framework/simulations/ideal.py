"""Ideal (lossless) siphon simulator.

This module codifies the closed-form relationships derived in
``docs/ideal_without_losses.md``.  It exposes light-weight dataclasses that
mirror the notation used throughout the documentation and helper functions to
compute velocities, heights, pressures, and complete time histories for a
lossless siphon draining a finite reservoir.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Sequence

import math

G = 9.80665  # m/s^2


@dataclass(frozen=True)
class FluidProperties:
    """Basic fluid properties used by the closed-form model."""

    density: float = 998.2  # kg/m^3 for water at ~20°C
    atmospheric_pressure: float = 101_325.0  # Pa
    vapor_pressure: float = 2_339.0  # Pa (water at 20°C)
    dynamic_viscosity: float = 1.002e-3  # Pa·s


@dataclass(frozen=True)
class Reservoir:
    """Finite reservoir feeding the siphon."""

    area: float  # m^2
    initial_height: float  # m, elevation of the free surface at t=0

    def validate(self) -> None:
        if self.area <= 0:
            raise ValueError("Reservoir area must be positive.")


@dataclass(frozen=True)
class TubeGeometry:
    """Geometric parameters of the siphon tube."""

    area: float  # m^2, assumed constant along the tube
    outlet_height: float  # m, datum for Bernoulli equations
    crest_height: float  # m, elevation of the highest point
    entry_height: float | None = None  # optional: intake elevation relative to datum

    def validate(self, reservoir: Reservoir) -> None:
        if self.area <= 0:
            raise ValueError("Tube area must be positive.")
        if self.outlet_height >= reservoir.initial_height:
            raise ValueError(
                "Outlet must sit below the initial reservoir surface for flow to start."
            )
        if self.crest_height < reservoir.initial_height:
            # Crest can be lower than reservoir surface, but warn if outrageous.
            pass
        if self.entry_height is not None and self.entry_height > reservoir.initial_height:
            raise ValueError("Inlet/entry height cannot exceed the reservoir surface.")

    @property
    def radius(self) -> float:
        return math.sqrt(self.area / math.pi)


@dataclass(frozen=True)
class IdealSiphonConfig:
    """Container bundling reservoir, tube, and fluid data."""

    reservoir: Reservoir
    tube: TubeGeometry
    fluid: FluidProperties = field(default_factory=FluidProperties)

    def __post_init__(self) -> None:
        self.reservoir.validate()
        self.tube.validate(self.reservoir)
        if self.area_ratio >= 1:
            raise ValueError(
                "The lossless derivation assumes a small tube relative to the reservoir"
                " (A_tube / A_reservoir < 1)."
            )

    @property
    def area_ratio(self) -> float:
        return self.tube.area / self.reservoir.area


@dataclass(frozen=True)
class IdealSiphonResult:
    """Time history returned by :func:`simulate_ideal`."""

    time: Sequence[float]
    surface_height: Sequence[float]
    velocity: Sequence[float]
    crest_pressure: Sequence[float]
    outlet_pressure: Sequence[float]
    termination_reason: str


def velocity_from_height(config: IdealSiphonConfig, surface_height: float) -> float:
    """Instantaneous tube velocity at a given reservoir surface height."""

    if surface_height <= config.tube.outlet_height:
        return 0.0
    k = config.area_ratio
    return math.sqrt(
        (2 * G * (surface_height - config.tube.outlet_height)) / (1 - k**2)
    )


def drainage_time(config: IdealSiphonConfig) -> float:
    """Closed-form drainage time for the reservoir."""

    k = config.area_ratio
    head = config.reservoir.initial_height - config.tube.outlet_height
    if head <= 0:
        return 0.0
    return (2 * math.sqrt(1 - k**2) / (k * math.sqrt(2 * G))) * math.sqrt(head)


def height_at_time(config: IdealSiphonConfig, time: float) -> float:
    """Reservoir surface height as a function of time."""

    k = config.area_ratio
    head0 = config.reservoir.initial_height - config.tube.outlet_height
    alpha = 0.5 * k * math.sqrt(2 * G / (1 - k**2))
    remaining = max(0.0, math.sqrt(head0) - alpha * time)
    return config.tube.outlet_height + remaining**2


def velocity_at_time(config: IdealSiphonConfig, time: float) -> float:
    """Tube velocity as a function of time."""

    v0 = velocity_from_height(config, config.reservoir.initial_height)
    k = config.area_ratio
    slope = (k * G) / (1 - k**2)
    v = max(0.0, v0 - slope * time)
    return v


def pressure_at_height(
    config: IdealSiphonConfig, surface_height: float, elevation: float
) -> float:
    """Absolute pressure at a point along the tube."""

    v = velocity_from_height(config, surface_height)
    k = config.area_ratio
    dynamic_term = 0.5 * config.fluid.density * (k**2 - 1) * v**2
    hydrostatic_term = config.fluid.density * G * (surface_height - elevation)
    return config.fluid.atmospheric_pressure + dynamic_term + hydrostatic_term


def crest_pressure(config: IdealSiphonConfig, surface_height: float) -> float:
    entry_height = config.tube.entry_height
    if entry_height is not None:
        crest_height = entry_height
    else:
        crest_height = config.tube.crest_height
    return pressure_at_height(config, surface_height, crest_height)


def simulate_ideal(
    config: IdealSiphonConfig,
    times: Iterable[float],
) -> IdealSiphonResult:
    """Evaluate the analytical solutions at the provided time samples."""

    times_list = list(times)
    heights = [height_at_time(config, t) for t in times_list]
    velocities = [velocity_at_time(config, t) for t in times_list]
    crest_pressures = [crest_pressure(config, h) for h in heights]
    outlet_pressures = [
        pressure_at_height(config, h, config.tube.outlet_height) for h in heights
    ]

    termination = (
        "completed"
        if times_list and times_list[-1] >= drainage_time(config)
        else "incomplete-grid"
    )
    return IdealSiphonResult(
        time=times_list,
        surface_height=heights,
        velocity=velocities,
        crest_pressure=crest_pressures,
        outlet_pressure=outlet_pressures,
        termination_reason=termination,
    )
