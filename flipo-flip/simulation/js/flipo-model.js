export function modelTerms(R, w, h) {
  const halfW = w / 2;
  const halfH = h / 2;
  const capOffset = Math.sqrt(Math.max(1e-8, R * R - halfW * halfW));
  const thetaEdge = Math.atan2(capOffset, halfW);
  const yTopCenter = halfH - capOffset;
  const yBottomCenter = -halfH + capOffset;
  return {
    halfW,
    halfH,
    capOffset,
    thetaEdge,
    yTopCenter,
    yBottomCenter,
  };
}

export function sampleOutlinePoints(R, w, h, arcSegments = 64, edgeSegments = 20) {
  const t = modelTerms(R, w, h);
  const points = [];

  for (let i = 0; i <= arcSegments; i += 1) {
    const f = i / arcSegments;
    const a = Math.PI - t.thetaEdge - (Math.PI - 2 * t.thetaEdge) * f;
    points.push({ x: R * Math.cos(a), y: t.yTopCenter + R * Math.sin(a) });
  }

  for (let i = 1; i <= edgeSegments; i += 1) {
    const f = i / edgeSegments;
    points.push({ x: t.halfW, y: t.halfH - h * f });
  }

  for (let i = 0; i <= arcSegments; i += 1) {
    const f = i / arcSegments;
    const a = 2 * Math.PI - t.thetaEdge - (Math.PI - 2 * t.thetaEdge) * f;
    points.push({ x: R * Math.cos(a), y: t.yBottomCenter + R * Math.sin(a) });
  }

  for (let i = 1; i <= edgeSegments; i += 1) {
    const f = i / edgeSegments;
    points.push({ x: -t.halfW, y: -t.halfH + h * f });
  }

  return points;
}

export function maxPureRollingAngle(R, w, h) {
  const t = modelTerms(R, w, h);
  return Math.max(0, Math.PI / 2 - t.thetaEdge);
}