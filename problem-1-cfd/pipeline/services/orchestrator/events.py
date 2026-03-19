"""Event detection and steady-state logic."""

from __future__ import annotations

from collections import deque
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


def _advance_window_start(
    times: list[float],
    window_start_index: int,
    current_time: float,
    window_seconds: float,
) -> int:
    window_start = current_time - window_seconds
    while window_start_index < len(times) and times[window_start_index] < window_start:
        window_start_index += 1
    return window_start_index


def _push_min_index(indices: deque[int], values: list[float], index: int) -> None:
    while indices and values[indices[-1]] >= values[index]:
        indices.pop()
    indices.append(index)


def _push_max_index(indices: deque[int], values: list[float], index: int) -> None:
    while indices and values[indices[-1]] <= values[index]:
        indices.pop()
    indices.append(index)


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

    height_min_indices: deque[int] = deque()
    height_max_indices: deque[int] = deque()
    q_balance_indices: deque[int] = deque()
    window_start_index = 0
    derivative_start_index = 1
    derivative_squares = [0.0] * len(times)
    derivative_is_valid = [False] * len(times)
    derivative_sum = 0.0
    derivative_count = 0
    q_differences: list[float] | None = None
    if require_q_balance and q_in is not None and q_out is not None:
        q_limit = min(len(q_in), len(q_out))
        q_differences = [abs(q_in[index] - q_out[index]) for index in range(q_limit)]

    for index, current_time in enumerate(times):
        height = heights[index]
        previous_height = heights[index - 1] if index > 0 else height
        previous_time = times[index - 1] if index > 0 else current_time

        window_start_index = _advance_window_start(times, window_start_index, current_time, thresholds["T_ss"])

        if index > 0:
            dt = current_time - previous_time
            if dt > 0:
                derivative = (height - previous_height) / dt
                derivative_squares[index] = derivative * derivative
                derivative_is_valid[index] = True
                derivative_sum += derivative_squares[index]
                derivative_count += 1

        while derivative_start_index < window_start_index + 1:
            if derivative_is_valid[derivative_start_index]:
                derivative_sum -= derivative_squares[derivative_start_index]
                derivative_count -= 1
            derivative_start_index += 1

        _push_min_index(height_min_indices, heights, index)
        _push_max_index(height_max_indices, heights, index)
        while height_min_indices and height_min_indices[0] < window_start_index:
            height_min_indices.popleft()
        while height_max_indices and height_max_indices[0] < window_start_index:
            height_max_indices.popleft()

        if q_differences is not None and index < len(q_differences):
            _push_max_index(q_balance_indices, q_differences, index)
        while q_balance_indices and q_balance_indices[0] < window_start_index:
            q_balance_indices.popleft()

        if state == "PRE_H0" and index > 0 and previous_height < h0_target <= height and height > previous_height:
            t_h0_up = _interpolate_crossing(previous_time, previous_height, current_time, height, h0_target)
            state = "POST_H0_MONITORING"

        height_span = 0.0
        rms_dhdt = math.inf
        q_balance = math.inf
        steady_now = False
        window_size = index - window_start_index + 1

        if state == "POST_H0_MONITORING" and window_size >= 2:
            height_span = heights[height_max_indices[0]] - heights[height_min_indices[0]]
            if derivative_count > 0:
                rms_dhdt = math.sqrt(derivative_sum / derivative_count)
            else:
                rms_dhdt = 0.0

            q_ok = True
            if require_q_balance and q_differences is not None and q_balance_indices:
                q_balance = q_differences[q_balance_indices[0]]
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
