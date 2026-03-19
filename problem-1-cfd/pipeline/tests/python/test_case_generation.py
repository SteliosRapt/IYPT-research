from __future__ import annotations

import copy
import json
from pathlib import Path
import pytest

from services.geometry.core import SOURCE_FILES, create_case_file, create_geometry_snapshot, default_transport_config
from services.orchestrator.case import (
    build_block_mesh_dict,
    build_transport_properties,
    generate_case,
    mesh_preset,
)
from services.utils import write_json
from services.viewer_data.mock import create_mock_run


def test_create_case_file_includes_transport_defaults() -> None:
    case_file = create_case_file()

    assert case_file["transport"] == default_transport_config()
    assert case_file["provenance"]["sourceFiles"] == SOURCE_FILES


def test_create_case_file_hashes_full_simulation_identity() -> None:
    base_case = create_case_file()
    transport_case = create_case_file(transport={"sigma": 0.081})
    meshing_case = create_case_file(meshing={"preset": "fine"})
    display_name_case = create_case_file(display_name="Variant")

    assert base_case["provenance"]["parameterHash"] == transport_case["provenance"]["parameterHash"]
    assert base_case["provenance"]["parameterHash"] == meshing_case["provenance"]["parameterHash"]
    assert base_case["caseId"] != transport_case["caseId"]
    assert base_case["caseId"] != meshing_case["caseId"]
    assert base_case["caseId"] != display_name_case["caseId"]


def test_generate_case_preserves_input_and_uses_forcing_velocity(tmp_path: Path) -> None:
    case_file = create_case_file()
    case_file["forcing"]["inflowVelocity"] = 0.037
    case_file["transport"]["sigma"] = 0.081
    original = copy.deepcopy(case_file)

    case_dir = generate_case(case_file, tmp_path / "generated")

    assert case_file == original
    generated_case = json.loads((case_dir / "case.json").read_text(encoding="utf-8"))
    velocity_file = (case_dir / "0" / "U").read_text(encoding="utf-8")
    transport_file = (case_dir / "constant" / "transportProperties").read_text(encoding="utf-8")
    control_dict = (case_dir / "system" / "controlDict").read_text(encoding="utf-8")
    topo_set_dict = (case_dir / "system" / "topoSetDict").read_text(encoding="utf-8")
    set_fields_dict = (case_dir / "system" / "setFieldsDict").read_text(encoding="utf-8")
    snappy_dict = (case_dir / "system" / "snappyHexMeshDict").read_text(encoding="utf-8")
    surface_feature_extract_dict = (case_dir / "system" / "surfaceFeatureExtractDict").read_text(encoding="utf-8")
    allrun = (case_dir / "Allrun").read_text(encoding="utf-8")

    assert generated_case["runStatus"]["state"] == "generated"
    assert "topInflow { type fixedValue; value uniform (0 -0.037 0); }" in velocity_file
    assert "sigma 0.081;" in transport_file
    assert "containerWaterVolume" in control_dict
    assert "tubeOutletFlow" in control_dict
    assert "topInflowFlow" in control_dict
    assert "type cellZoneSet;" in topo_set_dict
    assert "volScalarFieldValue alpha.water 1" in set_fields_dict
    assert "walls.stl" in snappy_dict
    assert "solidObstructions.stl" in snappy_dict
    assert "type searchableBox;" in snappy_dict
    assert "bendBoxP2" in snappy_dict
    assert "bendBoxes" not in snappy_dict
    assert "surfaceFeatureExtract" in allrun
    assert "setFields" in allrun
    assert "foamToVTK || true" in allrun
    assert "walls.stl" in surface_feature_extract_dict
    assert (case_dir / "constant" / "triSurface" / "walls.stl").exists()
    assert (case_dir / "constant" / "triSurface" / "topAtmosphere.stl").exists()
    assert (case_dir / "constant" / "triSurface" / "topInflow.stl").exists()
    assert (case_dir / "constant" / "triSurface" / "tubeOutlet.stl").exists()
    assert (case_dir / "constant" / "triSurface" / "solidObstructions.stl").exists()


def test_mesh_preset_derives_background_size_and_levels() -> None:
    snapshot = create_geometry_snapshot()
    domain_span = min(
        snapshot["parameters"]["W"],
        snapshot["parameters"]["h0"] + snapshot["parameters"]["h_a"],
        snapshot["derived"]["X5"] - snapshot["derived"]["S0"],
    )

    coarse = mesh_preset(snapshot["parameters"], snapshot["derived"], "coarse")
    medium = mesh_preset(snapshot["parameters"], snapshot["derived"], "medium")
    fine = mesh_preset(snapshot["parameters"], snapshot["derived"], "fine")

    assert coarse["backgroundCellSize"] == round(domain_span / 24.0, 6)
    assert medium["backgroundCellSize"] == round(domain_span / 36.0, 6)
    assert fine["backgroundCellSize"] == round(domain_span / 48.0, 6)
    assert coarse["refinementLevels"] == {"opening": 2, "bends": 2, "outlet": 2, "freeSurface": 2}
    assert medium["refinementLevels"] == {"opening": 3, "bends": 3, "outlet": 3, "freeSurface": 3}
    assert fine["refinementLevels"] == {"opening": 4, "bends": 4, "outlet": 4, "freeSurface": 4}


def test_block_mesh_dict_uses_expected_bounds_and_cell_counts() -> None:
    case_file = create_case_file()
    snapshot = create_geometry_snapshot(case_file["parameters"])
    case_file["meshing"] = mesh_preset(snapshot["parameters"], snapshot["derived"], "coarse")
    block_mesh_dict = build_block_mesh_dict(case_file, snapshot)

    parameters = snapshot["parameters"]
    derived = snapshot["derived"]
    margin = max(parameters["W"], parameters["h0"] + parameters["h_a"], derived["X5"] - derived["S0"]) * 0.25
    x_min = derived["S0"] - margin
    x_max = derived["X5"] + margin
    y_min = -margin * 0.5
    y_max = parameters["h0"] + parameters["h_a"] + margin
    z_min = -parameters["W"] / 2 - margin * 0.5
    z_max = parameters["W"] / 2 + margin * 0.5
    background = case_file["meshing"]["backgroundCellSize"]
    nx = max(8, int((x_max - x_min) / background))
    ny = max(8, int((y_max - y_min) / background))
    nz = max(8, int((z_max - z_min) / background))

    assert f"({x_min} {y_min} {z_min})" in block_mesh_dict
    assert f"({x_max} {y_max} {z_max})" in block_mesh_dict
    assert f"hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)" in block_mesh_dict


def test_transport_properties_use_explicit_case_values() -> None:
    transport_properties = build_transport_properties(
        {
            "transport": {
                "waterNu": 2e-6,
                "waterRho": 997.1,
                "airNu": 1.7e-5,
                "airRho": 1.1,
                "sigma": 0.081,
            }
        }
    )

    assert "nu 2e-06;" in transport_properties
    assert "rho 997.1;" in transport_properties
    assert "nu 1.7e-05;" in transport_properties
    assert "rho 1.1;" in transport_properties
    assert "sigma 0.081;" in transport_properties


def test_mock_manifest_reuses_case_provenance_metadata(tmp_path: Path) -> None:
    case_file = create_case_file()
    case_path = tmp_path / "case.json"
    write_json(case_path, case_file)

    viewer_dir = create_mock_run(case_path, tmp_path / "viewer")
    manifest = json.loads((viewer_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "mock"
    assert manifest["metadata"]["parameterHash"] == case_file["provenance"]["parameterHash"]
    assert manifest["metadata"]["sourceFiles"] == SOURCE_FILES


def test_generate_case_clears_stale_generated_outputs(tmp_path: Path) -> None:
    case_dir = generate_case(create_case_file(), tmp_path / "generated")
    stale_output = case_dir / "postProcessing" / "containerWaterVolume" / "0" / "volFieldValue.dat"
    stale_output.parent.mkdir(parents=True, exist_ok=True)
    stale_output.write_text("stale\n", encoding="utf-8")

    regenerated_dir = generate_case(create_case_file(transport={"sigma": 0.081}), case_dir)

    assert regenerated_dir == case_dir
    assert not stale_output.exists()


def test_generate_case_rejects_non_generated_directory(tmp_path: Path) -> None:
    target = tmp_path / "manual-dir"
    target.mkdir()
    (target / "notes.txt").write_text("do not overwrite\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match="Refusing to overwrite non-generated directory"):
        generate_case(create_case_file(), target)
