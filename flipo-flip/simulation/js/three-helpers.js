import * as THREE from "three";

export function fitCameraToObject(camera, renderer, controls, object, padding = 1.2) {
  if (!object) {
    return;
  }

  const width = Math.max(1, renderer.domElement.clientWidth);
  const height = Math.max(1, renderer.domElement.clientHeight);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();

  const box = new THREE.Box3().setFromObject(object);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());

  const fov = THREE.MathUtils.degToRad(camera.fov);
  const fovh = 2 * Math.atan(Math.tan(fov / 2) * camera.aspect);
  const dx = size.x / (2 * Math.tan(fovh / 2));
  const dy = size.y / (2 * Math.tan(fov / 2));
  const dz = size.z * 0.9;
  const distance = padding * Math.max(dx, dy, dz);

  const viewDir = new THREE.Vector3(1, 0.82, 1).normalize();
  camera.position.copy(center).add(viewDir.multiplyScalar(distance + 0.001));
  camera.near = Math.max(0.01, distance / 120);
  camera.far = Math.max(1000, distance * 120);
  camera.updateProjectionMatrix();

  controls.target.copy(center);
  controls.minDistance = Math.max(5, distance * 0.28);
  controls.maxDistance = Math.max(20, distance * 9);
  controls.update();
}

export function resizeRendererToDisplaySize(renderer, camera, controls, targetObject, padding = 1.2) {
  const canvas = renderer.domElement;
  const width = Math.max(1, Math.floor(canvas.clientWidth));
  const height = Math.max(1, Math.floor(canvas.clientHeight));
  const pixelRatio = renderer.getPixelRatio();
  const targetWidth = Math.floor(width * pixelRatio);
  const targetHeight = Math.floor(height * pixelRatio);
  const resized = canvas.width !== targetWidth || canvas.height !== targetHeight;
  if (resized) {
    renderer.setSize(width, height, false);
    if (targetObject) {
      fitCameraToObject(camera, renderer, controls, targetObject, padding);
    } else {
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }
  }
  return resized;
}