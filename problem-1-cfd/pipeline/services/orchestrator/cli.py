"""CLI for case generation and solver run orchestration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess

from .case import generate_case


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def run_case(case_dir: Path) -> None:
    case_file = load_json(case_dir / "case.json")
    solver = case_file["solver"]["solver"]
    has_openfoam = command_exists(solver)
    has_docker = command_exists("docker")

    if has_openfoam:
        result = subprocess.run(["bash", "Allrun"], cwd=case_dir, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Allrun exited with code {result.returncode} in {case_dir}")
        return

    if has_docker:
        raise RuntimeError(
            "Docker is present but no container orchestration is wired. "
            "Run the solver manually via Docker."
        )

    raise RuntimeError(
        f"Solver '{solver}' not found and Docker is not available. "
        "Install OpenFOAM or Docker to run this case."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Orchestrator CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate-case", help="Generate an OpenFOAM-style case directory.")
    generate_parser.add_argument("case_json", help="Path to the canonical case JSON.")
    generate_parser.add_argument("--output-dir", required=True, help="Output case directory.")

    run_parser = subparsers.add_parser("run-case", help="Run the generated case (requires OpenFOAM or Docker).")
    run_parser.add_argument("case_dir", help="Path to the generated case directory.")

    args = parser.parse_args()

    if args.command == "generate-case":
        case_file = load_json(args.case_json)
        output_dir = generate_case(case_file, Path(args.output_dir))
        print(output_dir)
        return

    run_case(Path(args.case_dir))


if __name__ == "__main__":
    main()

