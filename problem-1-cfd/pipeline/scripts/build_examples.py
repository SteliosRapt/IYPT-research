"""Regenerate the committed example assets."""

from __future__ import annotations

from pathlib import Path

from services.geometry.core import create_case_file, write_json
from services.orchestrator.case import generate_case
from services.viewer_data.mock import create_mock_run

ROOT_DIR = Path(__file__).resolve().parents[1]


def main() -> None:
    examples_dir = ROOT_DIR / "examples"
    case_path = examples_dir / "default-case.json"
    case_file = create_case_file()
    write_json(case_path, case_file)
    generate_case(case_file, examples_dir / "default-openfoam-case")
    create_mock_run(case_path, examples_dir / "default-mock")
    write_json(
        examples_dir / "index.json",
        {
            "runs": [
                {
                    "id": "default-mock",
                    "label": "Default mock run",
                    "manifest": "default-mock/manifest.json",
                }
            ]
        },
    )


if __name__ == "__main__":
    main()

