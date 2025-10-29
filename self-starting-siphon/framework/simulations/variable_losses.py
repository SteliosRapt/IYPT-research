"""Numerical siphon simulator with dynamic losses and regime transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence

import math

from .ideal import FluidProperties, IdealSiphonResult, Reservoir, TubeGeometry

G = 9.80665


@dataclass(frozen=True)
class SiphonSegment:
    """Piecewise-uniform description of the siphon tube."""

    length: float  # m
    diameter: float  # m
    roughness: float = 0.0  # m
    minor_loss: float = 0.0  # dimensionless K coefficient

    def __post_init__(self) -> None:
        if self.length <= 0:
            raise ValueError("Segment length must be positive.")
        if self.diameter <= 0:
            raise ValueError("Segment diameter must be positive.")
        if self.roughness < 0:
            raise ValueError("Segment roughness cannot be negative.")
        if self.minor_loss < 0:
            raise ValueError("Minor loss coefficients must be non-negative.")

    @property
    def area(self) -> float:
        return math.pi * (self.diameter / 2.0) ** 2


@dataclass(frozen=True)
class VariableLossConfig:
    """Configuration for the fully dynamic siphon simulator."""

    reservoir: Reservoir
    tube: TubeGeometry
    segments: Sequence[SiphonSegment]
    fluid: FluidProperties = field(default_factory=FluidProperties)
    max_time: float = 10_000.0
    max_steps: int = 100_000
    time_step: float = 0.05
    min_time_step: float = 1e-6
    newton_tolerance: float = 1e-8
    cavitation_margin: float = 0.0

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("At least one segment is required.")
        self.reservoir.validate()
        self.tube.validate(self.reservoir)
        if self.max_time <= 0 or self.max_steps <= 0:
            raise ValueError("max_time and max_steps must be positive.")
        if self.time_step <= 0 or self.min_time_step <= 0:
            raise ValueError("time_step and min_time_step must be positive.")
        if self.min_time_step > self.time_step:
            raise ValueError("min_time_step cannot exceed time_step.")

    @property
    def outlet_area(self) -> float:
        return self.segments[-1].area

    @property
    def crest_area(self) -> float:
        return self.segments[0].area

    @property
    def crest_height(self) -> float:
        if self.tube.entry_height is not None:
            return self.tube.entry_height
        return self.tube.crest_height


@dataclass(frozen=True)
class VariableLossResult(IdealSiphonResult):
    """Extends the standard result object with extra diagnostics."""

    reynolds_number: Sequence[float]
    total_loss_coefficient: Sequence[float]
    termination_reason: str


def _segment_reynolds(
    flow_rate: float, segment: SiphonSegment, fluid: FluidProperties
) -> float:
    velocity = flow_rate / segment.area
    return (fluid.density * velocity * segment.diameter) / fluid.dynamic_viscosity


def _friction_factor(reynolds: float, segment: SiphonSegment) -> tuple[float, float]:
    """Return Darcy friction factor and d(f)/d(Re)."""

    if reynolds <= 0:
        return float("inf"), 0.0
    if reynolds < 2_100:
        f = 64.0 / reynolds
        df_dre = -64.0 / (reynolds**2)
        return f, df_dre
    rough_term = segment.roughness / segment.diameter / 3.7
    turb_term = 5.74 / (reynolds**0.9)
    log_arg = rough_term + turb_term
    log_val = math.log10(log_arg)
    f = 0.25 / (log_val**2)
    dlog_dre = (-0.9 * 5.74 / (reynolds**1.9)) / (log_arg * math.log(10))
    df_dre = -0.5 / (log_val**3) * dlog_dre
    return f, df_dre


def _loss_coefficient(flow_rate: float, config: VariableLossConfig) -> tuple[float, float]:
    """Return total loss coefficient and its derivative w.r.t flow."""

    total = 0.0
    dtotal_dq = 0.0
    fluid = config.fluid
    for segment in config.segments:
        area = segment.area
        reynolds = _segment_reynolds(flow_rate, segment, fluid)
        dRe_dq = (fluid.density * segment.diameter) / (fluid.dynamic_viscosity * area)
        friction, df_dre = _friction_factor(reynolds, segment)
        df_dq = df_dre * dRe_dq
        total += friction * (segment.length / segment.diameter) + segment.minor_loss
        dtotal_dq += df_dq * (segment.length / segment.diameter)
    return total, dtotal_dq


def _energy_balance(
    flow_rate: float, head: float, config: VariableLossConfig
) -> tuple[float, float, float]:
    """Return (Phi(Q), dPhi/dQ, total loss coefficient)."""

    if flow_rate <= 0:
        return -head, 0.0, 0.0
    area_out = config.outlet_area
    dynamic = (flow_rate**2) / (2 * G * area_out**2)
    d_dynamic = flow_rate / (G * area_out**2)
    loss, dloss_dq = _loss_coefficient(flow_rate, config)
    phi = dynamic * (1 + loss) - head
    dphi = d_dynamic * (1 + loss) + dynamic * dloss_dq
    return phi, dphi, loss


def _solve_flow(head: float, config: VariableLossConfig, guess: float) -> tuple[float, float]:
    flow = max(guess, 1e-9)
    for _ in range(40):
        phi, dphi, loss = _energy_balance(flow, head, config)
        if abs(phi) < config.newton_tolerance:
            return flow, loss
        if dphi == 0:
            break
        flow -= phi / dphi
        if flow <= 0:
            flow = max(guess / 2.0, 1e-6)
    lower = 0.0
    upper = max(flow * 2.0, 1e-6)
    for _ in range(100):
        mid = 0.5 * (lower + upper)
        phi, _, loss = _energy_balance(mid, head, config)
        if abs(phi) < config.newton_tolerance:
            return mid, loss
        if phi > 0:
            upper = mid
        else:
            lower = mid
    return mid, loss


def simulate_variable_losses(config: VariableLossConfig) -> VariableLossResult:
    """March the nonlinear drainage problem forward in time."""

    times: List[float] = []
    heights: List[float] = []
    velocities: List[float] = []
    crest_pressures: List[float] = []
    outlet_pressures: List[float] = []
    reynolds_values: List[float] = []
    lambda_values: List[float] = []

    height = config.reservoir.initial_height
    time = 0.0
    dt = config.time_step
    guess_flow = 0.0
    steps = 0
    termination = "completed"

    while height > config.tube.outlet_height and time <= config.max_time and steps < config.max_steps:
        head = height - config.tube.outlet_height
        if head <= 0:
            break
        flow, loss = _solve_flow(head, config, guess_flow)
        area_out = config.outlet_area
        outlet_velocity = flow / area_out

        crest_velocity = flow / config.crest_area
        crest_pressure = (
            config.fluid.atmospheric_pressure
            + config.fluid.density * G * (height - config.crest_height)
            - 0.5 * config.fluid.density * crest_velocity**2
        )
        outlet_pressure = config.fluid.atmospheric_pressure

        if crest_pressure <= config.fluid.vapor_pressure + config.cavitation_margin:
            termination = "cavitation"
            break

        times.append(time)
        heights.append(height)
        velocities.append(outlet_velocity)
        crest_pressures.append(crest_pressure)
        outlet_pressures.append(outlet_pressure)
        reynolds_values.append(_segment_reynolds(flow, config.segments[-1], config.fluid))
        lambda_values.append(loss)

        dh = flow * dt / config.reservoir.area
        next_height = height - dh
        if next_height < config.tube.outlet_height:
            # shorten the final step to land on the outlet height
            dt = max(
                config.min_time_step,
                dt * (height - config.tube.outlet_height) / dh,
            )
            height = config.tube.outlet_height
            time += dt
            break

        height = next_height
        time += dt
        guess_flow = flow
        steps += 1

    if time > config.max_time:
        termination = "max-time"
    elif steps >= config.max_steps:
        termination = "max-steps"

    return VariableLossResult(
        time=times,
        surface_height=heights,
        velocity=velocities,
        crest_pressure=crest_pressures,
        outlet_pressure=outlet_pressures,
        reynolds_number=reynolds_values,
        total_loss_coefficient=lambda_values,
        termination_reason=termination,
    )
