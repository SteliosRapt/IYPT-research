"""Geometry normalization, derived values, and constraint checks."""

from __future__ import annotations

import math
from typing import Any

from .parameters import (
    CONSTRAINT_LABELS,
    DEFAULT_PARAMETERS,
    HTML_TO_CANONICAL_PARAMETER_MAP,
    TUBE_WALL_THICKNESS_RATIO,
)


def round_value(value: float) -> float:
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
            all_points.append({"x": round_value(current["x"]), "y": round_value(current["y"])})
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
            all_points.append({"x": round_value(current["x"]), "y": round_value(current["y"])})
            continue

        u_ax, u_ay = dx_a / len_a, dy_a / len_a
        u_bx, u_by = dx_b / len_b, dy_b / len_b
        dot = max(-1.0, min(1.0, u_ax * u_bx + u_ay * u_by))
        half_angle = math.acos(dot) / 2.0

        if abs(half_angle) < 1e-6 or abs(math.pi - half_angle * 2.0) < 1e-6:
            all_points.append({"x": round_value(current["x"]), "y": round_value(current["y"])})
            continue

        # True circular-arc fillet of radius `bend_radius`, tangent to both legs.
        # For a corner whose legs subtend interior half-angle `phi` (between the
        # back-leg and forward-leg directions), the tangent points sit a distance
        # d = R / tan(phi) from the corner. If the legs are too short for that, the
        # radius is reduced so the arc still fits. A circular arc keeps the inner
        # turn radius equal to R (>> bore radius), so the swept tube never folds
        # through itself at acute bends like the P3 valley.
        cos_between_legs = max(-1.0, min(1.0, (-u_ax) * u_bx + (-u_ay) * u_by))
        phi = math.acos(cos_between_legs) / 2.0  # half-angle between the two legs
        tan_phi = math.tan(phi)
        if tan_phi < 1e-6:
            all_points.append({"x": round_value(current["x"]), "y": round_value(current["y"])})
            continue
        radius = bend_radius
        offset = radius / tan_phi
        max_offset = min(len_a, len_b) * 0.45
        if offset > max_offset:
            offset = max_offset
            radius = offset * tan_phi
        p0x = current["x"] - u_ax * offset
        p0y = current["y"] - u_ay * offset
        p1x = current["x"] + u_bx * offset
        p1y = current["y"] + u_by * offset
        # Arc centre: along the inward bisector at distance R / sin(phi) from the corner.
        bisx, bisy = u_bx - u_ax, u_by - u_ay
        bis_len = math.hypot(bisx, bisy)
        if bis_len < 1e-9:
            all_points.append({"x": round_value(current["x"]), "y": round_value(current["y"])})
            continue
        bisx, bisy = bisx / bis_len, bisy / bis_len
        sin_phi = math.sin(phi)
        center_dist = radius / sin_phi if sin_phi > 1e-9 else radius
        cxs = current["x"] + bisx * center_dist
        cys = current["y"] + bisy * center_dist
        start_angle = math.atan2(p0y - cys, p0x - cxs)
        end_angle = math.atan2(p1y - cys, p1x - cxs)
        # Sweep the short way around the centre.
        delta = end_angle - start_angle
        while delta > math.pi:
            delta -= 2 * math.pi
        while delta < -math.pi:
            delta += 2 * math.pi

        all_points.append({"x": round_value(p0x), "y": round_value(p0y)})
        for step in range(1, arc_segments):
            ang = start_angle + delta * (step / arc_segments)
            qx = cxs + radius * math.cos(ang)
            qy = cys + radius * math.sin(ang)
            all_points.append({"x": round_value(qx), "y": round_value(qy)})
        all_points.append({"x": round_value(p1x), "y": round_value(p1y)})

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
        "W0": {"x": round_value(s0), "y": round_value(parameters["h0"])},
        "P1": {"x": 0.0, "y": round_value(parameters["h1"])},
        "W1": {"x": round_value(s1), "y": round_value(c1)},
        "P2": {"x": round_value(x2), "y": round_value(h2)},
        "P3": {"x": round_value(x3), "y": round_value(parameters["h3"])},
        "P4": {"x": round_value(x4), "y": round_value(h4)},
        "W2": {"x": round_value(s2), "y": round_value(c2)},
        "P5": {"x": round_value(x5), "y": round_value(parameters["h5"])},
    }

    return {
        "r": round_value(radius),
        "P4t": round_value(parameters["P4t"]),
        "h2": round_value(h2),
        "h4": round_value(h4),
        "X2": round_value(x2),
        "X3": round_value(x3),
        "X4": round_value(x4),
        "X5": round_value(x5),
        "S0": round_value(s0),
        "S1": round_value(s1),
        "S2": round_value(s2),
        "C1": round_value(c1),
        "C2": round_value(c2),
        "H0": round_value((4 * h2) / 5),
        "planArea": round_value(parameters["A0"]),
        "points": points,
        "tubePolyline": build_tube_path(
            [points["P1"], points["P2"], points["P3"], points["P4"], points["P5"]],
            parameters["bendR"],
        ),
        "holderBases": [
            {"name": "W1", "x": round_value(s1), "y": 0.0},
            {"name": "P3", "x": round_value(x3), "y": 0.0},
            {"name": "W2", "x": round_value(s2), "y": 0.0},
            {"name": "P4", "x": round_value(x4), "y": round_value(parameters["h0"])},
        ],
        "structure": {
            "containerLeft": round_value(s0),
            "containerRight": round_value(x2),
            "totalHeight": round_value(parameters["h0"] + parameters["h_a"]),
            "columnZ": [
                round_value(parameters["W"] / 2 - parameters["alpha"] / 2),
                round_value(-(parameters["W"] / 2 - parameters["alpha"] / 2)),
            ],
            "centerRail": {"startX": round_value(x2), "endX": round_value(x5), "y": 0.0},
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


def create_geometry_snapshot(raw: dict[str, Any] | None = None) -> dict[str, Any]:
    parameters = normalize_parameters(raw)
    derived = compute_derived(parameters)
    constraints = check_constraints(parameters, derived)
    return {"parameters": parameters, "derived": derived, "constraints": constraints}
