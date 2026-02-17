import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { STLExporter } from "three/addons/exporters/STLExporter.js";

import { clamp, roundHundredth, roundTenth, safeNumber } from "./math-utils.js";
import { maxPureRollingAngle } from "./flipo-model.js";
import { addLights, buildToy, disposeNode } from "./toy-builder.js";
import { buildSteinmetz } from "./geometry-steinmetz-view.js";
import { computeSideFrameBounds, drawSideView } from "./geometry-side-view.js";
import { fitCameraToObject, resizeRendererToDisplaySize } from "./three-helpers.js";

const ui = {
  radius: document.getElementById("radius"),
  radiusInput: document.getElementById("radiusInput"),
  width: document.getElementById("width"),
  widthInput: document.getElementById("widthInput"),
  height: document.getElementById("height"),
  heightInput: document.getElementById("heightInput"),
  meshDetail: document.getElementById("meshDetail"),
  meshDetailInput: document.getElementById("meshDetailInput"),
  rollSlider: document.getElementById("rollSlider"),
  rollVal: document.getElementById("rollVal"),
  resetDefaults: document.getElementById("resetDefaults"),
  resetView: document.getElementById("resetView"),
  downloadStl: document.getElementById("downloadStl"),
  note: document.getElementById("note"),
  sideCanvas: document.getElementById("sideCanvas"),
  toyCanvas: document.getElementById("toyCanvas"),
  steinCanvas: document.getElementById("steinCanvas"),
};

const DEFAULT_PARAMS = {
  R: 18,
  w: 13,
  h: 1,
  detail: 1.8,
};

const params = {
  R: DEFAULT_PARAMS.R,
  w: DEFAULT_PARAMS.w,
  h: DEFAULT_PARAMS.h,
  detail: DEFAULT_PARAMS.detail,
};

let rollingAngle = 0;
let sideFrame = null;
let toyGroup = null;
let toyExportObject = null;
let steinGroup = null;

const PARAM_MIN = 0.1;
const TOY_CAMERA_PADDING = 1.72;
const STEIN_CAMERA_PADDING = 1.56;
const ROLL_GUARD_RAD = 0.02;

const toyScene = new THREE.Scene();
toyScene.background = new THREE.Color(0xf8fbff);
const steinScene = new THREE.Scene();
steinScene.background = new THREE.Color(0xf8fbff);

const toyRenderer = new THREE.WebGLRenderer({ canvas: ui.toyCanvas, antialias: true, alpha: false });
const steinRenderer = new THREE.WebGLRenderer({ canvas: ui.steinCanvas, antialias: true, alpha: false });
toyRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
steinRenderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

const toyCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 2000);
const steinCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 2000);

const toyControls = new OrbitControls(toyCamera, ui.toyCanvas);
toyControls.enablePan = false;
toyControls.enableDamping = true;
toyControls.dampingFactor = 0.06;

const steinControls = new OrbitControls(steinCamera, ui.steinCanvas);
steinControls.enableDamping = true;
steinControls.dampingFactor = 0.06;

addLights(toyScene);
addLights(steinScene);

function setSliderRanges() {
  const rMax = 300;
  const wMax = Math.max(PARAM_MIN, roundTenth(2 * params.R - 0.1));
  const hMax = 10;

  ui.radius.max = String(rMax);
  ui.width.max = String(wMax);
  ui.height.max = String(hMax);
  ui.radiusInput.max = String(rMax);
  ui.widthInput.max = String(wMax);
  ui.heightInput.max = String(hMax);
  ui.meshDetail.max = "3.0";
  ui.meshDetailInput.max = "3.0";

  params.R = clamp(roundTenth(params.R), PARAM_MIN, rMax);
  params.w = clamp(roundTenth(params.w), PARAM_MIN, wMax);
  params.h = clamp(roundHundredth(params.h), PARAM_MIN, hMax);
  params.detail = clamp(roundTenth(params.detail), 0.5, 3.0);
}

function updateControlsFromState() {
  ui.radius.value = params.R.toFixed(1);
  ui.radiusInput.value = params.R.toFixed(1);
  ui.width.value = params.w.toFixed(1);
  ui.widthInput.value = params.w.toFixed(1);
  ui.height.value = params.h.toFixed(2);
  ui.heightInput.value = params.h.toFixed(2);
  ui.meshDetail.value = params.detail.toFixed(1);
  ui.meshDetailInput.value = params.detail.toFixed(1);
}

function applyInputState(next) {
  params.R = safeNumber(next.R, params.R);
  params.w = safeNumber(next.w, params.w);
  params.h = safeNumber(next.h, params.h);
  params.detail = safeNumber(next.detail, params.detail);
  setSliderRanges();
  updateControlsFromState();
}

function currentRollFraction() {
  return clamp(safeNumber(ui.rollSlider.value, 0) / 100, -1, 1);
}

function updateRollReadout(maxAngle) {
  const fraction = currentRollFraction();
  const angleDeg = THREE.MathUtils.radToDeg(fraction * maxAngle);
  ui.rollVal.textContent = `${(fraction * 100).toFixed(1)}% | ${angleDeg.toFixed(1)}°`;
}

function drawCurrentSideView() {
  if (!sideFrame) {
    return;
  }
  rollingAngle = sideFrame.maxAngle * currentRollFraction();
  updateRollReadout(sideFrame.maxAngle);
  drawSideView(ui.sideCanvas, params, sideFrame, rollingAngle);
}

function rebuildModels() {
  const computedFrame = computeSideFrameBounds(params.R, params.w, params.h);
  const guardedMaxAngle = Math.max(0, maxPureRollingAngle(params.R, params.w, params.h) - ROLL_GUARD_RAD);
  sideFrame = {
    ...computedFrame,
    maxAngle: Math.min(computedFrame.maxAngle, guardedMaxAngle),
  };

  const hasRollingRange = sideFrame.maxAngle > 1e-4;
  ui.rollSlider.disabled = !hasRollingRange;
  if (!hasRollingRange) {
    ui.rollSlider.value = "0";
  }

  if (toyGroup) {
    toyScene.remove(toyGroup);
    disposeNode(toyGroup);
  }
  if (steinGroup) {
    steinScene.remove(steinGroup);
    disposeNode(steinGroup);
  }
  if (toyExportObject) {
    disposeNode(toyExportObject);
  }

  const stein = buildSteinmetz(params.R, params.w, params.detail);
  steinGroup = stein.group;
  steinScene.add(steinGroup);

  const toy = buildToy(params.R, params.w, params.h, stein.patchInfos, { includeExportGroup: true });
  toyGroup = toy.group;
  toyExportObject = toy.exportObject;
  toyScene.add(toyGroup);

  for (const patch of stein.patchInfos) {
    patch.geometry.dispose();
  }

  fitCameraToObject(toyCamera, toyRenderer, toyControls, toyGroup, TOY_CAMERA_PADDING);
  fitCameraToObject(steinCamera, steinRenderer, steinControls, steinGroup, STEIN_CAMERA_PADDING);
  drawCurrentSideView();

  ui.note.textContent =
    `Red caps are clipped to side w with triangle clipping; toy uses those exact 3D caps. ` +
    `Center dashed circle marks the cylinder reference at the solid center. ` +
    `Mesh detail factor: ${params.detail.toFixed(1)}.`;
  ui.note.className = "";
}

function updateParam(key, rawValue) {
  const next = { R: params.R, w: params.w, h: params.h, detail: params.detail };
  next[key] = safeNumber(rawValue, next[key]);
  applyInputState(next);
  rebuildModels();
}

function bindParamControls(rangeInput, numberInput, key) {
  rangeInput.addEventListener("input", () => {
    updateParam(key, rangeInput.value);
  });
  numberInput.addEventListener("change", () => {
    updateParam(key, numberInput.value);
  });
}

bindParamControls(ui.radius, ui.radiusInput, "R");
bindParamControls(ui.width, ui.widthInput, "w");
bindParamControls(ui.height, ui.heightInput, "h");
bindParamControls(ui.meshDetail, ui.meshDetailInput, "detail");

ui.rollSlider.addEventListener("input", () => {
  drawCurrentSideView();
});

ui.resetDefaults.addEventListener("click", () => {
  applyInputState({
    R: DEFAULT_PARAMS.R,
    w: DEFAULT_PARAMS.w,
    h: DEFAULT_PARAMS.h,
    detail: DEFAULT_PARAMS.detail,
  });
  ui.rollSlider.value = "0";
  rebuildModels();
});

ui.resetView.addEventListener("click", () => {
  fitCameraToObject(toyCamera, toyRenderer, toyControls, toyGroup, TOY_CAMERA_PADDING);
  fitCameraToObject(steinCamera, steinRenderer, steinControls, steinGroup, STEIN_CAMERA_PADDING);
  drawCurrentSideView();
});

ui.downloadStl.addEventListener("click", () => {
  try {
    if (!toyExportObject) {
      return;
    }
    toyExportObject.updateMatrixWorld(true);
    const exporter = new STLExporter();
    const stl = exporter.parse(toyExportObject, { binary: false });
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
    ui.note.className = "warn";
  }
});

window.addEventListener("resize", () => {
  fitCameraToObject(toyCamera, toyRenderer, toyControls, toyGroup, TOY_CAMERA_PADDING);
  fitCameraToObject(steinCamera, steinRenderer, steinControls, steinGroup, STEIN_CAMERA_PADDING);
  drawCurrentSideView();
});

setSliderRanges();
updateControlsFromState();
rebuildModels();

function animate() {
  requestAnimationFrame(animate);

  resizeRendererToDisplaySize(toyRenderer, toyCamera, toyControls, toyGroup, TOY_CAMERA_PADDING);
  resizeRendererToDisplaySize(steinRenderer, steinCamera, steinControls, steinGroup, STEIN_CAMERA_PADDING);

  toyControls.update();
  steinControls.update();
  toyRenderer.render(toyScene, toyCamera);
  steinRenderer.render(steinScene, steinCamera);
}

animate();