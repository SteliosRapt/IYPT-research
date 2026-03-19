import "@kitware/vtk.js/Rendering/Profiles/Geometry";

import type { RunManifest } from "@fixed-geometry/shared-schema";
import vtkActor from "@kitware/vtk.js/Rendering/Core/Actor";
import vtkCellArray from "@kitware/vtk.js/Common/Core/CellArray";
import vtkGenericRenderWindow from "@kitware/vtk.js/Rendering/Misc/GenericRenderWindow";
import vtkMapper from "@kitware/vtk.js/Rendering/Core/Mapper";
import vtkPoints from "@kitware/vtk.js/Common/Core/Points";
import vtkPolyData from "@kitware/vtk.js/Common/DataModel/PolyData";
import { useEffect, useMemo, useRef } from "react";

import { descriptorGroupsToMeshes, type MeshJson } from "@/lib/meshBuilders";

type VisibilityMap = {
  container: boolean;
  tube: boolean;
  holders: boolean;
  columns: boolean;
};

function toPolyData(mesh: MeshJson) {
  const polyData = vtkPolyData.newInstance();
  const points = vtkPoints.newInstance();
  points.setData(Float32Array.from(mesh.points.flat()), 3);
  polyData.setPoints(points);
  const polys = vtkCellArray.newInstance({
    values: Uint32Array.from(mesh.triangles.flatMap((triangle) => [3, ...triangle])),
  });
  polyData.setPolys(polys);
  return polyData;
}

export function RunViewer({
  manifest,
  fixedGeometry,
  frame,
  visibility,
}: {
  manifest: RunManifest;
  fixedGeometry: Record<string, unknown[]>;
  frame: MeshJson | null;
  visibility: VisibilityMap;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const renderRef = useRef<vtkGenericRenderWindow | null>(null);
  const actorsRef = useRef<Record<string, vtkActor>>({});
  const lastLoadedCaseIdRef = useRef<string | null>(null);
  const fixedMeshes = useMemo(
    () => descriptorGroupsToMeshes(fixedGeometry as never),
    [fixedGeometry]
  );

  useEffect(() => {
    if (!containerRef.current) {
      return;
    }
    const genericRenderWindow = vtkGenericRenderWindow.newInstance();
    genericRenderWindow.setContainer(containerRef.current);
    genericRenderWindow.resize();
    const renderer = genericRenderWindow.getRenderer();
    renderer.setBackground(0.04, 0.04, 0.06);
    renderRef.current = genericRenderWindow;

    return () => {
      genericRenderWindow.delete();
      renderRef.current = null;
      actorsRef.current = {};
    };
  }, []);

  useEffect(() => {
    if (!renderRef.current) {
      return;
    }
    const renderer = renderRef.current.getRenderer();
    const shouldResetCamera = lastLoadedCaseIdRef.current !== manifest.caseId;

    for (const [key, mesh] of Object.entries(fixedMeshes)) {
      if (!actorsRef.current[key]) {
        const mapper = vtkMapper.newInstance();
        mapper.setInputData(toPolyData(mesh));
        const actor = vtkActor.newInstance();
        actor.setMapper(mapper);
        if (key === "container") {
          actor.getProperty().setColor(0.23, 0.35, 0.54);
          actor.getProperty().setOpacity(0.16);
        } else if (key === "tube") {
          actor.getProperty().setColor(0.9, 0.94, 1);
          actor.getProperty().setOpacity(0.3);
        } else if (key === "holders") {
          actor.getProperty().setColor(0.31, 0.73, 0.44);
        } else {
          actor.getProperty().setColor(0.6, 0.48, 1);
        }
        actorsRef.current[key] = actor;
        renderer.addActor(actor);
      } else {
        actorsRef.current[key].getMapper().setInputData(toPolyData(mesh));
      }
      actorsRef.current[key].setVisibility(visibility[key as keyof VisibilityMap]);
    }

    lastLoadedCaseIdRef.current = manifest.caseId;
    if (shouldResetCamera) {
      renderer.resetCamera();
    }
    renderRef.current.getRenderWindow().render();
  }, [fixedMeshes, visibility, manifest.caseId]);

  useEffect(() => {
    if (!renderRef.current) {
      return;
    }
    const renderer = renderRef.current.getRenderer();

    if (!actorsRef.current.fluid && frame) {
      const mapper = vtkMapper.newInstance();
      mapper.setInputData(toPolyData(frame));
      const actor = vtkActor.newInstance();
      actor.setMapper(mapper);
      actor.getProperty().setColor(0.18, 0.74, 0.95);
      actor.getProperty().setOpacity(0.48);
      actorsRef.current.fluid = actor;
      renderer.addActor(actor);
    } else if (actorsRef.current.fluid && frame) {
      actorsRef.current.fluid.getMapper().setInputData(toPolyData(frame));
      actorsRef.current.fluid.setVisibility(true);
    }

    renderRef.current.getRenderWindow().render();
  }, [frame]);

  return (
    <div className="viewer-panel">
      <div className="viewer-toolbar">
        <div>
          <p className="eyebrow">Viewer</p>
          <strong>{manifest.displayName}</strong>
        </div>
        <div className="status-badge">{manifest.events.currentState}</div>
      </div>
      <div ref={containerRef} className="vtk-container" />
    </div>
  );
}

