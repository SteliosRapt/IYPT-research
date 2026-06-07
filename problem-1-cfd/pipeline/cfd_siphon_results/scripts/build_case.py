"""Build a quasi-2D interFoam case of the EXPERIMENTAL self-starting siphon.

Geometry, pipe and fluid properties are taken from
Theory-and-real-experiment/Exp-data (1).xlsx (sheet 2) so the CFD can be compared
directly with the measured priming front L(t).

The fluid region (container reservoir + 5 mm straw bore) is built with Shapely,
its boundary is extruded into a thin z-slab and split into walls / atmosphere /
outlet STL patches, then meshed with blockMesh + snappyHexMesh (empty front/back
= true 2D) on OpenFOAM 2406.
"""
from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

from shapely.geometry import LineString, box
from shapely.ops import unary_union

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from services.geometry.derive import build_tube_path  # noqa: E402

CM = 0.01
# Experimental nodes (x, h) in metres.  A=inlet, B=first crest (below waterline),
# C=low point, D=main crest (above waterline), E=outlet.
NODES = {
    "A": (0.0 * CM, 1.0 * CM),
    "B": (7.5 * CM, 11.0 * CM),
    "C": (13.5 * CM, 5.0 * CM),
    "D": (21.4 * CM, 13.0 * CM),
    "E": (30.3 * CM, -1.7 * CM),
}
WATERLINE = 12.5 * CM
PIPE_D = 5.0e-3          # 5 mm straw
PIPE_R = PIPE_D / 2.0
BEND_R = 12.0e-3         # rounded bends (mm-scale straw bend)
SLAB = 4.0e-3            # z thickness of the 2D slab
CELL = 1.0e-3            # background cell size (x,y) -> ~5 cells across the bore

CONT_LEFT = -0.18        # container reservoir extent
CONT_RIGHT = 0.0         # straw enters through the right wall at x=0
CONT_TOP = 0.16
DOM_YMIN = -0.06         # below outlet E
PAD = 0.02


def rounded_centerline() -> list[tuple[float, float]]:
    # short horizontal stub inside the reservoir so the straw crosses the x=0 wall
    # perpendicularly (clean inlet gap), then A->B->C->D->E.
    raw = [
        {"x": -0.02, "y": NODES["A"][1]},
        {"x": NODES["A"][0], "y": NODES["A"][1]},
        {"x": NODES["B"][0], "y": NODES["B"][1]},
        {"x": NODES["C"][0], "y": NODES["C"][1]},
        {"x": NODES["D"][0], "y": NODES["D"][1]},
        {"x": NODES["E"][0], "y": NODES["E"][1]},
    ]
    pts = build_tube_path(raw, BEND_R)
    return [(p["x"], p["y"]) for p in pts]


def checkpoint_arclengths(center: list[tuple[float, float]]) -> dict:
    """Cumulative arclength (from inlet A) of each labelled node, measured along the
    rounded centreline, plus the per-vertex cumulative arclength array."""
    line = LineString(center)
    # arclength of A (first real node, where stub meets A at x=0)
    out = {}
    # cumulative arclength of each polyline vertex
    cum = [0.0]
    for i in range(1, len(center)):
        cum.append(cum[-1] + math.dist(center[i], center[i - 1]))
    # find vertex closest to each node, take its cumulative arclength; subtract A's
    def s_of(node):
        x, y = NODES[node]
        best = min(range(len(center)), key=lambda i: (center[i][0] - x) ** 2 + (center[i][1] - y) ** 2)
        return cum[best]
    sA = s_of("A")
    for n in NODES:
        out[n] = s_of(n) - sA
    return {"nodes": out, "cum": [c - sA for c in cum], "centerline": center, "total": cum[-1] - sA}


def boundary_patches(center: list[tuple[float, float]]):
    ribbon = LineString(center).buffer(PIPE_R, cap_style="flat", join_style="round")
    container = box(CONT_LEFT, 0.0, CONT_RIGHT + 1e-6, CONT_TOP)
    fluid = unary_union([container, ribbon])
    if fluid.geom_type == "MultiPolygon":
        fluid = max(fluid.geoms, key=lambda g: g.area)
    ring = list(fluid.exterior.coords)

    ex, ey = NODES["E"]
    walls, atm, outlet = [], [], []
    for i in range(len(ring) - 1):
        x0, y0 = ring[i]
        x1, y1 = ring[i + 1]
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        if my > CONT_TOP - 1e-4 and CONT_LEFT - 1e-3 < mx < CONT_RIGHT + 1e-3:
            atm.append(((x0, y0), (x1, y1)))
        elif math.hypot(mx - ex, my - ey) < PIPE_R * 1.6:
            outlet.append(((x0, y0), (x1, y1)))
        else:
            walls.append(((x0, y0), (x1, y1)))
    return walls, atm, outlet, fluid


def stl(name: str, segments) -> str:
    lines = [f"solid {name}"]
    for (x0, y0), (x1, y1) in segments:
        quad = [(x0, y0, 0.0), (x1, y1, 0.0), (x1, y1, SLAB), (x0, y0, SLAB)]
        for tri in ((quad[0], quad[1], quad[2]), (quad[0], quad[2], quad[3])):
            lines.append("  facet normal 0 0 0")
            lines.append("    outer loop")
            for v in tri:
                lines.append(f"      vertex {v[0]:.6g} {v[1]:.6g} {v[2]:.6g}")
            lines.append("    endloop")
            lines.append("  endfacet")
    lines.append(f"endsolid {name}")
    return "\n".join(lines) + "\n"


def write(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    out = Path(__file__).resolve().parent / "case"
    center = rounded_centerline()
    cp = checkpoint_arclengths(center)
    walls, atm, outlet, fluid = boundary_patches(center)

    tri = out / "constant" / "triSurface"
    write(tri / "walls.stl", stl("walls", walls))
    write(tri / "atmosphere.stl", stl("atmosphere", atm))
    write(tri / "outlet.stl", stl("outlet", outlet))

    minx, miny, maxx, maxy = (CONT_LEFT - PAD, DOM_YMIN, NODES["E"][0] + PAD, CONT_TOP + PAD)
    nx = max(8, round((maxx - minx) / CELL))
    ny = max(8, round((maxy - miny) / CELL))
    loc = (-0.09, 0.05, SLAB / 2)  # inside the reservoir water

    write(out / "system" / "blockMeshDict", f"""FoamFile {{ version 2.0; format ascii; class dictionary; object blockMeshDict; }}
convertToMeters 1;
vertices
(
 ({minx} {miny} 0) ({maxx} {miny} 0) ({maxx} {maxy} 0) ({minx} {maxy} 0)
 ({minx} {miny} {SLAB}) ({maxx} {miny} {SLAB}) ({maxx} {maxy} {SLAB}) ({minx} {maxy} {SLAB})
);
blocks ( hex (0 1 2 3 4 5 6 7) ({nx} {ny} 1) simpleGrading (1 1 1) );
edges ();
boundary
(
    frontAndBack {{ type empty; faces ( (0 1 2 3) (4 5 6 7) ); }}
    sides {{ type wall; faces ( (0 1 5 4) (2 3 7 6) (1 2 6 5) (0 3 7 4) ); }}
);
mergePatchPairs ();
""")

    write(out / "system" / "snappyHexMeshDict", f"""FoamFile {{ version 2.0; format ascii; class dictionary; object snappyHexMeshDict; }}
castellatedMesh true; snap true; addLayers false;
geometry
{{
    walls.stl {{ type triSurfaceMesh; name walls; }}
    atmosphere.stl {{ type triSurfaceMesh; name atmosphere; }}
    outlet.stl {{ type triSurfaceMesh; name outlet; }}
}}
castellatedMeshControls
{{
    maxLocalCells 2000000; maxGlobalCells 4000000; minRefinementCells 0;
    nCellsBetweenLevels 2; resolveFeatureAngle 30;
    features ( );
    refinementSurfaces
    {{
        walls {{ level (0 0); patchInfo {{ type wall; }} }}
        atmosphere {{ level (0 0); patchInfo {{ type patch; }} }}
        outlet {{ level (0 0); patchInfo {{ type patch; }} }}
    }}
    refinementRegions {{}}
    locationInMesh ({loc[0]} {loc[1]} {loc[2]});
    allowFreeStandingZoneFaces true;
}}
snapControls {{ nSmoothPatch 3; tolerance 2.0; nSolveIter 50; nRelaxIter 8; nFeatureSnapIter 12; implicitFeatureSnap true; explicitFeatureSnap false; }}
addLayersControls {{ relativeSizes true; layers {{}} expansionRatio 1.0; finalLayerThickness 0.3; minThickness 0.1; nGrow 0; featureAngle 60; nRelaxIter 3; nSmoothSurfaceNormals 1; nSmoothNormals 3; nSmoothThickness 10; maxFaceThicknessRatio 0.5; maxThicknessToMedialRatio 0.3; minMedialAxisAngle 90; nBufferCellsNoExtrude 0; nLayerIter 50; }}
meshQualityControls {{ maxNonOrtho 65; maxBoundarySkewness 20; maxInternalSkewness 4; maxConcave 80; minVol 1e-13; minTetQuality 1e-15; minArea -1; minTwist 0.02; minDeterminant 0.001; minFaceWeight 0.05; minVolRatio 0.01; minTriangleTwist -1; nSmoothScale 4; errorReduction 0.75; }}
mergeTolerance 1e-6;
""")

    # constant
    write(out / "constant" / "g", "FoamFile { version 2.0; format ascii; class uniformDimensionedVectorField; object g; }\ndimensions [0 1 -2 0 0 0 0];\nvalue (0 -9.81 0);\n")
    write(out / "constant" / "transportProperties", """FoamFile { version 2.0; format ascii; class dictionary; object transportProperties; }
phases (water air);
water { transportModel Newtonian; nu 1e-06; rho 998; }
air   { transportModel Newtonian; nu 1.48e-05; rho 1.2; }
sigma 0.073;
""")
    write(out / "constant" / "turbulenceProperties", "FoamFile { version 2.0; format ascii; class dictionary; object turbulenceProperties; }\nsimulationType laminar;\n")

    # system: controlDict / fvSchemes / fvSolution / setFieldsDict
    write(out / "system" / "controlDict", """FoamFile { version 2.0; format ascii; class dictionary; object controlDict; }
application interFoam; startFrom startTime; startTime 0; stopAt endTime; endTime 2.5;
deltaT 0.0005; writeControl adjustableRunTime; writeInterval 0.02; purgeWrite 0;
writeFormat ascii; writePrecision 8; writeCompression off; timeFormat general; timePrecision 6;
runTimeModifiable true; adjustTimeStep yes; maxCo 0.4; maxAlphaCo 0.4; maxDeltaT 0.002;
functions {}
""")
    write(out / "system" / "fvSchemes", """FoamFile { version 2.0; format ascii; class dictionary; object fvSchemes; }
ddtSchemes { default Euler; }
gradSchemes { default Gauss linear; }
divSchemes { div(rhoPhi,U) Gauss upwind; div(phi,alpha) Gauss vanLeer; div(phirb,alpha) Gauss linear; div(((rho*nuEff)*dev2(T(grad(U))))) Gauss linear; }
laplacianSchemes { default Gauss linear corrected; }
interpolationSchemes { default linear; }
snGradSchemes { default corrected; }
""")
    write(out / "system" / "fvSolution", """FoamFile { version 2.0; format ascii; class dictionary; object fvSolution; }
solvers
{
    "alpha.water.*" { nAlphaCorr 2; nAlphaSubCycles 1; cAlpha 1; MULESCorr yes; nLimiterIter 5; solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0; }
    "pcorr.*" { solver PCG; preconditioner DIC; tolerance 1e-5; relTol 0; }
    p_rgh { solver PCG; preconditioner DIC; tolerance 1e-7; relTol 0.05; }
    p_rghFinal { solver PCG; preconditioner DIC; tolerance 1e-7; relTol 0; }
    "(U|UFinal)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-7; relTol 0; }
}
PIMPLE { momentumPredictor no; nOuterCorrectors 1; nCorrectors 3; nNonOrthogonalCorrectors 1; }
""")
    write(out / "system" / "setFieldsDict", f"""FoamFile {{ version 2.0; format ascii; class dictionary; object setFieldsDict; }}
defaultFieldValues ( volScalarFieldValue alpha.water 0 );
regions
(
    boxToCell {{ box ({CONT_LEFT-PAD} 0 -1) ({CONT_RIGHT+0.002} {WATERLINE} 1); fieldValues ( volScalarFieldValue alpha.water 1 ); }}
);
""")

    # 0/
    write(out / "0" / "alpha.water", """FoamFile { version 2.0; format ascii; class volScalarField; object alpha.water; }
dimensions [0 0 0 0 0 0 0]; internalField uniform 0;
boundaryField
{
    walls { type zeroGradient; }
    atmosphere { type inletOutlet; inletValue uniform 0; value uniform 0; }
    outlet { type inletOutlet; inletValue uniform 0; value uniform 0; }
    frontAndBack { type empty; }
    sides { type zeroGradient; }
}
""")
    write(out / "0" / "U", """FoamFile { version 2.0; format ascii; class volVectorField; object U; }
dimensions [0 1 -1 0 0 0 0]; internalField uniform (0 0 0);
boundaryField
{
    walls { type noSlip; }
    atmosphere { type pressureInletOutletVelocity; value uniform (0 0 0); }
    outlet { type pressureInletOutletVelocity; value uniform (0 0 0); }
    frontAndBack { type empty; }
    sides { type noSlip; }
}
""")
    write(out / "0" / "p_rgh", """FoamFile { version 2.0; format ascii; class volScalarField; object p_rgh; }
dimensions [1 -1 -2 0 0 0 0]; internalField uniform 0;
boundaryField
{
    walls { type fixedFluxPressure; value uniform 0; }
    atmosphere { type totalPressure; p0 uniform 0; value uniform 0; }
    outlet { type totalPressure; p0 uniform 0; value uniform 0; }
    frontAndBack { type empty; }
    sides { type fixedFluxPressure; value uniform 0; }
}
""")
    write(out / "case.foam", "")
    write(out / "checkpoints.json", json.dumps({
        "nodes_xy": {k: list(v) for k, v in NODES.items()},
        "arclength": cp["nodes"], "total_pipe_length": cp["total"],
        "centerline": cp["centerline"], "cum_arclength": cp["cum"],
        "pipe_radius": PIPE_R, "waterline": WATERLINE, "slab": SLAB,
    }, indent=1))

    print("case dir:", out)
    print("fluid area (m^2, 2D):", round(fluid.area, 6))
    print("segments  walls/atm/outlet:", len(walls), len(atm), len(outlet))
    print("checkpoint arclengths (cm from A):", {k: round(v * 100, 2) for k, v in cp["nodes"].items()})
    print("total pipe length (cm):", round(cp["total"] * 100, 2), " (experiment 49.4)")
    print("mesh nx,ny:", nx, ny)


if __name__ == "__main__":
    main()
