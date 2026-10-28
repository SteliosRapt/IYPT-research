type VisibilityMap = {
  container: boolean;
  tube: boolean;
  holders: boolean;
  columns: boolean;
  labels: boolean;
};

export function VisibilityToggles({
  visibility,
  toggle,
}: {
  visibility: VisibilityMap;
  toggle: (key: keyof VisibilityMap) => void;
}) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Visibility</h2>
      </div>
      <div className="toggle-grid">
        {Object.entries(visibility).map(([key, value]) => (
          <label className="toggle" key={key}>
            <input type="checkbox" checked={value} onChange={() => toggle(key as keyof VisibilityMap)} />
            <span>{key}</span>
          </label>
        ))}
      </div>
    </section>
  );
}

