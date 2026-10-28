import { modelTerms, maxPureRollingAngle } from "./flipo-model.js";
import { clamp, lerp } from "./math-utils.js";

export function rotatePoint(point, theta) {
  const c = Math.cos(theta);
  const s = Math.sin(theta);
  return {
    x: c * point.x - s * point.y,
    y: s * point.x + c * point.y,
  };
}

export function poseFromPivot(theta, pivotLocal, pivotWorld) {
  const rotatedPivot = rotatePoint(pivotLocal, theta);
  return {
    theta,
    tx: pivotWorld.x - rotatedPivot.x,
    ty: pivotWorld.y - rotatedPivot.y,
  };
}

export function poseFromCenter(theta, centerLocal, centerWorld) {
  const rotatedCenter = rotatePoint(centerLocal, theta);
  return {
    theta,
    tx: centerWorld.x - rotatedCenter.x,
    ty: centerWorld.y - rotatedCenter.y,
  };
}

export function worldPoint(localPoint, pose) {
  const r = rotatePoint(localPoint, pose.theta);
  return { x: r.x + pose.tx, y: r.y + pose.ty };
}

export function buildCycle(R, w, h) {
  const t = modelTerms(R, w, h);
  const phiRaw = maxPureRollingAngle(R, w, h);
  const phi = Math.max(1e-6, phiRaw);

  const p = {
    rb: { x: t.halfW, y: -t.halfH },
    rt: { x: t.halfW, y: t.halfH },
    lt: { x: -t.halfW, y: t.halfH },
    lb: { x: -t.halfW, y: -t.halfH },
    cBot: { x: 0, y: t.yBottomCenter },
    cTop: { x: 0, y: t.yTopCenter },
  };

  function poseBottomRolling(phiValue, startContactX = 0) {
    const theta = -phiValue;
    const cx = startContactX + R * (phiValue + phi);
    return poseFromCenter(theta, p.cBot, { x: cx, y: R });
  }

  function poseTopRolling(phiValue, startContactX) {
    const theta = -Math.PI + phiValue;
    const cx = startContactX + R * (phi - phiValue);
    return poseFromCenter(theta, p.cTop, { x: cx, y: R });
  }

  const poseAEnd = poseBottomRolling(phi, 0);
  const rbWorld = worldPoint(p.rb, poseAEnd);

  const thetaBEnd = -Math.PI / 2;
  const poseBEnd = poseFromPivot(thetaBEnd, p.rb, rbWorld);
  const rtWorld = worldPoint(p.rt, poseBEnd);

  const thetaCEnd = -Math.PI + phi;
  const poseDEnd = poseFromPivot(thetaCEnd, p.rt, rtWorld);

  const poseEEnd = poseTopRolling(-phi, rtWorld.x);
  const ltWorld = worldPoint(p.lt, poseEEnd);

  const thetaFEnd = -1.5 * Math.PI;
  const poseFEnd = poseFromPivot(thetaFEnd, p.lt, ltWorld);
  const lbWorld = worldPoint(p.lb, poseFEnd);

  const thetaGEnd = -2 * Math.PI + phi;
  const poseGEnd = poseFromPivot(thetaGEnd, p.lb, lbWorld);
  const cycleShift = worldPoint(p.lb, poseGEnd).x;

  const phaseSpecs = [
    {
      name: "Pure patch rolling (bottom cap)",
      mode: "roll",
      weight: 2 * phi,
      sample: (u) => {
        const phiValue = lerp(-phi, phi, u);
        const pose = poseBottomRolling(phiValue, 0);
        const circleCenter = worldPoint(p.cBot, pose);
        return {
          pose,
          contactPoint: { x: circleCenter.x, y: 0 },
          circleCenter,
        };
      },
    },
    {
      name: "Patch switch: trailing-edge pivot",
      mode: "pivot",
      weight: Math.abs(-Math.PI / 2 - -phi),
      sample: (u) => {
        const theta = lerp(-phi, -Math.PI / 2, u);
        const pose = poseFromPivot(theta, p.rb, rbWorld);
        return {
          pose,
          contactPoint: { x: rbWorld.x, y: rbWorld.y },
          circleCenter: null,
        };
      },
    },
    {
      name: "Patch switch: leading-edge pivot",
      mode: "pivot",
      weight: Math.abs((-Math.PI + phi) - -Math.PI / 2),
      sample: (u) => {
        const theta = lerp(-Math.PI / 2, -Math.PI + phi, u);
        const pose = poseFromPivot(theta, p.rt, rtWorld);
        return {
          pose,
          contactPoint: { x: rtWorld.x, y: rtWorld.y },
          circleCenter: null,
        };
      },
    },
    {
      name: "Pure patch rolling (top cap)",
      mode: "roll",
      weight: 2 * phi,
      sample: (u) => {
        const phiValue = lerp(phi, -phi, u);
        const pose = poseTopRolling(phiValue, rtWorld.x);
        const circleCenter = worldPoint(p.cTop, pose);
        return {
          pose,
          contactPoint: { x: circleCenter.x, y: 0 },
          circleCenter,
        };
      },
    },
    {
      name: "Patch switch: trailing-edge pivot",
      mode: "pivot",
      weight: Math.abs(-1.5 * Math.PI - (-Math.PI - phi)),
      sample: (u) => {
        const theta = lerp(-Math.PI - phi, -1.5 * Math.PI, u);
        const pose = poseFromPivot(theta, p.lt, ltWorld);
        return {
          pose,
          contactPoint: { x: ltWorld.x, y: ltWorld.y },
          circleCenter: null,
        };
      },
    },
    {
      name: "Patch switch: leading-edge pivot",
      mode: "pivot",
      weight: Math.abs((-2 * Math.PI + phi) - -1.5 * Math.PI),
      sample: (u) => {
        const theta = lerp(-1.5 * Math.PI, -2 * Math.PI + phi, u);
        const pose = poseFromPivot(theta, p.lb, lbWorld);
        return {
          pose,
          contactPoint: { x: lbWorld.x, y: lbWorld.y },
          circleCenter: null,
        };
      },
    },
  ];

  const totalWeight = phaseSpecs.reduce((sum, item) => sum + item.weight, 0);
  let cursor = 0;
  for (const segment of phaseSpecs) {
    const span = totalWeight > 0 ? segment.weight / totalWeight : 1 / phaseSpecs.length;
    segment.start = cursor;
    segment.end = cursor + span;
    cursor = segment.end;
  }
  phaseSpecs[phaseSpecs.length - 1].end = 1;

  const initialSegmentIndex = 2;
  const startOffset = phaseSpecs[initialSegmentIndex].start;

  function stateAt(playhead) {
    const nonNegative = Math.max(0, playhead);
    const displayU = nonNegative - Math.floor(nonNegative);
    const shiftedPlayhead = nonNegative + startOffset;
    const cycleIndex = Math.floor(shiftedPlayhead);
    const cycleU = shiftedPlayhead - cycleIndex;

    let picked = phaseSpecs[phaseSpecs.length - 1];
    for (const segment of phaseSpecs) {
      if (cycleU <= segment.end) {
        picked = segment;
        break;
      }
    }

    const span = Math.max(1e-9, picked.end - picked.start);
    const segmentLocalU = clamp((cycleU - picked.start) / span, 0, 1);
    const sampled = picked.sample(segmentLocalU);
    const xShift = cycleIndex * cycleShift;
    const rawPhaseIndex = phaseSpecs.indexOf(picked);
    const phaseIndex = ((rawPhaseIndex - initialSegmentIndex + phaseSpecs.length) % phaseSpecs.length) + 1;

    const pose = {
      theta: sampled.pose.theta,
      tx: sampled.pose.tx + xShift,
      ty: sampled.pose.ty,
    };
    const contactPoint = {
      x: sampled.contactPoint.x + xShift,
      y: sampled.contactPoint.y,
    };
    const circleCenter = sampled.circleCenter
      ? { x: sampled.circleCenter.x + xShift, y: sampled.circleCenter.y }
      : null;

    return {
      pose,
      contactPoint,
      circleCenter,
      mode: picked.mode,
      phaseName: picked.name,
      phaseIndex,
      phaseCount: phaseSpecs.length,
      displayU,
      cycleIndex,
    };
  }

  return {
    phiMax: phiRaw,
    thetaEdge: t.thetaEdge,
    cycleShift,
    stateAt,
  };
}