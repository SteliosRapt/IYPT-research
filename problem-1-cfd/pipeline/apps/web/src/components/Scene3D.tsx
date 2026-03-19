import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import type { CanonicalParameters } from "@fixed-geometry/shared-schema";
import { useMemo } from "react";

import { buildSceneGroup } from "@/lib/sceneBuilder";

type VisibilityMap = {
  container: boolean;
  tube: boolean;
  holders: boolean;
  columns: boolean;
  labels: boolean;
};

export function Scene3D({
  parameters,
  visibility,
}: {
  parameters: CanonicalParameters;
  visibility: VisibilityMap;
}) {
  const sceneGroup = useMemo(
    () => buildSceneGroup(parameters, visibility).group,
    [parameters, visibility]
  );

  return (
    <div className="viewport-card">
      <Canvas camera={{ position: [0.45, 0.35, 0.55], fov: 45 }}>
        <color attach="background" args={["#0a0a0f"]} />
        <ambientLight intensity={0.85} />
        <directionalLight position={[1, 2, 1]} intensity={0.9} />
        <directionalLight position={[-1, 0.5, -1]} intensity={0.4} color="#8090ff" />
        <gridHelper args={[2, 40, "#1a1a25", "#1a1a25"]} />
        <primitive object={sceneGroup} />
        <OrbitControls enableDamping />
      </Canvas>
      <div className="viewport-overlay">Drag to orbit. Shift-drag to pan. Scroll to zoom.</div>
    </div>
  );
}

