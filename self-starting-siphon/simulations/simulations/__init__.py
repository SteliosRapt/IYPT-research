"""Simulation package exposing siphon modelling utilities."""

from .common import FluidProperties, ReservoirSetup, SimulationConfig, SimulationResult, TubeGeometry
from .multi_segment import MultiSegmentConfig, MultiSegmentInitialState, compute_initial_state, describe_state
from .multi_segment_physics import SegmentedTube, TubeSegment

__all__ = [
    "FluidProperties",
    "ReservoirSetup",
    "SimulationConfig",
    "SimulationResult",
    "TubeGeometry",
    "SegmentedTube",
    "TubeSegment",
    "MultiSegmentConfig",
    "MultiSegmentInitialState",
    "compute_initial_state",
    "describe_state",
]
