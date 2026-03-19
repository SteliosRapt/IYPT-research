import type { ParameterDefinition } from "@fixed-geometry/shared-schema";

type ParameterPanelProps = {
  title: string;
  definitions: ParameterDefinition[];
  values: Record<string, number>;
  onChange: (key: string, value: number) => void;
};

export function ParameterPanel({ title, definitions, values, onChange }: ParameterPanelProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>{title}</h2>
      </div>
      <div className="rows">
        {definitions.map((definition) => (
          <label className="param-row" key={definition.id}>
            <span>{definition.label}</span>
            <input
              type="range"
              min={definition.min}
              max={definition.max}
              step={definition.step}
              value={values[definition.id]}
              onChange={(event) =>
                onChange(definition.id, Number.parseFloat(event.currentTarget.value))
              }
            />
            <strong>{values[definition.id].toFixed(4)}</strong>
          </label>
        ))}
      </div>
    </section>
  );
}

