import {
  defaultParameters,
  parameterDefinitions,
  type CanonicalParameters,
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
  setParameter: (key: keyof CanonicalParameters, value: number) => void;
  resetParameters: () => void;
  toggleVisibility: (key: keyof VisibilityState) => void;
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
}));

