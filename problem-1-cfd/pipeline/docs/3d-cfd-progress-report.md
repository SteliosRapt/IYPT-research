# 3D CFD Progress Report

Date: 2026-06-07

## Short answer

Before this document, I had only written brief status notes in `docs/code-review-wave-handoff.md` and `docs/assumptions.md`. This is the standalone report requested after the Docker/OpenFOAM run.

The repository now has a reproducible progress-runner script at `scripts/openfoam_3d_progress_runner.sh`. The local machine also has ignored run artifacts under `tmp/siphon_exp/`. The best local 3D run reached `interFoam` and advanced to `0.00879628 s` of simulated time, which is `0.1759%` of a `5.0 s` target. That run used an unsnapped fast mesh, so it proves 3D solver startup and progress reporting, but it is not final-quality CFD validation.

## What existed before this run

- `cfd_siphon_results/` contained a rendered siphon animation and plots from a quasi-2D OpenFOAM result. It is useful, but it is not a completed full-3D CFD result.
- `tmp/siphon_exp/case3d/` contained a full-3D OpenFOAM case setup with `0/`, `constant/`, `system/`, and STL geometry. It did not contain solver time directories beyond the initial `0` directory.
- The committed sample viewer manifests under `examples/sample-runs/default-mock/` were marked as `status: mock`, so they were synthetic viewer data, not real CFD output.
- Loose root logs (`log.bm`, `log.sf`, `log.if`) showed an earlier failed attempt that was run from the repository root instead of a valid OpenFOAM case directory. That failure complained about a missing `system/controlDict`.

## Environment findings

- WSL was not usable from this environment. `wsl` reported that no Linux distribution was installed.
- Native Windows OpenFOAM commands such as `blockMesh`, `snappyHexMesh`, and `interFoam` were not on `PATH`.
- Docker Desktop was installed but initially stopped. I started Docker Desktop and used the Docker engine outside the sandbox after approval.
- No OpenFOAM Docker image was cached locally, so I pulled `opencfd/openfoam-default:2406`, matching the OpenFOAM 2406 version shown in the earlier logs.

## Implementation

I first created a temporary container runner under `tmp/siphon_exp/run_3d_short_container.sh`. Because `tmp/` is ignored, I preserved the useful implementation as a tracked script:

- `scripts/openfoam_3d_progress_runner.sh`

The runner is designed to execute inside an OpenFOAM container with this repository mounted at `/work`. It does the following:

1. Copies a source OpenFOAM case into a fresh run directory.
2. Writes `progress.log` and `progress.json`.
3. Runs `blockMesh`.
4. Runs `snappyHexMesh -overwrite` with a wall-clock budget.
5. Runs `checkMesh`.
6. Initializes the water field with `setFields`.
7. Creates or copies `decomposeParDict`.
8. Runs `decomposePar -force`.
9. Starts `mpirun --allow-run-as-root -np <NPROC> interFoam -parallel`.
10. Polls `log.interFoam` for the latest `Time = ...` line.
11. Converts that latest simulated time into percent progress against `TARGET_TIME`.
12. Requests a graceful stop by changing `stopAt` to `writeNow` once the target or wall-clock budget is reached.

The progress JSON shape is:

```json
{
  "updatedAt": "2026-06-07T13:01:51Z",
  "status": "completed",
  "stage": "interFoam",
  "targetSimulationSeconds": 5.0,
  "lastSimulationSeconds": 0.00879628,
  "progressPercent": 0.1759,
  "message": "solver reached wall budget and stopped cleanly"
}
```

Example container command:

```powershell
docker run --rm `
  -e RUN_ID=case3d-fast `
  -e FAST_MESH=1 `
  -e TARGET_TIME=5.0 `
  -e WRITE_INTERVAL=0.05 `
  -e MESH_BUDGET_SECONDS=420 `
  -e SOLVER_WALL_BUDGET_SECONDS=300 `
  -e NPROC=12 `
  -v "C:\Users\user\Desktop\Problem_1_CFD_1:/work" `
  opencfd/openfoam-default:2406 `
  bash /work/scripts/openfoam_3d_progress_runner.sh
```

While it runs, progress can be checked with:

```powershell
Get-Content tmp\siphon_exp\<run-id>\progress.json
Get-Content tmp\siphon_exp\<run-id>\progress.log -Tail 50 -Wait
docker ps --filter name=<run-id>
```

## What worked

### Docker/OpenFOAM runtime

- Docker Desktop started successfully.
- `opencfd/openfoam-default:2406` downloaded and exposed the expected OpenFOAM commands.
- The container could read and write the mounted repository.

### Full-quality snapped attempt

Run directory:

- `tmp/siphon_exp/case3d-short-20260607-153910/`

Results:

- `blockMesh` completed.
- `snappyHexMesh` progressed to about `1,006,534` cells.
- The run reached the snapping phase and continued doing real mesh work.
- Progress logging was useful; without it, the snapping phase would have looked idle.

### Fast unsnapped solver-progress attempt

Run directory:

- `tmp/siphon_exp/case3d-fast-20260607-155122/`

Results:

- `blockMesh` completed.
- `snappyHexMesh` completed in `167.79 s` with `FAST_MESH=1`, which disabled the snap phase in the copied run directory only.
- `checkMesh` reported:
  - `cells: 1006534`
  - `Number of regions: 1 (OK).`
  - `Mesh OK.`
- `setFields` completed.
- `decomposePar -force` completed with `NPROC=12`.
- `interFoam` started and ran in parallel.
- The solver wrote a processor time directory at `processor0/0.00879628`.
- The solver log ended with `End` and `Finalising parallel run`.

## What did not work

### WSL path

The existing helper scripts expected WSL and `/root/sx3`, but this machine currently reports no installed WSL distribution. That made the original WSL/OpenFOAM path unavailable.

### Native OpenFOAM path

No native OpenFOAM executables were available in PowerShell, so the only viable local route was Docker.

### First temporary runner

The first Docker runner used `python3` to write JSON. The OpenFOAM container did not include `python3`, so I rewrote the progress JSON writer in shell.

### OpenFOAM bashrc sourcing

The OpenFOAM image already had solver commands on `PATH`. Sourcing `/usr/lib/openfoam/openfoam2406/etc/bashrc` caused an early script exit in that image, so the runner now only sources the bashrc if `blockMesh` is not already available.

### Full snapped mesh within short budget

The production-style snapped mesh did not finish within a 600 second mesh budget. It reached the snapping phase after building about `1,006,534` cells, then timed out before `setFields` or `interFoam`.

### Five simulated seconds

The fast run reached only `0.00879628 s` of simulated time after about 300 seconds of solver wall time. A rough extrapolation from that run gives on the order of tens of hours, around 50 hours, to reach `5.0 s` on this CPU/container setup. That is only a rough estimate; solver time step size and convergence cost can change during the run.

### False-positive failure marker

The first version of the runner treated OpenFOAM's normal `trapFpe: Floating point exception trapping enabled` banner as a failure. The raw solver log did not show a crash; it ended normally. The tracked runner now avoids that false-positive check.

## What exists now

Tracked files:

- `scripts/openfoam_3d_progress_runner.sh`
- `docs/3d-cfd-progress-report.md`
- `docs/assumptions.md`
- `docs/code-review-wave-handoff.md`

Local ignored artifacts:

- `tmp/siphon_exp/case3d-short-20260607-153910/`
  - Full-quality snapped attempt.
  - Timed out during `snappyHexMesh` snapping.
- `tmp/siphon_exp/case3d-fast-20260607-155122/`
  - Fast unsnapped progress run.
  - Contains `progress.log`, `progress.json`, `log.interFoam`, processor directories, and output at `processor0/0.00879628`.
- `tmp/siphon_exp/case3d/`
  - Source 3D case setup used for the run.

Docker state:

- The stopped run containers were removed after preserving workspace logs.
- No OpenFOAM container was left running.
- The pulled `opencfd/openfoam-default:2406` image remains in Docker's local image cache.

## How to interpret the result

This is a successful 3D solver-start/progress check, not a final full-3D CFD result.

The fast run proves that the case can be copied, meshed in 3D, initialized, decomposed, run with `interFoam`, and monitored. It does not prove that the final free surface, wall treatment, or siphon physics are production-valid because the snap phase was disabled to get through the pipeline quickly.

For final validation, the next run should use the snapped mesh, let `snappyHexMesh` finish, and run for a much longer wall-clock budget.

## CPU versus GPU

The current path is CPU-based because it uses standard OpenFOAM commands from `opencfd/openfoam-default:2406`. Running Docker with a GPU would not automatically make this faster. The OpenFOAM solver itself must be built/configured to use GPU-capable linear algebra or GPU kernels.

For this case, GPU acceleration would likely target the expensive linear solves, especially pressure-related solves. NVIDIA AmgX is a GPU-accelerated library for sparse linear solvers and algebraic multigrid, and it supports MPI/distributed solver use. See NVIDIA's AmgX repository:

- https://github.com/NVIDIA/AMGX

The realistic GPU path would be:

1. Keep the CPU Docker/OpenFOAM path as the reference baseline.
2. Profile the run to confirm where time is spent: mesh generation, alpha advection, pressure solve, or MPI overhead.
3. Build a GPU-capable OpenFOAM environment using PETSc/PETSc4FOAM plus AmgX, or another maintained OpenFOAM GPU integration.
4. Update `fvSolution` to use the GPU-backed solvers for the matrices that dominate runtime.
5. Run a tiny validation case and compare CPU versus GPU results.
6. Only then run the 3D siphon case on GPU.

GPU risks:

- `snappyHexMesh` is still mainly CPU work in this workflow.
- VOF/interface advection may not move entirely to GPU.
- GPU memory could be limiting for larger snapped meshes.
- A GPU linear solver can change numerical behavior enough that validation against the CPU baseline is mandatory.
- OpenFOAM GPU acceleration is not a simple runtime flag for this repository.

## Google Colab GPU thoughts

Colab paid GPUs may help only if the solver actually uses the GPU. Google also states that Colab GPU availability varies over time and paid premium GPUs are subject to availability:

- https://research.google.com/colaboratory/faq.html

The regular hosted Colab notebook model is not ideal for this full OpenFOAM workflow because:

- Building OpenFOAM plus PETSc/AmgX can consume a lot of session time.
- Runtime lifetimes and hardware availability are not guaranteed.
- Docker-in-hosted-Colab is not the clean path for this workflow.
- Large mesh and processor directories are awkward on notebook storage.

Better Colab-adjacent options:

1. **Colab as a notebook front end to a local runtime**
   - Google documents local runtimes and a Docker runtime image. For GPU support, their local runtime docs require NVIDIA drivers and the NVIDIA container toolkit, and show `docker run --gpus=all`.
   - Source: https://research.google.com/colaboratory/local-runtimes.html
   - This is useful if you control a GPU machine locally or on a cloud VM and want Colab as the UI.

2. **Colab Enterprise or a dedicated GCP GPU VM**
   - Colab Enterprise documents GPU-backed default runtimes with L4/T4 availability depending on region.
   - Source: https://docs.cloud.google.com/colab/docs/default-runtimes-with-gpus
   - A dedicated GCP GPU VM is more practical for Docker, persistent build caches, longer runs, and custom OpenFOAM GPU images.

3. **Plain paid Colab Pro/Pro+ hosted runtime**
   - Good for exploratory notebooks, Python post-processing, plotting, and maybe compiling small experiments.
   - Less attractive for production OpenFOAM GPU work unless we can prepackage the GPU-enabled environment and tolerate runtime limits.

Docker GPU access itself requires exposing NVIDIA GPUs to containers with Docker's GPU support, for example `--gpus`.

- https://docs.docker.com/engine/containers/gpu/

## Recommended next steps

1. Run the full snapped mesh with a longer mesh budget, at least several hours, and preserve the mesh once it finishes.
2. Resume or rerun `interFoam` from the completed snapped mesh with a smaller initial target such as `0.05 s`, not `5.0 s`.
3. Add automatic reconstruction of the latest time with `reconstructPar -latestTime` after a clean solver stop.
4. Add a post-processing step that extracts front position, water volume, and outlet flow from the 3D result.
5. Before spending time on GPU work, profile the CPU run to identify the dominant cost.
6. If GPU work is justified, prototype PETSc4FOAM/AmgX on a small OpenFOAM case before trying the siphon case.
7. Prefer a dedicated GCP GPU VM or a Colab local runtime connected to a GPU VM over a transient hosted Colab notebook for the full GPU solver workflow.

## Bottom line

The run now has measurable 3D OpenFOAM progress reporting. It did not produce a final 5-second full-quality 3D CFD result. The local fast run reached `0.00879628 s` simulated time and shows that the pipeline can start and be monitored. The next real milestone is to finish the snapped mesh and run a much shorter validated physical target before attempting a long 5-second simulation or a GPU port.
