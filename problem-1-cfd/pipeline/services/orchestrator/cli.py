"""CLI for case generation and mock/solver run orchestration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from services.viewer_data.mock import create_mock_run

from .case import generate_case


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_case(case_dir: Path) -> Path:
    case_file = load_json(case_dir / "case.json")
    has_openfoam = command_exists(case_file["solver"]["solver"])
    has_docker = command_exists("docker")

    if has_openfoam:
        subprocess.run(["bash", "Allrun"], cwd=case_dir, check=False)
    elif has_docker:
        (case_dir / "run_result.txt").write_text(
            "Docker is present but no container orchestration is wired in this environment.\n",
            encoding="utf-8",
        )

    return create_mock_run(case_dir / "case.json", case_dir / "viewer")


def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate-case", help="Generate an OpenFOAM-style case directory.")
    generate_parser.add_argument("case_json", help="Path to the canonical case JSON.")
    generate_parser.add_argument("--output-dir", required=True, help="Output case directory.")

    run_parser = subparsers.add_parser("run-case", help="Run the generated case or fall back to mock data.")
    run_parser.add_argument("case_dir", help="Path to the generated case directory.")

    args = parser.parse_args()

    if args.command == "generate-case":
        case_file = load_json(args.case_json)
        output_dir = generate_case(case_file, Path(args.output_dir))
        print(output_dir)
        return

    output_dir = run_case(Path(args.case_dir))
    print(output_dir)


if __name__ == "__main__":
    main()

