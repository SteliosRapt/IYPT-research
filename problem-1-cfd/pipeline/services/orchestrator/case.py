"""Case generation utilities for OpenFOAM-style runs."""

from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

from services.geometry.core import (
    build_fixed_geometry_descriptors,
    build_fluid_geometry_descriptors,
    build_refinement_regions,
    build_solver_surface_stls,
    create_geometry_snapshot,
    default_event_thresholds,
    default_forcing_config,
    default_run_status,
    default_solver_config,
    default_transport_config,
)
from services.orchestrator.runtime import prepare_generated_case_dir
from services.utils import write_json, write_text


def mesh_preset(parameters: dict[str, float], derived: dict[str, Any], preset: str) -> dict[str, Any]:
    domain_span = min(parameters["W"], parameters["h0"] + parameters["h_a"], derived["X5"] - derived["S0"])
    divisors = {"coarse": 24.0, "medium": 36.0, "fine": 48.0}
    levels = {"coarse": 2, "medium": 3, "fine": 4}
    divisor = divisors.get(preset, 24.0)
    level = levels.get(preset, 2)
    return {
        "preset": preset,
        "backgroundCellSize": round(domain_span / divisor, 6),
        "refinementLevels": {
            "opening": level,
            "bends": level,
            "outlet": level,
            "freeSurface": level,
        },
    }


def _foam_vector(values: list[float]) -> str:
    return f"({values[0]} {values[1]} {values[2]})"


def build_block_mesh_dict(case_file: dict[str, Any], snapshot: dict[str, Any]) -> str:
    parameters = snapshot["parameters"]
    derived = snapshot["derived"]
    margin = max(parameters["W"], parameters["h0"] + parameters["h_a"], derived["X5"] - derived["S0"]) * 0.25
    x_min = derived["S0"] - margin
    x_max = derived["X5"] + margin
    y_min = -margin * 0.5
    y_max = parameters["h0"] + parameters["h_a"] + margin
    z_min = -parameters["W"] / 2 - margin * 0.5
    z_max = parameters["W"] / 2 + margin * 0.5
    background = case_file["meshing"]["backgroundCellSize"]
    nx = max(8, int((x_max - x_min) / background))
    ny = max(8, int((y_max - y_min) / background))
    nz = max(8, int((z_max - z_min) / background))

    return f"""
FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object blockMeshDict;
}}

convertToMeters 1;

vertices
(
    ({x_min} {y_min} {z_min})
    ({x_max} {y_min} {z_min})
    ({x_max} {y_max} {z_min})
    ({x_min} {y_max} {z_min})
    ({x_min} {y_min} {z_max})
    ({x_max} {y_min} {z_max})
    ({x_max} {y_max} {z_max})
    ({x_min} {y_max} {z_max})
);

blocks
(
    hex (0 1 2 3 4 5 6 7) ({nx} {ny} {nz}) simpleGrading (1 1 1)
);

edges ();
boundary ();
mergePatchPairs ();
"""


def build_snappy_hex_mesh_dict(case_file: dict[str, Any], snapshot: dict[str, Any]) -> str:
    refinement = case_file["meshing"]["refinementLevels"]
    derived = snapshot["derived"]
    parameters = snapshot["parameters"]
    loc_x = round((derived["S0"] + derived["X2"]) / 2, 6)
    loc_y = round(parameters["h0"] * 0.5, 6)
    searchable_boxes = build_refinement_regions(parameters, derived, case_file["forcing"])
    inner_radius = max(derived["r"] * (1 - parameters["wallThicknessRatio"]), derived["r"] * 0.1)

    tube_level = max(refinement["bends"], 3)
    geometry_entries = [
        ('walls.stl', 'walls'),
        ('tubeWall.stl', 'tubeWall'),
        ('topAtmosphere.stl', 'topAtmosphere'),
        ('topInflow.stl', 'topInflow'),
        ('tubeOutlet.stl', 'tubeOutlet'),
        ('solidObstructions.stl', 'solidObstructions'),
    ]
    tri_surface_text = "\n".join(
        f"""    {file_name}
    {{
        type triSurfaceMesh;
        name {surface_name};
    }}"""
        for file_name, surface_name in geometry_entries
    )
    box_text = "\n".join(
        f"""    {name}
    {{
        type searchableBox;
        min {_foam_vector(bounds["min"])};
        max {_foam_vector(bounds["max"])};
    }}"""
        for name, bounds in searchable_boxes.items()
    )

    return f"""
FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object snappyHexMeshDict;
}}

castellatedMesh true;
snap true;
addLayers false;

geometry
{{
{tri_surface_text}
{box_text}
}}

castellatedMeshControls
{{
    maxLocalCells 4000000;
    maxGlobalCells 8000000;
    minRefinementCells 0;
    nCellsBetweenLevels 3;
    resolveFeatureAngle 30;
    features
    (
        {{ file "walls.eMesh"; level 1; }}
        {{ file "tubeWall.eMesh"; level {tube_level}; }}
        {{ file "topAtmosphere.eMesh"; level 1; }}
        {{ file "topInflow.eMesh"; level 1; }}
        {{ file "tubeOutlet.eMesh"; level {tube_level}; }}
        {{ file "solidObstructions.eMesh"; level 1; }}
    );
    refinementSurfaces
    {{
        walls {{ level (1 1); patchInfo {{ type wall; }} }}
        tubeWall {{ level ({tube_level} {tube_level}); patchInfo {{ type wall; }} }}
        topAtmosphere {{ level (1 1); patchInfo {{ type patch; }} }}
        topInflow {{ level (1 1); patchInfo {{ type patch; }} }}
        tubeOutlet {{ level ({tube_level} {tube_level}); patchInfo {{ type patch; }} }}
        solidObstructions {{ level (1 1); patchInfo {{ type wall; }} }}
    }}
    refinementRegions
    {{
        tubeWall {{ mode distance; levels (({round(inner_radius * 1.6, 6)} {tube_level})); }}
        openingBox {{ mode inside; levels ((1E15 {tube_level})); }}
        bendBoxP2 {{ mode inside; levels ((1E15 {tube_level})); }}
        bendBoxP3 {{ mode inside; levels ((1E15 {tube_level})); }}
        bendBoxP4 {{ mode inside; levels ((1E15 {tube_level})); }}
        outletBox {{ mode inside; levels ((1E15 {tube_level})); }}
        freeSurfaceBox {{ mode inside; levels ((1E15 {refinement["freeSurface"]})); }}
    }}
    locationInMesh ({loc_x} {loc_y} 0);
    allowFreeStandingZoneFaces true;
}}

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
    nFeatureSnapIter 10;
    implicitFeatureSnap false;
    explicitFeatureSnap true;
    multiRegionFeatureSnap false;
}}

addLayersControls
{{
    relativeSizes true;
    layers {{}}
    expansionRatio 1.0;
    finalLayerThickness 0.3;
    minThickness 0.1;
    nGrow 0;
    featureAngle 60;
    slipFeatureAngle 30;
    nRelaxIter 3;
    nSmoothSurfaceNormals 1;
    nSmoothNormals 3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedialAxisAngle 90;
    nBufferCellsNoExtrude 0;
    nLayerIter 50;
}}

meshQualityControls
{{
    maxNonOrtho 65;
    maxBoundarySkewness 20;
    maxInternalSkewness 4;
    maxConcave 80;
    minVol 1e-13;
    minTetQuality 1e-15;
    minArea -1;
    minTwist 0.02;
    minDeterminant 0.001;
    minFaceWeight 0.05;
    minVolRatio 0.01;
    minTriangleTwist -1;
    nSmoothScale 4;
    errorReduction 0.75;
}}

mergeTolerance 1e-6;
"""


def build_surface_feature_extract_dict() -> str:
    return """
FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object surfaceFeatureExtractDict;
}

walls.stl
{
    extractionMethod extractFromSurface;
    includedAngle 150;
    writeObj yes;
}

tubeWall.stl
{
    extractionMethod extractFromSurface;
    includedAngle 150;
    writeObj yes;
}

topAtmosphere.stl
{
    extractionMethod extractFromSurface;
    includedAngle 150;
    writeObj yes;
}

topInflow.stl
{
    extractionMethod extractFromSurface;
    includedAngle 150;
    writeObj yes;
}

tubeOutlet.stl
{
    extractionMethod extractFromSurface;
    includedAngle 150;
    writeObj yes;
}

solidObstructions.stl
{
    extractionMethod extractFromSurface;
    includedAngle 150;
    writeObj yes;
}
"""


def build_control_dict(case_file: dict[str, Any]) -> str:
    solver = case_file["solver"]
    return f"""
FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object controlDict;
}}

application {solver["solver"]};
startFrom startTime;
startTime {solver["startTime"]};
stopAt endTime;
endTime {solver["endTime"]};
deltaT {solver["deltaT"]};
writeControl adjustableRunTime;
writeInterval {solver["writeInterval"]};
purgeWrite 0;
writeFormat ascii;
writePrecision 8;
writeCompression off;
timeFormat general;
timePrecision 6;
runTimeModifiable true;

adjustTimeStep yes;
maxCo 0.5;
maxAlphaCo 0.5;
maxDeltaT 0.05;

functions
{{
    containerWaterVolume
    {{
        type volFieldValue;
        libs ("libfieldFunctionObjects.so");
        writeFields false;
        regionType cellZone;
        name containerRegion;
        operation volIntegrate;
        fields (alpha.water);
        writeControl adjustableRunTime;
        writeInterval {solver["writeInterval"]};
    }}

    tubeOutletFlow
    {{
        type surfaceFieldValue;
        libs ("libfieldFunctionObjects.so");
        writeFields false;
        regionType patch;
        name tubeOutlet;
        operation areaIntegrate;
        fields (phi);
        writeControl adjustableRunTime;
        writeInterval {solver["writeInterval"]};
    }}

    topInflowFlow
    {{
        type surfaceFieldValue;
        libs ("libfieldFunctionObjects.so");
        writeFields false;
        regionType patch;
        name topInflow;
        operation areaIntegrate;
        fields (phi);
        writeControl adjustableRunTime;
        writeInterval {solver["writeInterval"]};
    }}
}}
"""


def build_field_file(class_name: str, dimensions: str, internal_value: str, boundary_text: str, object_name: str) -> str:
    return f"""
FoamFile
{{
    version 2.0;
    format ascii;
    class {class_name};
    object {object_name};
}}

dimensions {dimensions};
internalField {internal_value};
boundaryField
{{
{boundary_text}
}}
"""


def build_transport_properties(case_file: dict[str, Any]) -> str:
    transport = case_file.get("transport", {})
    water_nu = transport.get("waterNu", 1e-6)
    water_rho = transport.get("waterRho", 998.2)
    air_nu = transport.get("airNu", 1.5e-5)
    air_rho = transport.get("airRho", 1.2)
    sigma = transport.get("sigma", 0.072)
    return f"""
FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object transportProperties;
}}

phases (water air);

water
{{
    transportModel Newtonian;
    nu {water_nu};
    rho {water_rho};
}}

air
{{
    transportModel Newtonian;
    nu {air_nu};
    rho {air_rho};
}}

sigma {sigma};
"""


def build_fv_schemes() -> str:
    return """
FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object fvSchemes;
}

ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes
{
    div(rhoPhi,U) Gauss linearUpwind grad(U);
    div(phi,alpha) Gauss vanLeer;
    div(phirb,alpha) Gauss interfaceCompression;
    div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear;
}
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
"""


def build_fv_solution() -> str:
    return """
FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object fvSolution;
}

solvers
{
    "alpha.water.*"
    {
        nAlphaCorr 2;
        nAlphaSubCycles 1;
        cAlpha 1;
        MULESCorr yes;
        nLimiterIter 5;
        solver smoothSolver;
        smoother symGaussSeidel;
        tolerance 1e-8;
        relTol 0;
    }
    "pcorr.*"
    {
        solver PCG;
        preconditioner DIC;
        tolerance 1e-5;
        relTol 0;
    }
    p_rgh
    {
        solver PCG;
        preconditioner DIC;
        tolerance 1e-7;
        relTol 0.05;
    }
    p_rghFinal { $p_rgh; relTol 0; }
    "(U|UFinal)"
    {
        solver smoothSolver;
        smoother symGaussSeidel;
        tolerance 1e-6;
        relTol 0;
    }
}

PIMPLE
{
    momentumPredictor no;
    nOuterCorrectors 1;
    nCorrectors 3;
    nNonOrthogonalCorrectors 0;
}
"""


def build_topo_set_dict(case_file: dict[str, Any], snapshot: dict[str, Any]) -> str:
    parameters = snapshot["parameters"]
    derived = snapshot["derived"]
    return f"""
FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object topoSetDict;
}}

actions
(
    {{
        name containerRegion;
        type cellSet;
        action new;
        source boxToCell;
        sourceInfo
        {{
            box ({derived["S0"]} 0 {-parameters["W"] / 2}) ({derived["X2"]} {parameters["h0"] + parameters["h_a"]} {parameters["W"] / 2});
        }}
    }}
    {{
        name containerRegion;
        type cellZoneSet;
        action new;
        source setToCellZone;
        sourceInfo
        {{
            set containerRegion;
        }}
    }}
);
"""


def build_set_fields_dict(snapshot: dict[str, Any]) -> str:
    parameters = snapshot["parameters"]
    derived = snapshot["derived"]
    return f"""
FoamFile
{{
    version 2.0;
    format ascii;
    class dictionary;
    object setFieldsDict;
}}

defaultFieldValues
(
    volScalarFieldValue alpha.water 0
);

regions
(
    boxToCell
    {{
        box ({derived["S0"]} 0 {-parameters["W"] / 2}) ({derived["X2"]} {derived["H0"]} {parameters["W"] / 2});
        fieldValues
        (
            volScalarFieldValue alpha.water 1
        );
    }}
);
"""


def build_run_metadata(case_file: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "caseId": case_file["caseId"],
        "displayName": case_file["displayName"],
        "parameters": case_file["parameters"],
        "derived": snapshot["derived"],
        "meshing": case_file["meshing"],
        "transport": case_file["transport"],
        "solver": case_file["solver"],
        "forcing": case_file["forcing"],
        "eventThresholds": case_file["eventThresholds"],
    }


def generate_case(case_file: dict[str, Any], output_dir: Path) -> Path:
    case_file = copy.deepcopy(case_file)
    snapshot = create_geometry_snapshot(case_file["parameters"])
    meshing = mesh_preset(snapshot["parameters"], snapshot["derived"], case_file.get("meshing", {}).get("preset", "coarse"))
    case_file["meshing"] = meshing
    case_file["transport"] = {**default_transport_config(), **case_file.get("transport", {})}
    case_file["solver"] = {**default_solver_config(), **case_file.get("solver", {})}
    case_file["forcing"] = {**default_forcing_config(), **case_file.get("forcing", {})}
    case_file["eventThresholds"] = {**default_event_thresholds(), **case_file.get("eventThresholds", {})}
    case_file["runStatus"] = {**default_run_status(), **case_file.get("runStatus", {})}
    if case_file["runStatus"]["state"] == "not_started":
        case_file["runStatus"]["state"] = "generated"

    output_dir = prepare_generated_case_dir(output_dir)
    (output_dir / "0").mkdir(exist_ok=True)
    (output_dir / "constant" / "triSurface").mkdir(parents=True, exist_ok=True)
    (output_dir / "system").mkdir(exist_ok=True)
    (output_dir / "postProcessing").mkdir(exist_ok=True)

    fixed_geometry = build_fixed_geometry_descriptors(snapshot["parameters"], snapshot["derived"])
    fluid_geometry = build_fluid_geometry_descriptors(
        snapshot["parameters"],
        snapshot["derived"],
        case_file["forcing"],
        fixed_geometry,
    )
    surface_assets = build_solver_surface_stls(
        snapshot["parameters"],
        snapshot["derived"],
        case_file["forcing"],
        fixed_geometry,
    )

    write_json(output_dir / "case.json", case_file)
    write_json(output_dir / "geometry_snapshot.json", snapshot)
    write_json(output_dir / "fixed_geometry.json", fixed_geometry)
    write_json(output_dir / "constant" / "triSurface" / "fluid_geometry.json", fluid_geometry)
    write_json(output_dir / "run_metadata.json", build_run_metadata(case_file, snapshot))

    for file_name, stl_payload in surface_assets.items():
        write_text(output_dir / "constant" / "triSurface" / file_name, stl_payload)

    write_text(output_dir / "system" / "blockMeshDict", build_block_mesh_dict(case_file, snapshot))
    write_text(output_dir / "system" / "snappyHexMeshDict", build_snappy_hex_mesh_dict(case_file, snapshot))
    write_text(output_dir / "system" / "surfaceFeatureExtractDict", build_surface_feature_extract_dict())
    write_text(output_dir / "system" / "controlDict", build_control_dict(case_file))
    write_text(output_dir / "system" / "fvSchemes", build_fv_schemes())
    write_text(output_dir / "system" / "fvSolution", build_fv_solution())
    write_text(output_dir / "system" / "topoSetDict", build_topo_set_dict(case_file, snapshot))
    write_text(output_dir / "system" / "setFieldsDict", build_set_fields_dict(snapshot))
    write_text(output_dir / "constant" / "transportProperties", build_transport_properties(case_file))
    write_text(
        output_dir / "constant" / "turbulenceProperties",
        """
FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object turbulenceProperties;
}

simulationType laminar;
""",
    )
    write_text(
        output_dir / "constant" / "g",
        """
FoamFile
{
    version 2.0;
    format ascii;
    class uniformDimensionedVectorField;
    object g;
}

dimensions [0 1 -2 0 0 0 0];
value (0 -9.81 0);
""",
    )

    alpha_boundary = """
    walls { type zeroGradient; }
    tubeWall { type zeroGradient; }
    solidObstructions { type zeroGradient; }
    topAtmosphere { type inletOutlet; inletValue uniform 0; value uniform 0; }
    topInflow { type fixedValue; value uniform 1; }
    tubeOutlet { type inletOutlet; inletValue uniform 0; value uniform 0; }
    """
    inflow_velocity = abs(case_file["forcing"]["inflowVelocity"])
    velocity_boundary = f"""
    walls {{ type fixedValue; value uniform (0 0 0); }}
    tubeWall {{ type fixedValue; value uniform (0 0 0); }}
    solidObstructions {{ type fixedValue; value uniform (0 0 0); }}
    topAtmosphere {{ type pressureInletOutletVelocity; value uniform (0 0 0); }}
    topInflow {{ type fixedValue; value uniform (0 {-inflow_velocity} 0); }}
    tubeOutlet {{ type pressureInletOutletVelocity; value uniform (0 0 0); }}
    """
    pressure_boundary = """
    walls { type fixedFluxPressure; value uniform 0; }
    tubeWall { type fixedFluxPressure; value uniform 0; }
    solidObstructions { type fixedFluxPressure; value uniform 0; }
    topAtmosphere { type totalPressure; p0 uniform 0; value uniform 0; }
    topInflow { type totalPressure; p0 uniform 0; value uniform 0; }
    tubeOutlet { type totalPressure; p0 uniform 0; value uniform 0; }
    """

    write_text(
        output_dir / "0" / "alpha.water",
        build_field_file("volScalarField", "[0 0 0 0 0 0 0]", "uniform 0", alpha_boundary, "alpha.water"),
    )
    write_text(
        output_dir / "0" / "U",
        build_field_file("volVectorField", "[0 1 -1 0 0 0 0]", "uniform (0 0 0)", velocity_boundary, "U"),
    )
    write_text(
        output_dir / "0" / "p_rgh",
        build_field_file("volScalarField", "[1 -1 -2 0 0 0 0]", "uniform 0", pressure_boundary, "p_rgh"),
    )
    write_text(output_dir / ".foam", "")
    write_text(
        output_dir / "Allrun",
        f"""
        #!/usr/bin/env bash
        set -euo pipefail
        blockMesh
        surfaceFeatureExtract
        snappyHexMesh -overwrite
        topoSet
        setFields
        {case_file["solver"]["solver"]}
        foamToVTK || true
        """,
    )
    os.chmod(output_dir / "Allrun", 0o755)
    return output_dir
