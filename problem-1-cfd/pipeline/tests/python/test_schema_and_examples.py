from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT_DIR = Path(__file__).resolve().parents[2]
SCHEMA_DIR = ROOT_DIR / "packages" / "shared-schema" / "src" / "schemas"


def _load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))


def test_example_case_and_manifest_validate() -> None:
    parameters_schema = _load_schema("parameters.schema.json")
    case_schema = _load_schema("case.schema.json")
    manifest_schema = _load_schema("run-manifest.schema.json")
    registry = Registry()
    registry = registry.with_resource(
        parameters_schema["$id"],
        Resource.from_contents(parameters_schema),
    )
    registry = registry.with_resource(
        "parameters.schema.json",
        Resource.from_contents(parameters_schema),
    )
    case_validator = Draft202012Validator(case_schema, registry=registry)
    manifest_validator = Draft202012Validator(manifest_schema)

    case_payload = json.loads((ROOT_DIR / "examples" / "default-case.json").read_text(encoding="utf-8"))
    manifest_payload = json.loads((ROOT_DIR / "examples" / "default-mock" / "manifest.json").read_text(encoding="utf-8"))

    case_validator.validate(case_payload)
    manifest_validator.validate(manifest_payload)
