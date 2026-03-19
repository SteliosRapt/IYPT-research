"""
Render a simulation run as a side-elevation video (.mp4) or animated GIF.

Usage
-----
    py scripts/render_video.py [manifest_path] [--output OUTPUT] [--fps FPS] [--dpi DPI]

    manifest_path  Path to manifest.json inside a run output directory.
                   Defaults to examples/default-mock/manifest.json.
    --output       Output file path.  Extension controls format:
                     .mp4  requires ffmpeg on PATH
                     .gif  uses Pillow (bundled with matplotlib)
                   Defaults to <run_dir>/side_view.mp4
    --fps          Frames per second.  Default 15.
    --dpi          Render DPI.  Default 150.

The video shows a 2-D side elevation (looking along the Z axis, XY plane):
  - Container walls and tube path from fixed_geometry.json
  - Animated water surface (blue fill) from frame meshes
  - Time stamp and event markers
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import matplotlib.lines as mlines
import numpy as np
from matplotlib.animation import FuncAnimation


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_run(manifest_path: Path):
    base = manifest_path.parent
    manifest = load_json(manifest_path)
    geom    = load_json(base / manifest["geometryAssets"]["fixedJson"])
    height  = load_json(base / manifest["chartSeries"]["height"])
    q_out   = load_json(base / manifest["chartSeries"]["outletFlow"])
    frames  = [
        load_json(base / p)
        for p in manifest["fluidAssets"]["interfaceFrames"]
    ]
    return manifest, geom, height, q_out, frames


# ---------------------------------------------------------------------------
# Geometry extraction helpers
# ---------------------------------------------------------------------------

def _box_xy(descriptor: dict):
    """Return (x_min, y_min, x_max, y_max) for a box descriptor."""
    cx, cy, _ = descriptor["center"]
    sx, sy, _ = descriptor["size"]
    return cx - sx / 2, cy - sy / 2, cx + sx / 2, cy + sy / 2


def _tube_band(tube_descriptor: dict):
    """Return two numpy arrays (x_top, y_top), (x_bot, y_bot) bounding the tube."""
    path = np.array([[p[0], p[1]] for p in tube_descriptor["path"]])
    r    = tube_descriptor["outerRadius"]
    # Approximate band: shift path by ±r in the perpendicular direction.
    # For simplicity use ±r offset in Y (good enough for the near-horizontal
    # segments; bends will look slightly off but the intent is clear).
    return path, r


# ---------------------------------------------------------------------------
# Frame-level mesh → 2-D bounding box
# ---------------------------------------------------------------------------

def frame_water_box(frame: dict):
    """Return (x0, y0, x1, y1) of the water box projected onto XY."""
    pts = np.array(frame["points"])  # Nx3
    if len(pts) == 0:
        return None
    return pts[:, 0].min(), pts[:, 1].min(), pts[:, 0].max(), pts[:, 1].max()


# ---------------------------------------------------------------------------
# Scene drawing
# ---------------------------------------------------------------------------

DARK_BG   = "#0a0a0f"
WALL_C    = "#607090"
TUBE_C    = "#9ab4cc"
WATER_C   = "#1a6fcc"
PLUME_C   = "#3399ff"
HOLDER_C  = "#50bb70"
COLUMN_C  = "#9a7bff"
EVENT_C   = "#ffaa44"
TEXT_C    = "#d0d8e8"


def build_scene(ax, geom: dict):
    """Draw static geometry on ax.  Returns a dict of artists to update per frame."""
    ax.set_facecolor(DARK_BG)

    container = {d["name"]: d for d in geom["container"]}
    tube_desc  = geom["tube"][0]

    # --- Container walls (draw as rectangles, clipped to XY) ---
    for name, desc in container.items():
        if desc["type"] in ("box", "wallWithHole"):
            x0, y0, x1, y1 = _box_xy(desc)
            rect = mpatches.Rectangle(
                (x0, y0), x1 - x0, y1 - y0,
                linewidth=1.2, edgecolor=WALL_C, facecolor="none", zorder=3
            )
            ax.add_patch(rect)

    # --- Tube path band ---
    path, r = _tube_band(tube_desc)
    ax.plot(path[:, 0], path[:, 1] + r, color=TUBE_C, lw=1.0, alpha=0.6, zorder=3)
    ax.plot(path[:, 0], path[:, 1] - r, color=TUBE_C, lw=1.0, alpha=0.6, zorder=3)
    ax.fill_between(path[:, 0], path[:, 1] - r, path[:, 1] + r,
                    color=TUBE_C, alpha=0.12, zorder=2)

    # --- Holders (vertical sticks at their X centre) ---
    for holder in geom["holders"]:
        hx   = holder["center"][0]
        base = holder["baseY"]
        top  = base + holder["pointHeight"]
        ax.plot([hx, hx], [base, top], color=HOLDER_C, lw=2.0, alpha=0.7, zorder=4)

    # --- Columns (subtle) ---
    for col in geom["columns"]:
        if col["type"] == "box":
            x0, y0, x1, y1 = _box_xy(col)
            rect = mpatches.Rectangle(
                (x0, y0), x1 - x0, y1 - y0,
                linewidth=0.6, edgecolor=COLUMN_C, facecolor=COLUMN_C,
                alpha=0.15, zorder=2
            )
            ax.add_patch(rect)

    # --- Animated water patch (filled rectangle in container) ---
    water_patch = mpatches.Rectangle(
        (0, 0), 0, 0,
        facecolor=WATER_C, edgecolor="none", alpha=0.55, zorder=5
    )
    ax.add_patch(water_patch)

    # --- Animated outlet plume ---
    plume_patch = mpatches.Rectangle(
        (0, 0), 0, 0,
        facecolor=PLUME_C, edgecolor="none", alpha=0.45, zorder=5
    )
    ax.add_patch(plume_patch)

    return {"water": water_patch, "plume": plume_patch}


def update_frame(artists: dict, frame: dict, height_val: float, q_out_val: float,
                 geom: dict, manifest: dict, time_text):
    """Update animated artists for one timestep."""
    tube_desc = geom["tube"][0]
    container = {d["name"]: d for d in geom["container"]}

    # Container bounds
    right_wall = container.get("rightWall") or list(container.values())[2]
    left_wall  = container.get("leftWall")  or list(container.values())[1]
    x0_cont = left_wall["center"][0]  - left_wall["size"][0] / 2
    x1_cont = right_wall["center"][0] + right_wall["size"][0] / 2

    # Water box in container
    artists["water"].set_xy((x0_cont, 0))
    artists["water"].set_width(x1_cont - x0_cont)
    artists["water"].set_height(max(0.0, height_val))

    # Outlet plume (proportional to flow rate)
    path  = tube_desc["path"]
    r     = tube_desc["outerRadius"]
    p5x   = path[-1][0]
    p5y   = path[-1][1]
    plume_w = q_out_val * 180 if q_out_val > 0 else 0.0
    artists["plume"].set_xy((p5x, p5y - r))
    artists["plume"].set_width(plume_w)
    artists["plume"].set_height(r * 2)

    # Time stamp
    time_text.set_text(f"t = {frame['time']:.2f} s")


# ---------------------------------------------------------------------------
# Main render function
# ---------------------------------------------------------------------------

def render(manifest_path: Path, output_path: Path, fps: int, dpi: int):
    print(f"Loading run from {manifest_path} ...")
    manifest, geom, height_series, q_out_series, frames = load_run(manifest_path)

    times   = manifest["timeSteps"]
    heights = {pt["time"]: pt["value"] for pt in height_series}
    q_outs  = {pt["time"]: pt["value"] for pt in q_out_series}
    t_h0_up = manifest["events"]["t_h0_up"]
    t_steady = manifest["events"]["t_steady"]

    # Compute plot bounds from geometry
    container_boxes = [_box_xy(d) for d in geom["container"] if d["type"] in ("box", "wallWithHole")]
    tube_path = np.array([[p[0], p[1]] for p in geom["tube"][0]["path"]])
    r_tube = geom["tube"][0]["outerRadius"]
    all_x = [b[0] for b in container_boxes] + [b[2] for b in container_boxes] + list(tube_path[:, 0])
    all_y = [b[1] for b in container_boxes] + [b[3] for b in container_boxes] + list(tube_path[:, 1] + r_tube)
    pad = 0.03
    x_lo, x_hi = min(all_x) - pad, max(all_x) + pad
    y_lo, y_hi = -pad, max(all_y) + pad * 2

    # Figure
    aspect = (x_hi - x_lo) / (y_hi - y_lo)
    fig_w  = max(10, min(16, 10 * aspect))
    fig, ax = plt.subplots(figsize=(fig_w, 7), facecolor=DARK_BG)
    ax.set_xlim(x_lo, x_hi)
    ax.set_ylim(y_lo, y_hi)
    ax.set_aspect("equal")
    ax.tick_params(colors=TEXT_C)
    for spine in ax.spines.values():
        spine.set_edgecolor("#303050")
    ax.set_xlabel("x  (m)", color=TEXT_C, fontsize=8)
    ax.set_ylabel("y  (m)", color=TEXT_C, fontsize=8)
    ax.set_title("Fixed-geometry CFD — side elevation", color=TEXT_C, fontsize=10)

    artists = build_scene(ax, geom)

    # Event marker lines
    if t_h0_up is not None:
        ax.axhline(geom["tube"][0]["path"][-1][1] if False else 0,
                   color="none")  # placeholder; mark on time via text only

    # Time text
    time_text = ax.text(
        0.02, 0.97, "t = 0.00 s",
        transform=ax.transAxes, color=TEXT_C, fontsize=9,
        verticalalignment="top"
    )

    # Event annotations (fixed labels)
    event_y = y_hi * 0.93
    if t_h0_up is not None:
        ax.annotate(f"h₀ crossed\nt={t_h0_up:.2f}s",
                    xy=(x_lo + (x_hi - x_lo) * 0.05, event_y),
                    fontsize=7, color=EVENT_C)
    if t_steady is not None:
        ax.annotate(f"steady\nt={t_steady:.2f}s",
                    xy=(x_lo + (x_hi - x_lo) * 0.25, event_y),
                    fontsize=7, color=EVENT_C)

    # Legend
    legend_handles = [
        mpatches.Patch(color=WATER_C, alpha=0.55, label="Water"),
        mlines.Line2D([], [], color=TUBE_C, alpha=0.6, label="Tube"),
        mlines.Line2D([], [], color=HOLDER_C, lw=2, label="Holders"),
        mlines.Line2D([], [], color=WALL_C, label="Container"),
    ]
    ax.legend(handles=legend_handles, loc="upper right",
              facecolor="#15151f", edgecolor="#303050", labelcolor=TEXT_C,
              fontsize=7)

    plt.tight_layout()

    # Animation function
    def animate(i: int):
        t = times[i]
        h = heights.get(t, heights.get(round(t, 3), 0.0))
        q = q_outs.get(t, q_outs.get(round(t, 3), 0.0))
        update_frame(artists, frames[i], h, q, geom, manifest, time_text)
        return list(artists.values()) + [time_text]

    anim = FuncAnimation(fig, animate, frames=len(times),
                         interval=1000 // fps, blit=False)

    suffix = output_path.suffix.lower()
    if suffix == ".mp4":
        if shutil.which("ffmpeg"):
            print(f"Writing {output_path} (ffmpeg, {fps} fps, {dpi} dpi) ...")
            anim.save(str(output_path), writer="ffmpeg", fps=fps, dpi=dpi,
                      savefig_kwargs={"facecolor": DARK_BG})
        else:
            print("ffmpeg not found — saving PNG frames instead.")
            frames_dir = output_path.with_suffix("")
            frames_dir.mkdir(exist_ok=True)
            for i, t in enumerate(times):
                animate(i)
                fig.savefig(frames_dir / f"frame_{i:04d}.png", dpi=dpi,
                            facecolor=DARK_BG, bbox_inches="tight")
                if i % 20 == 0:
                    print(f"  frame {i}/{len(times)}")
            print(f"PNG frames saved to {frames_dir}/")
            print("To assemble into .mp4, install ffmpeg then run:")
            print(f"  ffmpeg -r {fps} -i {frames_dir}/frame_%04d.png -vcodec libx264 -pix_fmt yuv420p {output_path}")
            return
    elif suffix == ".gif":
        print(f"Writing {output_path} (Pillow GIF, {fps} fps) ...")
        anim.save(str(output_path), writer="pillow", fps=fps,
                  savefig_kwargs={"facecolor": DARK_BG})
    else:
        raise ValueError(f"Unsupported output format: {suffix}. Use .mp4 or .gif")

    print(f"Done -> {output_path}")
    plt.close(fig)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    root = Path(__file__).resolve().parents[1]
    default_manifest = root / "examples" / "default-mock" / "manifest.json"

    parser = argparse.ArgumentParser(description="Render simulation side-elevation video.")
    parser.add_argument("manifest", nargs="?", default=str(default_manifest),
                        help="Path to manifest.json (default: examples/default-mock/manifest.json)")
    parser.add_argument("--output", default=None,
                        help="Output file (.mp4 or .gif). Default: <run_dir>/side_view.mp4")
    parser.add_argument("--fps", type=int, default=15, help="Frames per second (default 15)")
    parser.add_argument("--dpi", type=int, default=150, help="Render DPI (default 150)")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        raise FileNotFoundError(f"manifest.json not found: {manifest_path}")

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = manifest_path.parent / "side_view.mp4"

    render(manifest_path, output_path, fps=args.fps, dpi=args.dpi)


if __name__ == "__main__":
    main()
