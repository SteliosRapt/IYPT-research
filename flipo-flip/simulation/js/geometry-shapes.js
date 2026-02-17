import * as THREE from "three";
import { modelTerms } from "./flipo-model.js";

export function makeTopCapShape(R, w, h) {
  const t = modelTerms(R, w, h);
  const shape = new THREE.Shape();
  shape.moveTo(-t.halfW, t.halfH);
  shape.absarc(0, t.yTopCenter, R, Math.PI - t.thetaEdge, t.thetaEdge, true);
  shape.lineTo(-t.halfW, t.halfH);
  return shape;
}

export function makeBottomCapShape(R, w, h) {
  const t = modelTerms(R, w, h);
  const shape = new THREE.Shape();
  shape.moveTo(t.halfW, -t.halfH);
  shape.absarc(0, t.yBottomCenter, R, 2 * Math.PI - t.thetaEdge, Math.PI + t.thetaEdge, true);
  shape.lineTo(t.halfW, -t.halfH);
  return shape;
}

export function makeFullToyShape(R, w, h) {
  const t = modelTerms(R, w, h);
  const shape = new THREE.Shape();
  shape.moveTo(-t.halfW, t.halfH);
  shape.absarc(0, t.yTopCenter, R, Math.PI - t.thetaEdge, t.thetaEdge, true);
  shape.lineTo(t.halfW, -t.halfH);
  shape.absarc(0, t.yBottomCenter, R, 2 * Math.PI - t.thetaEdge, Math.PI + t.thetaEdge, true);
  shape.lineTo(-t.halfW, t.halfH);
  return shape;
}