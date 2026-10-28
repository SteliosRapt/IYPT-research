"""Mesh and STL helpers for solver-consumable geometry assets."""

from __future__ import annotations

import math
from typing import Any


Mesh = tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]


def _cross(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _sub(left: tuple[float, float, float], right: tuple[float, float, float]) -> tuple[float, float, float]:
    return (left[0] - right[0], left[1] - right[1], left[2] - right[2])


def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    length = math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)
    if length <= 1e-12:
        return (0.0, 0.0, 0.0)
    return (vector[0] / length, vector[1] / length, vector[2] / length)


def combine_meshes(meshes: list[Mesh]) -> Mesh:
    points: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []

    for mesh_points, mesh_triangles in meshes:
        offset = len(points)
        points.extend(mesh_points)
        triangles.extend((a + offset, b + offset, c + offset) for a, b, c in mesh_triangles)

    return points, triangles


def box_mesh(center: tuple[float, float, float], size: tuple[float, float, float]) -> Mesh:
    cx, cy, cz = center
    sx, sy, sz = size
    hx = sx / 2
    hy = sy / 2
    hz = sz / 2
    points = [
        (cx - hx, cy - hy, cz - hz),
        (cx + hx, cy - hy, cz - hz),
        (cx + hx, cy + hy, cz - hz),
        (cx - hx, cy + hy, cz - hz),
        (cx - hx, cy - hy, cz + hz),
        (cx + hx, cy - hy, cz + hz),
        (cx + hx, cy + hy, cz + hz),
        (cx - hx, cy + hy, cz + hz),
    ]
    triangles = [
        (0, 1, 2),
        (0, 2, 3),
        (4, 6, 5),
        (4, 7, 6),
        (0, 4, 5),
        (0, 5, 1),
        (1, 5, 6),
        (1, 6, 2),
        (2, 6, 7),
        (2, 7, 3),
        (3, 7, 4),
        (3, 4, 0),
    ]
    return points, triangles


def triangular_prism_mesh(center: tuple[float, float, float], base: float, height: float, depth: float) -> Mesh:
    cx, cy, cz = center
    half_depth = depth / 2
    points = [
        (cx - base / 2, cy, cz - half_depth),
        (cx + base / 2, cy, cz - half_depth),
        (cx, cy + height, cz - half_depth),
        (cx - base / 2, cy, cz + half_depth),
        (cx + base / 2, cy, cz + half_depth),
        (cx, cy + height, cz + half_depth),
    ]
    triangles = [
        (0, 1, 2),
        (3, 5, 4),
        (0, 3, 4),
        (0, 4, 1),
        (1, 4, 5),
        (1, 5, 2),
        (2, 5, 3),
        (2, 3, 0),
    ]
    return points, triangles


def rect_plane_mesh(
    *,
    axis: str,
    coordinate: float,
    range_a: tuple[float, float],
    range_b: tuple[float, float],
    normal_positive: bool,
) -> Mesh:
    a0, a1 = range_a
    b0, b1 = range_b
    if axis == "x":
        points = [
            (coordinate, a0, b0),
            (coordinate, a1, b0),
            (coordinate, a1, b1),
            (coordinate, a0, b1),
        ]
    elif axis == "y":
        points = [
            (a0, coordinate, b0),
            (a1, coordinate, b0),
            (a1, coordinate, b1),
            (a0, coordinate, b1),
        ]
    else:
        points = [
            (a0, b0, coordinate),
            (a1, b0, coordinate),
            (a1, b1, coordinate),
            (a0, b1, coordinate),
        ]
    triangles = [(0, 1, 2), (0, 2, 3)] if normal_positive else [(0, 2, 1), (0, 3, 2)]
    return points, triangles


def framed_top_patch_mesh(
    *,
    center_x: float,
    center_y: float,
    outer_size: tuple[float, float],
    inner_size: tuple[float, float],
) -> Mesh:
    outer_x, outer_z = outer_size
    inner_x, inner_z = inner_size
    half_outer_x = outer_x / 2
    half_outer_z = outer_z / 2
    half_inner_x = inner_x / 2
    half_inner_z = inner_z / 2

    return combine_meshes(
        [
            rect_plane_mesh(
                axis="y",
                coordinate=center_y,
                range_a=(center_x - half_outer_x, center_x - half_inner_x),
                range_b=(-half_outer_z, half_outer_z),
                normal_positive=True,
            ),
            rect_plane_mesh(
                axis="y",
                coordinate=center_y,
                range_a=(center_x + half_inner_x, center_x + half_outer_x),
                range_b=(-half_outer_z, half_outer_z),
                normal_positive=True,
            ),
            rect_plane_mesh(
                axis="y",
                coordinate=center_y,
                range_a=(center_x - half_inner_x, center_x + half_inner_x),
                range_b=(half_inner_z, half_outer_z),
                normal_positive=True,
            ),
            rect_plane_mesh(
                axis="y",
                coordinate=center_y,
                range_a=(center_x - half_inner_x, center_x + half_inner_x),
                range_b=(-half_outer_z, -half_inner_z),
                normal_positive=True,
            ),
        ]
    )


def wall_with_hole_grid_mesh(
    *,
    x: float,
    y_range: tuple[float, float],
    z_range: tuple[float, float],
    hole_center_y: float,
    hole_radius: float,
    normal_positive: bool = True,
    steps: int = 48,
) -> Mesh:
    y0, y1 = y_range
    z0, z1 = z_range
    grid_steps = max(steps, 24)
    ys = [y0 + (y1 - y0) * index / grid_steps for index in range(grid_steps + 1)]
    zs = [z0 + (z1 - z0) * index / grid_steps for index in range(grid_steps + 1)]
    points: list[tuple[float, float, float]] = []
    point_index: dict[tuple[int, int], int] = {}
    triangles: list[tuple[int, int, int]] = []

    def get_point(yi: int, zi: int) -> int:
        key = (yi, zi)
        existing = point_index.get(key)
        if existing is not None:
            return existing
        point_index[key] = len(points)
        points.append((x, ys[yi], zs[zi]))
        return point_index[key]

    def outside_hole(sample_y: float, sample_z: float) -> bool:
        return (sample_y - hole_center_y) ** 2 + sample_z**2 >= hole_radius**2

    for yi in range(grid_steps):
        for zi in range(grid_steps):
            corners = [
                (ys[yi], zs[zi]),
                (ys[yi + 1], zs[zi]),
                (ys[yi + 1], zs[zi + 1]),
                (ys[yi], zs[zi + 1]),
            ]
            center_y = sum(point[0] for point in corners) / 4
            center_z = sum(point[1] for point in corners) / 4
            if not outside_hole(center_y, center_z):
                continue
            cell_points = [get_point(yi, zi), get_point(yi + 1, zi), get_point(yi + 1, zi + 1), get_point(yi, zi + 1)]
            if normal_positive:
                triangles.extend([(cell_points[0], cell_points[1], cell_points[2]), (cell_points[0], cell_points[2], cell_points[3])])
            else:
                triangles.extend([(cell_points[0], cell_points[2], cell_points[1]), (cell_points[0], cell_points[3], cell_points[2])])

    return points, triangles


def tube_side_mesh(path: list[tuple[float, float, float]], radius: float, radial_segments: int = 18) -> Mesh:
    if len(path) < 2:
        return [], []

    points: list[tuple[float, float, float]] = []
    triangles: list[tuple[int, int, int]] = []
    rings: list[list[int]] = []

    for index, point in enumerate(path):
        previous = path[max(index - 1, 0)]
        nxt = path[min(index + 1, len(path) - 1)]
        tangent = _normalize((nxt[0] - previous[0], nxt[1] - previous[1], nxt[2] - previous[2]))
        up_ref = (0.0, 1.0, 0.0) if abs(tangent[1]) < 0.99 else (1.0, 0.0, 0.0)
        right = _normalize(_cross(tangent, up_ref))
        real_up = _normalize(_cross(right, tangent))
        ring: list[int] = []

        for segment in range(radial_segments):
            angle = (segment / radial_segments) * math.pi * 2
            cos_value = math.cos(angle)
            sin_value = math.sin(angle)
            px = point[0] + radius * (cos_value * right[0] + sin_value * real_up[0])
            py = point[1] + radius * (cos_value * right[1] + sin_value * real_up[1])
            pz = point[2] + radius * (cos_value * right[2] + sin_value * real_up[2])
            ring.append(len(points))
            points.append((px, py, pz))

        rings.append(ring)

    for ring_index in range(len(rings) - 1):
        current_ring = rings[ring_index]
        next_ring = rings[ring_index + 1]
        for segment in range(radial_segments):
            next_segment = (segment + 1) % radial_segments
            triangles.append((current_ring[segment], current_ring[next_segment], next_ring[next_segment]))
            triangles.append((current_ring[segment], next_ring[next_segment], next_ring[segment]))

    return points, triangles


def tube_end_cap_mesh(path: list[tuple[float, float, float]], radius: float, radial_segments: int = 24) -> Mesh:
    if len(path) < 2:
        return [], []

    end_point = path[-1]
    previous = path[-2]
    tangent = _normalize((end_point[0] - previous[0], end_point[1] - previous[1], end_point[2] - previous[2]))
    up_ref = (0.0, 1.0, 0.0) if abs(tangent[1]) < 0.99 else (1.0, 0.0, 0.0)
    right = _normalize(_cross(tangent, up_ref))
    real_up = _normalize(_cross(right, tangent))

    points: list[tuple[float, float, float]] = [end_point]
    ring: list[int] = []
    for segment in range(radial_segments):
        angle = (segment / radial_segments) * math.pi * 2
        cos_value = math.cos(angle)
        sin_value = math.sin(angle)
        px = end_point[0] + radius * (cos_value * right[0] + sin_value * real_up[0])
        py = end_point[1] + radius * (cos_value * right[1] + sin_value * real_up[1])
        pz = end_point[2] + radius * (cos_value * right[2] + sin_value * real_up[2])
        ring.append(len(points))
        points.append((px, py, pz))

    triangles = [(0, ring[segment], ring[(segment + 1) % radial_segments]) for segment in range(radial_segments)]
    return points, triangles


def descriptor_to_mesh(descriptor: dict[str, Any]) -> Mesh:
    if descriptor["type"] == "box":
        return box_mesh(tuple(descriptor["center"]), tuple(descriptor["size"]))

    if descriptor["type"] == "wallWithHole":
        center = descriptor["center"]
        size = descriptor["size"]
        return wall_with_hole_grid_mesh(
            x=float(center[0] + size[0] / 2),
            y_range=(float(center[1] - size[1] / 2), float(center[1] + size[1] / 2)),
            z_range=(float(center[2] - size[2] / 2), float(center[2] + size[2] / 2)),
            hole_center_y=float(descriptor["hole"]["centerY"]),
            hole_radius=float(descriptor["hole"]["radius"]),
            normal_positive=True,
        )

    if descriptor["type"] == "tube":
        path = [tuple(point) for point in descriptor["path"]]
        return tube_side_mesh(path, float(descriptor["outerRadius"]))

    center = descriptor["center"]
    plate = box_mesh(
        (float(center[0]), float(center[1] + descriptor["pointHeight"] / 2), float(center[2])),
        (float(descriptor["plateThickness"]), float(descriptor["pointHeight"]), float(descriptor["hw"])),
    )
    left_prism = triangular_prism_mesh(
        (float(center[0]), float(center[1]), float(center[2] - descriptor["hw"] / 2 + descriptor["ht"] / 2)),
        float(descriptor["alpha"]),
        float(descriptor["alpha"]),
        float(descriptor["ht"]),
    )
    right_prism = triangular_prism_mesh(
        (float(center[0]), float(center[1]), float(center[2] + descriptor["hw"] / 2 - descriptor["ht"] / 2)),
        float(descriptor["alpha"]),
        float(descriptor["alpha"]),
        float(descriptor["ht"]),
    )
    return combine_meshes([plate, left_prism, right_prism])


def mesh_to_ascii_stl(name: str, mesh: Mesh) -> str:
    points, triangles = mesh
    lines = [f"solid {name}"]
    for a, b, c in triangles:
        pa = points[a]
        pb = points[b]
        pc = points[c]
        normal = _normalize(_cross(_sub(pb, pa), _sub(pc, pa)))
        lines.append(f"  facet normal {normal[0]:.9g} {normal[1]:.9g} {normal[2]:.9g}")
        lines.append("    outer loop")
        lines.append(f"      vertex {pa[0]:.9g} {pa[1]:.9g} {pa[2]:.9g}")
        lines.append(f"      vertex {pb[0]:.9g} {pb[1]:.9g} {pb[2]:.9g}")
        lines.append(f"      vertex {pc[0]:.9g} {pc[1]:.9g} {pc[2]:.9g}")
        lines.append("    endloop")
        lines.append("  endfacet")
    lines.append(f"endsolid {name}")
    return "\n".join(lines) + "\n"


def build_solver_surface_stls(
    parameters: dict[str, float],
    derived: dict[str, Any],
    forcing: dict[str, Any],
    fixed_geometry: dict[str, Any],
) -> dict[str, str]:
    total_height = parameters["h0"] + parameters["h_a"]
    inner_radius = max(derived["r"] * (1 - parameters["wallThicknessRatio"]), derived["r"] * 0.1)
    container_length = derived["X2"] - derived["S0"]
    patch_fraction = max(min(forcing.get("topPatchFraction", 0.18), 0.9), 0.05)
    top_patch_length = container_length * patch_fraction
    top_patch_width = parameters["W"] * patch_fraction
    inlet_center_x = derived["S0"] + container_length / 2

    walls_mesh = combine_meshes(
        [
            rect_plane_mesh(
                axis="y",
                coordinate=0.0,
                range_a=(derived["S0"], derived["X2"]),
                range_b=(-parameters["W"] / 2, parameters["W"] / 2),
                normal_positive=False,
            ),
            rect_plane_mesh(
                axis="x",
                coordinate=derived["S0"],
                range_a=(0.0, total_height),
                range_b=(-parameters["W"] / 2, parameters["W"] / 2),
                normal_positive=False,
            ),
            rect_plane_mesh(
                axis="z",
                coordinate=parameters["W"] / 2,
                range_a=(derived["S0"], derived["X2"]),
                range_b=(0.0, total_height),
                normal_positive=True,
            ),
            rect_plane_mesh(
                axis="z",
                coordinate=-parameters["W"] / 2,
                range_a=(derived["S0"], derived["X2"]),
                range_b=(0.0, total_height),
                normal_positive=False,
            ),
            wall_with_hole_grid_mesh(
                x=derived["X2"],
                y_range=(0.0, total_height),
                z_range=(-parameters["W"] / 2, parameters["W"] / 2),
                hole_center_y=derived["h2"],
                hole_radius=inner_radius,
                normal_positive=True,
            ),
        ]
    )
    # The tube wall (straw bore surface) is a dedicated patch so the mesher can
    # refine it far more aggressively than the big container walls. The bore is only
    # ~13 mm across, so without its own high refinement level snappyHexMesh cannot
    # carve a continuous open channel and no water can flow through the siphon.
    tube_wall_mesh = tube_side_mesh(
        [tuple((point["x"], point["y"], 0.0)) for point in derived["tubePolyline"]], inner_radius, radial_segments=28
    )
    top_atmosphere_mesh = framed_top_patch_mesh(
        center_x=inlet_center_x,
        center_y=total_height,
        outer_size=(container_length, parameters["W"]),
        inner_size=(top_patch_length, top_patch_width),
    )
    top_inflow_mesh = rect_plane_mesh(
        axis="y",
        coordinate=total_height,
        range_a=(inlet_center_x - top_patch_length / 2, inlet_center_x + top_patch_length / 2),
        range_b=(-top_patch_width / 2, top_patch_width / 2),
        normal_positive=True,
    )
    outlet_mesh = tube_end_cap_mesh([tuple((point["x"], point["y"], 0.0)) for point in derived["tubePolyline"]], inner_radius)
    solid_obstructions = combine_meshes(
        [descriptor_to_mesh(descriptor) for group in ("holders", "columns") for descriptor in fixed_geometry[group]]
    )

    return {
        "walls.stl": mesh_to_ascii_stl("walls", walls_mesh),
        "tubeWall.stl": mesh_to_ascii_stl("tubeWall", tube_wall_mesh),
        "solidObstructions.stl": mesh_to_ascii_stl("solidObstructions", solid_obstructions),
        "topAtmosphere.stl": mesh_to_ascii_stl("topAtmosphere", top_atmosphere_mesh),
        "topInflow.stl": mesh_to_ascii_stl("topInflow", top_inflow_mesh),
        "tubeOutlet.stl": mesh_to_ascii_stl("tubeOutlet", outlet_mesh),
    }
