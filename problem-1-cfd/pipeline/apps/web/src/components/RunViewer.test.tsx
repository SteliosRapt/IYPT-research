import { render } from "@testing-library/react";
import { beforeEach, expect, test, vi } from "vitest";

import type { RunManifest } from "@fixed-geometry/shared-schema";

import { RunViewer } from "./RunViewer";

type MockMapper = {
  inputDataHistory: unknown[];
  setInputData: (data: unknown) => void;
};

const mapperStore: MockMapper[] = [];
let resetCameraCalls = 0;

vi.mock("@kitware/vtk.js/Rendering/Profiles/Geometry", () => ({}));

vi.mock("@kitware/vtk.js/Rendering/Core/Mapper", () => ({
  default: {
    newInstance: () => {
      const mapper: MockMapper = {
        inputDataHistory: [],
        setInputData(data: unknown) {
          this.inputDataHistory.push(data);
        },
      };
      mapperStore.push(mapper);
      return mapper;
    },
  },
}));

vi.mock("@kitware/vtk.js/Rendering/Core/Actor", () => ({
  default: {
    newInstance: () => {
      let mapper: MockMapper | null = null;
      const property = {
        setColor: vi.fn(),
        setOpacity: vi.fn(),
      };
      return {
        setMapper(nextMapper: MockMapper) {
          mapper = nextMapper;
        },
        getMapper() {
          return mapper;
        },
        setVisibility: vi.fn(),
        getProperty() {
          return property;
        },
      };
    },
  },
}));

vi.mock("@kitware/vtk.js/Rendering/Misc/GenericRenderWindow", () => ({
  default: {
    newInstance: () => {
      const renderer = {
        addActor: vi.fn(),
        setBackground: vi.fn(),
        resetCamera: vi.fn(() => {
          resetCameraCalls += 1;
        }),
      };
      const renderWindow = {
        render: vi.fn(),
      };
      return {
        setContainer: vi.fn(),
        resize: vi.fn(),
        getRenderer: () => renderer,
        getRenderWindow: () => renderWindow,
        delete: vi.fn(),
      };
    },
  },
}));

vi.mock("@kitware/vtk.js/Common/Core/Points", () => ({
  default: {
    newInstance: () => ({
      setData: vi.fn(),
    }),
  },
}));

vi.mock("@kitware/vtk.js/Common/Core/CellArray", () => ({
  default: {
    newInstance: () => ({}),
  },
}));

vi.mock("@kitware/vtk.js/Common/DataModel/PolyData", () => ({
  default: {
    newInstance: () => ({
      setPoints: vi.fn(),
      setPolys: vi.fn(),
    }),
  },
}));

const baseManifest: RunManifest = {
  schemaVersion: "1.0.0",
  caseId: "case-a",
  displayName: "Run A",
  timeSteps: [0, 0.1],
  chartSeries: {
    height: "series/height.json",
    outletFlow: "series/outlet.json",
    dischargedVolume: "series/discharged.json",
  },
  geometryAssets: {
    fixedGlb: null,
    fixedJson: "fixed_geometry.json",
  },
  fluidAssets: {
    interfaceFrames: ["frames/frame_0000.json"],
  },
  events: {
    t_h0_up: null,
    t_steady: null,
    terminationReason: "mock",
    currentState: "PRE_H0",
  },
  status: "mock",
  paraview: {
    foamFile: null,
    vtkDir: null,
  },
  metadata: {
    parameterHash: "abc123",
    gitCommit: null,
    sourceFiles: ["experimental_setup.md", "setup_3d (2).html"],
    meshPreset: "coarse",
    solverName: "interFoam",
  },
};

const visibility = {
  container: true,
  tube: true,
  holders: true,
  columns: true,
};

beforeEach(() => {
  mapperStore.length = 0;
  resetCameraCalls = 0;
});

test("updates fixed geometry on manifest switch without resetting camera on frame-only updates", () => {
  const fixedGeometryA = {
    container: [{ type: "box", name: "bottom", center: [0, 0, 0], size: [1, 1, 1] }],
    tube: [],
    holders: [],
    columns: [],
  };
  const fixedGeometryB = {
    container: [{ type: "box", name: "bottom", center: [0, 0, 0], size: [2, 1, 1] }],
    tube: [],
    holders: [],
    columns: [],
  };
  const frameA = {
    points: [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
    triangles: [[0, 1, 2]],
  };
  const frameB = {
    points: [[0, 0, 0], [2, 0, 0], [0, 1, 0]],
    triangles: [[0, 1, 2]],
  };

  const { rerender } = render(
    <RunViewer
      manifest={baseManifest}
      fixedGeometry={fixedGeometryA}
      frame={frameA}
      visibility={visibility}
    />,
  );

  const containerMapper = mapperStore[0];
  expect(containerMapper.inputDataHistory).toHaveLength(1);
  expect(resetCameraCalls).toBe(1);

  rerender(
    <RunViewer
      manifest={baseManifest}
      fixedGeometry={fixedGeometryA}
      frame={frameB}
      visibility={visibility}
    />,
  );

  expect(containerMapper.inputDataHistory).toHaveLength(1);
  expect(resetCameraCalls).toBe(1);

  rerender(
    <RunViewer
      manifest={{ ...baseManifest, caseId: "case-b", displayName: "Run B" }}
      fixedGeometry={fixedGeometryB}
      frame={frameB}
      visibility={visibility}
    />,
  );

  expect(containerMapper.inputDataHistory).toHaveLength(2);
  expect(resetCameraCalls).toBe(2);
});
