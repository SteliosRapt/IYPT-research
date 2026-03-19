from __future__ import annotations

import json
from pathlib import Path

from services.geometry.core import create_case_file
from services.orchestrator.case import generate_case
from services.utils import write_json
from services.viewer_data.mock import create_mock_run


def test_case_generation_and_mock_run_smoke(tmp_path: Path) -> None:
    case_file = create_case_file()
    case_json = tmp_path / "case.json"
    write_json(case_json, case_file)

    case_dir = generate_case(json.loads(case_json.read_text(encoding="utf-8")), tmp_path / "generated")
    viewer_dir = create_mock_run(case_json, tmp_path / "viewer")

    assert (case_dir / "system" / "blockMeshDict").exists()
    assert (case_dir / "fixed_geometry.json").exists()
    assert (viewer_dir / "manifest.json").exists()
    assert (viewer_dir / "frames" / "frame_0000.json").exists()
