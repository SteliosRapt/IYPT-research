# IYPT Research

My work for the International Young Physicists' Tournament (IYPT): theory,
simulations, experiments and presentations, one folder per problem. Each folder
was its own repository; their full commit history is kept here.

## Problems

### [Self-starting siphon](self-starting-siphon/)
How a siphon primes itself, and how fast a reservoir then drains through it.

**Start with [`theory-and-experiments/siphon-theory-5.tex`](self-starting-siphon/theory-and-experiments/siphon-theory-5.tex)**, the most complete paper, and [`simulations/`](self-starting-siphon/simulations/) for the code. The other folders are earlier drafts, kept for their history. The full model's loss parameters are fitted to the same experiment it is compared with, so that comparison is a calibration, not an independent validation.

| Folder | What it is |
|---|---|
| [`simulations/`](self-starting-siphon/simulations/) | Python models of siphon drainage: ideal, constant-loss and Reynolds-dependent losses, plus a multi-crest geometry solver |
| [`framework/`](self-starting-siphon/framework/) | The overall theoretical, computational and experimental plan |
| [`priming-model-v1/`](self-starting-siphon/priming-model-v1/) | First LaTeX model of priming: equations of motion, Darcy–Weisbach and minor losses |
| [`slug-flow-model-v1/`](self-starting-siphon/slug-flow-model-v1/), [`slug-flow-model-v2/`](self-starting-siphon/slug-flow-model-v2/) | One-dimensional slug-flow model, two iterations |
| [`combined-models/`](self-starting-siphon/combined-models/) | Geometry, dynamics, losses and computation in one paper |
| [`experiments-v1/`](self-starting-siphon/experiments-v1/) | Experimental data and validation figures |
| [`theory-and-experiments/`](self-starting-siphon/theory-and-experiments/) | Latest write-up: theory and experiment together |

### [Flipo flip (IYPT 2026, Problem 6)](flipo-flip/)
A rectangular prism with Steinmetz-bicylinder caps that rolls in a six-phase cycle.

| Folder | What it is |
|---|---|
| [`simulation/`](flipo-flip/simulation/) | Interactive 3D visualization of the rolling cycle (kinematic, not a dynamics solver) with STL export, plus the LaTeX theory paper |
| [`presentation/`](flipo-flip/presentation/) | Tournament slides, speaker notes and opponent discussion |
| [`notes/`](flipo-flip/notes/) | Early notes |

### [Problem 1: CFD](problem-1-cfd/)
| Folder | What it is |
|---|---|
| [`pipeline/`](problem-1-cfd/pipeline/) | Rig description → browser configurator → OpenFOAM case generation → result viewers |
| [`setup/`](problem-1-cfd/setup/) | The original experimental setup and 3D rig model (the same files are also in `pipeline/`) |

The quasi-2D OpenFOAM run reproduces the priming qualitatively; its front is about 1.6× faster than the experiment ([`RESULTS.md`](problem-1-cfd/pipeline/cfd_siphon_results/RESULTS.md)). The full-3D pipeline has not yet completed a solver run.

### [IYPT 2027](iypt-2027/)
Preparation for the 2027 tournament.
