import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

import { clamp, safeNumber } from "./math-utils.js";
import { sampleOutlinePoints } from "./flipo-model.js";
import {
  buildIntersectionSquarePatch,
  cutMeshResolution,
  steinmetzPatchX,
  steinmetzPatchY,
} from "./steinmetz.js";
import { addLights, buildToy, disposeNode } from "./toy-builder.js";
import { resizeRendererToDisplaySize } from "./three-helpers.js";
import { buildCycle } from "./phases-cycle.js";
import { computeFrameBounds, draw as drawSideView } from "./phases-side-view.js";
import { fitToyCamera, makeDashedRollingCylinder, syncToyPose } from "./phases-3d-sync.js";

const ui = {
  radius: document.getElementById("radius"),
  radiusInput: document.getElementById("radiusInput"),
  width: document.getElementById("width"),
  widthInput: document.getElementById("widthInput"),
  height: document.getElementById("height"),
  heightInput: document.getElementById("heightInput"),
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
  note: document.getElementById("note"),
  sideCanvas: document.getElementById("sideCanvas"),
  toyCanvas: document.getElementById("toyCanvas"),
};

const DEFAULTS = {
  R: 18,
  w: 13,
  h: 1,
  speed: 1.0,
};

const params = {
  R: DEFAULTS.R,
  w: DEFAULTS.w,
  h: DEFAULTS.h,
};

const playback = {
  playhead: 0,
  playing: false,
  loop: true,
  speed: DEFAULTS.speed,
  lastTs: null,
  secondsPerCycle: 8.0,
};

const END_EPS = 1e-6;
const TOY_MESH_DETAIL = 1.8;

let outlineLocal = [];
let cycle = null;
let frameBounds = null;
let toyGroup = null;
let toyContactMarker = null;
let toyRollingCylinder = null;

const toyScene = new THREE.Scene();
toyScene.background = new THREE.Color(0xf8fbff);

const toyRenderer = new THREE.WebGLRenderer({ canvas: ui.toyCanvas, antialias: true, alpha: false });
toyRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

const toyCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 4000);
toyCamera.up.set(0, 0, 1);

const toyControls = new OrbitControls(toyCamera, ui.toyCanvas);
toyControls.enableDamping = true;
toyControls.dampingFactor = 0.06;
toyControls.enablePan = false;

addLights(toyScene);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(2500, 900),
  new THREE.MeshStandardMaterial({
    color: 0xeaf0fa,
    roughness: 0.95,
    metalness: 0.0,
  })
);
ground.position.set(0, 0, 0);
toyScene.add(ground);

const grid = new THREE.GridHelper(2500, 120, 0xc8d3e4, 0xdbe3ef);
grid.rotation.x = Math.PI / 2;
grid.position.z = 0.01;
const gridMats = Array.isArray(grid.material) ? grid.material : [grid.material];
for (const mat of gridMats) {
  mat.transparent = true;
  mat.opacity = 0.35;
}
toyScene.add(grid);

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

function rebuildToyModel() {
  if (toyGroup) {
    toyScene.remove(toyGroup);
    disposeNode(toyGroup);
    toyGroup = null;
  }
  if (toyContactMarker) {
    toyScene.remove(toyContactMarker);
    disposeNode(toyContactMarker);
    toyContactMarker = null;
  }
  if (toyRollingCylinder) {
    toyScene.remove(toyRollingCylinder);
    disposeNode(toyRollingCylinder);
    toyRollingCylinder = null;
  }

  const patchInfos = buildToyPatchInfos(params.R, params.w, TOY_MESH_DETAIL);
  const toy = buildToy(params.R, params.w, params.h, patchInfos, { includeExportGroup: false });
  toyGroup = toy.group;
  toyScene.add(toyGroup);

  for (const patch of patchInfos) {
    patch.geometry.dispose();
  }

  toyContactMarker = new THREE.Mesh(
    new THREE.SphereGeometry(Math.max(0.18, params.w * 0.03), 16, 16),
    new THREE.MeshStandardMaterial({
      color: 0xc81f1f,
      roughness: 0.45,
      metalness: 0.1,
    })
  );
  toyScene.add(toyContactMarker);

  toyRollingCylinder = makeDashedRollingCylinder(params.R, params.w);
  toyRollingCylinder.visible = false;
  toyScene.add(toyRollingCylinder);
}

function drawFrame() {
  const state = drawSideView(ui.sideCanvas, cycle, playback, outlineLocal, frameBounds, params, ui);
  syncToyPose(toyGroup, toyContactMarker, toyRollingCylinder, state);
}

function applyControlLimits() {
  const rMin = 0.2;
  const rMax = 300;
  const hMin = 0.1;
  const hMax = 25;

  params.R = clamp(params.R, rMin, rMax);
  const wMax = Math.max(0.2, 2 * params.R - 0.1);
  params.w = clamp(params.w, 0.2, wMax);
  params.h = clamp(params.h, hMin, hMax);

  ui.radius.min = String(rMin);
  ui.radius.max = String(rMax);
  ui.radiusInput.min = String(rMin);
  ui.radiusInput.max = String(rMax);
  ui.width.min = "0.2";
  ui.width.max = String(wMax);
  ui.widthInput.min = "0.2";
  ui.widthInput.max = String(wMax);
  ui.height.min = String(hMin);
  ui.height.max = String(hMax);
  ui.heightInput.min = String(hMin);
  ui.heightInput.max = String(hMax);
}

function syncGeometryControls() {
  ui.radius.value = params.R.toFixed(1);
  ui.radiusInput.value = params.R.toFixed(1);
  ui.width.value = params.w.toFixed(1);
  ui.widthInput.value = params.w.toFixed(1);
  ui.height.value = params.h.toFixed(2);
  ui.heightInput.value = params.h.toFixed(2);
  ui.speed.value = playback.speed.toFixed(1);
  ui.speedInput.value = playback.speed.toFixed(1);
  ui.loopToggle.checked = playback.loop;
}

function setPlayButtonLabel() {
  ui.playPause.textContent = playback.playing ? "Pause" : "Play";
  ui.playPause.className = playback.playing ? "" : "primary";
}

function rebuild() {
  applyControlLimits();
  syncGeometryControls();

  outlineLocal = sampleOutlinePoints(params.R, params.w, params.h, 72, 32);
  cycle = buildCycle(params.R, params.w, params.h);
  frameBounds = computeFrameBounds(cycle, outlineLocal, params);

  const phiDeg = (cycle.phiMax * 180) / Math.PI;
  const thetaEdgeDeg = (cycle.thetaEdge * 180) / Math.PI;
  ui.geomInfo.textContent =
    `theta_e = ${thetaEdgeDeg.toFixed(2)} deg, phi_max = ${phiDeg.toFixed(2)} deg, cycle shift = ${cycle.cycleShift.toFixed(2)} cm`;

  if (cycle.phiMax < 1e-4) {
    ui.note.textContent = "w is very small relative to R, so pure rolling phases are nearly zero-duration.";
  } else {
    ui.note.textContent = "";
  }

  rebuildToyModel();
  fitToyCamera(toyCamera, toyControls, ui.toyCanvas, toyGroup, frameBounds, params);
  drawFrame();
}

function updateParam(key, value) {
  params[key] = safeNumber(value, params[key]);
  playback.playhead = Math.min(playback.playhead, 1 - END_EPS);
  rebuild();
}

function bindParam(rangeEl, inputEl, key) {
  rangeEl.addEventListener("input", () => {
    updateParam(key, rangeEl.value);
  });
  inputEl.addEventListener("change", () => {
    updateParam(key, inputEl.value);
  });
}

bindParam(ui.radius, ui.radiusInput, "R");
bindParam(ui.width, ui.widthInput, "w");
bindParam(ui.height, ui.heightInput, "h");

ui.speed.addEventListener("input", () => {
  playback.speed = clamp(safeNumber(ui.speed.value, playback.speed), 0.1, 4);
  ui.speedInput.value = playback.speed.toFixed(1);
});

ui.speedInput.addEventListener("change", () => {
  playback.speed = clamp(safeNumber(ui.speedInput.value, playback.speed), 0.1, 4);
  ui.speed.value = playback.speed.toFixed(1);
  ui.speedInput.value = playback.speed.toFixed(1);
});

ui.phaseSlider.addEventListener("input", () => {
  const raw = clamp(safeNumber(ui.phaseSlider.value, 0), 0, 1000) / 1000;
  playback.playhead = raw >= 1 ? 1 - END_EPS : raw;
  playback.playing = false;
  setPlayButtonLabel();
  drawFrame();
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
  drawFrame();
});

ui.loopToggle.addEventListener("change", () => {
  playback.loop = ui.loopToggle.checked;
});

window.addEventListener("resize", () => {
  fitToyCamera(toyCamera, toyControls, ui.toyCanvas, toyGroup, frameBounds, params);
  drawFrame();
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

  drawFrame();
  if (resizeRendererToDisplaySize(toyRenderer, toyCamera, toyControls, null, 1.0)) {
    fitToyCamera(toyCamera, toyControls, ui.toyCanvas, toyGroup, frameBounds, params);
  }
  toyControls.update();
  toyRenderer.render(toyScene, toyCamera);
  requestAnimationFrame(animate);
}

applyControlLimits();
syncGeometryControls();
setPlayButtonLabel();
rebuild();
requestAnimationFrame(animate);