import {
  defaultParameters,
  defaultTransportConfig,
  parameterDefinitions,
  type CanonicalParameters,
  type MeshingConfig,
  type TransportConfig,
} from "@fixed-geometry/shared-schema";
import { create } from "zustand";

type VisibilityState = {
  container: boolean;
  tube: boolean;
  holders: boolean;
  columns: boolean;
  labels: boolean;
};

type AppState = {
  parameters: CanonicalParameters;
  visibility: VisibilityState;
  transport: TransportConfig;
  meshingPreset: MeshingConfig["preset"];
  showMeshDomain: boolean;
  showFluidInterior: boolean;
  setParameter: (key: keyof CanonicalParameters, value: number) => void;
  resetParameters: () => void;
  toggleVisibility: (key: keyof VisibilityState) => void;
  setTransport: (key: keyof TransportConfig, value: number) => void;
  setMeshingPreset: (preset: MeshingConfig["preset"]) => void;
  toggleMeshDomain: () => void;
  toggleFluidInterior: () => void;
};

export const visibilityKeys: Array<keyof VisibilityState> = [
  "container",
  "tube",
  "holders",
  "columns",
  "labels",
];

export const parameterSections = {
  primary: parameterDefinitions.filter((definition) => definition.section === "primary"),
  structural: parameterDefinitions.filter((definition) => definition.section === "structural"),
  bend: parameterDefinitions.filter((definition) => definition.section === "bend"),
};

export const useAppStore = create<AppState>((set) => ({
  parameters: { ...defaultParameters },
  visibility: {
    container: true,
    tube: true,
    holders: true,
    columns: true,
    labels: true,
  },
  transport: defaultTransportConfig(),
  meshingPreset: "coarse",
  showMeshDomain: false,
  showFluidInterior: false,
  setParameter: (key, value) =>
    set((state) => ({
      parameters: {
        ...state.parameters,
        [key]: value,
      },
    })),
  resetParameters: () => set({ parameters: { ...defaultParameters } }),
  toggleVisibility: (key) =>
    set((state) => ({
      visibility: {
        ...state.visibility,
        [key]: !state.visibility[key],
      },
    })),
  setTransport: (key, value) =>
    set((state) => ({
      transport: { ...state.transport, [key]: value },
    })),
  setMeshingPreset: (preset) => set({ meshingPreset: preset }),
  toggleMeshDomain: () =>
    set((state) => ({ showMeshDomain: !state.showMeshDomain })),
  toggleFluidInterior: () =>
    set((state) => ({ showFluidInterior: !state.showFluidInterior })),
}));

