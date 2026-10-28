import * as THREE from "three";

const TOY_CAMERA_PADDING = 1.65;

export function makeDashedLine(points, color, dashSize, gapSize, opacity = 0.72) {
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineDashedMaterial({
    color,
    transparent: true,
    opacity,
    dashSize,
    gapSize,
  });
  const line = new THREE.Line(geometry, material);
  line.computeLineDistances();
  return line;
}

export function makeDashedRollingCylinder(radius, length) {
  const group = new THREE.Group();
  const half = length / 2;
  const dashSize = Math.max(0.5, radius * 0.1);
  const gapSize = Math.max(0.24, radius * 0.055);
  const color = 0x7a8aa2;
  const segments = 84;

  function makeRing(yPos) {
    const points = [];
    for (let i = 0; i <= segments; i += 1) {
      const a = (i / segments) * Math.PI * 2;
      points.push(new THREE.Vector3(radius * Math.cos(a), yPos, radius * Math.sin(a)));
    }
    return makeDashedLine(points, color, dashSize, gapSize);
  }

  group.add(makeRing(-half));
  group.add(makeRing(half));
  group.add(
    makeDashedLine(
      [new THREE.Vector3(radius, -half, 0), new THREE.Vector3(radius, half, 0)],
      color,
      dashSize,
      gapSize
    )
  );
  group.add(
    makeDashedLine(
      [new THREE.Vector3(-radius, -half, 0), new THREE.Vector3(-radius, half, 0)],
      color,
      dashSize,
      gapSize
    )
  );
  group.add(
    makeDashedLine(
      [new THREE.Vector3(0, 0, -radius), new THREE.Vector3(0, 0, radius)],
      0x5f7088,
      Math.max(0.45, radius * 0.085),
      Math.max(0.22, radius * 0.045),
      0.78
    )
  );

  return group;
}

export function syncToyPose(toyGroup, contactMarker, rollingCylinder, state) {
  if (!toyGroup || !state) {
    return;
  }

  toyGroup.position.set(state.pose.tx, 0, state.pose.ty);
  toyGroup.rotation.set(0, -state.pose.theta, 0);

  if (contactMarker) {
    contactMarker.position.set(state.contactPoint.x, 0, state.contactPoint.y + 0.08);
  }

  if (rollingCylinder) {
    const showRollingCylinder = state.mode === "roll" && !!state.circleCenter;
    rollingCylinder.visible = showRollingCylinder;
    if (showRollingCylinder) {
      rollingCylinder.position.set(state.circleCenter.x, 0, state.circleCenter.y);
    }
  }
}

export function fitToyCamera(camera, controls, canvas, toyGroup, frameBounds, params) {
  if (!toyGroup || !frameBounds) {
    return;
  }

  const width = Math.max(1, Math.floor(canvas.clientWidth));
  const height = Math.max(1, Math.floor(canvas.clientHeight));
  camera.aspect = width / height;
  camera.updateProjectionMatrix();

  const pathCenterX = 0.5 * (frameBounds.xMin + frameBounds.xMax);
  const pathCenterZ = 0.5 * (frameBounds.yMin + frameBounds.yMax);

  const spanXPath = Math.max(1e-6, frameBounds.xMax - frameBounds.xMin);
  const spanZPath = Math.max(1e-6, frameBounds.yMax - frameBounds.yMin);
  const cylinderSpan = 2 * params.R;
  const spanX = Math.max(spanXPath, cylinderSpan);
  const spanZ = Math.max(spanZPath, cylinderSpan);
  const spanY = Math.max(params.w * 1.15, params.R * 0.9);

  const fov = THREE.MathUtils.degToRad(camera.fov);
  const fovh = 2 * Math.atan(Math.tan(fov / 2) * camera.aspect);
  const dx = spanX / (2 * Math.tan(fovh / 2));
  const dz = spanZ / (2 * Math.tan(fov / 2));
  const dy = spanY * 1.05;
  const distance = TOY_CAMERA_PADDING * Math.max(dx, dz, dy);

  const target = new THREE.Vector3(pathCenterX, 0, pathCenterZ);
  const viewDir = new THREE.Vector3(-1.18, 0.9, 0.78).normalize();
  camera.position.copy(target).add(viewDir.multiplyScalar(distance + 0.01));
  camera.near = Math.max(0.01, distance / 140);
  camera.far = Math.max(900, distance * 120);
  camera.updateProjectionMatrix();

  controls.target.copy(target);
  controls.minDistance = Math.max(8, distance * 0.28);
  controls.maxDistance = Math.max(60, distance * 9);
  controls.update();
}