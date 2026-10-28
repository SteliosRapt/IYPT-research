"""Compare CFD priming front L(t) with the experimental measurement.
Usage: compare.py <cfd_frontL.json> <out.png> [checkpoints.json]

checkpoints.json defaults to the copy next to this script; pass the one that
build_case.py wrote (case/checkpoints.json) if you regenerated the geometry."""
import json
import sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

cfd = json.load(open(sys.argv[1]))           # [[t, L_m], ...]
out = sys.argv[2]
here = Path(__file__).resolve().parent
exp = json.load(open(here / "exp_front.json"))           # [{t, V, L}], L in cm
cp_path = Path(sys.argv[3]) if len(sys.argv) > 3 else here / "checkpoints.json"
cp = json.load(open(cp_path))
node_s = {k: v * 100 for k, v in cp["arclength"].items()}  # cm

ct = np.array([r[0] for r in cfd])
cL = np.array([r[1] * 100 for r in cfd])     # cm
et = np.array([r["t"] for r in exp])
eL = np.array([r["L"] for r in exp])         # cm

# valid CFD front (front past the inlet, monotonic-ish)
ok = np.isfinite(cL) & (cL > 1)
ct, cL = ct[ok], cL[ok]

# Align time origins by matching the instant each front passes L_ref (tracking in the
# experiment began mid-priming, so only the relative timing / slope is physical).
L_ref = 22.0
def t_at(tarr, Larr, Lref):
    i = np.argmin(np.abs(Larr - Lref))
    return tarr[i]
shift = t_at(et, eL, L_ref) - t_at(ct, cL, L_ref)
ct_al = ct + shift

# front velocities (cm/s) by linear fit over the climbing region 20..42 cm
def slope(tarr, Larr):
    m = (Larr > 20) & (Larr < 42)
    if m.sum() < 3:
        return float("nan")
    return np.polyfit(tarr[m], Larr[m], 1)[0]
v_exp = slope(et, eL)
v_cfd = slope(ct_al, cL)

fig, ax = plt.subplots(figsize=(9, 6))
for k, s in node_s.items():
    ax.axhline(s, color="0.85", lw=1)
    ax.text(ax.get_xlim()[1], s, f" {k}", va="center", fontsize=9, color="0.4")
ax.plot(et, eL, "o", color="#d61f1f", ms=5, label=f"experiment (v≈{v_exp:.1f} cm/s)")
ax.plot(ct_al, cL, "-", color="#1f6fd6", lw=2, label=f"CFD interFoam (v≈{v_cfd:.1f} cm/s)")
ax.set_xlabel("time (s, aligned at L=22 cm)")
ax.set_ylabel("priming front arclength L (cm)")
ax.set_title("Self-starting siphon: priming front L(t) — CFD vs experiment")
ax.legend(loc="lower right")
ax.grid(alpha=0.25)
ax.set_ylim(0, 50)
fig.tight_layout()
fig.savefig(out, dpi=130)
print("wrote", out)
print(f"front velocity  experiment={v_exp:.1f} cm/s   CFD={v_cfd:.1f} cm/s   ratio={v_cfd/v_exp:.2f}")
print(f"CFD reaches L={cL.max():.1f} cm; experiment reaches {eL.max():.1f} cm")
