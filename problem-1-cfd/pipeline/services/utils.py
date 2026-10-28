"""Shared utility helpers used across Python services."""

from __future__ import annotations

from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
from typing import Any


def _canonical_number(value: int | float | Decimal) -> str:
    if isinstance(value, bool):
        raise TypeError("Booleans must be handled before number serialization.")
    if isinstance(value, int):
        return str(value)

    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    rendered = format(decimal_value, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    if rendered in {"", "-0"}:
        return "0"
    return rendered


def stable_serialize(value: Any) -> str:
    if value is None or isinstance(value, bool) or isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
        return _canonical_number(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(stable_serialize(item) for item in value) + "]"
    if isinstance(value, dict):
        items = [
            f"{json.dumps(str(key))}: {stable_serialize(value[key])}"
            for key in sorted(value)
        ]
        return "{" + ", ".join(items) + "}"
    raise TypeError(f"Unsupported value for stable serialization: {type(value)!r}")


def stable_hash(value: Any) -> str:
    payload = stable_serialize(value).encode("utf-8")
    return sha256(payload).hexdigest()[:10]


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
