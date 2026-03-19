"""Shared utility helpers used across Python services."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any


def stable_hash(parameters: dict[str, Any]) -> str:
    payload = json.dumps(parameters, sort_keys=True).encode("utf-8")
    return sha256(payload).hexdigest()[:10]


def write_json(path: Path, payload: dict[str, Any] | list[Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
