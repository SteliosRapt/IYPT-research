import type { FixedGeometryDescriptor } from "@fixed-geometry/shared-schema";

export type MeshJson = {
  points: number[][];
  triangles: number[][];
};

function combineMeshes(meshes: MeshJson[]): MeshJson {
  const points: number[][] = [];
  const triangles: number[][] = [];

  for (const mesh of meshes) {
    const offset = points.length;
    points.push(...mesh.points);
    triangles.push(
      ...mesh.triangles.map(([a, b, c]) => [a + offset, b + offset, c + offset])
    );
  }

  return { points, triangles };
}

export function boxMesh(
  center: [number, number, number],
  size: [number, number, number]
): MeshJson {
  const [cx, cy, cz] = center;
  const [sx, sy, sz] = size;
  const hx = sx / 2;
  const hy = sy / 2;
  const hz = sz / 2;
  const points = [
    [cx - hx, cy - hy, cz - hz],
    [cx + hx, cy - hy, cz - hz],
    [cx + hx, cy + hy, cz - hz],
    [cx - hx, cy + hy, cz - hz],
    [cx - hx, cy - hy, cz + hz],
    [cx + hx, cy - hy, cz + hz],
    [cx + hx, cy + hy, cz + hz],
    [cx - hx, cy + hy, cz + hz],
  ];
  const triangles = [
    [0, 1, 2], [0, 2, 3],
    [4, 6, 5], [4, 7, 6],
    [0, 4, 5], [0, 5, 1],
    [1, 5, 6], [1, 6, 2],
    [2, 6, 7], [2, 7, 3],
    [3, 7, 4], [3, 4, 0],
  ];
  return { points, triangles };
}

export function triangularPrismMesh(
  center: [number, number, number],
  base: number,
  height: number,
  depth: number
): MeshJson {
  const [cx, cy, cz] = center;
  const hz = depth / 2;
  const points = [
    [cx - base / 2, cy, cz - hz],
    [cx + base / 2, cy, cz - hz],
    [cx, cy + height, cz - hz],
    [cx - base / 2, cy, cz + hz],
    [cx + base / 2, cy, cz + hz],
    [cx, cy + height, cz + hz],
  ];
  const triangles = [
    [0, 1, 2],
    [3, 5, 4],
    [0, 3, 4], [0, 4, 1],
    [1, 4, 5], [1, 5, 2],
    [2, 5, 3], [2, 3, 0],
  ];
  return { points, triangles };
}

export function tubeMesh(
  path: [number, number, number][],
  radius: number,
  radialSegments = 18
): MeshJson {
  if (path.length < 2) {
    return { points: [], triangles: [] };
  }

  const points: number[][] = [];
  const triangles: number[][] = [];
  const rings: number[][] = [];

  for (let index = 0; index < path.length; index += 1) {
    const previous = path[Math.max(index - 1, 0)];
    const next = path[Math.min(index + 1, path.length - 1)];
    const tx = next[0] - previous[0];
    const ty = next[1] - previous[1];
    const tz = next[2] - previous[2];
    const tangentLength = Math.hypot(tx, ty, tz) || 1;
    const tangent = [tx / tangentLength, ty / tangentLength, tz / tangentLength] as const;
    const upRef = Math.abs(tangent[1]) < 0.99 ? [0, 1, 0] : [1, 0, 0];
    const rightRaw = [
      tangent[1] * upRef[2] - tangent[2] * upRef[1],
      tangent[2] * upRef[0] - tangent[0] * upRef[2],
      tangent[0] * upRef[1] - tangent[1] * upRef[0],
    ];
    const rightLength = Math.hypot(...rightRaw) || 1;
    const right = rightRaw.map((value) => value / rightLength) as [number, number, number];
    const realUpRaw = [
      right[1] * tangent[2] - right[2] * tangent[1],
      right[2] * tangent[0] - right[0] * tangent[2],
      right[0] * tangent[1] - right[1] * tangent[0],
    ];
    const realUpLength = Math.hypot(...realUpRaw) || 1;
    const realUp = realUpRaw.map((value) => value / realUpLength) as [number, number, number];
    const ring: number[] = [];

    for (let segment = 0; segment < radialSegments; segment += 1) {
      const angle = (segment / radialSegments) * Math.PI * 2;
      const cos = Math.cos(angle);
      const sin = Math.sin(angle);
      const px = path[index][0] + radius * (cos * right[0] + sin * realUp[0]);
      const py = path[index][1] + radius * (cos * right[1] + sin * realUp[1]);
      const pz = path[index][2] + radius * (cos * right[2] + sin * realUp[2]);
      ring.push(points.length);
      points.push([px, py, pz]);
    }

    rings.push(ring);
  }

  for (let ringIndex = 0; ringIndex < rings.length - 1; ringIndex += 1) {
    const currentRing = rings[ringIndex];
    const nextRing = rings[ringIndex + 1];
    for (let segment = 0; segment < radialSegments; segment += 1) {
      const nextSegment = (segment + 1) % radialSegments;
      triangles.push(
        [currentRing[segment], currentRing[nextSegment], nextRing[nextSegment]],
        [currentRing[segment], nextRing[nextSegment], nextRing[segment]]
      );
    }
  }

  return { points, triangles };
}

export function descriptorToMesh(descriptor: FixedGeometryDescriptor): MeshJson {
  if (descriptor.type === "box" || descriptor.type === "wallWithHole") {
    return boxMesh(descriptor.center, descriptor.size);
  }

  if (descriptor.type === "tube") {
    return tubeMesh(descriptor.path, descriptor.outerRadius);
  }

  const [cx, baseY, cz] = descriptor.center;
  const plate = boxMesh(
    [cx, baseY + descriptor.pointHeight / 2, cz],
    [descriptor.plateThickness, descriptor.pointHeight, descriptor.hw]
  );
  const leftTri = triangularPrismMesh(
    [cx, baseY, cz - descriptor.hw / 2 + descriptor.ht / 2],
    descriptor.alpha,
    descriptor.alpha,
    descriptor.ht
  );
  const rightTri = triangularPrismMesh(
    [cx, baseY, cz + descriptor.hw / 2 - descriptor.ht / 2],
    descriptor.alpha,
    descriptor.alpha,
    descriptor.ht
  );
  return combineMeshes([plate, leftTri, rightTri]);
}

export function descriptorGroupsToMeshes(
  descriptorGroups: Record<string, FixedGeometryDescriptor[]>
): Record<string, MeshJson> {
  return Object.fromEntries(
    Object.entries(descriptorGroups).map(([groupName, descriptors]) => [
      groupName,
      combineMeshes(descriptors.map(descriptorToMesh)),
    ])
  );
}

