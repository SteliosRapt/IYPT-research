import { safeNumber } from "./math-utils.js";
import { worldPoint } from "./phases-cycle.js";

const END_EPS = 1e-6;

function resizeCanvasToDisplaySize(canvas) {
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(40, Math.floor(rect.width));
  const height = Math.max(40, Math.floor(rect.height));
  const targetW = Math.floor(width * dpr);
  const targetH = Math.floor(height * dpr);
  if (canvas.width !== targetW || canvas.height !== targetH) {
    canvas.width = targetW;
    canvas.height = targetH;
  }
  return { width, height, dpr };
}

export function computeFrameBounds(cycle, outlineLocal, params) {
  const samples = 360;
  let xMin = Infinity;
  let xMax = -Infinity;
  let yMin = Infinity;
  let yMax = -Infinity;

  for (let i = 0; i <= samples; i += 1) {
    const u = i / samples;
    const state = cycle.stateAt(u * (1 - END_EPS));
    for (const local of outlineLocal) {
      const wp = worldPoint(local, state.pose);
      xMin = Math.min(xMin, wp.x);
      xMax = Math.max(xMax, wp.x);
      yMin = Math.min(yMin, wp.y);
      yMax = Math.max(yMax, wp.y);
    }
    xMin = Math.min(xMin, state.contactPoint.x);
    xMax = Math.max(xMax, state.contactPoint.x);
    yMin = Math.min(yMin, 0);
    if (state.circleCenter) {
      xMin = Math.min(xMin, state.circleCenter.x - params.R);
      xMax = Math.max(xMax, state.circleCenter.x + params.R);
      yMin = Math.min(yMin, state.circleCenter.y - params.R);
      yMax = Math.max(yMax, state.circleCenter.y + params.R);
    }
  }

  const spanX = Math.max(1e-6, xMax - xMin);
  const spanY = Math.max(1e-6, yMax - yMin);
  const padX = Math.max(0.9, spanX * 0.12);
  const padY = Math.max(0.9, spanY * 0.16);

  return {
    xMin: xMin - padX,
    xMax: xMax + padX,
    yMin: Math.min(-0.25 * padY, yMin - 0.12 * padY),
    yMax: yMax + padY,
  };
}

export function draw(canvas, cycle, playback, outlineLocal, frameBounds, params, ui) {
  const { width, height, dpr } = resizeCanvasToDisplaySize(canvas);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);

  if (!cycle || !frameBounds) {
    return null;
  }

  const state = cycle.stateAt(playback.playhead);

  const innerPad = 18;
  const sx = (width - 2 * innerPad) / Math.max(1e-9, frameBounds.xMax - frameBounds.xMin);
  const sy = (height - 2 * innerPad) / Math.max(1e-9, frameBounds.yMax - frameBounds.yMin);
  const scale = Math.min(sx, sy);
  const tx = innerPad - frameBounds.xMin * scale;
  const ty = height - innerPad + frameBounds.yMin * scale;

  function mapX(x) {
    return tx + x * scale;
  }

  function mapY(y) {
    return ty - y * scale;
  }

  const groundY = mapY(0);
  ctx.fillStyle = "#f8fbff";
  ctx.fillRect(0, 0, width, height);

  ctx.strokeStyle = "#4a5e79";
  ctx.lineWidth = 2;
  ctx.beginPath();
  ctx.moveTo(0, groundY);
  ctx.lineTo(width, groundY);
  ctx.stroke();

  const worldPoints = outlineLocal.map((pt) => worldPoint(pt, state.pose));
  const contactDisplay = state.contactPoint;
  const circleDisplay = state.circleCenter;

  if (circleDisplay) {
    ctx.setLineDash([8, 7]);
    ctx.strokeStyle = "#7a8aa2";
    ctx.lineWidth = 1.4;
    ctx.beginPath();
    ctx.arc(mapX(circleDisplay.x), mapY(circleDisplay.y), params.R * scale, 0, Math.PI * 2);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(mapX(circleDisplay.x), mapY(circleDisplay.y - params.R));
    ctx.lineTo(mapX(circleDisplay.x), mapY(circleDisplay.y + params.R));
    ctx.stroke();
    ctx.setLineDash([]);
  }

  ctx.beginPath();
  ctx.moveTo(mapX(worldPoints[0].x), mapY(worldPoints[0].y));
  for (let i = 1; i < worldPoints.length; i += 1) {
    ctx.lineTo(mapX(worldPoints[i].x), mapY(worldPoints[i].y));
  }
  ctx.closePath();
  ctx.fillStyle = "#6fa7e5";
  ctx.strokeStyle = "#1f4f88";
  ctx.lineWidth = 2;
  ctx.fill();
  ctx.stroke();

  ctx.fillStyle = "#c81f1f";
  ctx.beginPath();
  ctx.arc(mapX(contactDisplay.x), mapY(contactDisplay.y), 4, 0, Math.PI * 2);
  ctx.fill();

  if (circleDisplay) {
    ctx.fillStyle = "#111111";
    ctx.beginPath();
    ctx.arc(mapX(circleDisplay.x), mapY(circleDisplay.y), 3.4, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = "#314766";
  ctx.font = "12px Segoe UI, sans-serif";
  if (state.mode === "roll") {
    ctx.fillText("Dashed circle: active parent cylinder (pure patch rolling)", 12, 18);
  } else {
    ctx.fillText("Patch-switch pivot phase (cylinder outline hidden)", 12, 18);
  }
  ctx.fillText("Red point: instantaneous contact/pivot", 12, 34);

  ui.phaseName.textContent = state.phaseName;
  ui.phaseIndex.textContent = `${state.phaseIndex} / ${state.phaseCount}`;
  ui.phasePercent.textContent = `${(state.displayU * 100).toFixed(1)}%`;

  const sliderPct = state.displayU * 1000;
  if (Math.abs(safeNumber(ui.phaseSlider.value, 0) - sliderPct) > 0.35) {
    ui.phaseSlider.value = sliderPct.toFixed(1);
  }

  return state;
}