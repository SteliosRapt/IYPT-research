import * as THREE from "three";
import {
  buildIntersectionSquarePatch,
  cutMeshResolution,
  steinmetzPatchX,
  steinmetzPatchY,
} from "./steinmetz.js";
import { clamp } from "./math-utils.js";

export function displayMeshResolution(detail) {
  const d = clamp(detail, 0.5, 3.0);
  return {
    segA: Math.max(96, Math.min(360, Math.round(150 * d))),
    segB: Math.max(44, Math.min(180, Math.round(72 * d))),
  };
}

export function makeCenterDot(center, radius, color = 0xd72222) {
  const geometry = new THREE.SphereGeometry(radius, 16, 16);
  const material = new THREE.MeshStandardMaterial({
    color,
    emissive: 0x520909,
    emissiveIntensity: 0.32,
  });
  const dot = new THREE.Mesh(geometry, material);
  dot.position.copy(center);
  return dot;
}

export function makeDashedCylinderOutline(radius, length, axis = "y", color = 0x647892) {
  function makeDashedLine(points) {
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineDashedMaterial({
      color,
      transparent: true,
      opacity: 0.72,
      dashSize: Math.max(0.4, radius * 0.1),
      gapSize: Math.max(0.24, radius * 0.06),
    });
    const line = new THREE.Line(geometry, material);
    line.computeLineDistances();
    return line;
  }

  function makeRing(yPos, segments = 24) {
    const points = [];
    for (let i = 0; i <= segments; i += 1) {
      const a = (i / segments) * Math.PI * 2;
      points.push(new THREE.Vector3(radius * Math.cos(a), yPos, radius * Math.sin(a)));
    }
    return makeDashedLine(points);
  }

  const group = new THREE.Group();
  const half = length / 2;
  group.add(makeRing(-half));
  group.add(makeRing(half));

  const generatrixPoints = [
    new THREE.Vector3(radius, -half, 0),
    new THREE.Vector3(radius, half, 0),
    new THREE.Vector3(-radius, -half, 0),
    new THREE.Vector3(-radius, half, 0),
  ];

  for (let i = 0; i < generatrixPoints.length; i += 2) {
    group.add(makeDashedLine([generatrixPoints[i], generatrixPoints[i + 1]]));
  }

  if (axis === "x") {
    group.rotation.z = -Math.PI / 2;
  }
  if (axis === "z") {
    group.rotation.x = Math.PI / 2;
  }
  return group;
}

export function makeDashedCenterCircle(radius, color = 0x111111, segments = 88) {
  const points = [];
  for (let i = 0; i <= segments; i += 1) {
    const a = (i / segments) * Math.PI * 2;
    points.push(new THREE.Vector3(0, radius * Math.cos(a), radius * Math.sin(a)));
  }
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineDashedMaterial({
    color,
    transparent: true,
    opacity: 0.82,
    dashSize: Math.max(0.5, radius * 0.06),
    gapSize: Math.max(0.24, radius * 0.032),
    depthTest: false,
    depthWrite: false,
  });
  const circle = new THREE.Line(geometry, material);
  circle.computeLineDistances();
  circle.renderOrder = 35;
  return circle;
}

export function buildSteinmetz(R, w, detail) {
  const group = new THREE.Group();

  const shellMat = new THREE.MeshStandardMaterial({
    color: 0x6f88ac,
    transparent: true,
    opacity: 0.34,
    side: THREE.DoubleSide,
    roughness: 0.52,
    metalness: 0.08,
  });

  const displayRes = displayMeshResolution(detail);
  const patchYGeometry = steinmetzPatchY(R, displayRes.segA, displayRes.segB);
  const patchXGeometry = steinmetzPatchX(R, displayRes.segA, displayRes.segB);
  const patchY = new THREE.Mesh(patchYGeometry, shellMat);
  const patchX = new THREE.Mesh(patchXGeometry, shellMat.clone());
  group.add(patchY);
  group.add(patchX);

  group.add(makeDashedCylinderOutline(R, 2 * R, "y", 0x6f8199));
  group.add(makeDashedCylinderOutline(R, 2 * R, "x", 0x6f8199));
  group.add(makeDashedCenterCircle(R));

  const cutRes = cutMeshResolution(R, w, detail);
  const patchYCut = steinmetzPatchY(R, cutRes.segA, cutRes.segB);
  const patchXCut = steinmetzPatchX(R, cutRes.segA, cutRes.segB);

  const squareAInfo = buildIntersectionSquarePatch(R, w, 1, patchYCut, patchXCut);
  const squareBInfo = buildIntersectionSquarePatch(R, w, -1, patchYCut, patchXCut);
  patchYCut.dispose();
  patchXCut.dispose();

  const redMat = new THREE.MeshStandardMaterial({
    color: 0xda3b3b,
    emissive: 0x4a0909,
    emissiveIntensity: 0.25,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0.9,
  });

  const squareA = new THREE.Mesh(squareAInfo.geometry, redMat);
  const squareB = new THREE.Mesh(squareBInfo.geometry, redMat.clone());
  group.add(squareA);
  group.add(squareB);

  const edgeA = new THREE.LineSegments(
    new THREE.EdgesGeometry(squareAInfo.geometry, 36),
    new THREE.LineBasicMaterial({ color: 0x801212 })
  );
  const edgeB = new THREE.LineSegments(
    new THREE.EdgesGeometry(squareBInfo.geometry, 36),
    new THREE.LineBasicMaterial({ color: 0x801212 })
  );
  group.add(edgeA);
  group.add(edgeB);

  const dotRadius = Math.max(0.15, w * 0.03);
  group.add(makeCenterDot(squareAInfo.center, dotRadius));
  group.add(makeCenterDot(squareBInfo.center, dotRadius));

  return {
    group,
    patchInfos: [
      {
        center: squareAInfo.center.clone(),
        signZ: squareAInfo.signZ,
        patchSide: squareAInfo.patchSide,
        geometry: squareAInfo.geometry.clone(),
      },
      {
        center: squareBInfo.center.clone(),
        signZ: squareBInfo.signZ,
        patchSide: squareBInfo.patchSide,
        geometry: squareBInfo.geometry.clone(),
      },
    ],
  };
}