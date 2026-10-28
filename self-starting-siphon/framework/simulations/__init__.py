"""Simulation toolkit for siphon dynamics."""

from .ideal import (
    FluidProperties,
    IdealSiphonConfig,
    IdealSiphonResult,
    Reservoir,
    TubeGeometry,
    simulate_ideal,
)
from .constant_losses import ConstantLossConfig, simulate_constant_losses
from .variable_losses import (
    VariableLossConfig,
    VariableLossResult,
    SiphonSegment,
    simulate_variable_losses,
)

__all__ = [
    "FluidProperties",
    "Reservoir",
    "TubeGeometry",
    "IdealSiphonConfig",
    "IdealSiphonResult",
    "simulate_ideal",
    "ConstantLossConfig",
    "simulate_constant_losses",
    "VariableLossConfig",
    "VariableLossResult",
    "SiphonSegment",
    "simulate_variable_losses",
]
