# Self-Starting Siphon — CFD vs Experiment

A real OpenFOAM (interFoam VOF) simulation of the **experimental self-starting
siphon** from `Theory-and-real-experiment/Exp-data (1).xlsx`, with the priming front
compared directly to the measured data.

## Files

| File | What it is |
|------|------------|
| `siphon_experiment.mp4` / `.gif` | 3D-rendered animation of water priming through the straw, coloured by velocity, with checkpoints A–E and the green priming-front marker |
| `siphon_comparison.png` | Priming front position L(t): CFD vs experiment |
| `f_prime.png` | Still during priming (front climbing over crest D) |
| `f_discharge.png` | Still of the established siphon discharging (whole tube flowing) |
| `scripts/build_case.py` | Builds the quasi-2D OpenFOAM case from the experimental geometry |
| `scripts/analyze.py` | Tracks the front L(t) and renders the animation |
| `scripts/compare.py` | Produces the CFD-vs-experiment plot |
| `scripts/exp_front.json` | Experimental front data (from the xlsx) |
| `scripts/checkpoints.json` | Geometry: centreline, node positions, A–E arclengths |

## Geometry (from the experiment)

5 mm drinking-straw bore; nodes (x, h in cm): **A**(0,1) inlet, **B**(7.5,11) first
crest *below* the 12.5 cm waterline, **C**(13.5,5) low point, **D**(21.4,13) main
crest *above* the waterline, **E**(30.3,−1.7) outlet. The "first crest below the
waterline" is the self-starting mechanism.

## Method

`build_case.py` constructs the fluid region (reservoir + straw bore) with Shapely,
extrudes its boundary into a thin z-slab and meshes it with blockMesh + snappyHexMesh
(empty front/back ⇒ true 2D), ~31k cells, 5 cells across the 5 mm bore. interFoam
(OpenFOAM 2406) is initialised with the reservoir filled to the waterline and the
straw full of air, then runs with gravity only — no forced inflow, no suction.

## Result

The siphon **self-primes**: water enters the submerged inlet, climbs over crest B,
through the low point C, over the *above-waterline* crest D, and discharges at E —
then the whole tube runs as an established siphon (~0.5 m/s).

**CFD vs experiment (priming front L(t)):**
- Both self-prime. The CFD front traverses A→E in ≈1 s. The experimental front was
  tracked only from L = 19.3 cm (t = 0.4 s) to L = 43.6 cm (t = 1.8 s), so the
  experiment's full A→E time is not measured; the curves are aligned in time at L = 22 cm.
- The CFD front **pauses at crests B and D** then accelerates — the energy-barrier
  behaviour the theory paper analyses via the priming integral I(L).
- The CFD front is **~1.6× faster** than the experiment. A likely cause is that a 2D
  slot has less wall drag than a round 5 mm straw (smaller wetted perimeter / larger
  hydraulic diameter), so 2D under-predicts friction. This is a hypothesis: mesh
  resolution, geometry, front detection, surface tension and the time alignment have
  not been ruled out (no mesh-convergence or 3D comparison yet). The qualitative
  priming behaviour agrees; the absolute front speed does not.

## Limitations / next steps

- Quasi-2D (centre-plane). A full 3D run of the 5 mm bore would capture round-pipe
  friction (the generator now meshes a 3D bore correctly — `tubeOutlet` gets faces —
  but resolving 5 mm in 3D needs millions of cells).
- Container drawdown is not matched in 2D (irrelevant during the ~1 s priming window).
- Surface tension and minor (entrance/bend) losses are only partially captured.

## Reproduce

```bash
# from cfd_siphon_results/
python scripts/build_case.py                   # writes scripts/case (incl. checkpoints.json)
# in WSL with OpenFOAM 2406 sourced:
#   cp -r scripts/case /root/sx && cd /root/sx && blockMesh && snappyHexMesh -overwrite && setFields && interFoam
xvfb-run -a python3 scripts/analyze.py /root/sx out      # animation + out_frontL.json
python scripts/compare.py out_frontL.json comparison.png scripts/case/checkpoints.json
```
