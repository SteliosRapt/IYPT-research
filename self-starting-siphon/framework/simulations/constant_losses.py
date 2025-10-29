"""Siphon simulator with a constant head-loss coefficient.

Implements the analytical model derived in ``docs/constant_losses.md``.  The
loss coefficient encapsulates distributed and minor losses that do not vary with
flow rate, making the resulting equations closed form.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import math

from .ideal import (
    FluidProperties,
    IdealSiphonConfig,
    IdealSiphonResult,
    Reservoir,
    TubeGeometry,
    crest_pressure,
    height_at_time,
    velocity_at_time,
)

G = 9.80665


@dataclass(frozen=True)
class ConstantLossConfig(IdealSiphonConfig):
    """Extends :class:`IdealSiphonConfig` with a head-loss coefficient."""

    loss_coefficient: float = 0.0

    def __post_init__(self) -> None:  # type: ignore[override]
        super().__post_init__()
        if self.loss_coefficient < 0:
            raise ValueError("Loss coefficient must be non-negative.")

    @property
    def effective_area_ratio(self) -> float:
        return self.area_ratio


def drainage_time(config: ConstantLossConfig) -> float:
    k = config.area_ratio
    head = config.reservoir.initial_height - config.tube.outlet_height
    denom = 1 - k**2 + config.loss_coefficient
    if head <= 0:
        return 0.0
    return (2 * math.sqrt(denom) / (k * math.sqrt(2 * G))) * math.sqrt(head)


def height_at_time_with_losses(config: ConstantLossConfig, time: float) -> float:
    k = config.area_ratio
    denom = 1 - k**2 + config.loss_coefficient
    head0 = config.reservoir.initial_height - config.tube.outlet_height
    alpha = 0.5 * k * math.sqrt(2 * G / denom)
    remaining = max(0.0, math.sqrt(head0) - alpha * time)
    return config.tube.outlet_height + remaining**2


def velocity_at_time_with_losses(config: ConstantLossConfig, time: float) -> float:
    k = config.area_ratio
    denom = 1 - k**2 + config.loss_coefficient
    v0 = math.sqrt((2 * G * (config.reservoir.initial_height - config.tube.outlet_height)) / denom)
    slope = (k * G) / denom
    return max(0.0, v0 - slope * time)


def simulate_constant_losses(
    config: ConstantLossConfig,
    times: Iterable[float],
) -> IdealSiphonResult:
    """Return the closed-form solution evaluated at specific times."""

    times_list = list(times)
    heights = [height_at_time_with_losses(config, t) for t in times_list]
    velocities = [velocity_at_time_with_losses(config, t) for t in times_list]
    crest_pressures = [crest_pressure(config, h) for h in heights]
    outlet_pressures = [
        config.fluid.atmospheric_pressure
        + config.fluid.density * G * (h - config.tube.outlet_height)
        - 0.5 * config.fluid.density * velocities[i] ** 2
        for i, h in enumerate(heights)
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
