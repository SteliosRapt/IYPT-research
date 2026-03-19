import { expect, test } from "vitest";

import caseIdentityContract from "./fixtures/case-identity-contract.json";
import geometryContract from "./fixtures/geometry-contract.json";
import {
  createDefaultCase,
  createGeometrySnapshot,
  defaultParameters,
  defaultTransportConfig,
  parameterDefinitions,
  schemas,
  SOURCE_FILES,
} from "./index.js";

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
  expect(snapshot.derived.sqrtArgs).toEqual({
    arg1: 0.029975000000000016,
    arg2: 0.005175000000000006,
    arg3: 0.013800000000000007,
    arg4: 0.03272500000000003,
  });
  expect(snapshot.constraints.every((constraint) => constraint.ok)).toBe(true);
});

test("default case uses Python-compatible hashing and shared provenance constants", async () => {
  const caseFile = await createDefaultCase({ ...defaultParameters });

  expect(caseFile.caseId).toBe("case-2598074512");
  expect(caseFile.provenance.parameterHash).toBe("254df71f13");
  expect(caseFile.provenance.sourceFiles).toEqual([...SOURCE_FILES]);
  expect(caseFile.transport).toEqual(defaultTransportConfig());
  expect(caseFile.runStatus.state).toBe("not_started");
});

test("case identity changes when transport or meshing changes", async () => {
  const baseCase = await createDefaultCase({ ...defaultParameters });
  const sigmaCase = await createDefaultCase(
    { ...defaultParameters },
    { ...defaultTransportConfig(), sigma: 0.081 },
    "coarse"
  );
  const fineCase = await createDefaultCase({ ...defaultParameters }, undefined, "fine");

  expect(baseCase.provenance.parameterHash).toBe(sigmaCase.provenance.parameterHash);
  expect(baseCase.caseId).not.toBe(sigmaCase.caseId);
  expect(baseCase.caseId).not.toBe(fineCase.caseId);
});

for (const fixtureCase of caseIdentityContract.cases) {
  test(`case identity contract matches ${fixtureCase.name}`, async () => {
    const caseFile = await createDefaultCase(
      fixtureCase.parameters,
      fixtureCase.transport ?? undefined,
      fixtureCase.meshingPreset as "coarse" | "medium" | "fine"
    );

    expect(caseFile.caseId).toBe(fixtureCase.caseId);
    expect(caseFile.provenance.parameterHash).toBe(fixtureCase.parameterHash);
  });
}

for (const contractCase of geometryContract.cases) {
  test(`geometry contract fixture matches ${contractCase.name}`, () => {
    const snapshot = createGeometrySnapshot(contractCase.raw);

    expect(snapshot.parameters).toEqual(contractCase.parameters);
    expect(snapshot.derived).toEqual(contractCase.derived);
    expect(snapshot.constraints).toEqual(contractCase.constraints);
  });
}
