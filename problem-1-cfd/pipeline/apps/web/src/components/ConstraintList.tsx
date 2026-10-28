import type { ConstraintResult } from "@fixed-geometry/shared-schema";

export function ConstraintList({ constraints }: { constraints: ConstraintResult[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <h2>Constraints</h2>
      </div>
      <div className="constraint-list">
        {constraints.map((constraint) => (
          <p
            key={constraint.id}
            className={constraint.ok ? "constraint constraint-ok" : "constraint constraint-fail"}
          >
            {constraint.ok ? "PASS" : "FAIL"} {constraint.label}
          </p>
        ))}
      </div>
    </section>
  );
}

