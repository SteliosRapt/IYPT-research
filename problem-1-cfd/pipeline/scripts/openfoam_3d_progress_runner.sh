#!/usr/bin/env bash
set -u

# Run this inside an OpenFOAM container with the repository mounted at /work.
# Example host command:
# docker run --rm -e RUN_ID=case3d-fast -e FAST_MESH=1 -v "$PWD:/work" \
#   opencfd/openfoam-default:2406 bash /work/scripts/openfoam_3d_progress_runner.sh

ROOT=${ROOT:-/work}
SRC_CASE=${SRC_CASE:-$ROOT/tmp/siphon_exp/case3d}
RUN_ID=${RUN_ID:-case3d-progress}
RUN_ROOT=${RUN_ROOT:-$ROOT/tmp/siphon_exp}
DECOMPOSE_DICT=${DECOMPOSE_DICT:-$ROOT/tmp/siphon_exp/decomposeParDict}
RUN="$RUN_ROOT/$RUN_ID"
PROGRESS="$RUN/progress.log"
PROGRESS_JSON="$RUN/progress.json"
TARGET_TIME=${TARGET_TIME:-5.0}
WRITE_INTERVAL=${WRITE_INTERVAL:-0.05}
MESH_BUDGET_SECONDS=${MESH_BUDGET_SECONDS:-600}
SOLVER_WALL_BUDGET_SECONDS=${SOLVER_WALL_BUDGET_SECONDS:-300}
NPROC=${NPROC:-12}
FAST_MESH=${FAST_MESH:-0}

log() {
  mkdir -p "$RUN"
  printf '[%s] %s\n' "$(date -Iseconds)" "$*" | tee -a "$PROGRESS"
}

write_json() {
  local status=$1
  local stage=$2
  local sim_time=${3:-0}
  local percent=${4:-0}
  local message=${5:-}
  local escaped_message
  escaped_message=$(printf '%s' "$message" | sed 's/\\/\\\\/g; s/"/\\"/g')
  cat > "$PROGRESS_JSON" <<JSON
{
  "updatedAt": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "status": "$status",
  "stage": "$stage",
  "targetSimulationSeconds": $TARGET_TIME,
  "lastSimulationSeconds": ${sim_time:-0},
  "progressPercent": ${percent:-0},
  "message": "$escaped_message"
}
JSON
}

last_time() {
  grep -E '^Time = ' log.interFoam 2>/dev/null | tail -1 | awk '{print $3}'
}

progress_percent() {
  awk -v t="${1:-0}" -v target="$TARGET_TIME" 'BEGIN {
    if (target <= 0) print 0;
    else {
      pct = 100 * (t + 0) / target;
      if (pct > 100) pct = 100;
      printf "%.4f", pct;
    }
  }'
}

if [ ! -d "$SRC_CASE" ]; then
  echo "Source case missing: $SRC_CASE" >&2
  exit 2
fi

if [ -e "$RUN/.started" ]; then
  echo "Run directory already used: $RUN" >&2
  exit 2
fi

mkdir -p "$RUN"
touch "$RUN/.started"
write_json running setup 0 0 "copying 3D case"
log "copying case from $SRC_CASE to $RUN"
cp -a "$SRC_CASE/." "$RUN/"

if ! command -v blockMesh >/dev/null 2>&1; then
  source /usr/lib/openfoam/openfoam2406/etc/bashrc >/dev/null 2>&1 || true
fi

cd "$RUN" || exit 2
log "OpenFOAM commands: blockMesh=$(command -v blockMesh) interFoam=$(command -v interFoam)"
log "target simulation time=${TARGET_TIME}s, mesh budget=${MESH_BUDGET_SECONDS}s, solver wall budget=${SOLVER_WALL_BUDGET_SECONDS}s"
if [ "$FAST_MESH" = "1" ]; then
  log "FAST_MESH=1: disabling snappyHexMesh snap phase for a quick solver-progress run"
  sed -i 's/castellatedMesh true; snap true; addLayers false;/castellatedMesh true; snap false; addLayers false;/' system/snappyHexMeshDict
fi

write_json running blockMesh 0 0 "running blockMesh"
log "blockMesh start"
if blockMesh > log.blockMesh 2>&1; then
  log "blockMesh OK"
else
  log "blockMesh FAIL"
  tail -20 log.blockMesh | tee -a "$PROGRESS"
  write_json failed blockMesh 0 0 "blockMesh failed"
  exit 1
fi

write_json running snappyHexMesh 0 0 "running snappyHexMesh"
log "snappyHexMesh start"
timeout "${MESH_BUDGET_SECONDS}s" snappyHexMesh -overwrite > log.snappyHexMesh 2>&1 &
SNPID=$!
SNSTART=$(date +%s)
LAST_SNAPPY=""
while kill -0 "$SNPID" 2>/dev/null; do
  sleep 15
  EL=$(( $(date +%s) - SNSTART ))
  LINE=$(grep -E 'cells:|After refinement|Finished meshing|Snap|Layer|Writing mesh|Time =' log.snappyHexMesh 2>/dev/null | tail -1 || true)
  if [ "$LINE" != "$LAST_SNAPPY" ]; then
    log "snappy progress elapsed=${EL}s ${LINE:-waiting for snappy output}"
    LAST_SNAPPY="$LINE"
  else
    log "snappy progress elapsed=${EL}s"
  fi
done
wait "$SNPID"
SNRC=$?
if [ "$SNRC" -ne 0 ]; then
  log "snappyHexMesh failed or timed out rc=$SNRC"
  tail -30 log.snappyHexMesh | tee -a "$PROGRESS"
  write_json failed snappyHexMesh 0 0 "snappyHexMesh failed or timed out"
  exit 1
fi
log "snappyHexMesh OK"

write_json running checkMesh 0 0 "running checkMesh"
checkMesh > log.checkMesh 2>&1 || true
grep -E 'cells:|Number of regions|Mesh OK|Failed' log.checkMesh | tail -8 | while read -r line; do
  log "checkMesh $line"
done

if [ -f "$DECOMPOSE_DICT" ]; then
  cp "$DECOMPOSE_DICT" system/decomposeParDict
else
  cat > system/decomposeParDict <<DICT
FoamFile { version 2.0; format ascii; class dictionary; object decomposeParDict; }
numberOfSubdomains $NPROC;
method scotch;
DICT
fi
sed -i "s/^endTime .*/endTime         $TARGET_TIME;/" system/controlDict
sed -i "s/^writeInterval .*/writeInterval   $WRITE_INTERVAL;/" system/controlDict
sed -i "s/^purgeWrite .*/purgeWrite      0;/" system/controlDict
rm -rf processor* [0-9]*.[0-9]* 2>/dev/null || true

write_json running setFields 0 0 "initializing water field"
log "setFields start"
if setFields > log.setFields 2>&1; then
  log "setFields OK"
else
  log "setFields FAIL"
  tail -20 log.setFields | tee -a "$PROGRESS"
  write_json failed setFields 0 0 "setFields failed"
  exit 1
fi

write_json running decomposePar 0 0 "decomposing case"
log "decomposePar start nproc=$NPROC"
if decomposePar -force > log.decomposePar 2>&1; then
  log "decomposePar OK"
else
  log "decomposePar FAIL"
  tail -30 log.decomposePar | tee -a "$PROGRESS"
  write_json failed decomposePar 0 0 "decomposePar failed"
  exit 1
fi

write_json running interFoam 0 0 "running solver"
log "interFoam start nproc=$NPROC"
export OMPI_ALLOW_RUN_AS_ROOT=1
export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
mpirun --allow-run-as-root -np "$NPROC" interFoam -parallel > log.interFoam 2>&1 &
IFPID=$!
IFSTART=$(date +%s)
LAST_REPORTED=""
while kill -0 "$IFPID" 2>/dev/null; do
  sleep 15
  EL=$(( $(date +%s) - IFSTART ))
  T=$(last_time)
  PCT=$(progress_percent "${T:-0}")
  REPORT="solver elapsed=${EL}s simTime=${T:-not-started}s target=${TARGET_TIME}s progress=${PCT}%"
  if [ "$REPORT" != "$LAST_REPORTED" ]; then
    log "$REPORT"
    write_json running interFoam "${T:-0}" "$PCT" "$REPORT"
    LAST_REPORTED="$REPORT"
  fi
  HIT=$(awk -v t="${T:-0}" -v target="$TARGET_TIME" 'BEGIN { print ((t + 0) >= target) ? 1 : 0 }')
  if [ "$HIT" = "1" ] || [ "$EL" -ge "$SOLVER_WALL_BUDGET_SECONDS" ]; then
    log "requesting graceful solver stop elapsed=${EL}s simTime=${T:-0}s"
    sed -i 's/^stopAt .*/stopAt          writeNow;/' system/controlDict
    break
  fi
done

STOP_WAIT_START=$(date +%s)
while kill -0 "$IFPID" 2>/dev/null; do
  sleep 5
  WAITED=$(( $(date +%s) - STOP_WAIT_START ))
  T=$(last_time)
  PCT=$(progress_percent "${T:-0}")
  log "waiting for solver exit waited=${WAITED}s simTime=${T:-not-started}s progress=${PCT}%"
  write_json stopping interFoam "${T:-0}" "$PCT" "waiting for solver to stop"
  if [ "$WAITED" -ge 60 ]; then
    log "killing solver after graceful-stop timeout"
    kill "$IFPID" 2>/dev/null || true
    break
  fi
done
wait "$IFPID" || true

T=$(last_time)
PCT=$(progress_percent "${T:-0}")
if grep -qiE 'FOAM FATAL|--> FOAM|SIGFPE|segmentation fault' log.interFoam 2>/dev/null; then
  log "interFoam reported errors"
  grep -iE 'FOAM FATAL|--> FOAM|SIGFPE|segmentation fault' log.interFoam | tail -12 | tee -a "$PROGRESS"
  write_json failed interFoam "${T:-0}" "$PCT" "interFoam reported errors"
  exit 1
fi

NT=$(find processor0 -maxdepth 1 -type d -regex '.*/[0-9]+(\.[0-9]+)?' 2>/dev/null | wc -l)
log "interFoam finished/paused lastSimTime=${T:-0}s progress=${PCT}% processor0TimeDirs=$NT"
write_json completed interFoam "${T:-0}" "$PCT" "solver run ended"
