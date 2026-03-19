"""Geometry descriptor builders for viewer/debug outputs."""

from __future__ import annotations

from typing import Any


def inner_tube_radius(parameters: dict[str, float], derived: dict[str, Any]) -> float:
    return max(derived["r"] * (1 - parameters["wallThicknessRatio"]), derived["r"] * 0.1)


def top_patch_bounds(parameters: dict[str, float], derived: dict[str, Any], forcing: dict[str, Any]) -> dict[str, float]:
    patch_fraction = max(min(forcing.get("topPatchFraction", 0.18), 0.9), 0.05)
    container_length = derived["X2"] - derived["S0"]
    patch_length = container_length * patch_fraction
    patch_width = parameters["W"] * patch_fraction
    inlet_center_x = derived["S0"] + container_length / 2
    return {
        "x0": inlet_center_x - patch_length / 2,
        "x1": inlet_center_x + patch_length / 2,
        "z0": -patch_width / 2,
        "z1": patch_width / 2,
        "y": parameters["h0"] + parameters["h_a"],
    }


def build_refinement_regions(
    parameters: dict[str, float],
    derived: dict[str, Any],
    forcing: dict[str, Any],
) -> dict[str, dict[str, list[float]]]:
    tube_radius = inner_tube_radius(parameters, derived)
    opening_half_width = max(tube_radius * 1.5, parameters["Ct"] * 1.5)
    bend_half_extent = max(parameters["bendR"] * 1.25, tube_radius * 2.0, parameters["alpha"])
    free_surface_half_height = max(tube_radius * 1.5, parameters["Ct"] * 2.0)
    total_height = parameters["h0"] + parameters["h_a"]

    return {
        "openingBox": {
            "min": [derived["X2"] - parameters["Ct"], derived["h2"] - opening_half_width, -opening_half_width],
            "max": [derived["X2"] + parameters["Ct"], derived["h2"] + opening_half_width, opening_half_width],
        },
        "bendBoxP2": {
            "min": [derived["points"]["P2"]["x"] - bend_half_extent, derived["points"]["P2"]["y"] - bend_half_extent, -bend_half_extent],
            "max": [derived["points"]["P2"]["x"] + bend_half_extent, derived["points"]["P2"]["y"] + bend_half_extent, bend_half_extent],
        },
        "bendBoxP3": {
            "min": [derived["points"]["P3"]["x"] - bend_half_extent, derived["points"]["P3"]["y"] - bend_half_extent, -bend_half_extent],
            "max": [derived["points"]["P3"]["x"] + bend_half_extent, derived["points"]["P3"]["y"] + bend_half_extent, bend_half_extent],
        },
        "bendBoxP4": {
            "min": [derived["points"]["P4"]["x"] - bend_half_extent, derived["points"]["P4"]["y"] - bend_half_extent, -bend_half_extent],
            "max": [derived["points"]["P4"]["x"] + bend_half_extent, derived["points"]["P4"]["y"] + bend_half_extent, bend_half_extent],
        },
        "outletBox": {
            "min": [derived["X5"] - tube_radius, parameters["h5"] - opening_half_width, -opening_half_width],
            "max": [derived["X5"] + opening_half_width, parameters["h5"] + opening_half_width, opening_half_width],
        },
        "freeSurfaceBox": {
            "min": [derived["S0"], max(0.0, derived["H0"] - free_surface_half_height), -parameters["W"] / 2],
            "max": [derived["X2"], min(total_height, derived["H0"] + free_surface_half_height), parameters["W"] / 2],
        },
    }


def build_fixed_geometry_descriptors(parameters: dict[str, float], derived: dict[str, Any]) -> dict[str, Any]:
    container_length = derived["X2"] - derived["S0"]
    center_x = derived["S0"] + container_length / 2
    total_height = parameters["h0"] + parameters["h_a"]
    alpha = parameters["alpha"]
    front_z = parameters["W"] / 2 - alpha / 2
    back_z = -front_z
    beam_length = max(derived["X4"] - alpha / 2 - derived["X2"], 0.0)
    beam_center = derived["X2"] + beam_length / 2 if beam_length > 0 else derived["X2"]
    inner_radius = inner_tube_radius(parameters, derived)

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
    patch = top_patch_bounds(parameters, derived, forcing)
    inner_radius = inner_tube_radius(parameters, derived)
    container_length = derived["X2"] - derived["S0"]

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
            "center": [(derived["S0"] + derived["X2"]) / 2, patch["y"], 0.0],
            "size": [container_length, parameters["W"]],
        },
        "topInflow": {
            "type": "rect",
            "enabled": forcing.get("mode", "inflow_patch") == "inflow_patch",
            "center": [(patch["x0"] + patch["x1"]) / 2, patch["y"], 0.0],
            "size": [patch["x1"] - patch["x0"], patch["z1"] - patch["z0"]],
        },
        "tubeOutlet": {
            "type": "tubeOutlet",
            "center": [derived["X5"], parameters["h5"], 0.0],
            "radius": inner_radius,
        },
    }
