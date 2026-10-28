"""Canonical geometry parameters and shared constants."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
SOURCE_FILES = ["experimental_setup.md", "setup_3d (2).html"]
SCHEMA_DIR = ROOT_DIR / "packages" / "shared-schema" / "src" / "schemas"
TUBE_WALL_THICKNESS_RATIO = 0.2
CASE_RUN_STATUS_STATES = ("not_started", "generated", "running", "done", "failed")


@dataclass(frozen=True)
class ParameterDefinition:
    identifier: str
    label: str
    section: str
    min_value: float
    max_value: float
    step: float
    default: float


PARAMETER_DEFINITIONS = [
    ParameterDefinition("A0", "A0", "primary", 0.01, 0.5, 0.001, 0.105),
    ParameterDefinition("h0", "h0", "primary", 0.05, 0.6, 0.005, 0.3),
    ParameterDefinition("h1", "h1", "primary", 0.01, 0.25, 0.005, 0.04),
    ParameterDefinition("h3", "h3", "primary", 0.01, 0.25, 0.005, 0.12),
    ParameterDefinition("h5", "h5", "primary", 0.01, 0.25, 0.005, 0.065),
    ParameterDefinition("Y2", "Y2", "primary", 0.005, 0.2, 0.005, 0.015),
    ParameterDefinition("Y4", "Y4", "primary", 0.005, 0.3, 0.005, 0.035),
    ParameterDefinition("W1", "W1", "primary", 0.01, 0.3, 0.005, 0.06),
    ParameterDefinition("W2", "W2", "primary", 0.01, 0.3, 0.005, 0.03),
    ParameterDefinition("L1", "L1", "primary", 0.05, 0.8, 0.005, 0.3),
    ParameterDefinition("L2", "L2", "primary", 0.05, 0.6, 0.005, 0.18),
    ParameterDefinition("L3", "L3", "primary", 0.05, 0.8, 0.005, 0.245),
    ParameterDefinition("L4", "L4", "primary", 0.05, 0.8, 0.005, 0.325),
    ParameterDefinition("A", "A", "primary", 0.0001, 0.005, 0.0001, 0.0002),
    ParameterDefinition("W", "W", "primary", 0.03, 0.5, 0.005, 0.3),
    ParameterDefinition("alpha", "alpha", "structural", 0.005, 0.06, 0.001, 0.02),
    ParameterDefinition("Ct", "Ct", "structural", 0.001, 0.02, 0.001, 0.004),
    ParameterDefinition("ht", "ht", "structural", 0.001, 0.02, 0.001, 0.003),
    ParameterDefinition("P24t", "P24t", "structural", 0.001, 0.06, 0.001, 0.015),
    ParameterDefinition("hw", "hw", "structural", 0.005, 0.06, 0.001, 0.02),
    ParameterDefinition("h_a", "h_a", "structural", 0.0, 0.05, 0.001, 0.01),
    ParameterDefinition("bendR", "bendR", "bend", 0.005, 0.08, 0.001, 0.024),
]

DEFAULT_PARAMETERS = {definition.identifier: definition.default for definition in PARAMETER_DEFINITIONS}

HTML_TO_CANONICAL_PARAMETER_MAP = {
    "A0": "A0",
    "h0": "h0",
    "h1": "h1",
    "h3": "h3",
    "h5": "h5",
    "Y2": "Y2",
    "Y4": "Y4",
    "W1p": "W1",
    "W2p": "W2",
    "L1": "L1",
    "L2": "L2",
    "L3": "L3",
    "L4": "L4",
    "A_tube": "A",
    "Wc": "W",
    "alpha": "alpha",
    "Ct": "Ct",
    "ht": "ht",
    "P24t": "P24t",
    "hw": "hw",
    "ha": "h_a",
    "bendR": "bendR",
}

CONSTRAINT_LABELS = [
    ("S0_negative", "S0 < 0"),
    ("ordering", "0 < S1 < X2 < X3 < X4 < S2 < X5"),
    ("tube_heights_below_h0", "h1, h2, h3, h5 < h0"),
    ("valleys_below_h2", "h1, h3 < h2"),
    ("h2_below_h4", "h2 < h4"),
    ("left_clearance", "|S0| >= sqrt(A/pi) + Ct/2"),
    ("S1_clearance", "S1 >= sqrt(A/pi) + alpha/2"),
    ("X2_clearance", "X2 >= S1 + alpha/2 + Ct/2"),
    ("X3_clearance", "X3 >= X2 + alpha/2 + Ct/2"),
    ("X4_clearance", "X4 >= X3 + alpha"),
    ("S2_clearance", "S2 >= X4 + alpha + sqrt(A/pi)"),
    ("X5_clearance", "X5 >= alpha/2 + S2"),
    ("alpha_vs_Ct", "alpha >= Ct"),
    ("alpha_vs_radius", "alpha >= 2.5 * sqrt(A/pi)"),
    ("P24t_vs_alpha", "P24t <= alpha"),
    ("arg1", "L1^2 >= (h2 - h1)^2"),
    ("arg2", "L2^2 >= (h3 - h2)^2"),
    ("arg3", "L3^2 >= (h4 - h3)^2"),
    ("arg4", "L4^2 >= (h5 - h4)^2"),
]
