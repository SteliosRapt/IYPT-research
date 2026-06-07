"""Track the priming front L(t) from the CFD and render the siphon animation
with the A-E checkpoints marked. Usage: analyze.py <case_dir> <out_prefix>"""
from __future__ import annotations

import json
import os
import sys
import numpy as np
import pyvista as pv
import imageio.v2 as imageio

case_dir = sys.argv[1]
out_prefix = sys.argv[2]
cp = json.load(open(os.path.join(case_dir, "checkpoints.json")))
center = np.array(cp["centerline"])          # (N,2)
cum = np.array(cp["cum_arclength"])           # (N,) arclength from A
nodes = cp["nodes_xy"]
node_s = cp["arclength"]
pr = cp["pipe_radius"]
slab = cp["slab"]


def arclength_of(points_xy):
    """Nearest-centreline arclength for each (x,y); also perpendicular distance."""
    d2 = ((points_xy[:, None, 0] - center[None, :, 0]) ** 2
          + (points_xy[:, None, 1] - center[None, :, 1]) ** 2)
    idx = d2.argmin(axis=1)
    return cum[idx], np.sqrt(d2[np.arange(len(points_xy)), idx])


foam = os.path.join(case_dir, "case.foam")
open(foam, "a").close()
pv.global_theme.allow_empty_mesh = True
reader = pv.OpenFOAMReader(foam)
reader.enable_all_patch_arrays()
times = [t for t in reader.time_values if t > 0]
print("frames:", len(times))

# checkpoint markers (3D, at slab mid-plane)
zc = slab / 2
node_pts = {k: np.array([v[0], v[1], zc]) for k, v in nodes.items()}

pl = pv.Plotter(off_screen=True, window_size=[1366, 720])
pl.set_background("white")
# frame the whole siphon, slight 3D tilt so the slab reads as a solid object
cx, cy = 0.065, 0.045
CAMPOS = [(cx, cy, 0.92), (cx, cy, zc), (0, 1, 0)]


def set_cam():
    pl.camera_position = CAMPOS
    pl.camera.azimuth = 12
    pl.camera.elevation = 10

writer = imageio.get_writer(out_prefix + ".mp4", fps=15, codec="libx264", quality=8)
gif_frames = []
front_L = []

for i, t in enumerate(times):
    reader.set_active_time_value(t)
    d = reader.read()
    m = d["internalMesh"]
    if "alpha.water" not in m.array_names:
        front_L.append((t, np.nan))
        continue
    cc = m.cell_centers()
    pts = np.asarray(cc.points)
    alpha = np.asarray(cc["alpha.water"])
    s, perp = arclength_of(pts[:, :2])
    # front = furthest arclength reached by water inside the bore, past the low point
    in_bore = perp < pr * 1.8
    watery = alpha > 0.5
    sel = in_bore & watery & (s > node_s["A"] + 0.02)
    L = float(np.nanmax(s[sel])) if sel.any() else node_s["A"]
    front_L.append((t, L))

    # render
    pl.clear()
    water = m.threshold(0.5, scalars="alpha.water")
    walls = None
    try:
        walls = d["boundary"]["walls"]
    except Exception:
        pass
    if walls is not None:
        pl.add_mesh(walls, color="#c8d2dc", opacity=0.25)
    if water.n_cells > 0:
        umag = np.linalg.norm(np.asarray(water["U"]), axis=1) if "U" in water.array_names else None
        if umag is not None:
            pl.add_mesh(water, scalars=umag, cmap="turbo", clim=[0, 0.6],
                        show_scalar_bar=True, scalar_bar_args={"title": "|U| m/s", "color": "black"})
        else:
            pl.add_mesh(water, color="#1f8fd6")
    # checkpoint markers + labels
    labelpts, labels = [], []
    for k in ["A", "B", "C", "D", "E"]:
        p = node_pts[k]
        pl.add_mesh(pv.Sphere(radius=0.004, center=p), color="#d61f1f")
        labelpts.append(p + np.array([0, 0.012, 0]))
        labels.append(f"{k} ({node_s[k]*100:.0f}cm)")
    pl.add_point_labels(np.array(labelpts), labels, font_size=14, text_color="black",
                        shape=None, always_visible=True)
    # front marker: point on centreline at arclength L
    j = int(np.argmin(np.abs(cum - L)))
    fp = np.array([center[j, 0], center[j, 1], zc])
    pl.add_mesh(pv.Sphere(radius=0.005, center=fp), color="#10b020")
    pl.add_text(f"t = {t:5.2f} s    front L = {L*100:5.1f} cm    (experimental self-starting siphon, interFoam VOF)",
                position="upper_left", font_size=12, color="black")
    set_cam()
    img = pl.screenshot(return_img=True)
    writer.append_data(img)
    gif_frames.append(img)
    if i % 15 == 0:
        print(f"frame {i} t={t:.2f} L={L*100:.1f}cm")

writer.close()
imageio.mimsave(out_prefix + ".gif", gif_frames[::3], fps=8)
json.dump([[float(t), float(L)] for t, L in front_L], open(out_prefix + "_frontL.json", "w"))
print("WROTE", out_prefix + ".mp4", "frames", len(gif_frames))
print("final front L:", round(front_L[-1][1] * 100, 1), "cm")
