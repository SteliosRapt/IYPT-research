from __future__ import annotations

import json
from pathlib import Path

from services.geometry.core import create_case_file, create_geometry_snapshot
from services.orchestrator.case import generate_case
from services.utils import write_json
from services.viewer_data.cli import build_manifest
from services.viewer_data.mock import (
    MOCK_TIME_STEP_COUNT,
    MOCK_TIME_STEP_SECONDS,
    create_mock_run,
    create_time_series,
    write_legacy_vtk,
)
from services.viewer_data.real import create_real_run


def test_create_time_series_has_expected_lengths_and_monotonic_discharge() -> None:
    case_file = create_case_file()
    snapshot = create_geometry_snapshot(case_file["parameters"])
    series = create_time_series(case_file, snapshot)

    assert len(series["time"]) == MOCK_TIME_STEP_COUNT
    assert len(series["height"]) == MOCK_TIME_STEP_COUNT
    assert len(series["q_in"]) == MOCK_TIME_STEP_COUNT
    assert len(series["q_out"]) == MOCK_TIME_STEP_COUNT
    assert len(series["discharged"]) == MOCK_TIME_STEP_COUNT
    assert series["time"][0] == 0.0
    assert series["time"][-1] == round((MOCK_TIME_STEP_COUNT - 1) * MOCK_TIME_STEP_SECONDS, 3)
    assert series["discharged"] == sorted(series["discharged"])


def test_write_legacy_vtk_outputs_polydata_file(tmp_path: Path) -> None:
    output = tmp_path / "frame.vtk"
    write_legacy_vtk(
        output,
        {
            "points": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
            "triangles": [[0, 1, 2]],
        },
    )

    vtk_text = output.read_text(encoding="utf-8")

    assert "# vtk DataFile Version 3.0" in vtk_text
    assert "DATASET POLYDATA" in vtk_text
    assert "POINTS 3 float" in vtk_text
    assert "POLYGONS 1 4" in vtk_text


def test_create_mock_run_writes_manifest_series_and_frames(tmp_path: Path) -> None:
    case_file = create_case_file()
    case_path = tmp_path / "case.json"
    write_json(case_path, case_file)

    viewer_dir = create_mock_run(case_path, tmp_path / "viewer")
    manifest = json.loads((viewer_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "mock"
    assert len(manifest["timeSteps"]) == MOCK_TIME_STEP_COUNT
    assert len(manifest["fluidAssets"]["interfaceFrames"]) == MOCK_TIME_STEP_COUNT
    assert (viewer_dir / manifest["fluidAssets"]["interfaceFrames"][0]).exists()
    assert (viewer_dir / manifest["chartSeries"]["height"]).exists()
    assert (viewer_dir / "vtk" / "frame_0000.vtk").exists()


def test_build_manifest_creates_viewer_directory_for_generated_case(tmp_path: Path) -> None:
    case_dir = generate_case(create_case_file(), tmp_path / "generated")

    viewer_dir = build_manifest(case_dir)
    manifest = json.loads((viewer_dir / "manifest.json").read_text(encoding="utf-8"))

    assert viewer_dir == case_dir / "viewer"
    assert manifest["caseId"] == create_case_file()["caseId"]
    assert manifest["status"] == "mock"


def test_create_real_run_uses_solver_outputs_for_series_and_paraview_links(tmp_path: Path) -> None:
    case_dir = generate_case(create_case_file(), tmp_path / "generated")
    post_processing = case_dir / "postProcessing"
    (post_processing / "containerWaterVolume" / "0").mkdir(parents=True)
    (post_processing / "tubeOutletFlow" / "0").mkdir(parents=True)
    (post_processing / "topInflowFlow" / "0").mkdir(parents=True)
    (case_dir / "VTK").mkdir(exist_ok=True)
    (case_dir / "VTK" / "mesh.vtk").write_text("# vtk\n", encoding="utf-8")
    (post_processing / "containerWaterVolume" / "0" / "volFieldValue.dat").write_text(
        "# Time volume\n0.0 0.0252\n0.1 0.0273\n0.2 0.0294\n",
        encoding="utf-8",
    )
    (post_processing / "tubeOutletFlow" / "0" / "surfaceFieldValue.dat").write_text(
        "# Time phi\n0.0 -0.00011\n0.1 -0.00012\n0.2 -0.00013\n",
        encoding="utf-8",
    )
    (post_processing / "topInflowFlow" / "0" / "surfaceFieldValue.dat").write_text(
        "# Time phi\n0.0 -0.00014\n0.1 -0.00014\n0.2 -0.00014\n",
        encoding="utf-8",
    )

    viewer_dir = create_real_run(case_dir, case_dir / "viewer")
    manifest = json.loads((viewer_dir / "manifest.json").read_text(encoding="utf-8"))
    height_series = json.loads((viewer_dir / manifest["chartSeries"]["height"]).read_text(encoding="utf-8"))
    outlet_flow = json.loads((viewer_dir / manifest["chartSeries"]["outletFlow"]).read_text(encoding="utf-8"))

    assert manifest["status"] == "done"
    assert manifest["paraview"]["foamFile"] == "../.foam"
    assert manifest["paraview"]["vtkDir"] == "../VTK"
    assert height_series[0]["value"] == 0.24
    assert outlet_flow[0]["value"] == 0.00011
    assert len(manifest["fluidAssets"]["interfaceFrames"]) == 3


def test_create_real_run_leaves_vtk_dir_empty_when_solver_vtk_assets_are_missing(tmp_path: Path) -> None:
    case_dir = generate_case(create_case_file(), tmp_path / "generated")
    post_processing = case_dir / "postProcessing"
    (post_processing / "containerWaterVolume" / "0").mkdir(parents=True)
    (post_processing / "tubeOutletFlow" / "0").mkdir(parents=True)
    (post_processing / "containerWaterVolume" / "0" / "volFieldValue.dat").write_text(
        "# Time volume\n0.0 0.0252\n0.1 0.0273\n0.2 0.0294\n",
        encoding="utf-8",
    )
    (post_processing / "tubeOutletFlow" / "0" / "surfaceFieldValue.dat").write_text(
        "# Time phi\n0.0 -0.00011\n0.1 -0.00012\n0.2 -0.00013\n",
        encoding="utf-8",
    )

    viewer_dir = create_real_run(case_dir, case_dir / "viewer")
    manifest = json.loads((viewer_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "done"
    assert manifest["paraview"]["foamFile"] == "../.foam"
    assert manifest["paraview"]["vtkDir"] is None
