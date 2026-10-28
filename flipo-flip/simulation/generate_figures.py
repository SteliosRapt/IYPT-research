"""
Generate all figures for the Flipo Flip IYPT 2026 theory paper.

3D figures: Playwright screenshots of the existing Three.js simulation.
2D figures: Matplotlib with LaTeX fonts, output as PDF vectors.

Usage:
    py generate_figures.py
"""

import math
import os
import sys
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, FancyArrowPatch
from matplotlib.lines import Line2D

# ── Paths ──
SCRIPT_DIR = Path(__file__).parent
FIGURES_DIR = SCRIPT_DIR / "figures"
HTML_PATH = SCRIPT_DIR / "flipo_flip_simulation.html"

# ── Default geometric parameters (from simulation) ──
R = 18.0   # bicylinder radius, cm
W = 13.0   # square side, cm
H = 1.0    # prism height, cm

# ── Matplotlib config ──
matplotlib.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
    "text.usetex": True,
    "axes.linewidth": 0.8,
    "lines.linewidth": 1.2,
    "figure.dpi": 150,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})

FIG_WIDTH_SINGLE = 5.5   # inches, single-column
FIG_WIDTH_FULL = 11.0     # inches, full-width


# ═══════════════════════════════════════════════════════════════
#  CORE GEOMETRY (ported from flipo_flip_simulation.html)
# ═══════════════════════════════════════════════════════════════

def model_terms(R, w, h):
    """Compute derived geometry terms. Port of JS modelTerms (line 471)."""
    halfW = w / 2
    halfH = h / 2
    capOffset = math.sqrt(max(1e-6, R * R - halfW * halfW))
    thetaEdge = math.atan2(capOffset, halfW)
    yTopCenter = halfH - capOffset
    yBottomCenter = -halfH + capOffset
    return {
        "halfW": halfW,
        "halfH": halfH,
        "capOffset": capOffset,
        "thetaEdge": thetaEdge,
        "yTopCenter": yTopCenter,
        "yBottomCenter": yBottomCenter,
    }


def max_pure_rolling_angle(R, w, h):
    """Exact geometric limit (no safety margin). Port of JS line 1082."""
    t = model_terms(R, w, h)
    return max(0.0, math.pi / 2 - t["thetaEdge"])


def sample_outline_points(R, w, h, arc_segments=128, edge_segments=20):
    """Sample closed outline in body frame. Port of JS sampleOutlinePoints (line 1053)."""
    t = model_terms(R, w, h)
    points = []
    # Top arc: angle from (pi - thetaEdge) to thetaEdge
    for i in range(arc_segments + 1):
        f = i / arc_segments
        a = (math.pi - t["thetaEdge"]) - (math.pi - 2 * t["thetaEdge"]) * f
        points.append((R * math.cos(a), t["yTopCenter"] + R * math.sin(a)))
    # Right edge
    for i in range(1, edge_segments + 1):
        f = i / edge_segments
        points.append((t["halfW"], t["halfH"] - h * f))
    # Bottom arc: angle from (2*pi - thetaEdge) to (pi + thetaEdge)
    for i in range(arc_segments + 1):
        f = i / arc_segments
        a = (2 * math.pi - t["thetaEdge"]) - (math.pi - 2 * t["thetaEdge"]) * f
        points.append((R * math.cos(a), t["yBottomCenter"] + R * math.sin(a)))
    # Left edge
    for i in range(1, edge_segments + 1):
        f = i / edge_segments
        points.append((-t["halfW"], -t["halfH"] + h * f))
    return points


def world_pose_for_rolling(points, R, w, h, angle):
    """Transform body-frame points to world frame for rolling on bottom cap.
    Port of JS worldPoseForRolling (line 1097).
    World frame: floor at y=0, contact at (R*angle, 0), arc center at (R*angle, R).
    """
    t = model_terms(R, w, h)
    cx_local = 0.0
    cy_local = t["yBottomCenter"]
    cx_world = R * angle
    cy_world = R
    body_angle = -angle
    c = math.cos(body_angle)
    s = math.sin(body_angle)
    result = []
    for px, py in points:
        dx = px - cx_local
        dy = py - cy_local
        xr = c * dx - s * dy + cx_world
        yr = s * dx + c * dy + cy_world
        result.append((xr, yr))
    return result


def world_pose_edge_pivot(points, pivot_x, pivot_y, pivot_body_x, pivot_body_y, body_angle):
    """Rotate body-frame points about a fixed pivot point on the ground.
    pivot_x, pivot_y: world position of the pivot.
    pivot_body_x, pivot_body_y: body-frame position of the pivot point.
    body_angle: total rotation of the body about the pivot.
    """
    c = math.cos(body_angle)
    s = math.sin(body_angle)
    result = []
    for px, py in points:
        dx = px - pivot_body_x
        dy = py - pivot_body_y
        xr = c * dx - s * dy + pivot_x
        yr = s * dx + c * dy + pivot_y
        result.append((xr, yr))
    return result


def body_to_world_neutral(points, R, w, h):
    """Shift body-frame points to world frame at neutral position (phi=0).
    Floor at y=0, bottom arc tangent at origin.
    """
    t = model_terms(R, w, h)
    # Bottom of bottom arc in body frame: y = yBottomCenter - R
    # Shift so this is at y=0:
    shift_y = R - t["yBottomCenter"]
    return [(px, py + shift_y) for px, py in points]


# ═══════════════════════════════════════════════════════════════
#  MATPLOTLIB HELPER
# ═══════════════════════════════════════════════════════════════

def draw_toy_polygon(ax, world_pts, color="#6fa7e5", edgecolor="#1f4f88", lw=1.5, alpha=1.0, zorder=2):
    """Draw a filled toy outline polygon."""
    wx = [p[0] for p in world_pts]
    wy = [p[1] for p in world_pts]
    ax.fill(wx, wy, color=color, edgecolor=edgecolor, linewidth=lw, alpha=alpha, zorder=zorder)


def draw_ground(ax, xmin, xmax):
    """Draw a ground line at y=0."""
    ax.plot([xmin, xmax], [0, 0], color="#495b75", linewidth=2, zorder=1)


def draw_rolling_circle(ax, cx, cy, R):
    """Draw a dashed rolling circle."""
    theta = np.linspace(0, 2 * np.pi, 300)
    ax.plot(cx + R * np.cos(theta), cy + R * np.sin(theta),
            "--", color="#7a8aa2", linewidth=1.0, alpha=0.7)
    # Vertical diameter
    ax.plot([cx, cx], [cy - R, cy + R], "--", color="#7a8aa2", linewidth=0.8, alpha=0.6)


def draw_rotation_axis(ax, x, y, size=8, color="#c53030"):
    """Draw a red cross marking the rotation axis."""
    ax.plot(x, y, "x", color=color, markersize=size, markeredgewidth=2.5, zorder=15)


# ═══════════════════════════════════════════════════════════════
#  PLAYWRIGHT 3D FIGURES
# ═══════════════════════════════════════════════════════════════

def generate_playwright_figures():
    """Capture 3 PNG screenshots from the Three.js simulation."""
    from playwright.sync_api import sync_playwright

    html_content = HTML_PATH.read_text(encoding="utf-8")

    # Inject global exports into the ES module scope
    injection = """
    // === INJECTED FOR FIGURE GENERATION ===
    window.__toyScene = toyScene;
    window.__toyCamera = toyCamera;
    window.__toyRenderer = toyRenderer;
    window.__toyControls = toyControls;
    window.__toyGroup = toyGroup;
    window.__steinScene = steinScene;
    window.__steinCamera = steinCamera;
    window.__steinRenderer = steinRenderer;
    window.__steinControls = steinControls;
    window.__steinGroup = steinGroup;
    window.__THREE = THREE;
    window.__fitCameraToObject = fitCameraToObject;
    window.__TOY_CAMERA_PADDING = TOY_CAMERA_PADDING;
    window.__STEIN_CAMERA_PADDING = STEIN_CAMERA_PADDING;
    window.__params = params;
    window.__ready = true;
    """
    modified_html = html_content.replace(
        "    animate();",
        injection + "\n    animate();",
    )

    file_url = HTML_PATH.resolve().as_uri()

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1200, "height": 900},
            device_scale_factor=3,
        )
        page = context.new_page()

        # Intercept the HTML load and serve modified version
        def route_handler(route):
            route.fulfill(body=modified_html, content_type="text/html")

        page.route(file_url, route_handler)
        page.goto(file_url)
        page.wait_for_function("() => window.__ready === true", timeout=15000)
        page.wait_for_timeout(1000)

        # ── Figure 1: Toy Preview ──
        print("  Capturing fig_toy_preview.png ...")
        page.evaluate("""() => {
            const scene = window.__toyScene;
            const camera = window.__toyCamera;
            const renderer = window.__toyRenderer;
            const controls = window.__toyControls;
            const group = window.__toyGroup;
            const THREE = window.__THREE;
            scene.background = new THREE.Color(0xffffff);
            window.__fitCameraToObject(camera, renderer, controls, group, window.__TOY_CAMERA_PADDING);
            renderer.render(scene, camera);
        }""")
        page.wait_for_timeout(300)
        page.locator("#toyCanvas").screenshot(
            path=str(FIGURES_DIR / "fig_toy_preview.png")
        )

        # ── Figure 2: Steinmetz with Caps ──
        print("  Capturing fig_steinmetz_caps.png ...")
        page.evaluate("""() => {
            const scene = window.__steinScene;
            const camera = window.__steinCamera;
            const renderer = window.__steinRenderer;
            const controls = window.__steinControls;
            const group = window.__steinGroup;
            const THREE = window.__THREE;
            scene.background = new THREE.Color(0xffffff);
            window.__fitCameraToObject(camera, renderer, controls, group, window.__STEIN_CAMERA_PADDING);
            renderer.render(scene, camera);
        }""")
        page.wait_for_timeout(300)
        page.locator("#steinCanvas").screenshot(
            path=str(FIGURES_DIR / "fig_steinmetz_caps.png")
        )

        # ── Figure 3: Steinmetz Side View ──
        print("  Capturing fig_steinmetz_side.png ...")
        page.evaluate("""() => {
            const scene = window.__steinScene;
            const camera = window.__steinCamera;
            const renderer = window.__steinRenderer;
            const controls = window.__steinControls;
            const group = window.__steinGroup;
            const THREE = window.__THREE;
            const R = window.__params.R;

            scene.background = new THREE.Color(0xffffff);

            // Add perfect circle overlay in YZ plane for comparison
            const segments = 256;
            const circlePoints = [];
            for (let i = 0; i <= segments; i++) {
                const a = (i / segments) * Math.PI * 2;
                circlePoints.push(new THREE.Vector3(0, R * Math.cos(a), R * Math.sin(a)));
            }
            const circleGeo = new THREE.BufferGeometry().setFromPoints(circlePoints);
            const circleMat = new THREE.LineBasicMaterial({
                color: 0xff0000, linewidth: 2, depthTest: false
            });
            const circleOutline = new THREE.Line(circleGeo, circleMat);
            circleOutline.renderOrder = 999;
            scene.add(circleOutline);

            // Camera along X-axis looking at origin
            const box = new THREE.Box3().setFromObject(group);
            const size = box.getSize(new THREE.Vector3());
            const fov = THREE.MathUtils.degToRad(camera.fov);
            const dist = (Math.max(size.y, size.z) / 2) / Math.tan(fov / 2) * 1.4;
            camera.position.set(dist, 0, 0);
            camera.lookAt(0, 0, 0);
            camera.near = 0.1;
            camera.far = dist * 10;
            camera.updateProjectionMatrix();
            controls.target.set(0, 0, 0);
            controls.update();
            renderer.render(scene, camera);
        }""")
        page.wait_for_timeout(300)
        page.locator("#steinCanvas").screenshot(
            path=str(FIGURES_DIR / "fig_steinmetz_side.png")
        )

        browser.close()
    print("  Playwright figures done.")


# ═══════════════════════════════════════════════════════════════
#  MATPLOTLIB 2D FIGURES
# ═══════════════════════════════════════════════════════════════

def generate_fig_cross_section():
    """Figure 4: Cross-section with floor at y=0, neutral position.
    Annotations use O_bot (at y=R above floor) for R, d, theta_e.
    """
    print("  Generating fig_cross_section.pdf ...")
    t = model_terms(R, W, H)
    # Shift so bottom arc tangent at (0, 0)
    shift_y = R - t["yBottomCenter"]

    # World-frame positions
    ytop_w = t["yTopCenter"] + shift_y   # ≈ -14.57 (below floor — O_top)
    ybot_w = t["yBottomCenter"] + shift_y  # = R = 18  (above toy — O_bot)
    prism_top = t["halfH"] + shift_y      # top face of prism
    prism_bot = -t["halfH"] + shift_y     # bottom face of prism
    corner_tr = (t["halfW"], prism_bot)   # bottom-right corner (trailing when rolling right)

    fig, ax = plt.subplots(1, 1, figsize=(FIG_WIDTH_SINGLE, 7.0))

    # -- Rectangle --
    rx = [-t["halfW"], t["halfW"], t["halfW"], -t["halfW"], -t["halfW"]]
    ry = [prism_bot, prism_bot, prism_top, prism_top, prism_bot]
    ax.fill(rx, ry, color="#dbeafe", edgecolor="black", linewidth=1.2, zorder=2)

    # -- Top arc --
    theta_top = np.linspace(t["thetaEdge"], math.pi - t["thetaEdge"], 300)
    ax.plot(R * np.cos(theta_top), ytop_w + R * np.sin(theta_top),
            color="#1a5fb4", linewidth=2.2, zorder=3)

    # -- Bottom arc --
    theta_bot = np.linspace(math.pi + t["thetaEdge"], 2 * math.pi - t["thetaEdge"], 300)
    ax.plot(R * np.cos(theta_bot), ybot_w + R * np.sin(theta_bot),
            color="#1a5fb4", linewidth=2.2, zorder=3)

    # -- Dashed parent circle (bottom cap) for context --
    theta_full = np.linspace(0, 2 * math.pi, 400)
    ax.plot(R * np.cos(theta_full), ybot_w + R * np.sin(theta_full),
            "--", color="gray", linewidth=0.5, alpha=0.35, zorder=1)

    # -- Arc centers --
    ax.plot(0, ybot_w, "o", color="red", markersize=5, zorder=5)
    ax.annotate(r"$O_{\mathrm{bot}}$", (0, ybot_w),
                textcoords="offset points", xytext=(8, 4), fontsize=10)
    # O_top is far below floor; mark it lightly
    ax.plot(0, ytop_w, "o", color="red", markersize=3, alpha=0.4, zorder=5)
    ax.annotate(r"$O_{\mathrm{top}}$", (0, ytop_w),
                textcoords="offset points", xytext=(8, 2), fontsize=8, alpha=0.5)

    # -- Dimension: R (from O_bot straight down to contact) --
    x_R = -2.5
    ax.annotate("", xy=(x_R, 0), xytext=(x_R, ybot_w),
                arrowprops=dict(arrowstyle="<->", color="#c53030", lw=1.2))
    ax.text(x_R - 1.2, ybot_w / 2, r"$R$", fontsize=12, color="#c53030",
            ha="center", va="center")

    # -- Dimension: w --
    y_w = prism_bot - 2.0
    ax.annotate("", xy=(t["halfW"], y_w), xytext=(-t["halfW"], y_w),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.0))
    ax.text(0, y_w - 1.2, r"$w$", fontsize=11, ha="center")

    # -- Dimension: h --
    x_h = -t["halfW"] - 2.5
    ax.annotate("", xy=(x_h, prism_top), xytext=(x_h, prism_bot),
                arrowprops=dict(arrowstyle="<->", color="black", lw=1.0))
    ax.text(x_h - 1.2, shift_y, r"$h$", fontsize=11, ha="center", va="center")

    # -- Dimension: d (cap offset: from bottom prism face to O_bot) --
    x_d = 2.0
    ax.annotate("", xy=(x_d, prism_bot), xytext=(x_d, ybot_w),
                arrowprops=dict(arrowstyle="<->", color="#2d7d46", lw=1.2))
    ax.text(x_d + 1.0, (prism_bot + ybot_w) / 2, r"$d$",
            fontsize=12, color="#2d7d46", va="center")

    # -- Angle theta_e (at O_bot, from downward vertical to line to corner) --
    # Line from O_bot to bottom-right corner
    ax.plot([0, corner_tr[0]], [ybot_w, corner_tr[1]],
            "-", color="#888888", linewidth=0.8, zorder=1)
    # Downward vertical from O_bot
    ax.plot([0, 0], [ybot_w, ybot_w - 6.0],
            "-", color="#888888", linewidth=0.8, zorder=1)
    # theta_e arc: angle from downward vertical (-pi/2) to the line to corner
    # Line to corner from O_bot: direction (halfW, corner_y - ybot_w) = (halfW, -(capOffset))
    # angle from +x axis: atan2(-capOffset, halfW) = -thetaEdge
    # Angle from downward vertical (-pi/2) to this line: phi_max (≈21.17°)
    # Draw arc from angle -pi/2 to angle -thetaEdge (sweeping phi_max)
    arc_r = 4.5
    theta_arc = np.linspace(-math.pi / 2, -t["thetaEdge"], 60)
    ax.plot(arc_r * np.cos(theta_arc), ybot_w + arc_r * np.sin(theta_arc),
            "-", color="#cc6600", linewidth=2.0, zorder=4)
    # Label
    ax.text(1.8, ybot_w - 5.5, r"$\theta_e$", fontsize=12, color="#cc6600")

    # -- Floor line --
    draw_ground(ax, -R - 3, R + 3)

    # -- Contact point --
    ax.plot(0, 0, "o", color="#c81f1f", markersize=6, zorder=10)
    ax.annotate("Contact", (0, 0), textcoords="offset points",
                xytext=(6, -14), fontsize=8, color="#c81f1f")

    # -- CoM / prism center --
    ax.plot(0, shift_y, "o", color="black", markersize=3, zorder=5)
    ax.annotate("CoM", (0, shift_y),
                textcoords="offset points", xytext=(6, -10), fontsize=8)

    # -- Corner labels --
    ax.annotate(r"$\bigl(-\frac{w}{2},\,-\frac{h}{2}\bigr)$",
                (-t["halfW"], prism_bot),
                textcoords="offset points", xytext=(-52, -14), fontsize=7)
    ax.annotate(r"$\bigl(\frac{w}{2},\,-\frac{h}{2}\bigr)$",
                corner_tr,
                textcoords="offset points", xytext=(5, -14), fontsize=7)
    ax.annotate(r"$\bigl(\frac{w}{2},\,\frac{h}{2}\bigr)$",
                (t["halfW"], prism_top),
                textcoords="offset points", xytext=(5, 5), fontsize=7)

    ax.set_aspect("equal")
    ax.set_xlim(-R - 4, R + 4)
    ax.set_ylim(-4, ybot_w + 5)
    ax.axis("off")
    fig.savefig(FIGURES_DIR / "fig_cross_section.pdf")
    plt.close(fig)


def generate_fig_2d_side_view():
    """Figure 5: 2D side view at neutral position (phi=0)."""
    print("  Generating fig_2d_side_view.pdf ...")
    t = model_terms(R, W, H)
    local_pts = sample_outline_points(R, W, H)
    world_pts = world_pose_for_rolling(local_pts, R, W, H, 0.0)

    fig, ax = plt.subplots(1, 1, figsize=(FIG_WIDTH_SINGLE, 4.5))

    pad = 6
    draw_ground(ax, -R - pad, R + pad)
    draw_rolling_circle(ax, 0, R, R)
    draw_toy_polygon(ax, world_pts)

    # Contact point
    ax.plot(0, 0, "o", color="#c81f1f", markersize=6, zorder=10)
    ax.annotate("Contact point", (0, 0),
                textcoords="offset points", xytext=(8, -14), fontsize=8, color="#c81f1f")

    # Circle center
    ax.plot(0, R, "o", color="black", markersize=5, zorder=10)
    ax.annotate("Arc centre", (0, R),
                textcoords="offset points", xytext=(8, 5), fontsize=8)

    ax.set_aspect("equal")
    ax.set_xlim(-R - pad, R + pad)
    ax.set_ylim(-2, 2 * R + pad)
    ax.axis("off")
    fig.savefig(FIGURES_DIR / "fig_2d_side_view.pdf")
    plt.close(fig)


def generate_fig_rotation_phases():
    """Figure 6: Four subplots showing rotation axis instances.

    Rolling rightward on bottom arc. Geometry:
    - At phi_max, trailing corner (+halfW, -halfH) touches the ground.
    - Trailing pivot: body rotates from -phi_max to -pi/2 (sweep = thetaEdge).
    - Flat on ground: right edge (h-tall) lies on floor, body angle = -pi/2.
    - Leading pivot: pivot at (+halfW, +halfH), body goes from -pi/2 to -(pi - phi_max).
    """
    print("  Generating fig_rotation_phases.pdf ...")
    t = model_terms(R, W, H)
    phi_max = max_pure_rolling_angle(R, W, H)
    theta_e = t["thetaEdge"]  # ~68.83 deg — the edge-pivot sweep angle
    local_pts = sample_outline_points(R, W, H)

    fig, axes = plt.subplots(1, 4, figsize=(FIG_WIDTH_FULL + 2, 3.8))

    # Trailing corner body frame coords
    trailing_body = (t["halfW"], -t["halfH"])

    # -- (a) Pure patch rolling at phi = phi_max * 0.5 --
    angle_a = phi_max * 0.5
    pts_a = world_pose_for_rolling(local_pts, R, W, H, angle_a)
    cx_a = R * angle_a
    xmin_a = min(p[0] for p in pts_a)
    xmax_a = max(p[0] for p in pts_a)
    pad_a = 3
    draw_ground(axes[0], xmin_a - pad_a, xmax_a + pad_a)
    draw_toy_polygon(axes[0], pts_a)
    draw_rolling_circle(axes[0], cx_a, R, R)
    draw_rotation_axis(axes[0], cx_a, 0)
    axes[0].set_title(r"(a) Patch rolling", fontsize=9)
    axes[0].annotate("Rotation axis\n(contact point)", (cx_a, 0),
                     textcoords="offset points", xytext=(6, -22), fontsize=6, color="#c53030")
    axes[0].set_aspect("equal")
    axes[0].set_xlim(xmin_a - pad_a, xmax_a + pad_a)
    ymax_a = max(p[1] for p in pts_a)
    axes[0].set_ylim(-2, ymax_a + pad_a)
    axes[0].axis("off")

    # -- (b) Trailing-edge pivot (shown mid-pivot) --
    # At phi_max, trailing corner hits the ground. Show 40% through the pivot.
    trail_world = world_pose_for_rolling([trailing_body], R, W, H, phi_max)[0]
    x_trail = trail_world[0]  # = R * phi_max, y = 0
    # Body angle goes from -phi_max to -pi/2 during trailing pivot.
    # At 40% through: body_angle = -phi_max - 0.4 * theta_e
    trail_pivot_angle = -phi_max - 0.4 * theta_e
    pts_b = world_pose_edge_pivot(local_pts, x_trail, 0.0,
                                  t["halfW"], -t["halfH"], trail_pivot_angle)
    xmin_b = min(p[0] for p in pts_b)
    xmax_b = max(p[0] for p in pts_b)
    pad_b = 3
    draw_ground(axes[1], xmin_b - pad_b, xmax_b + pad_b)
    draw_toy_polygon(axes[1], pts_b)
    draw_rotation_axis(axes[1], x_trail, 0)
    axes[1].set_title(r"(b) Trailing-edge pivot", fontsize=9)
    axes[1].annotate("Rotation axis\n(trailing corner)", (x_trail, 0),
                     textcoords="offset points", xytext=(6, -22), fontsize=6, color="#c53030")
    axes[1].set_aspect("equal")
    axes[1].set_xlim(xmin_b - pad_b, xmax_b + pad_b)
    ymax_b = max(p[1] for p in pts_b)
    axes[1].set_ylim(-2, ymax_b + pad_b)
    axes[1].axis("off")

    # -- (c) Flat face on ground (pivot transfer instant) --
    # Body angle = -pi/2. The right edge (h-tall) lies flat on the ground.
    # Trailing corner (+halfW, -halfH) at (x_trail, 0).
    flat_angle = -math.pi / 2
    flat_pts = world_pose_edge_pivot(local_pts, x_trail, 0.0,
                                     t["halfW"], -t["halfH"], flat_angle)
    xmin_c = min(p[0] for p in flat_pts)
    xmax_c = max(p[0] for p in flat_pts)
    pad_c = 3
    draw_ground(axes[2], xmin_c - pad_c, xmax_c + pad_c)
    draw_toy_polygon(axes[2], flat_pts)
    axes[2].set_title(r"(c) Flat on ground", fontsize=9)
    axes[2].annotate("No unique rotation axis\n(pivot transfer instant)",
                     ((xmin_c + xmax_c) / 2, max(p[1] for p in flat_pts) + 1.5),
                     fontsize=6, ha="center", color="#666666")
    axes[2].set_aspect("equal")
    axes[2].set_xlim(xmin_c - pad_c, xmax_c + pad_c)
    ymax_c = max(p[1] for p in flat_pts)
    axes[2].set_ylim(-2, ymax_c + pad_c)
    axes[2].axis("off")

    # -- (d) Leading-edge pivot --
    # Leading corner is (+halfW, +halfH) in body frame.
    # When flat (body_angle = -pi/2), leading corner is at (x_trail + H, 0).
    x_lead = x_trail + H
    # Body angle goes from -pi/2 to -(pi - phi_max) during leading pivot.
    # Show 40% through: body_angle = -pi/2 - 0.4 * theta_e
    lead_pivot_angle = -math.pi / 2 - 0.4 * theta_e
    pts_d = world_pose_edge_pivot(local_pts, x_lead, 0.0,
                                  t["halfW"], t["halfH"], lead_pivot_angle)
    xmin_d = min(p[0] for p in pts_d)
    xmax_d = max(p[0] for p in pts_d)
    pad_d = 3
    draw_ground(axes[3], xmin_d - pad_d, xmax_d + pad_d)
    draw_toy_polygon(axes[3], pts_d)
    draw_rotation_axis(axes[3], x_lead, 0)
    axes[3].set_title(r"(d) Leading-edge pivot", fontsize=9)
    axes[3].annotate("Rotation axis\n(leading corner)", (x_lead, 0),
                     textcoords="offset points", xytext=(6, -22), fontsize=6, color="#c53030")
    axes[3].set_aspect("equal")
    axes[3].set_xlim(xmin_d - pad_d, xmax_d + pad_d)
    ymax_d = max(p[1] for p in pts_d)
    axes[3].set_ylim(-2, ymax_d + pad_d)
    axes[3].axis("off")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_rotation_phases.pdf")
    plt.close(fig)


def generate_fig_critical_angles():
    """Figure 7: Two panels showing theta_e and phi_max."""
    print("  Generating fig_critical_angles.pdf ...")
    t = model_terms(R, W, H)
    phi_max = max_pure_rolling_angle(R, W, H)
    shift_y = R - t["yBottomCenter"]

    # World positions
    ybot_w = R  # O_bot world y
    prism_top = t["halfH"] + shift_y
    prism_bot = -t["halfH"] + shift_y
    corner_br = (t["halfW"], prism_bot)  # bottom-right corner

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(FIG_WIDTH_FULL, 5.5))

    # ── Left panel: theta_e at O_bot ──
    # Show bottom portion: prism rectangle, bottom arc, O_bot, theta_e angle

    # Rectangle
    rx = [-t["halfW"], t["halfW"], t["halfW"], -t["halfW"], -t["halfW"]]
    ry = [prism_bot, prism_bot, prism_top, prism_top, prism_bot]
    ax1.fill(rx, ry, color="#dbeafe", alpha=0.3, edgecolor="black", linewidth=1.0, zorder=2)

    # Bottom arc
    theta_bot = np.linspace(math.pi + t["thetaEdge"], 2 * math.pi - t["thetaEdge"], 300)
    ax1.plot(R * np.cos(theta_bot), ybot_w + R * np.sin(theta_bot),
             color="#1a5fb4", linewidth=2.2, zorder=3)

    # Dashed parent circle (bottom cap)
    theta_full = np.linspace(0, 2 * math.pi, 400)
    ax1.plot(R * np.cos(theta_full), ybot_w + R * np.sin(theta_full),
             "--", color="gray", linewidth=0.5, alpha=0.35)

    # O_bot center
    ax1.plot(0, ybot_w, "o", color="red", markersize=6, zorder=5)
    ax1.annotate(r"$O_{\mathrm{bot}}$", (0, ybot_w),
                 textcoords="offset points", xytext=(8, 4), fontsize=11)

    # Line from O_bot to bottom-right corner
    ax1.plot([0, corner_br[0]], [ybot_w, corner_br[1]],
             "-", color="#555555", linewidth=1.0, zorder=1)
    # Downward vertical from O_bot
    ax1.plot([0, 0], [ybot_w, ybot_w - 7],
             "-", color="#555555", linewidth=1.0, zorder=1)

    # theta_e angle arc: from downward vertical (-pi/2) to line to corner (-thetaEdge)
    # This sweeps an angle of phi_max = pi/2 - thetaEdge ≈ 21.17°
    arc_r = 5.0
    theta_arc = np.linspace(-math.pi / 2, -t["thetaEdge"], 80)
    ax1.plot(arc_r * np.cos(theta_arc), ybot_w + arc_r * np.sin(theta_arc),
             "-", color="#cc6600", linewidth=2.2, zorder=4)
    # Arrow at end
    ax1.annotate("", xy=(arc_r * math.cos(-t["thetaEdge"]),
                         ybot_w + arc_r * math.sin(-t["thetaEdge"])),
                 xytext=(arc_r * math.cos(-t["thetaEdge"] - 0.05),
                         ybot_w + arc_r * math.sin(-t["thetaEdge"] - 0.05)),
                 arrowprops=dict(arrowstyle="->", color="#cc6600", lw=1.5))
    ax1.text(2.0, ybot_w - 6.0, r"$\theta_e$", fontsize=14, color="#cc6600")

    # R label (from O_bot to corner)
    ax1.annotate("", xy=corner_br, xytext=(0, ybot_w),
                 arrowprops=dict(arrowstyle="<->", color="#c53030", lw=1.0))
    mid_x = corner_br[0] / 2
    mid_y = (ybot_w + corner_br[1]) / 2
    ax1.text(mid_x + 1.0, mid_y + 0.8, r"$R$", fontsize=12, color="#c53030")

    # Floor
    draw_ground(ax1, -R - 3, R + 3)

    ax1.set_title(r"Edge angle $\theta_e$", fontsize=11)
    ax1.set_aspect("equal")
    ax1.set_xlim(-R - 2, R + 2)
    ax1.set_ylim(-3, ybot_w + 5)
    ax1.axis("off")

    # ── Right panel: phi_max rolling range ──
    draw_ground(ax2, -R - 5, R + 5)
    draw_rolling_circle(ax2, 0, R, R)

    # Draw toy at neutral
    local_pts = sample_outline_points(R, W, H)
    world_pts = world_pose_for_rolling(local_pts, R, W, H, 0.0)
    draw_toy_polygon(ax2, world_pts, alpha=0.3)

    # Draw toy at phi_max (ghost)
    world_pts_max = world_pose_for_rolling(local_pts, R, W, H, phi_max)
    draw_toy_polygon(ax2, world_pts_max, color="#a0c4e8", edgecolor="#4a7aaa",
                     alpha=0.3, lw=1.0)

    # Draw toy at -phi_max (ghost)
    world_pts_min = world_pose_for_rolling(local_pts, R, W, H, -phi_max)
    draw_toy_polygon(ax2, world_pts_min, color="#a0c4e8", edgecolor="#4a7aaa",
                     alpha=0.3, lw=1.0)

    # Arc contact range on ground
    ax2.plot([R * (-phi_max), R * phi_max], [0, 0],
             "-", color="#c53030", linewidth=4, alpha=0.4, zorder=3)
    ax2.plot(R * phi_max, 0, "o", color="#c53030", markersize=6, zorder=10)
    ax2.plot(-R * phi_max, 0, "o", color="#c53030", markersize=6, zorder=10)
    ax2.plot(0, 0, "o", color="black", markersize=4, zorder=10)

    # phi_max angle arc at circle center
    arc_r2 = R * 0.35
    phi_arc = np.linspace(-math.pi / 2, -math.pi / 2 + phi_max, 60)
    ax2.plot(arc_r2 * np.cos(phi_arc), R + arc_r2 * np.sin(phi_arc),
             "-", color="#c53030", linewidth=2.0)
    ax2.annotate("", xy=(arc_r2 * math.cos(-math.pi / 2 + phi_max),
                         R + arc_r2 * math.sin(-math.pi / 2 + phi_max)),
                 xytext=(arc_r2 * math.cos(-math.pi / 2 + phi_max - 0.05),
                         R + arc_r2 * math.sin(-math.pi / 2 + phi_max - 0.05)),
                 arrowprops=dict(arrowstyle="->", color="#c53030", lw=1.5))
    ax2.text(arc_r2 * 0.7, R - arc_r2 * 0.85, r"$\varphi_{\max}$",
             fontsize=13, color="#c53030")

    ax2.set_title(r"Maximum rolling angle $\varphi_{\max}$", fontsize=11)
    ax2.set_aspect("equal")
    ax2.set_xlim(-R - 5, R + 5)
    ax2.set_ylim(-3, 2 * R + 5)
    ax2.axis("off")

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_critical_angles.pdf")
    plt.close(fig)


def world_pose_for_top_arc_rolling(points, R, w, h, phi_top, x_start):
    """Transform body-frame points to world frame for rolling on top cap.

    At phi_top=0, the top arc corner (+halfW, +halfH) is on the ground at x_start.
    The body angle at phi_top=0 is -(pi - phi_max), continuing to rotate by -phi_top.
    The top arc center tracks at height R above the ground.
    """
    t = model_terms(R, w, h)
    phi_max_val = max_pure_rolling_angle(R, w, h)
    cx_local = 0.0
    cy_local = t["yTopCenter"]
    cx_world = x_start + R * phi_top
    cy_world = R
    body_angle = -(math.pi - phi_max_val) - phi_top
    c = math.cos(body_angle)
    s = math.sin(body_angle)
    result = []
    for px, py in points:
        dx = px - cx_local
        dy = py - cy_local
        xr = c * dx - s * dy + cx_world
        yr = s * dx + c * dy + cy_world
        result.append((xr, yr))
    return result


def generate_fig_rolling_composite():
    """Figure 8: 8 snapshots through one half-revolution, overlaid.

    Half-revolution sequence (rolling rightward on bottom arc):
      1. Bottom arc at phi=0 (neutral)
      2. Bottom arc at phi=phi_max/2
      3. Bottom arc at phi=phi_max (arc end, trailing corner on ground)
      4. Trailing pivot ~50% (body_angle = -phi_max - 0.5*thetaEdge)
      5. Flat on ground (body_angle = -pi/2, right edge on floor)
      6. Leading pivot ~50% (body_angle = -pi/2 - 0.5*thetaEdge)
      7. Leading pivot complete (top arc tangent, body_angle = -(pi - phi_max))
      8. Top arc rolling at phi_top = phi_max/2
    """
    print("  Generating fig_rolling_composite.pdf ...")
    t = model_terms(R, W, H)
    phi_max = max_pure_rolling_angle(R, W, H)
    theta_e = t["thetaEdge"]
    local_pts = sample_outline_points(R, W, H)

    fig, ax = plt.subplots(1, 1, figsize=(FIG_WIDTH_FULL + 2, 4.5))

    # Key world positions
    trailing_body = (t["halfW"], -t["halfH"])
    trail_world = world_pose_for_rolling([trailing_body], R, W, H, phi_max)[0]
    x_trail = trail_world[0]  # = R * phi_max
    x_lead = x_trail + H      # leading corner when flat

    # Color gradient
    n_snapshots = 8
    cmap = plt.cm.Blues
    colors = [cmap(0.25 + 0.65 * i / (n_snapshots - 1)) for i in range(n_snapshots)]
    alphas = np.linspace(0.25, 0.75, n_snapshots)

    all_xs = []
    all_ys = []

    def add_snapshot(idx, pts, label=None):
        draw_toy_polygon(ax, pts, color=colors[idx], edgecolor="black",
                         lw=0.6, alpha=alphas[idx], zorder=2 + idx)
        all_xs.extend([p[0] for p in pts])
        all_ys.extend([p[1] for p in pts])

    # 1. phi=0 (neutral on bottom arc)
    add_snapshot(0, world_pose_for_rolling(local_pts, R, W, H, 0.0))

    # 2. phi=phi_max/2 (mid arc rolling)
    add_snapshot(1, world_pose_for_rolling(local_pts, R, W, H, phi_max * 0.5))

    # 3. phi=phi_max (arc end, trailing corner on ground)
    add_snapshot(2, world_pose_for_rolling(local_pts, R, W, H, phi_max))

    # 4. Trailing edge pivot ~50% through
    trail_body_angle = -phi_max - 0.5 * theta_e
    add_snapshot(3, world_pose_edge_pivot(local_pts, x_trail, 0.0,
                                         t["halfW"], -t["halfH"], trail_body_angle))

    # 5. Flat on ground (body angle = -pi/2)
    add_snapshot(4, world_pose_edge_pivot(local_pts, x_trail, 0.0,
                                         t["halfW"], -t["halfH"], -math.pi / 2))

    # 6. Leading edge pivot ~50% through
    lead_body_angle = -math.pi / 2 - 0.5 * theta_e
    add_snapshot(5, world_pose_edge_pivot(local_pts, x_lead, 0.0,
                                         t["halfW"], t["halfH"], lead_body_angle))

    # 7. Leading edge pivot complete (top arc tangent to ground)
    lead_body_full = -(math.pi - phi_max)
    add_snapshot(6, world_pose_edge_pivot(local_pts, x_lead, 0.0,
                                         t["halfW"], t["halfH"], lead_body_full))

    # 8. Rolling on top arc at phi_top = phi_max/2
    add_snapshot(7, world_pose_for_top_arc_rolling(local_pts, R, W, H,
                                                    phi_max * 0.5, x_lead))

    x_pad = 5
    y_pad = 5
    xmin = min(all_xs) - x_pad
    xmax = max(all_xs) + x_pad
    ymax = max(all_ys) + y_pad

    draw_ground(ax, xmin, xmax)

    # Phase annotation
    cx_1 = sum(p[0] for p in world_pose_for_rolling(local_pts, R, W, H, 0.0)) / len(local_pts)
    ax.annotate(r"$\varphi = 0$", (cx_1, -1.5), fontsize=7, ha="center", color="#444444")

    ax.set_aspect("equal")
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(-2.5, ymax)
    ax.axis("off")

    fig.savefig(FIGURES_DIR / "fig_rolling_composite.pdf")
    plt.close(fig)


def generate_fig_com_height():
    """Figure 9: CoM height vs cumulative angle through one full cycle.
    Zero friction, zero restitution. Shows geometric energy loss from
    angular momentum conservation at the trailing-to-leading pivot transfer.

    Half-revolution phases (cumulative angle in brackets):
      Phase 1: Bottom arc rolling   phi: 0 → phi_max            [0, phi_max]
      Phase 2: Trailing-edge pivot  alpha: 0 → theta_e          [phi_max, phi_max + theta_e]
      Phase 3: Leading-edge pivot   alpha: 0 → theta_e          [phi_max + theta_e, phi_max + 2*theta_e]
      Phase 4: Top arc rolling      phi_top: 0 → phi_max        [phi_max + 2*theta_e, pi]
    Total: phi_max + theta_e + theta_e + phi_max = 2*(phi_max + theta_e) = pi  ✓
    """
    print("  Generating fig_com_height.pdf ...")
    t = model_terms(R, W, H)
    phi_max = max_pure_rolling_angle(R, W, H)
    theta_e = t["thetaEdge"]  # ≈ 68.83° — the edge-pivot sweep angle

    # Vector from bottom arc center to CoM in body frame: (0, -yBottomCenter)
    d_cm_y = -t["yBottomCenter"]  # = halfH - capOffset ≈ -16.286

    # Distance from CoM (0,0) to each corner in body frame
    ell = math.sqrt(t["halfW"] ** 2 + t["halfH"] ** 2)  # ≈ 6.519

    n = 300

    # ── Phase 1: Bottom arc rolling (phi: 0 → phi_max) ──
    # Arc center at (R*phi, R). CoM at (*, R + d_cm_y * cos(phi))
    phi_1 = np.linspace(0, phi_max, n)
    y_1 = R + d_cm_y * np.cos(phi_1)
    # At phi=0: y = 18 + (-16.286)*1 = 1.714
    # At phi_max: y = 18 + (-16.286)*cos(21.17°) ≈ 2.814

    # ── Phase 2: Trailing-edge pivot (alpha: 0 → theta_e) ──
    # Pivot: trailing corner (+halfW, -halfH) on ground at (x_trail, 0).
    # Body angle: -(phi_max + alpha), going from -phi_max to -pi/2.
    # CoM height: yr = -halfW * sin(body_angle) - halfH * cos(body_angle) + 0
    # = halfW * sin(phi_max + alpha) + halfH * cos(phi_max + alpha)
    alpha_2 = np.linspace(0, theta_e, n)
    y_2 = t["halfW"] * np.sin(phi_max + alpha_2) + t["halfH"] * np.cos(phi_max + alpha_2)
    # At alpha=0: halfW*sin(phi_max) + halfH*cos(phi_max) ≈ 2.348 + 0.466 = 2.814 ✓
    # At alpha=theta_e: halfW*sin(pi/2) + halfH*cos(pi/2) = halfW = 6.5 ✓

    # ── Phase 3: Leading-edge pivot (alpha: 0 → theta_e) ──
    # Pivot: leading corner (+halfW, +halfH) on ground at (x_lead, 0).
    # Body angle: -(pi/2 + alpha), going from -pi/2 to -(pi - phi_max).
    # CoM height: yr = -halfW * sin(body_angle) - halfH * cos(body_angle)
    # = halfW * sin(pi/2 + alpha) + halfH * cos(pi/2 + alpha)
    # = halfW * cos(alpha) - halfH * sin(alpha)
    # WAIT: Let me derive carefully using the world_pose_edge_pivot formula.
    # yr = sin(body_angle)*(0 - halfW) + cos(body_angle)*(0 - halfH) + 0
    # body_angle = -(pi/2 + alpha)
    # sin(-(pi/2+alpha)) = -cos(alpha)
    # cos(-(pi/2+alpha)) = -sin(alpha)
    # yr = (-cos(alpha))*(-halfW) + (-sin(alpha))*(-halfH)
    # = halfW*cos(alpha) + halfH*sin(alpha)
    alpha_3 = np.linspace(0, theta_e, n)
    y_3 = t["halfW"] * np.cos(alpha_3) + t["halfH"] * np.sin(alpha_3)
    # At alpha=0: halfW = 6.5 ✓ (matches end of trailing pivot)
    # At alpha=theta_e: halfW*cos(theta_e) + halfH*sin(theta_e) ≈ 2.348 + 0.466 = 2.814 ✓

    # ── Phase 4: Top arc rolling (phi_top: 0 → phi_max) ──
    # Top arc center at (*, R). Body angle = -(pi - phi_max) - phi_top.
    # CoM height: yr = cos(body_angle) * (0 - yTopCenter) + R
    # = (0 - yTopCenter) * cos(-(pi - phi_max) - phi_top) + R
    # cos(-(pi-phi_max)-phi_top) = cos(pi - phi_max + phi_top) = -cos(phi_max - phi_top)
    # yr = (-yTopCenter) * (-cos(phi_max - phi_top)) + R
    # = yTopCenter * cos(phi_max - phi_top) + R
    # = (halfH - capOffset) * cos(phi_max - phi_top) + R
    # = d_cm_y_top * cos(phi_max - phi_top) + R  where d_cm_y_top = halfH - capOffset = d_cm_y
    # WAIT: actually d_cm_y = halfH - capOffset = -16.286 (same value!)
    # yr = (-16.286) * cos(phi_max - phi_top) + 18
    # Wait, let me be more explicit:
    # yr = (0 - yTopCenter) * cos(body_angle) + R  ... no.
    # From the rolling transform:
    # dy = py_cm - cy_local = 0 - yTopCenter = -yTopCenter = -(halfH - capOffset) = capOffset - halfH
    # yr = sin(body_angle)*dx + cos(body_angle)*dy + R = cos(body_angle)*(-yTopCenter) + R
    # = (-yTopCenter) * cos(-(pi - phi_max + phi_top)) + R
    # -yTopCenter = capOffset - halfH ≈ 16.286
    # cos(-(pi - phi_max + phi_top)) = cos(pi - phi_max + phi_top) = -cos(phi_max - phi_top)
    # yr = 16.286 * (-cos(phi_max - phi_top)) + 18 = -16.286*cos(phi_max - phi_top) + 18
    phi_4 = np.linspace(0, phi_max, n)
    y_4 = -(-t["yTopCenter"]) * np.cos(phi_max - phi_4) + R
    # Equivalently: y_4 = -(capOffset - halfH) * cos(phi_max - phi_top) + R
    # At phi_top=0: -16.286*cos(phi_max) + 18 ≈ -15.186 + 18 = 2.814 ✓
    # At phi_top=phi_max: -16.286*cos(0) + 18 = 1.714 ✓

    # ── Stitch cumulative angles ──
    cumul_1 = phi_1                          # [0, phi_max]
    cumul_2 = phi_max + alpha_2              # [phi_max, phi_max + theta_e]
    cumul_3 = phi_max + theta_e + alpha_3    # [phi_max + theta_e, phi_max + 2*theta_e]
    cumul_4 = phi_max + 2 * theta_e + phi_4  # [phi_max + 2*theta_e, pi]

    all_cumul = np.concatenate([cumul_1, cumul_2[1:], cumul_3[1:], cumul_4[1:]])
    all_y = np.concatenate([y_1, y_2[1:], y_3[1:], y_4[1:]])

    # Convert to degrees
    all_cumul_deg = np.degrees(all_cumul)

    fig, ax = plt.subplots(1, 1, figsize=(FIG_WIDTH_SINGLE + 1, 4.0))

    ax.plot(all_cumul_deg, all_y, "-", color="#1a5fb4", linewidth=1.8)

    # Phase boundaries (vertical dashed lines)
    b1 = phi_max
    b2 = phi_max + theta_e
    b3 = phi_max + 2 * theta_e
    for b, label in [(b1, "Arc end /\nTrailing pivot"),
                     (b2, "Flat on ground /\nLeading pivot"),
                     (b3, "Next arc begins")]:
        ax.axvline(x=np.degrees(b), color="#c53030", linestyle="--", linewidth=0.8, alpha=0.7)
        ax.text(np.degrees(b) + 0.5, 0.5, label,
                fontsize=6.5, color="#c53030", va="bottom", rotation=90)

    # Phase labels at top
    phase_mids = [
        cumul_1[-1] / 2,
        phi_max + theta_e / 2,
        phi_max + theta_e + theta_e / 2,
        phi_max + 2 * theta_e + phi_max / 2,
    ]
    phase_names = ["Bottom arc\nrolling", "Trailing\npivot", "Leading\npivot", "Top arc\nrolling"]
    y_label = max(all_y) + 0.5
    for mid, name in zip(phase_mids, phase_names):
        ax.text(np.degrees(mid), y_label, name,
                fontsize=7, ha="center", va="bottom", color="#444444")

    # Annotate the flat-on-ground peak
    ax.annotate(r"$y_{\mathrm{cm}} = w/2$",
                xy=(np.degrees(b2), t["halfW"]),
                textcoords="offset points", xytext=(12, 5),
                fontsize=8, color="#2d7d46",
                arrowprops=dict(arrowstyle="->", color="#2d7d46", lw=0.8))

    ax.set_xlabel(r"Cumulative rotation angle (degrees)")
    ax.set_ylabel(r"Centre-of-mass height (cm)")
    ax.grid(True, alpha=0.25)
    ax.set_xlim(0, 180)
    ax.set_ylim(0, max(all_y) + 2)

    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "fig_com_height.pdf")
    plt.close(fig)


# ═══════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    FIGURES_DIR.mkdir(exist_ok=True)
    print(f"Output directory: {FIGURES_DIR}")

    # Derived values for reference
    t = model_terms(R, W, H)
    phi_max = max_pure_rolling_angle(R, W, H)
    print(f"R={R}, w={W}, h={H}")
    print(f"capOffset = {t['capOffset']:.3f}")
    print(f"thetaEdge = {math.degrees(t['thetaEdge']):.2f} deg")
    print(f"phi_max   = {math.degrees(phi_max):.2f} deg")
    print(f"yTopCenter = {t['yTopCenter']:.3f}")
    print(f"yBottomCenter = {t['yBottomCenter']:.3f}")
    print()

    # 3D figures via Playwright
    print("=== Playwright 3D Figures ===")
    generate_playwright_figures()
    print()

    # 2D figures via matplotlib
    print("=== Matplotlib 2D Figures ===")
    generate_fig_cross_section()
    generate_fig_2d_side_view()
    generate_fig_rotation_phases()
    generate_fig_critical_angles()
    generate_fig_rolling_composite()
    generate_fig_com_height()
    print()

    print("All 9 figures generated successfully.")
    for f in sorted(FIGURES_DIR.iterdir()):
        size = f.stat().st_size
        print(f"  {f.name:40s} {size:>10,} bytes")


if __name__ == "__main__":
    main()
