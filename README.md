# IYPT Research

My work for the International Young Physicists' Tournament (IYPT): theory,
simulations, experiments and presentations, one folder per problem. Each folder
was its own repository; their full commit history is kept here.

## Problems

### [Self-starting siphon](self-starting-siphon/)
How a siphon primes itself, and how fast a reservoir then drains through it.

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
| [`simulation/`](flipo-flip/simulation/) | Interactive 3D web simulation with STL export, plus the LaTeX theory paper |
| [`presentation/`](flipo-flip/presentation/) | Tournament slides, speaker notes and opponent discussion |
| [`notes/`](flipo-flip/notes/) | Early notes |

### [Problem 1: CFD](problem-1-cfd/)
| Folder | What it is |
|---|---|
| [`pipeline/`](problem-1-cfd/pipeline/) | Rig description → browser configurator → OpenFOAM case generation → result viewers |
| [`setup/`](problem-1-cfd/setup/) | The original experimental setup and 3D rig model |

### [IYPT 2027](iypt-2027/)
Preparation for the 2027 tournament.
