"""Regenerate the committed example assets."""

from __future__ import annotations

from pathlib import Path

from services.geometry.core import create_case_file
from services.orchestrator.case import generate_case
from services.utils import write_json
from services.viewer_data.mock import create_mock_run

ROOT_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    examples_dir = ROOT_DIR / "examples"
    catalog_dir = examples_dir / "catalog"
    sample_cases_dir = examples_dir / "sample-cases"
    sample_runs_dir = examples_dir / "sample-runs"
    case_path = sample_cases_dir / "default-case.json"
    case_file = create_case_file()
    write_json(case_path, case_file)
    generate_case(case_file, sample_cases_dir / "default-openfoam-case")
    create_mock_run(case_path, sample_runs_dir / "default-mock")
    index_payload = {
        "runs": [
            {
                "id": "default-mock",
                "label": "Default mock run",
                "manifest": "sample-runs/default-mock/manifest.json",
            }
        ]
    }
    write_json(
        catalog_dir / "index.json",
        index_payload,
    )
    write_json(examples_dir / "index.json", index_payload)


if __name__ == "__main__":
    main()

