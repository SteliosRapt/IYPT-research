from __future__ import annotations

import re
from pathlib import Path

from services.geometry.core import DEFAULT_PARAMETERS, HTML_TO_CANONICAL_PARAMETER_MAP

ROOT_DIR = Path(__file__).resolve().parents[2]


def test_html_defaults_match_canonical_defaults() -> None:
    html = (ROOT_DIR / "setup_3d (2).html").read_text(encoding="utf-8")
    matches = re.findall(r"\{ id:'([^']+)'.*?default:([0-9.]+) \}", html)
    defaults = {
        HTML_TO_CANONICAL_PARAMETER_MAP.get(identifier, identifier): float(default_value)
        for identifier, default_value in matches
    }

    assert defaults == DEFAULT_PARAMETERS


def test_markdown_contains_required_geometry_statements() -> None:
    markdown = (ROOT_DIR / "experimental_setup.md").read_text(encoding="utf-8")
    assert "No holders at P₁, P₂, or P₅" in markdown
    assert "rightmost structure ends exactly at X₅" in markdown
    assert "rounded bends" in markdown
    assert "P₂, P₃, and P₄" in markdown
    assert "Tube path" in markdown
    assert "P₁ → (W₁) → P₂ → P₃ → P₄ → (W₂) → P₅" in markdown
