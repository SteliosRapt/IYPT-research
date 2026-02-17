import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLExporter } from "three/addons/exporters/STLExporter.js";

import { clamp, roundHundredth, roundTenth, safeNumber } from "./math-utils.js";
import { sampleOutlinePoints } from "./flipo-model.js";
import { addLights, buildToy, disposeNode } from "./toy-builder.js";
import { buildSteinmetz } from "./geometry-steinmetz-view.js";
import { fitCameraToObject, resizeRendererToDisplaySize } from "./three-helpers.js";
import { buildCycle } from "./phases-cycle.js";
import { computeFrameBounds, draw as drawPhasesSideView } from "./phases-side-view.js";
import { fitToyCamera, makeDashedRollingCylinder, syncToyPose } from "./phases-3d-sync.js";
import {
  buildIntersectionSquarePatch,
  cutMeshResolution,
  steinmetzPatchX,
  steinmetzPatchY,
} from "./steinmetz.js";

const ui = {
  radius: document.getElementById("radius"),
  radiusInput: document.getElementById("radiusInput"),
  width: document.getElementById("width"),
  widthInput: document.getElementById("widthInput"),
  height: document.getElementById("height"),
  heightInput: document.getElementById("heightInput"),
  meshDetail: document.getElementById("meshDetail"),
  meshDetailInput: document.getElementById("meshDetailInput"),
  phaseSlider: document.getElementById("phaseSlider"),
  phasePercent: document.getElementById("phasePercent"),
  playPause: document.getElementById("playPause"),
  resetCycle: document.getElementById("resetCycle"),
  loopToggle: document.getElementById("loopToggle"),
  speed: document.getElementById("speed"),
  speedInput: document.getElementById("speedInput"),
  phaseName: document.getElementById("phaseName"),
  phaseIndex: document.getElementById("phaseIndex"),
  geomInfo: document.getElementById("geomInfo"),
  resetDefaults: document.getElementById("resetDefaults"),
  resetView: document.getElementById("resetView"),
  downloadStl: document.getElementById("downloadStl"),
  note: document.getElementById("note"),
  playbackDock: document.getElementById("playbackDock"),
  geoToyCanvas: document.getElementById("geoToyCanvas"),
  geoSteinCanvas: document.getElementById("geoSteinCanvas"),
  phaseSideCanvas: document.getElementById("phaseSideCanvas"),
  phaseToyCanvas: document.getElementById("phaseToyCanvas"),
};

const missingUi = Object.entries(ui)
  .filter(([, node]) => !node)
  .map(([key]) => key);
if (missingUi.length) {
  throw new Error(`Unified simulation missing required elements: ${missingUi.join(", ")}`);
}

const panelToggles = Array.from(document.querySelectorAll("input[data-target-panel]"));

const DEFAULTS = {
  R: 18,
  w: 13,
  h: 1,
  detail: 1.8,
  speed: 1.0,
  loop: true,
};

const params = {
  R: DEFAULTS.R,
  w: DEFAULTS.w,
  h: DEFAULTS.h,
  detail: DEFAULTS.detail,
};

const playback = {
  playhead: 0,
  playing: false,
  loop: DEFAULTS.loop,
  speed: DEFAULTS.speed,
  lastTs: null,
  secondsPerCycle: 8.0,
};

const LIMITS = {
  rMin: 0.2,
  rMax: 300,
  wMin: 0.2,
  hMin: 0.1,
  hMax: 25,
  detailMin: 0.5,
  detailMax: 3.0,
  speedMin: 0.1,
  speedMax: 4.0,
};

const END_EPS = 1e-6;
const GEO_TOY_CAMERA_PADDING = 1.72;
const STEIN_CAMERA_PADDING = 1.56;

let geometryToyGroup = null;
let geometryToyExport = null;
let steinGroup = null;

let phaseOutlineLocal = [];
let phaseCycle = null;
let phaseFrameBounds = null;
let phaseToyGroup = null;
let phaseContactMarker = null;
let phaseRollingCylinder = null;

const geometryToyScene = new THREE.Scene();
geometryToyScene.background = new THREE.Color(0xf8fbff);
const steinScene = new THREE.Scene();
steinScene.background = new THREE.Color(0xf8fbff);
const phaseToyScene = new THREE.Scene();
phaseToyScene.background = new THREE.Color(0xf8fbff);

const geometryToyRenderer = new THREE.WebGLRenderer({
  canvas: ui.geoToyCanvas,
  antialias: true,
  alpha: false,
});
const steinRenderer = new THREE.WebGLRenderer({
  canvas: ui.geoSteinCanvas,
  antialias: true,
  alpha: false,
});
const phaseToyRenderer = new THREE.WebGLRenderer({
  canvas: ui.phaseToyCanvas,
  antialias: true,
  alpha: false,
});

geometryToyRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
steinRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
phaseToyRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

const geometryToyCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 2000);
const steinCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 2000);
const phaseToyCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 4000);
phaseToyCamera.up.set(0, 0, 1);

const geometryToyControls = new OrbitControls(geometryToyCamera, ui.geoToyCanvas);
geometryToyControls.enablePan = false;
geometryToyControls.enableDamping = true;
geometryToyControls.dampingFactor = 0.06;

const steinControls = new OrbitControls(steinCamera, ui.geoSteinCanvas);
steinControls.enableDamping = true;
steinControls.dampingFactor = 0.06;

const phaseToyControls = new OrbitControls(phaseToyCamera, ui.phaseToyCanvas);
phaseToyControls.enableDamping = true;
phaseToyControls.dampingFactor = 0.06;
phaseToyControls.enablePan = false;

addLights(geometryToyScene);
addLights(steinScene);
addLights(phaseToyScene);

const phaseGround = new THREE.Mesh(
  new THREE.PlaneGeometry(2500, 900),
  new THREE.MeshStandardMaterial({
    color: 0xeaf0fa,
    roughness: 0.95,
    metalness: 0.0,
  })
);
phaseGround.position.set(0, 0, 0);
phaseToyScene.add(phaseGround);

const phaseGrid = new THREE.GridHelper(2500, 120, 0xc8d3e4, 0xdbe3ef);
phaseGrid.rotation.x = Math.PI / 2;
phaseGrid.position.z = 0.01;
const phaseGridMats = Array.isArray(phaseGrid.material) ? phaseGrid.material : [phaseGrid.material];
for (const mat of phaseGridMats) {
  mat.transparent = true;
  mat.opacity = 0.35;
}
phaseToyScene.add(phaseGrid);

function panelChecked(id) {
  const toggle = panelToggles.find((item) => item.dataset.targetPanel === id);
  return !!toggle?.checked;
}

function applyPanelVisibility() {
  for (const toggle of panelToggles) {
    const panel = document.getElementById(toggle.dataset.targetPanel);
    if (panel) {
      panel.hidden = !toggle.checked;
    }
  }
}

function updatePlaybackDockVisibility() {
  const phaseVisible = panelChecked("panel-phase-2d") || panelChecked("panel-phase-3d");
  ui.playbackDock.hidden = !phaseVisible;
}

function setPlayButtonLabel() {
  ui.playPause.textContent = playback.playing ? "Pause" : "Play";
  ui.playPause.className = playback.playing ? "" : "primary";
}

function setControlRangesAndClampState() {
  params.R = clamp(roundTenth(params.R), LIMITS.rMin, LIMITS.rMax);
  const wMax = Math.max(LIMITS.wMin, roundTenth(2 * params.R - 0.1));
  params.w = clamp(roundTenth(params.w), LIMITS.wMin, wMax);
  params.h = clamp(roundHundredth(params.h), LIMITS.hMin, LIMITS.hMax);
  params.detail = clamp(roundTenth(params.detail), LIMITS.detailMin, LIMITS.detailMax);
  playback.speed = clamp(roundTenth(playback.speed), LIMITS.speedMin, LIMITS.speedMax);

  ui.radius.min = String(LIMITS.rMin);
  ui.radius.max = String(LIMITS.rMax);
  ui.radiusInput.min = String(LIMITS.rMin);
  ui.radiusInput.max = String(LIMITS.rMax);

  ui.width.min = String(LIMITS.wMin);
  ui.width.max = String(wMax);
  ui.widthInput.min = String(LIMITS.wMin);
  ui.widthInput.max = String(wMax);

  ui.height.min = String(LIMITS.hMin);
  ui.height.max = String(LIMITS.hMax);
  ui.heightInput.min = String(LIMITS.hMin);
  ui.heightInput.max = String(LIMITS.hMax);

  ui.meshDetail.min = String(LIMITS.detailMin);
  ui.meshDetail.max = String(LIMITS.detailMax);
  ui.meshDetailInput.min = String(LIMITS.detailMin);
  ui.meshDetailInput.max = String(LIMITS.detailMax);

  ui.speed.min = String(LIMITS.speedMin);
  ui.speed.max = String(LIMITS.speedMax);
  ui.speedInput.min = String(LIMITS.speedMin);
  ui.speedInput.max = String(LIMITS.speedMax);
}

function syncControlsFromState() {
  ui.radius.value = params.R.toFixed(1);
  ui.radiusInput.value = params.R.toFixed(1);
  ui.width.value = params.w.toFixed(1);
  ui.widthInput.value = params.w.toFixed(1);
  ui.height.value = params.h.toFixed(2);
  ui.heightInput.value = params.h.toFixed(2);
  ui.meshDetail.value = params.detail.toFixed(1);
  ui.meshDetailInput.value = params.detail.toFixed(1);
  ui.speed.value = playback.speed.toFixed(1);
  ui.speedInput.value = playback.speed.toFixed(1);
  ui.loopToggle.checked = playback.loop;
}

function buildToyPatchInfos(R, w, detail) {
  const cutRes = cutMeshResolution(R, w, detail);
  const patchYCut = steinmetzPatchY(R, cutRes.segA, cutRes.segB);
  const patchXCut = steinmetzPatchX(R, cutRes.segA, cutRes.segB);
  const squareAInfo = buildIntersectionSquarePatch(R, w, 1, patchYCut, patchXCut);
  const squareBInfo = buildIntersectionSquarePatch(R, w, -1, patchYCut, patchXCut);
  patchYCut.dispose();
  patchXCut.dispose();
  return [
    {
      center: squareAInfo.center.clone(),
      signZ: squareAInfo.signZ,
      patchSide: squareAInfo.patchSide,
      geometry: squareAInfo.geometry,
    },
    {
      center: squareBInfo.center.clone(),
      signZ: squareBInfo.signZ,
      patchSide: squareBInfo.patchSide,
      geometry: squareBInfo.geometry,
    },
  ];
}

function rebuildGeometryModels() {
  if (geometryToyGroup) {
    geometryToyScene.remove(geometryToyGroup);
    disposeNode(geometryToyGroup);
    geometryToyGroup = null;
  }
  if (steinGroup) {
    steinScene.remove(steinGroup);
    disposeNode(steinGroup);
    steinGroup = null;
  }
  if (geometryToyExport) {
    disposeNode(geometryToyExport);
    geometryToyExport = null;
  }

  const stein = buildSteinmetz(params.R, params.w, params.detail);
  steinGroup = stein.group;
  steinScene.add(steinGroup);

  const toy = buildToy(params.R, params.w, params.h, stein.patchInfos, { includeExportGroup: true });
  geometryToyGroup = toy.group;
  geometryToyExport = toy.exportObject;
  geometryToyScene.add(geometryToyGroup);

  for (const patch of stein.patchInfos) {
    patch.geometry.dispose();
  }

  fitCameraToObject(geometryToyCamera, geometryToyRenderer, geometryToyControls, geometryToyGroup, GEO_TOY_CAMERA_PADDING);
  fitCameraToObject(steinCamera, steinRenderer, steinControls, steinGroup, STEIN_CAMERA_PADDING);
}

function rebuildPhaseModel() {
  phaseOutlineLocal = sampleOutlinePoints(params.R, params.w, params.h, 72, 32);
  phaseCycle = buildCycle(params.R, params.w, params.h);
  phaseFrameBounds = computeFrameBounds(phaseCycle, phaseOutlineLocal, params);

  const phiDeg = (phaseCycle.phiMax * 180) / Math.PI;
  const thetaEdgeDeg = (phaseCycle.thetaEdge * 180) / Math.PI;
  ui.geomInfo.textContent =
    `theta_e = ${thetaEdgeDeg.toFixed(2)} deg, phi_max = ${phiDeg.toFixed(2)} deg, cycle shift = ${phaseCycle.cycleShift.toFixed(2)} cm`;

  if (phaseCycle.phiMax < 1e-4) {
    ui.note.textContent = "w is very small relative to R, so pure rolling phases are nearly zero-duration.";
  } else {
    ui.note.textContent = "";
  }

  if (phaseToyGroup) {
    phaseToyScene.remove(phaseToyGroup);
    disposeNode(phaseToyGroup);
    phaseToyGroup = null;
  }
  if (phaseContactMarker) {
    phaseToyScene.remove(phaseContactMarker);
    disposeNode(phaseContactMarker);
    phaseContactMarker = null;
  }
  if (phaseRollingCylinder) {
    phaseToyScene.remove(phaseRollingCylinder);
    disposeNode(phaseRollingCylinder);
    phaseRollingCylinder = null;
  }

  const patchInfos = buildToyPatchInfos(params.R, params.w, params.detail);
  const toy = buildToy(params.R, params.w, params.h, patchInfos, { includeExportGroup: false });
  phaseToyGroup = toy.group;
  phaseToyScene.add(phaseToyGroup);

  for (const patch of patchInfos) {
    patch.geometry.dispose();
  }

  phaseContactMarker = new THREE.Mesh(
    new THREE.SphereGeometry(Math.max(0.18, params.w * 0.03), 16, 16),
    new THREE.MeshStandardMaterial({
      color: 0xc81f1f,
      roughness: 0.45,
      metalness: 0.1,
    })
  );
  phaseToyScene.add(phaseContactMarker);

  phaseRollingCylinder = makeDashedRollingCylinder(params.R, params.w);
  phaseRollingCylinder.visible = false;
  phaseToyScene.add(phaseRollingCylinder);

  fitToyCamera(phaseToyCamera, phaseToyControls, ui.phaseToyCanvas, phaseToyGroup, phaseFrameBounds, params);
  drawPhaseFrame();
}

function drawPhaseFrame() {
  const state = drawPhasesSideView(
    ui.phaseSideCanvas,
    phaseCycle,
    playback,
    phaseOutlineLocal,
    phaseFrameBounds,
    params,
    ui
  );
  syncToyPose(phaseToyGroup, phaseContactMarker, phaseRollingCylinder, state);
}

function rebuildAll() {
  setControlRangesAndClampState();
  syncControlsFromState();
  playback.playhead = Math.min(playback.playhead, 1 - END_EPS);
  rebuildGeometryModels();
  rebuildPhaseModel();
}

function resetAllToDefaults() {
  params.R = DEFAULTS.R;
  params.w = DEFAULTS.w;
  params.h = DEFAULTS.h;
  params.detail = DEFAULTS.detail;
  playback.speed = DEFAULTS.speed;
  playback.loop = DEFAULTS.loop;
  playback.playhead = 0;
  playback.playing = false;
  setPlayButtonLabel();
  rebuildAll();
}

function bindParam(rangeEl, inputEl, key) {
  rangeEl.addEventListener("input", () => {
    params[key] = safeNumber(rangeEl.value, params[key]);
    rebuildAll();
  });
  inputEl.addEventListener("change", () => {
    params[key] = safeNumber(inputEl.value, params[key]);
    rebuildAll();
  });
}

bindParam(ui.radius, ui.radiusInput, "R");
bindParam(ui.width, ui.widthInput, "w");
bindParam(ui.height, ui.heightInput, "h");
bindParam(ui.meshDetail, ui.meshDetailInput, "detail");

ui.speed.addEventListener("input", () => {
  playback.speed = clamp(safeNumber(ui.speed.value, playback.speed), LIMITS.speedMin, LIMITS.speedMax);
  ui.speedInput.value = playback.speed.toFixed(1);
});

ui.speedInput.addEventListener("change", () => {
  playback.speed = clamp(safeNumber(ui.speedInput.value, playback.speed), LIMITS.speedMin, LIMITS.speedMax);
  ui.speed.value = playback.speed.toFixed(1);
  ui.speedInput.value = playback.speed.toFixed(1);
});

ui.phaseSlider.addEventListener("input", () => {
  const raw = clamp(safeNumber(ui.phaseSlider.value, 0), 0, 1000) / 1000;
  playback.playhead = raw >= 1 ? 1 - END_EPS : raw;
  playback.playing = false;
  setPlayButtonLabel();
  drawPhaseFrame();
});

ui.playPause.addEventListener("click", () => {
  if (!playback.loop && playback.playhead >= 1 - END_EPS) {
    playback.playhead = 0;
  }
  playback.playing = !playback.playing;
  setPlayButtonLabel();
});

ui.resetCycle.addEventListener("click", () => {
  playback.playhead = 0;
  playback.playing = false;
  setPlayButtonLabel();
  drawPhaseFrame();
});

ui.loopToggle.addEventListener("change", () => {
  playback.loop = ui.loopToggle.checked;
});

ui.resetDefaults.addEventListener("click", () => {
  resetAllToDefaults();
});

ui.resetView.addEventListener("click", () => {
  fitCameraToObject(geometryToyCamera, geometryToyRenderer, geometryToyControls, geometryToyGroup, GEO_TOY_CAMERA_PADDING);
  fitCameraToObject(steinCamera, steinRenderer, steinControls, steinGroup, STEIN_CAMERA_PADDING);
  fitToyCamera(phaseToyCamera, phaseToyControls, ui.phaseToyCanvas, phaseToyGroup, phaseFrameBounds, params);
  drawPhaseFrame();
});

ui.downloadStl.addEventListener("click", () => {
  try {
    if (!geometryToyExport) {
      return;
    }
    geometryToyExport.updateMatrixWorld(true);
    const exporter = new STLExporter();
    const stl = exporter.parse(geometryToyExport, { binary: false });
    const blob =
      stl instanceof DataView
        ? new Blob([stl], { type: "application/octet-stream" })
        : new Blob([stl], { type: "model/stl" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `flipo_flip_R${params.R}_w${params.w}_h${params.h}.stl`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  } catch (err) {
    ui.note.textContent = `STL export failed: ${String(err)}`;
  }
});

for (const toggle of panelToggles) {
  toggle.addEventListener("change", () => {
    applyPanelVisibility();
    updatePlaybackDockVisibility();
    drawPhaseFrame();
    window.dispatchEvent(new Event("resize"));
  });
}

window.addEventListener("resize", () => {
  fitCameraToObject(geometryToyCamera, geometryToyRenderer, geometryToyControls, geometryToyGroup, GEO_TOY_CAMERA_PADDING);
  fitCameraToObject(steinCamera, steinRenderer, steinControls, steinGroup, STEIN_CAMERA_PADDING);
  fitToyCamera(phaseToyCamera, phaseToyControls, ui.phaseToyCanvas, phaseToyGroup, phaseFrameBounds, params);
  drawPhaseFrame();
});

function animate(ts) {
  if (playback.lastTs === null) {
    playback.lastTs = ts;
  }

  const dt = Math.max(0, (ts - playback.lastTs) * 0.001);
  playback.lastTs = ts;

  if (playback.playing) {
    playback.playhead += (dt * playback.speed) / playback.secondsPerCycle;
    if (playback.loop) {
      if (playback.playhead >= 1) {
        playback.playhead -= Math.floor(playback.playhead);
      }
    } else if (playback.playhead >= 1 - END_EPS) {
      playback.playhead = 1 - END_EPS;
      playback.playing = false;
      setPlayButtonLabel();
    }
  }

  drawPhaseFrame();

  resizeRendererToDisplaySize(
    geometryToyRenderer,
    geometryToyCamera,
    geometryToyControls,
    geometryToyGroup,
    GEO_TOY_CAMERA_PADDING
  );
  resizeRendererToDisplaySize(steinRenderer, steinCamera, steinControls, steinGroup, STEIN_CAMERA_PADDING);
  if (resizeRendererToDisplaySize(phaseToyRenderer, phaseToyCamera, phaseToyControls, null, 1.0)) {
    fitToyCamera(phaseToyCamera, phaseToyControls, ui.phaseToyCanvas, phaseToyGroup, phaseFrameBounds, params);
  }

  geometryToyControls.update();
  steinControls.update();
  phaseToyControls.update();

  geometryToyRenderer.render(geometryToyScene, geometryToyCamera);
  steinRenderer.render(steinScene, steinCamera);
  phaseToyRenderer.render(phaseToyScene, phaseToyCamera);

  requestAnimationFrame(animate);
}

applyPanelVisibility();
updatePlaybackDockVisibility();
setPlayButtonLabel();
rebuildAll();
requestAnimationFrame(animate);
