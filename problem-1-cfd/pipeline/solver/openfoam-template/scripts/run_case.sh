#!/usr/bin/env bash
set -euo pipefail

case_dir="${1:-/workspace/examples/default-openfoam-case}"
solver_name="${2:-interFoam}"

cd "$case_dir"
blockMesh
surfaceFeatureExtract || true
snappyHexMesh -overwrite
topoSet
"$solver_name"
foamToVTK

