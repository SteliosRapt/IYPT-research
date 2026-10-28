"""Canonical case-file assembly."""

from __future__ import annotations

from typing import Any

from services.utils import stable_hash

from .derive import create_geometry_snapshot
from .parameters import CASE_RUN_STATUS_STATES, DEFAULT_PARAMETERS, SOURCE_FILES, TUBE_WALL_THICKNESS_RATIO

DEFAULT_DISPLAY_NAME = "Default fixed-geometry case"


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


def _normalize_display_name(display_name: str | None) -> str:
    if isinstance(display_name, str) and display_name.strip():
        return display_name.strip()
    return DEFAULT_DISPLAY_NAME


def compute_parameter_hash(parameters: dict[str, float]) -> str:
    return stable_hash(parameters)


def build_case_identity_payload(
    *,
    parameters: dict[str, float],
    transport: dict[str, Any],
    forcing: dict[str, Any],
    solver: dict[str, Any],
    event_thresholds: dict[str, Any],
    meshing: dict[str, Any],
    display_name: str,
) -> dict[str, Any]:
    return {
        "displayName": display_name,
        "eventThresholds": event_thresholds,
        "forcing": forcing,
        "meshing": {"preset": meshing["preset"]},
        "parameters": {key: parameters[key] for key in DEFAULT_PARAMETERS},
        "solver": solver,
        "transport": transport,
    }


def compute_case_id(
    *,
    parameters: dict[str, float],
    transport: dict[str, Any],
    forcing: dict[str, Any],
    solver: dict[str, Any],
    event_thresholds: dict[str, Any],
    meshing: dict[str, Any],
    display_name: str,
) -> str:
    case_hash = stable_hash(
        build_case_identity_payload(
            parameters=parameters,
            transport=transport,
            forcing=forcing,
            solver=solver,
            event_thresholds=event_thresholds,
            meshing=meshing,
            display_name=display_name,
        )
    )
    return f"case-{case_hash}"


def create_case_file(
    raw: dict[str, Any] | None = None,
    *,
    display_name: str | None = None,
    transport: dict[str, Any] | None = None,
    forcing: dict[str, Any] | None = None,
    solver: dict[str, Any] | None = None,
    event_thresholds: dict[str, Any] | None = None,
    meshing: dict[str, Any] | None = None,
    outputs: dict[str, Any] | None = None,
    run_status: dict[str, Any] | None = None,
) -> dict[str, Any]:
    snapshot = create_geometry_snapshot(raw)
    parameters = {key: value for key, value in snapshot["parameters"].items() if key in DEFAULT_PARAMETERS}
    forcing_config = {**default_forcing_config(), **(forcing or {})}
    transport_config = {**default_transport_config(), **(transport or {})}
    solver_config = {**default_solver_config(), **(solver or {})}
    event_config = {**default_event_thresholds(), **(event_thresholds or {})}
    meshing_config = {**default_meshing_config(), **(meshing or {})}
    output_config = {"exportRoot": "examples/generated/case-default", "manifestPath": None, **(outputs or {})}
    run_status_config = {**default_run_status(), **(run_status or {})}
    resolved_display_name = _normalize_display_name(display_name)
    parameter_hash = compute_parameter_hash(parameters)
    return {
        "schemaVersion": "1.0.0",
        "caseId": compute_case_id(
            parameters=parameters,
            transport=transport_config,
            forcing=forcing_config,
            solver=solver_config,
            event_thresholds=event_config,
            meshing=meshing_config,
            display_name=resolved_display_name,
        ),
        "displayName": resolved_display_name,
        "parameters": parameters,
        "derived": snapshot["derived"],
        "geometry": {
            "fluidBoundaryPatches": ["walls", "topAtmosphere", "topInflow", "tubeOutlet"],
            "fixedGeometryGroups": ["container", "tube", "holders", "columns"],
        },
        "meshing": meshing_config,
        "transport": transport_config,
        "solver": solver_config,
        "forcing": forcing_config,
        "eventThresholds": event_config,
        "outputs": output_config,
        "runStatus": run_status_config,
        "provenance": {
            "parameterHash": parameter_hash,
            "gitCommit": None,
            "sourceFiles": SOURCE_FILES,
        },
    }
