"""Physics helpers for multi-segment siphon geometries."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import sin
from typing import Iterable, Sequence

import numpy as np

from .common import FluidProperties


def _darcy_friction_factor(reynolds: float, relative_roughness: float) -> float:
    """Return the Darcy friction factor for laminar or turbulent flow."""

    if reynolds <= 0:
        return 0.0
    if reynolds < 2000.0:
        return 64.0 / reynolds
    # Swamee–Jain explicit approximation for turbulent flow
    return 0.25 / (
        np.log10(relative_roughness / 3.7 + 5.74 / reynolds**0.9) ** 2
    )


@dataclass(frozen=True)
class TubeSegment:
    """Single straight tube segment within a multi-crest siphon."""

    length: float
    diameter: float
    angle_deg: float
    minor_loss_coefficients: Sequence[float] = field(default_factory=tuple)
    roughness: float | None = None

    def __post_init__(self) -> None:
        if self.length <= 0:
            raise ValueError("Segment length must be positive.")
        if self.diameter <= 0:
            raise ValueError("Segment diameter must be positive.")

    @property
    def area(self) -> float:
        radius = self.diameter / 2.0
        return float(np.pi * radius**2)

    @property
    def relative_roughness(self) -> float:
        if self.roughness is None:
            return 0.0
        return max(self.roughness / self.diameter, 0.0)

    @property
    def minor_losses(self) -> float:
        return float(np.sum(self.minor_loss_coefficients)) if self.minor_loss_coefficients else 0.0

    @property
    def elevation_change(self) -> float:
        """Return the vertical change induced by this segment (positive rises)."""

        return self.length * sin(np.deg2rad(self.angle_deg))


@dataclass(frozen=True)
class SegmentLoss:
    """Loss contribution for a single segment."""

    index: int
    friction_factor: float
    reynolds_number: float
    major_lambda: float
    minor_lambda: float

    @property
    def total_lambda(self) -> float:
        return self.major_lambda + self.minor_lambda


@dataclass(frozen=True)
class LossBreakdown:
    """Aggregate the head-loss contributions for a segmented tube."""

    entry_lambda: float
    exit_lambda: float
    segments: tuple[SegmentLoss, ...]

    @property
    def total_lambda(self) -> float:
        return self.entry_lambda + self.exit_lambda + sum(seg.total_lambda for seg in self.segments)


@dataclass(frozen=True)
class SegmentedTube:
    """Description of a siphon tube assembled from straight segments."""

    entry_height: float
    outlet_height: float
    segments: Sequence[TubeSegment]
    entry_minor_losses: Sequence[float] = field(default_factory=tuple)
    exit_minor_losses: Sequence[float] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.segments:
            raise ValueError("At least one segment is required for a segmented tube.")
        self._validate_geometry()

    def _validate_geometry(self) -> None:
        heights = self.node_heights()
        outlet_height = heights[-1]
        if not np.isclose(outlet_height, self.outlet_height, atol=1e-6):
            raise ValueError(
                "Segment heights do not terminate at the declared outlet height."
            )
        areas = [seg.area for seg in self.segments]
        if not np.allclose(areas, areas[0], rtol=1e-6, atol=0.0):
            raise ValueError(
                "All segments must currently share the same cross-sectional area."
            )

    @property
    def area(self) -> float:
        return self.segments[0].area

    @property
    def diameter(self) -> float:
        return self.segments[0].diameter

    def area_ratio(self, reservoir_surface_area: float) -> float:
        if reservoir_surface_area <= 0:
            raise ValueError("Reservoir surface area must be positive when computing k.")
        return self.area / reservoir_surface_area

    def node_heights(self) -> np.ndarray:
        """Return the heights of every node, starting with the entry."""

        heights = [self.entry_height]
        current = self.entry_height
        for segment in self.segments:
            current += segment.elevation_change
            heights.append(current)
        return np.array(heights, dtype=float)

    def crest_indices(self) -> tuple[int, ...]:
        """Return the indices of local maxima in the node heights."""

        heights = self.node_heights()
        crests: list[int] = []
        for idx in range(1, len(heights) - 1):
            if heights[idx] >= heights[idx - 1] and heights[idx] >= heights[idx + 1]:
                crests.append(idx)
        if heights[0] > heights[1]:
            crests.insert(0, 0)
        return tuple(crests)

    def _entry_lambda(self) -> float:
        return float(np.sum(self.entry_minor_losses)) if self.entry_minor_losses else 0.0

    def _exit_lambda(self) -> float:
        return float(np.sum(self.exit_minor_losses)) if self.exit_minor_losses else 0.0

    def loss_breakdown(self, velocity: float, fluid: FluidProperties) -> LossBreakdown:
        if velocity <= 0:
            empty = tuple(
                SegmentLoss(index=i, friction_factor=0.0, reynolds_number=0.0, major_lambda=0.0, minor_lambda=seg.minor_losses)
                for i, seg in enumerate(self.segments)
            )
            return LossBreakdown(
                entry_lambda=self._entry_lambda(),
                exit_lambda=self._exit_lambda(),
                segments=empty,
            )

        density = fluid.density
        viscosity = fluid.viscosity
        segments: list[SegmentLoss] = []
        for idx, segment in enumerate(self.segments):
            reynolds = max(density * velocity * segment.diameter / viscosity, 1.0)
            friction_factor = _darcy_friction_factor(reynolds, segment.relative_roughness)
            major_lambda = friction_factor * (segment.length / segment.diameter)
            minor_lambda = segment.minor_losses
            segments.append(
                SegmentLoss(
                    index=idx,
                    friction_factor=friction_factor,
                    reynolds_number=reynolds,
                    major_lambda=major_lambda,
                    minor_lambda=minor_lambda,
                )
            )
        return LossBreakdown(
            entry_lambda=self._entry_lambda(),
            exit_lambda=self._exit_lambda(),
            segments=tuple(segments),
        )

    def pressure_profile(
        self,
        velocity: float,
        fluid: FluidProperties,
        breakdown: LossBreakdown,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Return node heights, static pressures, and energy heads along the tube."""

        heights = self.node_heights()
        num_nodes = len(heights)
        g = fluid.gravity
        dyn_head = velocity**2 / (2.0 * g)

        energy_heads = np.empty(num_nodes, dtype=float)
        pressures = np.empty(num_nodes, dtype=float)

        # Outlet node sits just upstream of the exit fittings. The jet leaves at
        # atmospheric pressure, so the energy head here also carries the exit
        # minor losses (matching the energy balance used in solve_velocity).
        exit_head_loss = breakdown.exit_lambda * dyn_head
        energy_heads[-1] = self.outlet_height + dyn_head + exit_head_loss
        pressures[-1] = fluid.atmospheric_pressure + fluid.density * g * exit_head_loss

        segment_losses = breakdown.segments
        for idx in range(len(self.segments) - 1, -1, -1):
            loss_lambda = segment_losses[idx].total_lambda if segment_losses else 0.0
            energy_heads[idx] = energy_heads[idx + 1] + loss_lambda * dyn_head
            pressures[idx] = fluid.atmospheric_pressure + fluid.density * g * (
                energy_heads[idx] - heights[idx] - dyn_head
            )

        return heights, pressures, energy_heads


def solve_velocity(
    head: float,
    area_ratio: float,
    tube: SegmentedTube,
    fluid: FluidProperties,
    max_iterations: int = 80,
    tolerance: float = 1e-8,
) -> tuple[float, LossBreakdown]:
    """Solve for the steady velocity in a primed multi-segment siphon."""

    if head <= 0:
        breakdown = tube.loss_breakdown(0.0, fluid)
        return 0.0, breakdown

    g = fluid.gravity
    k = area_ratio
    ideal_velocity = np.sqrt(2.0 * g * head / max(1e-12, 1.0 - k**2))

    lower = 0.0
    upper = ideal_velocity
    final_breakdown: LossBreakdown | None = None

    for _ in range(max_iterations):
        mid = 0.5 * (lower + upper)
        breakdown = tube.loss_breakdown(mid, fluid)
        total_lambda = breakdown.total_lambda
        residual = mid**2 * (1.0 - k**2 + total_lambda) - 2.0 * g * head
        if abs(residual) < tolerance:
            final_breakdown = breakdown
            velocity = mid
            break
        if residual > 0.0:
            upper = mid
        else:
            lower = mid
    else:
        velocity = 0.5 * (lower + upper)
        final_breakdown = tube.loss_breakdown(velocity, fluid)

    if final_breakdown is None:
        final_breakdown = tube.loss_breakdown(velocity, fluid)

    return velocity, final_breakdown


def crest_pressures(
    tube: SegmentedTube,
    heights: Iterable[float],
    pressures: Iterable[float],
) -> tuple[tuple[int, float], ...]:
    """Return (index, pressure) pairs for each crest node."""

    height_array = np.array(list(heights), dtype=float)
    pressure_array = np.array(list(pressures), dtype=float)
    indices = tube.crest_indices()
    return tuple((int(idx), float(pressure_array[idx])) for idx in indices)
