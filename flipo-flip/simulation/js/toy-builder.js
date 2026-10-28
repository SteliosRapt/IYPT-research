import * as THREE from "three";

export function cloneAndAlignPatchToPrismFace(sourceGeometry, signZ, h) {
  const geometry = sourceGeometry.clone();
  const pos = geometry.getAttribute("position");
  if (!pos || pos.count === 0) {
    return geometry;
  }
  if (!geometry.boundingBox) {
    geometry.computeBoundingBox();
  }
  const box = geometry.boundingBox;
  const sourceFaceZ = signZ >= 0 ? box.min.z : box.max.z;
  const targetFaceZ = signZ >= 0 ? h / 2 : -h / 2;
  geometry.translate(0, 0, targetFaceZ - sourceFaceZ);
  geometry.computeVertexNormals();
  return geometry;
}

export function makeCapIntersectionOutlines(R, w, sourceGeometry, signZ, h, segments = 64) {
  if (!sourceGeometry.boundingBox) {
    sourceGeometry.computeBoundingBox();
  }
  const box = sourceGeometry.boundingBox;
  const sourceFaceZ = signZ >= 0 ? box.min.z : box.max.z;
  const targetFaceZ = signZ >= 0 ? h / 2 : -h / 2;
  const zShift = targetFaceZ - sourceFaceZ;
  const half = w / 2;
  const pointsA = [];
  const pointsB = [];

  for (let i = 0; i <= segments; i += 1) {
    const t = -half + (2 * half * i) / segments;
    const z = signZ * Math.sqrt(Math.max(0, R * R - t * t)) + zShift;
    pointsA.push(new THREE.Vector3(t, t, z));
    pointsB.push(new THREE.Vector3(t, -t, z));
  }

  const mat = new THREE.LineBasicMaterial({ color: 0x111111, transparent: true, opacity: 0.78 });
  const lineA = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pointsA), mat);
  const lineB = new THREE.Line(new THREE.BufferGeometry().setFromPoints(pointsB), mat.clone());
  return [lineA, lineB];
}

export function buildToy(R, w, h, patchInfos, { includeExportGroup = false } = {}) {
  const group = new THREE.Group();
  const exportGroup = includeExportGroup ? new THREE.Group() : null;

  const prismMat = new THREE.MeshStandardMaterial({
    color: 0x8394ab,
    roughness: 0.52,
    metalness: 0.08,
  });
  const capMat = new THREE.MeshStandardMaterial({
    color: 0x3d88de,
    roughness: 0.45,
    metalness: 0.06,
    side: THREE.DoubleSide,
  });

  const prismGeometry = new THREE.BoxGeometry(w, w, h);
  const prism = new THREE.Mesh(prismGeometry, prismMat);
  group.add(prism);

  if (exportGroup) {
    exportGroup.add(new THREE.Mesh(prismGeometry.clone(), new THREE.MeshBasicMaterial()));
  }

  const prismEdgeLines = new THREE.LineSegments(
    new THREE.EdgesGeometry(prismGeometry, 1),
    new THREE.LineBasicMaterial({ color: 0x111111, transparent: true, opacity: 0.78 })
  );
  group.add(prismEdgeLines);

  for (const info of patchInfos) {
    const sourcePos = info.geometry.getAttribute("position");
    if (!sourcePos || sourcePos.count === 0) {
      continue;
    }

    const alignedGeo = cloneAndAlignPatchToPrismFace(info.geometry, info.signZ, h);
    const capMesh = new THREE.Mesh(alignedGeo, capMat);
    group.add(capMesh);

    const seamLines = makeCapIntersectionOutlines(R, w, info.geometry, info.signZ, h);
    group.add(seamLines[0]);
    group.add(seamLines[1]);

    if (exportGroup) {
      exportGroup.add(new THREE.Mesh(alignedGeo.clone(), new THREE.MeshBasicMaterial()));
    }
  }

  return { group, exportObject: exportGroup };
}

export function disposeNode(node) {
  if (!node) {
    return;
  }
  node.traverse((obj) => {
    if (obj.geometry) {
      obj.geometry.dispose();
    }
    if (obj.material) {
      if (Array.isArray(obj.material)) {
        obj.material.forEach((m) => m.dispose());
      } else {
        obj.material.dispose();
      }
    }
  });
}

export function addLights(scene) {
  const hemi = new THREE.HemisphereLight(0xffffff, 0xb8c6dc, 0.8);
  scene.add(hemi);

  const key = new THREE.DirectionalLight(0xffffff, 0.95);
  key.position.set(2.8, 3.3, 2.2);
  scene.add(key);

  const fill = new THREE.DirectionalLight(0xffffff, 0.35);
  fill.position.set(-2, 1, -2);
  scene.add(fill);
}