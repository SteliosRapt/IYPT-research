"""CLI for mock viewer data and manifest assembly."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from services.utils import write_json
from .mock import create_mock_run
from .real import create_real_run, has_real_post_processing

ROOT_DIR = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = ROOT_DIR / "examples"
INDEX_PATH = EXAMPLES_DIR / "index.json"


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _update_index(run_output_dir: Path, label: str | None) -> None:
    """Register run_output_dir in examples/index.json if it lives under examples/."""
    try:
        rel = run_output_dir.resolve().relative_to(EXAMPLES_DIR.resolve())
    except ValueError:
        return  # output is outside examples/ — skip index update

    manifest_rel = str(rel / "manifest.json").replace("\\", "/")
    run_id = rel.parts[0]
    display_label = label or run_id.replace("-", " ").replace("_", " ").title()

    index: dict = {"runs": []}
    if INDEX_PATH.exists():
        index = load_json(INDEX_PATH)

    existing_ids = {r["id"] for r in index["runs"]}
    if run_id not in existing_ids:
        index["runs"].append({"id": run_id, "label": display_label, "manifest": manifest_rel})
        write_json(INDEX_PATH, index)
        print(f"Registered run '{run_id}' in {INDEX_PATH}")


def build_manifest(case_dir: Path) -> Path:
    viewer_dir = case_dir / "viewer"
    viewer_dir.mkdir(exist_ok=True)
    if has_real_post_processing(case_dir):
        return create_real_run(case_dir, viewer_dir)
    return create_mock_run(case_dir / "case.json", viewer_dir)


def main() -> None:
    parser = argparse.ArgumentParser(description="Viewer-data CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    mock_parser = subparsers.add_parser("mock-run", help="Generate a synthetic run for a case JSON.")
    mock_parser.add_argument("case_json", help="Path to the canonical case JSON.")
    mock_parser.add_argument("--output-dir", required=True, help="Output directory.")
    mock_parser.add_argument("--label", default=None, help="Human-readable label for the run index.")

    manifest_parser = subparsers.add_parser("build-manifest", help="Build or refresh a viewer manifest from a generated case.")
    manifest_parser.add_argument("case_dir", help="Path to the generated case directory.")

    args = parser.parse_args()

    if args.command == "mock-run":
        output = create_mock_run(args.case_json, args.output_dir)
        _update_index(Path(args.output_dir).resolve(), args.label)
        print(output)
        return

    output = build_manifest(Path(args.case_dir))
    print(output)


if __name__ == "__main__":
    main()
