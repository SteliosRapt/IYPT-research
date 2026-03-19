"""Synthetic viewer-data generation for environments without OpenFOAM."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from services.geometry.core import (
    build_fixed_geometry_descriptors,
    create_geometry_snapshot,
    default_event_thresholds,
    stable_hash,
    write_json,
)
from services.orchestrator.events import analyze_series


def integrate_series(times: list[float], values: list[float]) -> list[float]:
    total = 0.0
    output = [0.0]
    for index in range(1, len(times)):
        dt = times[index] - times[index - 1]
        total += 0.5 * (values[index] + values[index - 1]) * dt
        output.append(round(total, 8))
    return output


def create_time_series(case_file: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, list[float]]:
    h0 = case_file["parameters"]["h0"]
    h_initial = snapshot["derived"]["H0"]
    times = [round(index * 0.1, 3) for index in range(121)]
    heights: list[float] = []
    q_out: list[float] = []
    q_in: list[float] = []

    for time in times:
        steady_height = h0 + 0.0075
        height = steady_height - (steady_height - h_initial) * math.exp(-0.8 * time)
        damping = 0.0025 * math.exp(-1.1 * max(time - 2.0, 0)) * math.sin(4.0 * max(time - 2.0, 0))
        height += damping
        height = min(height, case_file["parameters"]["h0"] + case_file["parameters"]["h_a"] * 0.9)
        q_out_value = max(0.0, 0.00035 * (1 - math.exp(-0.7 * max(time - 1.6, 0))) * math.exp(-0.06 * max(time - 5.0, 0)))
        q_in_value = 0.00042 if time < 8.0 else 0.00018
        heights.append(round(height, 6))
        q_out.append(round(q_out_value, 8))
        q_in.append(round(q_in_value, 8))

    discharged = integrate_series(times, q_out)
    return {"time": times, "height": heights, "q_out": q_out, "q_in": q_in, "discharged": discharged}


def _box_surface(x0: float, x1: float, y0: float, y1: float, z0: float, z1: float) -> dict[str, Any]:
    points = [
        [x0, y0, z0],
        [x1, y0, z0],
        [x1, y1, z0],
        [x0, y1, z0],
        [x0, y0, z1],
        [x1, y0, z1],
        [x1, y1, z1],
        [x0, y1, z1],
    ]
    triangles = [
        [0, 1, 2], [0, 2, 3],
        [4, 6, 5], [4, 7, 6],
        [0, 4, 5], [0, 5, 1],
        [1, 5, 6], [1, 6, 2],
        [2, 6, 7], [2, 7, 3],
        [3, 7, 4], [3, 4, 0],
    ]
    return {"points": points, "triangles": triangles}


def _combine_meshes(meshes: list[dict[str, Any]]) -> dict[str, Any]:
    points: list[list[float]] = []
    triangles: list[list[int]] = []
    for mesh in meshes:
        offset = len(points)
        points.extend(mesh["points"])
        triangles.extend([[triangle[0] + offset, triangle[1] + offset, triangle[2] + offset] for triangle in mesh["triangles"]])
    return {"points": points, "triangles": triangles}


def write_legacy_vtk(path: Path, mesh: dict[str, Any]) -> None:
    lines = [
        "# vtk DataFile Version 3.0",
        "fixed-geometry viewer frame",
        "ASCII",
        "DATASET POLYDATA",
        f"POINTS {len(mesh['points'])} float",
    ]
    lines.extend(f"{x} {y} {z}" for x, y, z in mesh["points"])
    lines.append(f"POLYGONS {len(mesh['triangles'])} {len(mesh['triangles']) * 4}")
    lines.extend(f"3 {a} {b} {c}" for a, b, c in mesh["triangles"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def create_mock_run(case_json: str | Path, output_dir: str | Path) -> Path:
    case_path = Path(case_json)
    case_file = json.loads(case_path.read_text(encoding="utf-8"))
    snapshot = create_geometry_snapshot(case_file["parameters"])
    time_series = create_time_series(case_file, snapshot)
    event_thresholds = {**default_event_thresholds(), **case_file.get("eventThresholds", {})}
    summary = analyze_series(
        time_series["time"],
        time_series["height"],
        case_file["parameters"]["h0"],
        event_thresholds,
        q_in=time_series["q_in"],
        q_out=time_series["q_out"],
    )
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "series").mkdir(exist_ok=True)
    (output_root / "frames").mkdir(exist_ok=True)
    (output_root / "vtk").mkdir(exist_ok=True)

    write_json(output_root / "series" / "height.json", [{"time": t, "value": v} for t, v in zip(time_series["time"], time_series["height"], strict=True)])
    write_json(output_root / "series" / "outlet_flow.json", [{"time": t, "value": v} for t, v in zip(time_series["time"], time_series["q_out"], strict=True)])
    write_json(output_root / "series" / "discharged_volume.json", [{"time": t, "value": v} for t, v in zip(time_series["time"], time_series["discharged"], strict=True)])
    write_json(output_root / "event_states.json", summary.states)
    write_json(output_root / "fixed_geometry.json", build_fixed_geometry_descriptors(snapshot["parameters"], snapshot["derived"]))

    x0 = snapshot["derived"]["S0"]
    x1 = snapshot["derived"]["X2"]
    z0 = -case_file["parameters"]["W"] / 2
    z1 = case_file["parameters"]["W"] / 2
    outlet_x0 = snapshot["derived"]["X5"]
    outlet_x1 = snapshot["derived"]["X5"] + 0.035
    outlet_z0 = -snapshot["derived"]["r"]
    outlet_z1 = snapshot["derived"]["r"]
    frame_paths: list[str] = []

    for index, (time_value, height_value, q_out_value) in enumerate(
        zip(time_series["time"], time_series["height"], time_series["q_out"], strict=True)
    ):
        water_box = _box_surface(x0, x1, 0.0, height_value, z0, z1)
        outlet_plume_height = snapshot["derived"]["points"]["P5"]["y"] + snapshot["derived"]["r"] * 0.4
        plume_length = outlet_x0 + q_out_value * 180
        plume_box = _box_surface(outlet_x0, plume_length if plume_length > outlet_x0 else outlet_x1, outlet_plume_height - snapshot["derived"]["r"], outlet_plume_height + snapshot["derived"]["r"], outlet_z0, outlet_z1)
        combined = _combine_meshes([water_box, plume_box])
        frame_name = f"frame_{index:04d}.json"
        frame_paths.append(f"frames/{frame_name}")
        write_json(output_root / "frames" / frame_name, {"time": time_value, **combined})
        write_legacy_vtk(output_root / "vtk" / f"frame_{index:04d}.vtk", combined)

    status = "mock"
    termination_reason = summary.termination_reason
    current_state = summary.states[-1]["state"] if summary.states else "PRE_H0"
    manifest = {
        "schemaVersion": "1.0.0",
        "caseId": case_file["caseId"],
        "displayName": case_file["displayName"],
        "timeSteps": time_series["time"],
        "chartSeries": {
            "height": "series/height.json",
            "outletFlow": "series/outlet_flow.json",
            "dischargedVolume": "series/discharged_volume.json",
        },
        "geometryAssets": {
            "fixedGlb": None,
            "fixedJson": "fixed_geometry.json",
        },
        "fluidAssets": {
            "interfaceFrames": frame_paths,
        },
        "events": {
            "t_h0_up": summary.t_h0_up,
            "t_steady": summary.t_steady,
            "terminationReason": termination_reason,
            "currentState": current_state,
        },
        "status": status,
        "paraview": {
            "foamFile": None,
            "vtkDir": "vtk",
        },
        "metadata": {
            "parameterHash": stable_hash(case_file["parameters"]),
            "gitCommit": None,
            "sourceFiles": ["experimental_setup.md", "setup_3d (2).html"],
            "meshPreset": case_file["meshing"]["preset"],
            "solverName": case_file["solver"]["solver"],
        },
    }
    write_json(output_root / "manifest.json", manifest)
    return output_root
