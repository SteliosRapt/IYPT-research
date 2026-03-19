"""Local smoke runner for the Python pipeline."""

from __future__ import annotations

from pathlib import Path

from services.geometry.core import create_case_file, write_json
from services.orchestrator.case import generate_case
from services.viewer_data.mock import create_mock_run


def main() -> None:
    output_root = Path("tmp") / "smoke"
    output_root.mkdir(parents=True, exist_ok=True)
    case_file = create_case_file()
    case_path = output_root / "case.json"
    write_json(case_path, case_file)
    case_dir = generate_case(case_file, output_root / "openfoam-case")
    viewer_dir = create_mock_run(case_path, output_root / "viewer")
    print(case_dir)
    print(viewer_dir)


if __name__ == "__main__":
    main()

