import { modelTerms, sampleOutlinePoints, maxPureRollingAngle } from "./flipo-model.js";

export function worldPoseForRolling(points, R, w, h, angle) {
  const t = modelTerms(R, w, h);
  const circleCenterLocal = { x: 0, y: t.yBottomCenter };
  const circleCenterWorld = { x: R * angle, y: R };
  const bodyAngle = -angle;
  const c = Math.cos(bodyAngle);
  const s = Math.sin(bodyAngle);

  return points.map((p) => {
    const dx = p.x - circleCenterLocal.x;
    const py = p.y - circleCenterLocal.y;
    const xr = c * dx - s * py + circleCenterWorld.x;
    const yr = s * dx + c * py + circleCenterWorld.y;
    return { x: xr, y: yr };
  });
}

export function computeSideFrameBounds(R, w, h) {
  const localPoints = sampleOutlinePoints(R, w, h);
  const maxAngle = maxPureRollingAngle(R, w, h);
  const samples = 42;
  let xMin = Infinity;
  let xMax = -Infinity;
  let yMin = Infinity;
  let yMax = -Infinity;

  for (let i = 0; i <= samples; i += 1) {
    const f = -1 + (2 * i) / samples;
    const angle = f * maxAngle;
    const worldPoints = worldPoseForRolling(localPoints, R, w, h, angle);
    const cx = R * angle;
    for (const p of worldPoints) {
      xMin = Math.min(xMin, p.x);
      xMax = Math.max(xMax, p.x);
      yMin = Math.min(yMin, p.y);
      yMax = Math.max(yMax, p.y);
    }
    xMin = Math.min(xMin, cx - R);
    xMax = Math.max(xMax, cx + R);
    yMin = Math.min(yMin, 0, R - R);
    yMax = Math.max(yMax, R + R);
  }

  const xAbs = Math.max(Math.abs(xMin), Math.abs(xMax));
  const spanX = Math.max(1e-6, 2 * xAbs);
  const floorY = Math.min(0, yMin);
  const spanY = Math.max(1e-6, yMax - floorY);
  const padX = Math.max(0.8, spanX * 0.14);
  const padY = Math.max(0.8, spanY * 0.2);

  return {
    maxAngle,
    xMin: -xAbs - padX,
    xMax: xAbs + padX,
    yMin: floorY - padY * 0.2,
    yMax: yMax + padY,
  };
}

export function drawSideView(canvas, params, sideFrame, rollingAngle) {
  const rect = canvas.getBoundingClientRect();
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  const width = Math.max(30, Math.floor(rect.width));
  const height = Math.max(30, Math.floor(rect.height));
  canvas.width = Math.floor(width * dpr);
  canvas.height = Math.floor(height * dpr);

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);

  const frame = sideFrame || computeSideFrameBounds(params.R, params.w, params.h);
  const localPoints = sampleOutlinePoints(params.R, params.w, params.h);
  const worldPoints = worldPoseForRolling(localPoints, params.R, params.w, params.h, rollingAngle);
  const circleCenter = { x: params.R * rollingAngle, y: params.R };

  const innerPad = 18;
  const sx = (width - 2 * innerPad) / Math.max(1e-6, frame.xMax - frame.xMin);
  const sy = (height - 2 * innerPad) / Math.max(1e-6, frame.yMax - frame.yMin);
  const scale = Math.min(sx, sy);

  const tx = innerPad - frame.xMin * scale;
  const ty = height - innerPad + frame.yMin * scale;

  function mapX(x) {
    return tx + x * scale;
  }
  function mapY(y) {
    return ty - y * scale;
  }

  const groundY = mapY(0);
  ctx.lineWidth = 2;
  ctx.strokeStyle = "#495b75";
  ctx.beginPath();
  ctx.moveTo(0, groundY);
  ctx.lineTo(width, groundY);
  ctx.stroke();

  ctx.setLineDash([6, 6]);
  ctx.strokeStyle = "#9aa8bd";
  ctx.lineWidth = 1.2;
  ctx.beginPath();
  ctx.moveTo(mapX(-params.R * frame.maxAngle), groundY);
  ctx.lineTo(mapX(params.R * frame.maxAngle), groundY);
  ctx.stroke();

  ctx.setLineDash([8, 7]);
  ctx.strokeStyle = "#7a8aa2";
  ctx.lineWidth = 1.4;
  ctx.beginPath();
  ctx.arc(mapX(circleCenter.x), mapY(circleCenter.y), params.R * scale, 0, Math.PI * 2);
  ctx.stroke();
  ctx.beginPath();
  ctx.moveTo(mapX(circleCenter.x), mapY(circleCenter.y - params.R));
  ctx.lineTo(mapX(circleCenter.x), mapY(circleCenter.y + params.R));
  ctx.stroke();
  ctx.setLineDash([]);

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
  ctx.arc(mapX(circleCenter.x), mapY(0), 4, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#111111";
  ctx.beginPath();
  ctx.arc(mapX(circleCenter.x), mapY(circleCenter.y), 3.4, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = "#314766";
  ctx.font = "12px Segoe UI, sans-serif";
  ctx.fillText("Dashed circle: rolling parent cylinder", 12, 18);
  ctx.fillText("Red point: instantaneous contact", 12, 34);
  ctx.fillText("Black point: cylinder center", 12, 50);
}