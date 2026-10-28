import type { CanonicalParameters, ParameterDefinition } from "../types";

export const parameterDefinitions: ParameterDefinition[] = [
  { id: "A0", label: "A0", section: "primary", min: 0.01, max: 0.5, step: 0.001, defaultValue: 0.105 },
  { id: "h0", label: "h0", section: "primary", min: 0.05, max: 0.6, step: 0.005, defaultValue: 0.3 },
  { id: "h1", label: "h1", section: "primary", min: 0.01, max: 0.25, step: 0.005, defaultValue: 0.04 },
  { id: "h3", label: "h3", section: "primary", min: 0.01, max: 0.25, step: 0.005, defaultValue: 0.12 },
  { id: "h5", label: "h5", section: "primary", min: 0.01, max: 0.25, step: 0.005, defaultValue: 0.065 },
  { id: "Y2", label: "Y2", section: "primary", min: 0.005, max: 0.2, step: 0.005, defaultValue: 0.015 },
  { id: "Y4", label: "Y4", section: "primary", min: 0.005, max: 0.3, step: 0.005, defaultValue: 0.035 },
  { id: "W1", label: "W1", section: "primary", min: 0.01, max: 0.3, step: 0.005, defaultValue: 0.06 },
  { id: "W2", label: "W2", section: "primary", min: 0.01, max: 0.3, step: 0.005, defaultValue: 0.03 },
  { id: "L1", label: "L1", section: "primary", min: 0.05, max: 0.8, step: 0.005, defaultValue: 0.3 },
  { id: "L2", label: "L2", section: "primary", min: 0.05, max: 0.6, step: 0.005, defaultValue: 0.18 },
  { id: "L3", label: "L3", section: "primary", min: 0.05, max: 0.8, step: 0.005, defaultValue: 0.245 },
  { id: "L4", label: "L4", section: "primary", min: 0.05, max: 0.8, step: 0.005, defaultValue: 0.325 },
  { id: "A", label: "A", section: "primary", min: 0.0001, max: 0.005, step: 0.0001, defaultValue: 0.0002 },
  { id: "W", label: "W", section: "primary", min: 0.03, max: 0.5, step: 0.005, defaultValue: 0.3 },
  { id: "alpha", label: "alpha", section: "structural", min: 0.005, max: 0.06, step: 0.001, defaultValue: 0.02 },
  { id: "Ct", label: "Ct", section: "structural", min: 0.001, max: 0.02, step: 0.001, defaultValue: 0.004 },
  { id: "ht", label: "ht", section: "structural", min: 0.001, max: 0.02, step: 0.001, defaultValue: 0.003 },
  { id: "P24t", label: "P24t", section: "structural", min: 0.001, max: 0.06, step: 0.001, defaultValue: 0.015 },
  { id: "hw", label: "hw", section: "structural", min: 0.005, max: 0.06, step: 0.001, defaultValue: 0.02 },
  { id: "h_a", label: "h_a", section: "structural", min: 0, max: 0.05, step: 0.001, defaultValue: 0.01 },
  { id: "bendR", label: "bendR", section: "bend", min: 0.005, max: 0.08, step: 0.001, defaultValue: 0.024 }
];

export const defaultParameters: CanonicalParameters = parameterDefinitions.reduce(
  (accumulator, definition) => ({
    ...accumulator,
    [definition.id]: definition.defaultValue
  }),
  {} as CanonicalParameters
);

