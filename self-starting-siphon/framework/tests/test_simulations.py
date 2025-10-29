import math

import pytest

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from simulations import (
    ConstantLossConfig,
    IdealSiphonConfig,
    Reservoir,
    SiphonSegment,
    TubeGeometry,
    VariableLossConfig,
    simulate_constant_losses,
    simulate_ideal,
    simulate_variable_losses,
)


def build_basic_config():
    reservoir = Reservoir(area=1.0, initial_height=2.0)
    tube = TubeGeometry(area=0.01, outlet_height=0.0, crest_height=1.5)
    return IdealSiphonConfig(reservoir=reservoir, tube=tube)


def test_ideal_velocity_matches_formula():
    config = build_basic_config()
    result = simulate_ideal(config, [0.0])
    expected = math.sqrt(2 * 9.80665 * (config.reservoir.initial_height - config.tube.outlet_height) / (1 - config.area_ratio**2))
    assert result.velocity[0] == pytest.approx(expected)


def test_constant_loss_reduces_velocity():
    base = build_basic_config()
    loss_config = ConstantLossConfig(
        reservoir=base.reservoir,
        tube=base.tube,
        loss_coefficient=2.0,
    )
    ideal = simulate_ideal(base, [0.0, 1.0])
    constant = simulate_constant_losses(loss_config, [0.0, 1.0])
    assert constant.velocity[0] < ideal.velocity[0]


def test_variable_loss_simulation_runs():
    base = build_basic_config()
    segment = SiphonSegment(length=2.0, diameter=0.113)
    config = VariableLossConfig(
        reservoir=base.reservoir,
        tube=base.tube,
        segments=[segment],
        max_time=100.0,
        time_step=0.1,
    )
    result = simulate_variable_losses(config)
    assert result.time  # non-empty
    assert result.termination_reason in {"completed", "cavitation", "max-time", "max-steps"}
