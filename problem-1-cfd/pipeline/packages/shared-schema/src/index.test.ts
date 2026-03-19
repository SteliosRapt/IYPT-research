import { expect, test } from "vitest";

import { createGeometrySnapshot, defaultParameters, parameterDefinitions, schemas } from "./index.js";

test("default parameters match metadata entries", () => {
  expect(parameterDefinitions).toHaveLength(22);
  for (const definition of parameterDefinitions) {
    expect(defaultParameters[definition.id]).toBe(definition.defaultValue);
  }
});

test("schemas are exported", () => {
  expect(schemas.parameters.type).toBe("object");
  expect(schemas.case.type).toBe("object");
  expect(schemas.runManifest.type).toBe("object");
});

test("default geometry matches the source-of-truth defaults", () => {
  const snapshot = createGeometrySnapshot({ ...defaultParameters });

  expect(snapshot.derived.h2).toBe(0.285);
  expect(snapshot.derived.h4).toBe(0.335);
  expect(snapshot.derived.X2).toBe(0.173132896932);
  expect(snapshot.derived.X5).toBe(0.543444296177);
  expect(snapshot.constraints.every((constraint) => constraint.ok)).toBe(true);
});
