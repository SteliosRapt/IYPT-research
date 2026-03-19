"""Case generation utilities for OpenFOAM-style runs."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from services.geometry.core import (
    ROOT_DIR,
    build_fixed_geometry_descriptors,
    build_fluid_geometry_descriptors,
    create_geometry_snapshot,
    default_event_thresholds,
    default_forcing_config,
    default_solver_config,
    write_json,
)


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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


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


def build_snappy_hex_mesh_dict(case_file: dict[str, Any]) -> str:
    refinement = case_file["meshing"]["refinementLevels"]
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
    fluid_geometry.json
    {{
        type triSurfaceMesh;
        name walls;
    }}
}}

castellatedMeshControls
{{
    maxLocalCells 100000;
    maxGlobalCells 200000;
    minRefinementCells 0;
    nCellsBetweenLevels 3;
    resolveFeatureAngle 30;
    locationInMesh (0 0.05 0);
}}

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 30;
    nRelaxIter 5;
}}

meshQualityControls {{}}

refinementRegions
{{
    openingBox {{ mode inside; levels ((1E15 {refinement["opening"]})); }}
    bendBoxes {{ mode inside; levels ((1E15 {refinement["bends"]})); }}
    outletBox {{ mode inside; levels ((1E15 {refinement["outlet"]})); }}
    freeSurfaceBox {{ mode inside; levels ((1E15 {refinement["freeSurface"]})); }}
}}
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


def build_transport_properties() -> str:
    return """
FoamFile
{
    version 2.0;
    format ascii;
    class dictionary;
    object transportProperties;
}

phases (water air);

water
{
    transportModel Newtonian;
    nu 1e-06;
    rho 998.2;
}

air
{
    transportModel Newtonian;
    nu 1.5e-05;
    rho 1.2;
}

sigma 0.072;
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
    "alpha.water.*" { nAlphaCorr 1; nAlphaSubCycles 1; cAlpha 1; }
    p_rgh { solver PCG; preconditioner DIC; tolerance 1e-7; relTol 0.01; }
    p_rghFinal { $p_rgh; relTol 0; }
    U { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-6; relTol 0.1; }
}

PIMPLE
{
    momentumPredictor yes;
    nOuterCorrectors 1;
    nCorrectors 2;
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
);
"""


def build_run_metadata(case_file: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "caseId": case_file["caseId"],
        "parameters": case_file["parameters"],
        "derived": snapshot["derived"],
        "meshing": case_file["meshing"],
        "solver": case_file["solver"],
        "forcing": case_file["forcing"],
        "eventThresholds": case_file["eventThresholds"],
    }


def generate_case(case_file: dict[str, Any], output_dir: Path) -> Path:
    snapshot = create_geometry_snapshot(case_file["parameters"])
    meshing = mesh_preset(snapshot["parameters"], snapshot["derived"], case_file.get("meshing", {}).get("preset", "coarse"))
    case_file["meshing"] = meshing
    case_file["solver"] = {**default_solver_config(), **case_file.get("solver", {})}
    case_file["forcing"] = {**default_forcing_config(), **case_file.get("forcing", {})}
    case_file["eventThresholds"] = {**default_event_thresholds(), **case_file.get("eventThresholds", {})}

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "0").mkdir(exist_ok=True)
    (output_dir / "constant" / "triSurface").mkdir(parents=True, exist_ok=True)
    (output_dir / "system").mkdir(exist_ok=True)
    (output_dir / "postProcessing").mkdir(exist_ok=True)

    fixed_geometry = build_fixed_geometry_descriptors(snapshot["parameters"], snapshot["derived"])
    fluid_geometry = build_fluid_geometry_descriptors(snapshot["parameters"], snapshot["derived"], case_file["forcing"])
    write_json(output_dir / "case.json", case_file)
    write_json(output_dir / "geometry_snapshot.json", snapshot)
    write_json(output_dir / "fixed_geometry.json", fixed_geometry)
    write_json(output_dir / "constant" / "triSurface" / "fluid_geometry.json", fluid_geometry)
    write_json(output_dir / "run_metadata.json", build_run_metadata(case_file, snapshot))

    write_text(output_dir / "system" / "blockMeshDict", build_block_mesh_dict(case_file, snapshot))
    write_text(output_dir / "system" / "snappyHexMeshDict", build_snappy_hex_mesh_dict(case_file))
    write_text(output_dir / "system" / "controlDict", build_control_dict(case_file))
    write_text(output_dir / "system" / "fvSchemes", build_fv_schemes())
    write_text(output_dir / "system" / "fvSolution", build_fv_solution())
    write_text(output_dir / "system" / "topoSetDict", build_topo_set_dict(case_file, snapshot))
    write_text(output_dir / "constant" / "transportProperties", build_transport_properties())
    write_text(output_dir / "constant" / "g", "dimensions [0 1 -2 0 0 0 0];\nvalue (0 -9.81 0);")

    alpha_boundary = """
    walls { type zeroGradient; }
    topAtmosphere { type inletOutlet; inletValue uniform 0; value uniform 0; }
    topInflow { type fixedValue; value uniform 1; }
    tubeOutlet { type inletOutlet; inletValue uniform 0; value uniform 0; }
    """
    velocity_boundary = """
    walls { type fixedValue; value uniform (0 0 0); }
    topAtmosphere { type pressureInletOutletVelocity; value uniform (0 0 0); }
    topInflow { type fixedValue; value uniform (0 -0.02 0); }
    tubeOutlet { type pressureInletOutletVelocity; value uniform (0 0 0); }
    """
    pressure_boundary = """
    walls { type fixedFluxPressure; value uniform 0; }
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
    write_text(
        output_dir / ".foam",
        "",
    )
    write_text(
        output_dir / "Allrun",
        f"""
        #!/usr/bin/env bash
        set -euo pipefail
        blockMesh
        surfaceFeatureExtract || true
        snappyHexMesh -overwrite
        topoSet
        {case_file["solver"]["solver"]}
        """,
    )
    os.chmod(output_dir / "Allrun", 0o755)
    return output_dir
