"""Canonical geometry computations derived from the source-of-truth files."""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any

from services.utils import stable_hash

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


def _round(value: float) -> float:
    return round(value, 12)


def _clamped_sqrt(value: float) -> float:
    return math.sqrt(value) if value > 0 else 0.0


def normalize_parameters(raw: dict[str, Any] | None = None) -> dict[str, float]:
    merged = dict(DEFAULT_PARAMETERS)
    if raw:
        for key, value in raw.items():
            if value is None:
                continue
            mapped = HTML_TO_CANONICAL_PARAMETER_MAP.get(key, key)
            merged[mapped] = float(value)
    merged["P4t"] = merged["alpha"]
    merged["wallThicknessRatio"] = TUBE_WALL_THICKNESS_RATIO
    return merged


def build_tube_path(points: list[dict[str, float]], bend_radius: float) -> list[dict[str, float]]:
    all_points: list[dict[str, float]] = []
    arc_segments = 24

    for index, current in enumerate(points):
        if index in (0, len(points) - 1):
            all_points.append({"x": _round(current["x"]), "y": _round(current["y"])})
            continue

        previous = points[index - 1]
        nxt = points[index + 1]
        dx_a = current["x"] - previous["x"]
        dy_a = current["y"] - previous["y"]
        dx_b = nxt["x"] - current["x"]
        dy_b = nxt["y"] - current["y"]
        len_a = math.hypot(dx_a, dy_a)
        len_b = math.hypot(dx_b, dy_b)

        if len_a < 1e-8 or len_b < 1e-8:
            all_points.append({"x": _round(current["x"]), "y": _round(current["y"])})
            continue

        u_ax, u_ay = dx_a / len_a, dy_a / len_a
        u_bx, u_by = dx_b / len_b, dy_b / len_b
        dot = max(-1.0, min(1.0, u_ax * u_bx + u_ay * u_by))
        half_angle = math.acos(dot) / 2.0

        if abs(half_angle) < 1e-6 or abs(math.pi - half_angle * 2.0) < 1e-6:
            all_points.append({"x": _round(current["x"]), "y": _round(current["y"])})
            continue

        offset = min(bend_radius, len_a * 0.45, len_b * 0.45)
        p0x = current["x"] - u_ax * offset
        p0y = current["y"] - u_ay * offset
        p1x = current["x"] + u_bx * offset
        p1y = current["y"] + u_by * offset
        pcx = 2 * current["x"] - 0.5 * (p0x + p1x)
        pcy = 2 * current["y"] - 0.5 * (p0y + p1y)

        all_points.append({"x": _round(p0x), "y": _round(p0y)})
        for step in range(1, arc_segments):
            s = step / arc_segments
            one_minus_s = 1.0 - s
            qx = one_minus_s * one_minus_s * p0x + 2 * one_minus_s * s * pcx + s * s * p1x
            qy = one_minus_s * one_minus_s * p0y + 2 * one_minus_s * s * pcy + s * s * p1y
            all_points.append({"x": _round(qx), "y": _round(qy)})
        all_points.append({"x": _round(p1x), "y": _round(p1y)})

    return all_points


def compute_derived(parameters: dict[str, float]) -> dict[str, Any]:
    radius = math.sqrt(parameters["A"] / math.pi)
    h2 = parameters["h0"] - parameters["Y2"]
    h4 = parameters["h0"] + parameters["Y4"]
    arg1 = parameters["L1"] ** 2 - (h2 - parameters["h1"]) ** 2
    x2 = _clamped_sqrt(arg1)
    arg2 = parameters["L2"] ** 2 - (parameters["h3"] - h2) ** 2
    x3 = _clamped_sqrt(arg2) + x2
    arg3 = parameters["L3"] ** 2 - (h4 - parameters["h3"]) ** 2
    x4 = _clamped_sqrt(arg3) + x3
    arg4 = parameters["L4"] ** 2 - (parameters["h5"] - h4) ** 2
    x5 = _clamped_sqrt(arg4) + x4
    s1 = parameters["W1"]
    s2 = x5 - parameters["W2"]
    s0 = x2 - parameters["A0"] / parameters["W"]
    c1 = ((h2 - parameters["h1"]) / x2) * s1 + parameters["h1"] if x2 > 0 else parameters["h1"]
    c2 = ((parameters["h5"] - h4) / (x5 - x4)) * (s2 - x4) + h4 if x5 > x4 else h4

    points = {
        "W0": {"x": _round(s0), "y": _round(parameters["h0"])},
        "P1": {"x": 0.0, "y": _round(parameters["h1"])},
        "W1": {"x": _round(s1), "y": _round(c1)},
        "P2": {"x": _round(x2), "y": _round(h2)},
        "P3": {"x": _round(x3), "y": _round(parameters["h3"])},
        "P4": {"x": _round(x4), "y": _round(h4)},
        "W2": {"x": _round(s2), "y": _round(c2)},
        "P5": {"x": _round(x5), "y": _round(parameters["h5"])},
    }

    return {
        "r": _round(radius),
        "P4t": _round(parameters["P4t"]),
        "h2": _round(h2),
        "h4": _round(h4),
        "X2": _round(x2),
        "X3": _round(x3),
        "X4": _round(x4),
        "X5": _round(x5),
        "S0": _round(s0),
        "S1": _round(s1),
        "S2": _round(s2),
        "C1": _round(c1),
        "C2": _round(c2),
        "H0": _round((4 * h2) / 5),
        "planArea": _round(parameters["A0"]),
        "points": points,
        "tubePolyline": build_tube_path(
            [points["P1"], points["P2"], points["P3"], points["P4"], points["P5"]],
            parameters["bendR"],
        ),
        "holderBases": [
            {"name": "W1", "x": _round(s1), "y": 0.0},
            {"name": "P3", "x": _round(x3), "y": 0.0},
            {"name": "W2", "x": _round(s2), "y": 0.0},
            {"name": "P4", "x": _round(x4), "y": _round(parameters["h0"])},
        ],
        "structure": {
            "containerLeft": _round(s0),
            "containerRight": _round(x2),
            "totalHeight": _round(parameters["h0"] + parameters["h_a"]),
            "columnZ": [
                _round(parameters["W"] / 2 - parameters["alpha"] / 2),
                _round(-(parameters["W"] / 2 - parameters["alpha"] / 2)),
            ],
            "centerRail": {"startX": _round(x2), "endX": _round(x5), "y": 0.0},
        },
        "sqrtArgs": {"arg1": arg1, "arg2": arg2, "arg3": arg3, "arg4": arg4},
    }


def check_constraints(parameters: dict[str, float], derived: dict[str, Any]) -> list[dict[str, Any]]:
    checks = [
        derived["S0"] < 0,
        0 < derived["S1"] < derived["X2"] < derived["X3"] < derived["X4"] < derived["S2"] < derived["X5"],
        parameters["h1"] < parameters["h0"]
        and derived["h2"] < parameters["h0"]
        and parameters["h3"] < parameters["h0"]
        and parameters["h5"] < parameters["h0"],
        parameters["h1"] < derived["h2"] and parameters["h3"] < derived["h2"],
        derived["h2"] < derived["h4"],
        abs(derived["S0"]) >= derived["r"] + parameters["Ct"] / 2,
        derived["S1"] >= derived["r"] + parameters["alpha"] / 2,
        derived["X2"] >= derived["S1"] + parameters["alpha"] / 2 + parameters["Ct"] / 2,
        derived["X3"] >= derived["X2"] + parameters["alpha"] / 2 + parameters["Ct"] / 2,
        derived["X4"] >= derived["X3"] + parameters["alpha"],
        derived["S2"] >= derived["X4"] + parameters["alpha"] + derived["r"],
        derived["X5"] >= parameters["alpha"] / 2 + derived["S2"],
        parameters["alpha"] >= parameters["Ct"],
        parameters["alpha"] >= 2.5 * derived["r"],
        parameters["P24t"] <= parameters["alpha"],
        derived["sqrtArgs"]["arg1"] >= 0,
        derived["sqrtArgs"]["arg2"] >= 0,
        derived["sqrtArgs"]["arg3"] >= 0,
        derived["sqrtArgs"]["arg4"] >= 0,
    ]
    return [
        {"id": identifier, "label": label, "ok": checks[index]}
        for index, (identifier, label) in enumerate(CONSTRAINT_LABELS)
    ]


def build_fixed_geometry_descriptors(parameters: dict[str, float], derived: dict[str, Any]) -> dict[str, Any]:
    container_length = derived["X2"] - derived["S0"]
    center_x = derived["S0"] + container_length / 2
    total_height = parameters["h0"] + parameters["h_a"]
    alpha = parameters["alpha"]
    front_z = parameters["W"] / 2 - alpha / 2
    back_z = -front_z
    beam_length = max(derived["X4"] - alpha / 2 - derived["X2"], 0.0)
    beam_center = derived["X2"] + beam_length / 2 if beam_length > 0 else derived["X2"]
    inner_radius = max(derived["r"] * (1 - parameters["wallThicknessRatio"]), derived["r"] * 0.1)

    return {
        "container": [
            {
                "type": "box",
                "name": "bottom",
                "center": [center_x, 0.0, 0.0],
                "size": [container_length + parameters["Ct"], parameters["Ct"], parameters["W"]],
            },
            {
                "type": "box",
                "name": "leftWall",
                "center": [derived["S0"], total_height / 2, 0.0],
                "size": [parameters["Ct"], total_height, parameters["W"]],
            },
            {
                "type": "wallWithHole",
                "name": "rightWall",
                "center": [derived["X2"], total_height / 2, 0.0],
                "size": [parameters["Ct"], total_height, parameters["W"]],
                "hole": {"radius": derived["r"], "centerY": derived["h2"]},
            },
            {
                "type": "box",
                "name": "frontWall",
                "center": [center_x, total_height / 2, parameters["W"] / 2],
                "size": [container_length + parameters["Ct"], total_height, parameters["Ct"]],
            },
            {
                "type": "box",
                "name": "backWall",
                "center": [center_x, total_height / 2, -parameters["W"] / 2],
                "size": [container_length + parameters["Ct"], total_height, parameters["Ct"]],
            },
        ],
        "tube": [
            {
                "type": "tube",
                "name": "tubeShell",
                "path": [[point["x"], point["y"], 0.0] for point in derived["tubePolyline"]],
                "outerRadius": derived["r"],
                "innerRadius": inner_radius,
                "wallThickness": derived["r"] - inner_radius,
            }
        ],
        "holders": [
            {
                "type": "holder",
                "name": "W1Holder",
                "center": [derived["S1"], 0.0, 0.0],
                "pointHeight": derived["C1"],
                "baseY": 0.0,
                "alpha": parameters["alpha"],
                "hw": parameters["hw"],
                "ht": parameters["ht"],
                "plateThickness": parameters["Ct"],
                "tubeRadius": derived["r"],
            },
            {
                "type": "holder",
                "name": "P3Holder",
                "center": [derived["X3"], 0.0, 0.0],
                "pointHeight": parameters["h3"],
                "baseY": 0.0,
                "alpha": parameters["alpha"],
                "hw": parameters["hw"],
                "ht": parameters["ht"],
                "plateThickness": parameters["Ct"],
                "tubeRadius": derived["r"],
            },
            {
                "type": "holder",
                "name": "W2Holder",
                "center": [derived["S2"], 0.0, 0.0],
                "pointHeight": derived["C2"],
                "baseY": 0.0,
                "alpha": parameters["alpha"],
                "hw": parameters["hw"],
                "ht": parameters["ht"],
                "plateThickness": parameters["Ct"],
                "tubeRadius": derived["r"],
            },
            {
                "type": "holder",
                "name": "P4Holder",
                "center": [derived["X4"], parameters["h0"], 0.0],
                "pointHeight": parameters["Y4"],
                "baseY": parameters["h0"],
                "alpha": parameters["alpha"],
                "hw": parameters["hw"],
                "ht": parameters["ht"],
                "plateThickness": parameters["Ct"],
                "tubeRadius": derived["r"],
            },
        ],
        "columns": [
            {
                "type": "box",
                "name": "P4Platform",
                "center": [derived["X4"], parameters["h0"], 0.0],
                "size": [alpha, parameters["Ct"], parameters["W"]],
            },
            {
                "type": "box",
                "name": "FrontColumn",
                "center": [derived["X4"], parameters["h0"] / 2, front_z],
                "size": [alpha, parameters["h0"], alpha],
            },
            {
                "type": "box",
                "name": "BackColumn",
                "center": [derived["X4"], parameters["h0"] / 2, back_z],
                "size": [alpha, parameters["h0"], alpha],
            },
            {
                "type": "box",
                "name": "FrontTopBeam",
                "center": [beam_center, parameters["h0"], front_z],
                "size": [beam_length, parameters["Ct"], alpha],
            },
            {
                "type": "box",
                "name": "BackTopBeam",
                "center": [beam_center, parameters["h0"], back_z],
                "size": [beam_length, parameters["Ct"], alpha],
            },
            {
                "type": "box",
                "name": "FrontBottomBeam",
                "center": [beam_center, 0.0, front_z],
                "size": [beam_length, parameters["Ct"], alpha],
            },
            {
                "type": "box",
                "name": "BackBottomBeam",
                "center": [beam_center, 0.0, back_z],
                "size": [beam_length, parameters["Ct"], alpha],
            },
            {
                "type": "box",
                "name": "FloorPlatform",
                "center": [derived["X4"], 0.0, 0.0],
                "size": [alpha, parameters["Ct"], parameters["W"]],
            },
            {
                "type": "box",
                "name": "CenterRail",
                "center": [(derived["X2"] + derived["X5"]) / 2, 0.0, 0.0],
                "size": [max(derived["X5"] - derived["X2"], 0.0), parameters["Ct"], alpha],
            },
        ],
    }


def build_fluid_geometry_descriptors(
    parameters: dict[str, float],
    derived: dict[str, Any],
    forcing: dict[str, Any],
    fixed_geometry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    patch_fraction = max(min(forcing.get("topPatchFraction", 0.18), 0.9), 0.05)
    container_length = derived["X2"] - derived["S0"]
    patch_length = container_length * patch_fraction
    patch_width = parameters["W"] * patch_fraction
    inlet_center_x = derived["S0"] + container_length / 2
    inner_radius = max(derived["r"] * (1 - parameters["wallThicknessRatio"]), derived["r"] * 0.1)

    # Solid obstacles are any fixed-geometry surfaces that protrude into the fluid
    # domain and must be subtracted from the fluid volume.  Holders and columns are
    # the primary culprits — their structural members pass through the tube interior
    # or sit inside the container.  snappyHexMesh uses these surfaces to carve solid
    # regions out of the background mesh, so all of them must be listed here.
    solid_obstacles: list[Any] = []
    if fixed_geometry is not None:
        solid_obstacles.extend(fixed_geometry.get("holders", []))
        solid_obstacles.extend(fixed_geometry.get("columns", []))

    return {
        "walls": {
            "containerInterior": {
                "bounds": {
                    "x": [derived["S0"], derived["X2"]],
                    "y": [0.0, parameters["h0"] + parameters["h_a"]],
                    "z": [-parameters["W"] / 2, parameters["W"] / 2],
                },
                "openingHeight": derived["h2"],
                "openingRadius": derived["r"],
            },
            "tubeInterior": {
                "path": [[point["x"], point["y"], 0.0] for point in derived["tubePolyline"]],
                "radius": inner_radius,
            },
        },
        "solidObstructions": solid_obstacles,
        "topAtmosphere": {
            "type": "rect",
            "center": [inlet_center_x, parameters["h0"] + parameters["h_a"], 0.0],
            "size": [container_length, parameters["W"]],
        },
        "topInflow": {
            "type": "rect",
            "enabled": forcing.get("mode", "inflow_patch") == "inflow_patch",
            "center": [inlet_center_x, parameters["h0"] + parameters["h_a"], 0.0],
            "size": [patch_length, patch_width],
        },
        "tubeOutlet": {
            "type": "tubeOutlet",
            "center": [derived["X5"], parameters["h5"], 0.0],
            "radius": inner_radius,
        },
    }


def create_geometry_snapshot(raw: dict[str, Any] | None = None) -> dict[str, Any]:
    parameters = normalize_parameters(raw)
    derived = compute_derived(parameters)
    constraints = check_constraints(parameters, derived)
    return {"parameters": parameters, "derived": derived, "constraints": constraints}
def default_forcing_config() -> dict[str, Any]:
    return {
        "mode": "inflow_patch",
        "topPatchFraction": 0.18,
        "inflowVelocity": 0.02,
        "volumetricSourceRate": 0.0,
        "reservoirHead": 0.0,
    }


def default_transport_config() -> dict[str, Any]:
    return {
        "waterNu": 1e-6,
        "waterRho": 998.2,
        "airNu": 1.5e-5,
        "airRho": 1.2,
        "sigma": 0.072,
    }


def default_solver_config() -> dict[str, Any]:
    return {
        "solver": "interFoam",
        "startTime": 0.0,
        "endTime": 15.0,
        "deltaT": 0.02,
        "writeInterval": 0.1,
        "chunkDuration": 0.5,
        "tubeWallThicknessRatio": TUBE_WALL_THICKNESS_RATIO,
    }


def default_meshing_config() -> dict[str, Any]:
    return {"preset": "coarse"}


def default_event_thresholds() -> dict[str, Any]:
    return {
        "eps_H": 1e-3,
        "eps_dHdt": 1e-4,
        "eps_Q": 1e-6,
        "T_ss": 1.0,
        "dwell": 1.0,
        "requireQBalance": False,
    }


def default_run_status() -> dict[str, Any]:
    return {"state": CASE_RUN_STATUS_STATES[0]}


def create_case_file(raw: dict[str, Any] | None = None) -> dict[str, Any]:
    snapshot = create_geometry_snapshot(raw)
    forcing = default_forcing_config()
    parameter_hash = stable_hash(snapshot["parameters"])
    return {
        "schemaVersion": "1.0.0",
        "caseId": f"case-{parameter_hash}",
        "displayName": "Default fixed-geometry case",
        "parameters": {key: value for key, value in snapshot["parameters"].items() if key in DEFAULT_PARAMETERS},
        "derived": snapshot["derived"],
        "geometry": {
            "fluidBoundaryPatches": ["walls", "topAtmosphere", "topInflow", "tubeOutlet"],
            "fixedGeometryGroups": ["container", "tube", "holders", "columns"],
        },
        "meshing": default_meshing_config(),
        "transport": default_transport_config(),
        "solver": default_solver_config(),
        "forcing": forcing,
        "eventThresholds": default_event_thresholds(),
        "outputs": {"exportRoot": "examples/generated/case-default", "manifestPath": None},
        "runStatus": default_run_status(),
        "provenance": {
            "parameterHash": parameter_hash,
            "gitCommit": None,
            "sourceFiles": SOURCE_FILES,
        },
    }
