from __future__ import annotations

from services.geometry.core import create_case_file, create_geometry_snapshot
from services.viewer_data.mock import create_time_series
from services.orchestrator.events import analyze_series


def test_event_detector_finds_crossing_and_steady_state() -> None:
    case_file = create_case_file()
    snapshot = create_geometry_snapshot(case_file["parameters"])
    time_series = create_time_series(case_file, snapshot)

    summary = analyze_series(
        time_series["time"],
        time_series["height"],
        case_file["parameters"]["h0"],
        case_file["eventThresholds"],
        q_in=time_series["q_in"],
        q_out=time_series["q_out"],
    )

    assert summary.t_h0_up is not None
    assert summary.t_steady is not None
    assert summary.t_h0_up < summary.t_steady
    assert summary.termination_reason == "steady_state_reached"

