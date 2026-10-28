"""Real solver-backed viewer-data generation."""

from __future__ import annotations

import json
import os
from pathlib import Path

from .common import write_viewer_run

CONTAINER_WATER_VOLUME_OBJECT = "containerWaterVolume"
TUBE_OUTLET_FLOW_OBJECT = "tubeOutletFlow"
TOP_INFLOW_FLOW_OBJECT = "topInflowFlow"


def _parse_float_token(token: str) -> float | None:
    cleaned = token.strip().strip("(),")
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def _parse_series_file(path: Path) -> list[tuple[float, float]]:
    samples: list[tuple[float, float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        tokens = stripped.split()
        if len(tokens) < 2:
            continue
        time_value = _parse_float_token(tokens[0])
        value = next(
            (
                parsed
                for parsed in (_parse_float_token(token) for token in reversed(tokens[1:]))
                if parsed is not None
            ),
            None,
        )
        if time_value is None or value is None:
            continue
        samples.append((round(time_value, 9), value))
    return samples


def _load_measurement_series(case_dir: Path, object_name: str) -> list[tuple[float, float]]:
    object_dir = case_dir / "postProcessing" / object_name
    if not object_dir.exists():
        return []
    samples_by_time: dict[float, float] = {}
    for path in sorted(path for path in object_dir.rglob("*") if path.is_file()):
        for time_value, value in _parse_series_file(path):
            samples_by_time[time_value] = value
    return sorted(samples_by_time.items())


def _sample_series_at(samples: list[tuple[float, float]], time_value: float) -> float:
    if not samples:
        return 0.0
    if time_value <= samples[0][0]:
        return samples[0][1]
    if time_value >= samples[-1][0]:
        return samples[-1][1]
    for index in range(1, len(samples)):
        left_time, left_value = samples[index - 1]
        right_time, right_value = samples[index]
        if time_value == right_time:
            return right_value
        if left_time <= time_value <= right_time:
            span = right_time - left_time
            if span <= 0:
                return right_value
            fraction = (time_value - left_time) / span
            return left_value + fraction * (right_value - left_value)
    return samples[-1][1]


def _dominant_sign(values: list[float]) -> float:
    if not values:
        return 1.0
    dominant = max(values, key=lambda value: abs(value))
    return -1.0 if dominant < 0 else 1.0


def has_real_post_processing(case_dir: str | Path) -> bool:
    root = Path(case_dir)
    return bool(_load_measurement_series(root, CONTAINER_WATER_VOLUME_OBJECT)) and bool(
        _load_measurement_series(root, TUBE_OUTLET_FLOW_OBJECT)
    )


def create_real_run(case_dir: str | Path, output_dir: str | Path) -> Path:
    case_root = Path(case_dir)
    output_root = Path(output_dir)
    case_file = json.loads((case_root / "case.json").read_text(encoding="utf-8"))

    volume_samples = _load_measurement_series(case_root, CONTAINER_WATER_VOLUME_OBJECT)
    outlet_flow_samples = _load_measurement_series(case_root, TUBE_OUTLET_FLOW_OBJECT)
    inflow_flow_samples = _load_measurement_series(case_root, TOP_INFLOW_FLOW_OBJECT)
    if not volume_samples:
        raise FileNotFoundError(
            f"Missing '{CONTAINER_WATER_VOLUME_OBJECT}' post-processing output in {case_root / 'postProcessing'}."
        )
    if not outlet_flow_samples:
        raise FileNotFoundError(
            f"Missing '{TUBE_OUTLET_FLOW_OBJECT}' post-processing output in {case_root / 'postProcessing'}."
        )

    plan_area = float(case_file["derived"]["planArea"])
    times = [time_value for time_value, _ in volume_samples]
    heights = [round(max(volume, 0.0) / plan_area, 6) for _, volume in volume_samples]

    raw_q_out = [_sample_series_at(outlet_flow_samples, time_value) for time_value in times]
    outlet_sign = _dominant_sign(raw_q_out)
    q_out = [round(max(outlet_sign * value, 0.0), 8) for value in raw_q_out]

    q_in = None
    if inflow_flow_samples:
        q_in = [round(abs(_sample_series_at(inflow_flow_samples, time_value)), 8) for time_value in times]

    foam_file = case_root / ".foam"
    vtk_dir = case_root / "VTK"
    foam_rel = None
    vtk_rel = None
    if foam_file.exists():
        foam_rel = os.path.relpath(foam_file, output_root).replace("\\", "/")
    if vtk_dir.exists():
        vtk_rel = os.path.relpath(vtk_dir, output_root).replace("\\", "/")

    return write_viewer_run(
        case_file,
        output_root,
        times=times,
        heights=heights,
        q_out=q_out,
        q_in=q_in,
        status="done",
        paraview_foam=foam_rel,
        paraview_vtk_dir=vtk_rel,
    )
