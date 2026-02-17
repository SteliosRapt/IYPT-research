import * as THREE from "three";
import { clamp } from "./math-utils.js";

export function steinmetzPatchY(R, segmentsA = 160, segmentsB = 72) {
  const positions = [];
  const normals = [];
  const indices = [];

  for (let i = 0; i <= segmentsA; i += 1) {
    const a = (i / segmentsA) * Math.PI * 2;
    const c = Math.cos(a);
    const s = Math.sin(a);
    const limit = R * Math.abs(c);

    for (let j = 0; j <= segmentsB; j += 1) {
      const t = -1 + (2 * j) / segmentsB;
      const x = R * c;
      const y = t * limit;
      const z = R * s;
      positions.push(x, y, z);
      normals.push(c, 0, s);
    }
  }

  for (let i = 0; i < segmentsA; i += 1) {
    for (let j = 0; j < segmentsB; j += 1) {
      const a = i * (segmentsB + 1) + j;
      const b = (i + 1) * (segmentsB + 1) + j;
      const c = b + 1;
      const d = a + 1;
      indices.push(a, b, d, b, c, d);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geometry.setIndex(indices);
  return geometry;
}

export function steinmetzPatchX(R, segmentsA = 160, segmentsB = 72) {
  const positions = [];
  const normals = [];
  const indices = [];

  for (let i = 0; i <= segmentsA; i += 1) {
    const a = (i / segmentsA) * Math.PI * 2;
    const c = Math.cos(a);
    const s = Math.sin(a);
    const limit = R * Math.abs(c);

    for (let j = 0; j <= segmentsB; j += 1) {
      const t = -1 + (2 * j) / segmentsB;
      const x = t * limit;
      const y = R * c;
      const z = R * s;
      positions.push(x, y, z);
      normals.push(0, c, s);
    }
  }

  for (let i = 0; i < segmentsA; i += 1) {
    for (let j = 0; j < segmentsB; j += 1) {
      const a = i * (segmentsB + 1) + j;
      const b = (i + 1) * (segmentsB + 1) + j;
      const c = b + 1;
      const d = a + 1;
      indices.push(a, b, d, b, c, d);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geometry.setIndex(indices);
  return geometry;
}

export function clipPolygonByPlane(vertices, signedDistance, epsilon = 1e-6) {
  if (vertices.length === 0) {
    return [];
  }
  const out = [];
  let prev = vertices[vertices.length - 1];
  let prevDist = signedDistance(prev.p);
  let prevInside = prevDist >= -epsilon;

  for (const curr of vertices) {
    const currDist = signedDistance(curr.p);
    const currInside = currDist >= -epsilon;

    if (currInside !== prevInside) {
      const denom = prevDist - currDist;
      const t = Math.abs(denom) < 1e-12 ? 0 : prevDist / denom;
      const point = prev.p.clone().lerp(curr.p, t);
      const normal = prev.n.clone().lerp(curr.n, t).normalize();
      out.push({ p: point, n: normal });
    }

    if (currInside) {
      out.push({ p: curr.p.clone(), n: curr.n.clone() });
    }

    prev = curr;
    prevDist = currDist;
    prevInside = currInside;
  }

  return out;
}

export function extractTrianglesInSquareWindow(sourceGeometry, center, halfSide, signZ, zMin, epsilon = 1e-5) {
  const positions = sourceGeometry.getAttribute("position");
  const normals = sourceGeometry.getAttribute("normal");
  const index = sourceGeometry.getIndex();

  const outPos = [];
  const outNorm = [];
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();
  const na = new THREE.Vector3();
  const nb = new THREE.Vector3();
  const nc = new THREE.Vector3();

  for (let i = 0; i < index.count; i += 3) {
    const ia = index.getX(i);
    const ib = index.getX(i + 1);
    const ic = index.getX(i + 2);

    a.fromBufferAttribute(positions, ia);
    b.fromBufferAttribute(positions, ib);
    c.fromBufferAttribute(positions, ic);
    na.fromBufferAttribute(normals, ia);
    nb.fromBufferAttribute(normals, ib);
    nc.fromBufferAttribute(normals, ic);

    let poly = [
      { p: a.clone(), n: na.clone() },
      { p: b.clone(), n: nb.clone() },
      { p: c.clone(), n: nc.clone() },
    ];

    poly = clipPolygonByPlane(poly, (p) => p.x - (center.x - halfSide), epsilon);
    poly = clipPolygonByPlane(poly, (p) => (center.x + halfSide) - p.x, epsilon);
    poly = clipPolygonByPlane(poly, (p) => p.y - (center.y - halfSide), epsilon);
    poly = clipPolygonByPlane(poly, (p) => (center.y + halfSide) - p.y, epsilon);
    poly = clipPolygonByPlane(poly, (p) => signZ * p.z - zMin, epsilon);

    if (poly.length < 3) {
      continue;
    }

    for (let k = 1; k < poly.length - 1; k += 1) {
      const p0 = poly[0];
      const p1 = poly[k];
      const p2 = poly[k + 1];
      outPos.push(
        p0.p.x,
        p0.p.y,
        p0.p.z,
        p1.p.x,
        p1.p.y,
        p1.p.z,
        p2.p.x,
        p2.p.y,
        p2.p.z
      );
      outNorm.push(
        p0.n.x,
        p0.n.y,
        p0.n.z,
        p1.n.x,
        p1.n.y,
        p1.n.z,
        p2.n.x,
        p2.n.y,
        p2.n.z
      );
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(outPos, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(outNorm, 3));
  if (outPos.length > 0) {
    geometry.computeBoundingBox();
    geometry.computeBoundingSphere();
  }
  return geometry;
}

export function mergeTriangleSoup(geometries) {
  const mergedPos = [];
  const mergedNorm = [];

  for (const geometry of geometries) {
    if (!geometry) {
      continue;
    }
    const pos = geometry.getAttribute("position");
    const norm = geometry.getAttribute("normal");
    if (!pos || pos.count === 0) {
      continue;
    }
    if (!norm) {
      geometry.computeVertexNormals();
    }
    const n = geometry.getAttribute("normal");
    for (let i = 0; i < pos.count; i += 1) {
      mergedPos.push(pos.getX(i), pos.getY(i), pos.getZ(i));
      mergedNorm.push(n.getX(i), n.getY(i), n.getZ(i));
    }
  }

  const merged = new THREE.BufferGeometry();
  merged.setAttribute("position", new THREE.Float32BufferAttribute(mergedPos, 3));
  merged.setAttribute("normal", new THREE.Float32BufferAttribute(mergedNorm, 3));
  if (mergedPos.length > 0) {
    merged.computeBoundingBox();
    merged.computeBoundingSphere();
  }
  return merged;
}

export function buildIntersectionSquarePatch(R, w, signZ, patchYGeometry, patchXGeometry) {
  const patchSide = Math.max(0.1, w);
  const halfSide = patchSide / 2;
  const center = new THREE.Vector3(0, 0, signZ >= 0 ? R : -R);
  const zMin = Math.sqrt(Math.max(0, R * R - halfSide * halfSide));
  const zSign = signZ >= 0 ? 1 : -1;

  const partY = extractTrianglesInSquareWindow(patchYGeometry, center, halfSide, zSign, zMin);
  const partX = extractTrianglesInSquareWindow(patchXGeometry, center, halfSide, zSign, zMin);
  const geometry = mergeTriangleSoup([partY, partX]);
  partY.dispose();
  partX.dispose();

  return {
    geometry,
    center,
    patchSide,
    signZ: zSign,
  };
}

export function cutMeshResolution(R, w, detail) {
  const d = clamp(detail, 0.5, 3.0);
  const targetEdge = Math.max(0.04, Math.min(0.9, w / (8 * d)));
  return {
    segA: Math.max(180, Math.min(420, Math.ceil((2 * Math.PI * R) / targetEdge))),
    segB: Math.max(84, Math.min(220, Math.ceil((2 * R) / targetEdge))),
  };
}