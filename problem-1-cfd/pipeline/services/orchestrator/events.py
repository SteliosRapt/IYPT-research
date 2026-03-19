"""Event detection and steady-state logic."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


@dataclass
class EventSummary:
    t_h0_up: float | None
    t_steady: float | None
    termination_reason: str
    states: list[dict[str, Any]]


def _interpolate_crossing(t0: float, h0_value: float, t1: float, h1_value: float, target: float) -> float:
    if h1_value == h0_value:
        return t1
    fraction = (target - h0_value) / (h1_value - h0_value)
    return t0 + max(0.0, min(1.0, fraction)) * (t1 - t0)


def _window_indices(times: list[float], center_index: int, window_seconds: float) -> list[int]:
    window_start = times[center_index] - window_seconds
    return [index for index, value in enumerate(times[: center_index + 1]) if value >= window_start]


def analyze_series(
    times: list[float],
    heights: list[float],
    h0_target: float,
    thresholds: dict[str, Any],
    q_in: list[float] | None = None,
    q_out: list[float] | None = None,
) -> EventSummary:
    state = "PRE_H0"
    states: list[dict[str, Any]] = []
    t_h0_up: float | None = None
    t_steady: float | None = None
    dwell_start: float | None = None
    termination_reason = "max_time_reached"
    require_q_balance = thresholds.get("requireQBalance", False)

    if not times:
        return EventSummary(None, None, "no_samples", states)

    for index, current_time in enumerate(times):
        height = heights[index]
        previous_height = heights[index - 1] if index > 0 else height
        previous_time = times[index - 1] if index > 0 else current_time

        if state == "PRE_H0" and index > 0 and previous_height < h0_target <= height and height > previous_height:
            t_h0_up = _interpolate_crossing(previous_time, previous_height, current_time, height, h0_target)
            state = "POST_H0_MONITORING"

        window = _window_indices(times, index, thresholds["T_ss"])
        derivative_values: list[float] = []
        for window_index in window[1:]:
            dt = times[window_index] - times[window_index - 1]
            if dt <= 0:
                continue
            derivative_values.append((heights[window_index] - heights[window_index - 1]) / dt)

        height_span = 0.0
        rms_dhdt = math.inf
        q_balance = math.inf
        steady_now = False

        if state == "POST_H0_MONITORING" and len(window) >= 2:
            window_heights = [heights[window_index] for window_index in window]
            height_span = max(window_heights) - min(window_heights)
            if derivative_values:
                rms_dhdt = math.sqrt(sum(value * value for value in derivative_values) / len(derivative_values))
            else:
                rms_dhdt = 0.0

            q_ok = True
            if require_q_balance and q_in is not None and q_out is not None:
                q_window = window[-min(len(window), len(q_in), len(q_out)) :]
                q_balance = max(abs(q_in[i] - q_out[i]) for i in q_window)
                q_ok = q_balance < thresholds["eps_Q"]

            steady_now = (
                height_span < thresholds["eps_H"]
                and rms_dhdt < thresholds["eps_dHdt"]
                and q_ok
            )

            if steady_now:
                if dwell_start is None:
                    dwell_start = current_time
                if current_time - dwell_start >= thresholds["dwell"]:
                    state = "DONE"
                    t_steady = current_time
                    termination_reason = "steady_state_reached"
            else:
                dwell_start = None

        states.append(
            {
                "time": current_time,
                "state": state,
                "height": height,
                "heightSpan": height_span,
                "rmsDHdt": None if rms_dhdt is math.inf else rms_dhdt,
                "qBalance": None if q_balance is math.inf else q_balance,
                "steady": steady_now,
            }
        )

        if state == "DONE":
            break

    return EventSummary(t_h0_up, t_steady, termination_reason, states)
