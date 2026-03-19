from __future__ import annotations

import json
from pathlib import Path

from services.geometry.core import create_case_file, create_geometry_snapshot

ROOT_DIR = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT_DIR / "packages" / "shared-schema" / "src" / "fixtures" / "geometry-contract.json"
CASE_IDENTITY_FIXTURE_PATH = ROOT_DIR / "packages" / "shared-schema" / "src" / "fixtures" / "case-identity-contract.json"


def test_python_geometry_matches_shared_contract_fixture() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    for case in payload["cases"]:
        snapshot = create_geometry_snapshot(case["raw"])

        assert snapshot["parameters"] == case["parameters"]
        assert snapshot["derived"] == case["derived"]
        assert snapshot["constraints"] == case["constraints"]


def test_python_case_identity_matches_shared_contract_fixture() -> None:
    payload = json.loads(CASE_IDENTITY_FIXTURE_PATH.read_text(encoding="utf-8"))

    for case in payload["cases"]:
        case_file = create_case_file(
            case["parameters"] or None,
            transport=case["transport"],
            meshing={"preset": case["meshingPreset"]},
        )

        assert case_file["caseId"] == case["caseId"]
        assert case_file["provenance"]["parameterHash"] == case["parameterHash"]
