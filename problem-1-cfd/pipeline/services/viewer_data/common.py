"""Shared helpers for viewer-data assembly."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.geometry.core import (
    SOURCE_FILES,
    build_fixed_geometry_descriptors,
    create_geometry_snapshot,
    default_event_thresholds,
)
from services.orchestrator.events import analyze_series
from services.utils import stable_hash, write_json

VIEWER_OUTLET_EXTENSION = 0.035
VIEWER_OUTLET_PLUME_HEIGHT_RATIO = 0.4
VIEWER_PLUME_LENGTH_SCALE = 180.0


def integrate_series(times: list[float], values: list[float]) -> list[float]:
    total = 0.0
    output = [0.0]
    for index in range(1, len(times)):
        dt = times[index] - times[index - 1]
        total += 0.5 * (values[index] + values[index - 1]) * dt
        output.append(round(total, 8))
    return output


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
        triangles.extend(
            [
                [triangle[0] + offset, triangle[1] + offset, triangle[2] + offset]
                for triangle in mesh["triangles"]
            ]
        )
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


def load_case_snapshot(case_file: dict[str, Any]) -> dict[str, Any]:
    return {
        "parameters": {
            **case_file["parameters"],
            "P4t": case_file["derived"]["P4t"],
            "wallThicknessRatio": case_file["solver"]["tubeWallThicknessRatio"],
        },
        "derived": case_file["derived"],
        "constraints": create_geometry_snapshot(case_file["parameters"])["constraints"],
    }


def write_viewer_run(
    case_file: dict[str, Any],
    output_dir: str | Path,
    *,
    times: list[float],
    heights: list[float],
    q_out: list[float],
    q_in: list[float] | None = None,
    status: str,
    paraview_foam: str | None = None,
    paraview_vtk_dir: str | None = None,
) -> Path:
    snapshot = load_case_snapshot(case_file)
    parameter_hash = case_file.get("provenance", {}).get("parameterHash", stable_hash(snapshot["parameters"]))
    source_files = case_file.get("provenance", {}).get("sourceFiles", SOURCE_FILES)
    discharged = integrate_series(times, q_out)
    event_thresholds = {**default_event_thresholds(), **case_file.get("eventThresholds", {})}
    summary = analyze_series(
        times,
        heights,
        case_file["parameters"]["h0"],
        event_thresholds,
        q_in=q_in,
        q_out=q_out,
    )
    output_root = Path(output_dir)
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "series").mkdir(exist_ok=True)
    (output_root / "frames").mkdir(exist_ok=True)
    (output_root / "vtk").mkdir(exist_ok=True)

    write_json(
        output_root / "series" / "height.json",
        [{"time": t, "value": v} for t, v in zip(times, heights, strict=True)],
    )
    write_json(
        output_root / "series" / "outlet_flow.json",
        [{"time": t, "value": v} for t, v in zip(times, q_out, strict=True)],
    )
    write_json(
        output_root / "series" / "discharged_volume.json",
        [{"time": t, "value": v} for t, v in zip(times, discharged, strict=True)],
    )
    write_json(output_root / "event_states.json", summary.states)
    write_json(
        output_root / "fixed_geometry.json",
        build_fixed_geometry_descriptors(snapshot["parameters"], snapshot["derived"]),
    )

    x0 = snapshot["derived"]["S0"]
    x1 = snapshot["derived"]["X2"]
    z0 = -case_file["parameters"]["W"] / 2
    z1 = case_file["parameters"]["W"] / 2
    outlet_x0 = snapshot["derived"]["X5"]
    outlet_x1 = snapshot["derived"]["X5"] + VIEWER_OUTLET_EXTENSION
    outlet_z0 = -snapshot["derived"]["r"]
    outlet_z1 = snapshot["derived"]["r"]
    frame_paths: list[str] = []

    for index, (time_value, height_value, q_out_value) in enumerate(zip(times, heights, q_out, strict=True)):
        water_box = _box_surface(x0, x1, 0.0, height_value, z0, z1)
        outlet_plume_height = (
            snapshot["derived"]["points"]["P5"]["y"]
            + snapshot["derived"]["r"] * VIEWER_OUTLET_PLUME_HEIGHT_RATIO
        )
        plume_length = outlet_x0 + q_out_value * VIEWER_PLUME_LENGTH_SCALE
        plume_box = _box_surface(
            outlet_x0,
            plume_length if plume_length > outlet_x0 else outlet_x1,
            outlet_plume_height - snapshot["derived"]["r"],
            outlet_plume_height + snapshot["derived"]["r"],
            outlet_z0,
            outlet_z1,
        )
        combined = _combine_meshes([water_box, plume_box])
        frame_name = f"frame_{index:04d}.json"
        frame_paths.append(f"frames/{frame_name}")
        write_json(output_root / "frames" / frame_name, {"time": time_value, **combined})
        write_legacy_vtk(output_root / "vtk" / f"frame_{index:04d}.vtk", combined)

    current_state = summary.states[-1]["state"] if summary.states else "PRE_H0"
    manifest = {
        "schemaVersion": "1.0.0",
        "caseId": case_file["caseId"],
        "displayName": case_file["displayName"],
        "timeSteps": times,
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
            "terminationReason": summary.termination_reason,
            "currentState": current_state,
        },
        "status": status,
        "paraview": {
            "foamFile": paraview_foam,
            "vtkDir": paraview_vtk_dir,
        },
        "metadata": {
            "parameterHash": parameter_hash,
            "gitCommit": None,
            "sourceFiles": source_files,
            "meshPreset": case_file["meshing"]["preset"],
            "solverName": case_file["solver"]["solver"],
        },
    }
    write_json(output_root / "manifest.json", manifest)
    return output_root
