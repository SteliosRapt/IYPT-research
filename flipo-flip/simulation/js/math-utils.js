export function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

export function safeNumber(value, fallback) {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
}

export function lerp(a, b, u) {
  return a + (b - a) * u;
}

export function roundTenth(value) {
  return Math.round(value * 10) / 10;
}

export function roundHundredth(value) {
  return Math.round(value * 100) / 100;
}