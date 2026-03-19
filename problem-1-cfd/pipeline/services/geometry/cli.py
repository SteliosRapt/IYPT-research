"""CLI entrypoints for geometry export and case creation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    build_fixed_geometry_descriptors,
    build_fluid_geometry_descriptors,
    create_case_file,
    create_geometry_snapshot,
    default_forcing_config,
    write_json,
)


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def export_case(case_path: Path, output_dir: Path | None) -> Path:
    case_file = load_json(case_path)
    snapshot = create_geometry_snapshot(case_file["parameters"])
    forcing = case_file.get("forcing", default_forcing_config())
    export_root = output_dir or Path(case_file.get("outputs", {}).get("exportRoot", case_path.parent / case_file["caseId"]))
    export_root.mkdir(parents=True, exist_ok=True)

    write_json(export_root / "case.json", case_file)
    write_json(export_root / "geometry_snapshot.json", snapshot)
    write_json(
        export_root / "fixed_geometry.json",
        build_fixed_geometry_descriptors(snapshot["parameters"], snapshot["derived"]),
    )
    write_json(
        export_root / "fluid_geometry.json",
        build_fluid_geometry_descriptors(snapshot["parameters"], snapshot["derived"], forcing),
    )
    return export_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Geometry service CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    create_parser = subparsers.add_parser("create-case", help="Create a canonical case file.")
    create_parser.add_argument("--output", required=True, help="Output case JSON path.")

    export_parser = subparsers.add_parser("export-case", help="Export geometry assets from a case JSON.")
    export_parser.add_argument("case_json", help="Path to the canonical case JSON.")
    export_parser.add_argument("--output-dir", help="Output directory for exported assets.")

    snapshot_parser = subparsers.add_parser("snapshot", help="Write a geometry snapshot for the default case.")
    snapshot_parser.add_argument("--output", required=True, help="Output snapshot path.")

    args = parser.parse_args()

    if args.command == "create-case":
        case_file = create_case_file()
        write_json(Path(args.output), case_file)
        return

    if args.command == "export-case":
        export_root = export_case(Path(args.case_json), Path(args.output_dir) if args.output_dir else None)
        print(export_root)
        return

    snapshot = create_geometry_snapshot()
    write_json(Path(args.output), snapshot)


if __name__ == "__main__":
    main()
