import {
  buildFixedGeometryDescriptors,
  createDefaultCase,
  createGeometrySnapshot,
  type CanonicalParameters,
  type FixedGeometryDescriptor,
} from "@fixed-geometry/shared-schema";
import { GLTFExporter } from "three/examples/jsm/exporters/GLTFExporter.js";
import { STLExporter } from "three/examples/jsm/exporters/STLExporter.js";
import * as THREE from "three";

type VisibilityMap = {
  container: boolean;
  tube: boolean;
  holders: boolean;
  columns: boolean;
  labels: boolean;
};

function makeBox(
  descriptor: Extract<FixedGeometryDescriptor, { type: "box" | "wallWithHole" }>,
  material: THREE.Material
) {
  const mesh = new THREE.Mesh(
    new THREE.BoxGeometry(...descriptor.size),
    material
  );
  mesh.position.set(...descriptor.center);
  mesh.name = descriptor.name;
  return mesh;
}

function makeHolder(
  descriptor: Extract<FixedGeometryDescriptor, { type: "holder" }>,
  material: THREE.Material
) {
  const group = new THREE.Group();
  const plate = new THREE.Mesh(
    new THREE.BoxGeometry(
      descriptor.plateThickness,
      descriptor.pointHeight,
      descriptor.hw
    ),
    material
  );
  plate.position.set(0, descriptor.pointHeight / 2, 0);
  group.add(plate);

  const shape = new THREE.Shape();
  shape.moveTo(-descriptor.alpha / 2, 0);
  shape.lineTo(descriptor.alpha / 2, 0);
  shape.lineTo(0, descriptor.alpha);
  shape.closePath();

  for (const sign of [-1, 1]) {
    const prism = new THREE.Mesh(
      new THREE.ExtrudeGeometry(shape, {
        depth: descriptor.ht,
        bevelEnabled: false,
      }),
      material
    );
    prism.geometry.translate(0, 0, -descriptor.ht / 2);
    prism.position.set(0, 0, sign * (descriptor.hw / 2 - descriptor.ht / 2));
    group.add(prism);
  }

  group.position.set(...descriptor.center);
  group.name = descriptor.name;
  return group;
}

function makeTube(
  descriptor: Extract<FixedGeometryDescriptor, { type: "tube" }>,
  material: THREE.Material
) {
  const curve = new THREE.CatmullRomCurve3(
    descriptor.path.map((point) => new THREE.Vector3(...point)),
    false,
    "catmullrom",
    0
  );
  const mesh = new THREE.Mesh(
    new THREE.TubeGeometry(curve, 240, descriptor.outerRadius, 18, false),
    material
  );
  mesh.name = descriptor.name;
  return mesh;
}

export function buildSceneGroup(
  parameters: CanonicalParameters,
  visibility: VisibilityMap
) {
  const snapshot = createGeometrySnapshot(parameters);
  const descriptors = buildFixedGeometryDescriptors(
    snapshot.parameters,
    snapshot.derived
  );
  const group = new THREE.Group();

  const materials = {
    container: new THREE.MeshPhysicalMaterial({
      color: 0x3a5a8a,
      transparent: true,
      opacity: 0.18,
      roughness: 0.4,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
    tube: new THREE.MeshPhysicalMaterial({
      color: 0xddeeff,
      transparent: true,
      opacity: 0.35,
      roughness: 0.05,
      clearcoat: 1,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
    holders: new THREE.MeshStandardMaterial({ color: 0x50bb70, roughness: 0.5 }),
    columns: new THREE.MeshStandardMaterial({ color: 0x9a7bff, roughness: 0.5 }),
    holeRing: new THREE.MeshBasicMaterial({ color: 0x9ad0ff, side: THREE.DoubleSide }),
    label: new THREE.MeshBasicMaterial({ color: 0xff6644 }),
  };

  const groups = [
    ["container", visibility.container, descriptors.container, materials.container],
    ["tube", visibility.tube, descriptors.tube, materials.tube],
    ["holders", visibility.holders, descriptors.holders, materials.holders],
    ["columns", visibility.columns, descriptors.columns, materials.columns],
  ] as const;

  for (const [, enabled, descriptorGroup, material] of groups) {
    if (!enabled) {
      continue;
    }
    for (const descriptor of descriptorGroup) {
      if (descriptor.type === "box") {
        group.add(makeBox(descriptor, material));
      } else if (descriptor.type === "wallWithHole") {
        const wall = makeBox(descriptor, material);
        const ring = new THREE.Mesh(
          new THREE.RingGeometry(
            descriptor.hole.radius * 0.7,
            descriptor.hole.radius,
            32
          ),
          materials.holeRing
        );
        ring.rotation.y = Math.PI / 2;
        ring.position.set(
          descriptor.center[0] + descriptor.size[0] / 2 + 0.0005,
          descriptor.hole.centerY,
          0
        );
        wall.add(ring);
        group.add(wall);
      } else if (descriptor.type === "tube") {
        group.add(makeTube(descriptor, material));
      } else {
        group.add(makeHolder(descriptor, material));
      }
    }
  }

  if (visibility.labels) {
    const labelGroup = new THREE.Group();
    const labelPoints = [
      snapshot.derived.points.P1,
      snapshot.derived.points.W1,
      snapshot.derived.points.P2,
      snapshot.derived.points.P3,
      snapshot.derived.points.P4,
      snapshot.derived.points.W2,
      snapshot.derived.points.P5,
    ];
    for (const point of labelPoints) {
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(0.004, 10, 8),
        materials.label
      );
      sphere.position.set(point.x, point.y, 0);
      labelGroup.add(sphere);

      const line = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(point.x, 0, 0),
          new THREE.Vector3(point.x, point.y, 0),
        ]),
        new THREE.LineBasicMaterial({ color: 0xff6644, transparent: true, opacity: 0.35 })
      );
      labelGroup.add(line);
    }
    group.add(labelGroup);
  }

  return { snapshot, descriptors, group };
}

function downloadBlob(blob: Blob, fileName: string) {
  const anchor = document.createElement("a");
  anchor.href = URL.createObjectURL(blob);
  anchor.download = fileName;
  anchor.click();
  URL.revokeObjectURL(anchor.href);
}

export async function exportCaseJson(parameters: CanonicalParameters) {
  const caseFile = createDefaultCase(parameters);
  downloadBlob(
    new Blob([JSON.stringify(caseFile, null, 2)], { type: "application/json" }),
    `${caseFile.caseId}.json`
  );
}

export async function exportStl(parameters: CanonicalParameters, visibility: VisibilityMap) {
  const { group } = buildSceneGroup(parameters, visibility);
  const exporter = new STLExporter();
  const result = exporter.parse(group, { binary: true }) as ArrayBuffer;
  downloadBlob(new Blob([result], { type: "model/stl" }), "experimental_setup.stl");
}

export async function exportGlb(parameters: CanonicalParameters, visibility: VisibilityMap) {
  const { group } = buildSceneGroup(parameters, visibility);
  const exporter = new GLTFExporter();
  const glb = await new Promise<ArrayBuffer>((resolve) => {
    exporter.parse(
      group,
      (value) => resolve(value as ArrayBuffer),
      (error) => {
        throw error;
      },
      { binary: true }
    );
  });
  downloadBlob(new Blob([glb], { type: "model/gltf-binary" }), "experimental_setup.glb");
}

