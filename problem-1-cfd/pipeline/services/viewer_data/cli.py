"""CLI for mock viewer data and manifest assembly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .mock import create_mock_run


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_manifest(case_dir: Path) -> Path:
    viewer_dir = case_dir / "viewer"
    viewer_dir.mkdir(exist_ok=True)
    return create_mock_run(case_dir / "case.json", viewer_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Viewer-data CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    mock_parser = subparsers.add_parser("mock-run", help="Generate a synthetic run for a case JSON.")
    mock_parser.add_argument("case_json", help="Path to the canonical case JSON.")
    mock_parser.add_argument("--output-dir", required=True, help="Output directory.")

    manifest_parser = subparsers.add_parser("build-manifest", help="Build or refresh a viewer manifest from a generated case.")
    manifest_parser.add_argument("case_dir", help="Path to the generated case directory.")

    args = parser.parse_args()

    if args.command == "mock-run":
        output = create_mock_run(args.case_json, args.output_dir)
        print(output)
        return

    output = build_manifest(Path(args.case_dir))
    print(output)


if __name__ == "__main__":
    main()
