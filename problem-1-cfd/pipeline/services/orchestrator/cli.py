"""CLI for case generation and solver run orchestration."""

from __future__ import annotations

import argparse
from pathlib import Path

from .case import generate_case
from .runtime import command_exists, load_json, run_case


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

