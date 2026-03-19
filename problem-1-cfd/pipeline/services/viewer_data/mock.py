"""Synthetic viewer-data generation for environments without OpenFOAM."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from services.geometry.core import create_geometry_snapshot
from .common import integrate_series, write_legacy_vtk, write_viewer_run

MOCK_TIME_STEP_SECONDS = 0.1
MOCK_TIME_STEP_COUNT = 121
MOCK_STEADY_HEIGHT_OFFSET = 0.0075
MOCK_HEIGHT_APPROACH_RATE = 0.8
MOCK_DAMPING_AMPLITUDE = 0.0025
MOCK_DAMPING_DECAY_RATE = 1.1
MOCK_DAMPING_START_TIME = 2.0
MOCK_DAMPING_FREQUENCY = 4.0
MOCK_HEIGHT_CAP_RATIO = 0.9
MOCK_OUTLET_FLOW_SCALE = 0.00035
MOCK_OUTLET_FLOW_RISE_RATE = 0.7
MOCK_OUTLET_FLOW_RISE_START_TIME = 1.6
MOCK_OUTLET_FLOW_DECAY_RATE = 0.06
MOCK_OUTLET_FLOW_DECAY_START_TIME = 5.0
MOCK_INFLOW_RATE_EARLY = 0.00042
MOCK_INFLOW_RATE_LATE = 0.00018
MOCK_INFLOW_SWITCH_TIME = 8.0


def create_time_series(case_file: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, list[float]]:
    h0 = case_file["parameters"]["h0"]
    h_initial = snapshot["derived"]["H0"]
    times = [round(index * MOCK_TIME_STEP_SECONDS, 3) for index in range(MOCK_TIME_STEP_COUNT)]
    heights: list[float] = []
    q_out: list[float] = []
    q_in: list[float] = []

    for time in times:
        steady_height = h0 + MOCK_STEADY_HEIGHT_OFFSET
        height = steady_height - (steady_height - h_initial) * math.exp(-MOCK_HEIGHT_APPROACH_RATE * time)
        damping_time = max(time - MOCK_DAMPING_START_TIME, 0.0)
        damping = (
            MOCK_DAMPING_AMPLITUDE
            * math.exp(-MOCK_DAMPING_DECAY_RATE * damping_time)
            * math.sin(MOCK_DAMPING_FREQUENCY * damping_time)
        )
        height += damping
        height = min(height, case_file["parameters"]["h0"] + case_file["parameters"]["h_a"] * MOCK_HEIGHT_CAP_RATIO)
        outlet_rise_time = max(time - MOCK_OUTLET_FLOW_RISE_START_TIME, 0.0)
        outlet_decay_time = max(time - MOCK_OUTLET_FLOW_DECAY_START_TIME, 0.0)
        q_out_value = max(
            0.0,
            MOCK_OUTLET_FLOW_SCALE
            * (1 - math.exp(-MOCK_OUTLET_FLOW_RISE_RATE * outlet_rise_time))
            * math.exp(-MOCK_OUTLET_FLOW_DECAY_RATE * outlet_decay_time),
        )
        q_in_value = MOCK_INFLOW_RATE_EARLY if time < MOCK_INFLOW_SWITCH_TIME else MOCK_INFLOW_RATE_LATE
        heights.append(round(height, 6))
        q_out.append(round(q_out_value, 8))
        q_in.append(round(q_in_value, 8))

    discharged = integrate_series(times, q_out)
    return {"time": times, "height": heights, "q_out": q_out, "q_in": q_in, "discharged": discharged}


def create_mock_run(case_json: str | Path, output_dir: str | Path) -> Path:
    case_path = Path(case_json)
    case_file = json.loads(case_path.read_text(encoding="utf-8"))
    snapshot = create_geometry_snapshot(case_file["parameters"])
    time_series = create_time_series(case_file, snapshot)
    return write_viewer_run(
        case_file,
        output_dir,
        times=time_series["time"],
        heights=time_series["height"],
        q_out=time_series["q_out"],
        q_in=time_series["q_in"],
        status="mock",
        paraview_foam=None,
        paraview_vtk_dir="vtk",
    )
