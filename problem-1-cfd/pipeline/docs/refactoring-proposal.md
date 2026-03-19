> Superseded by `docs/remediation-roadmap.md`.
> Retained for historical context only.

# Refactoring Proposal — Fixed-Geometry CFD Pipeline

## Scope and Principles

This proposal targets maintainability, testability, and correctness without changing
observable behaviour.  Each item is independent; they can be adopted in any order.
Items are ranked by expected impact vs effort.

---

## R1 — Split `geometry/core.py` into focused modules  *(High impact / Low risk)*

### Problem

`core.py` (562 lines) does five unrelated things:
1. Parameter definitions and defaults
2. Geometry maths (derive, constrain)
3. Descriptor builders (fixed + fluid geometry)
4. Case-file defaults and assembly
5. I/O helpers (`write_json`, `stable_hash`)

This makes it hard to read, import selectively, or test individual concerns.

### Proposal

```
services/geometry/
├── __init__.py          (re-exports public API unchanged)
├── parameters.py        PARAMETER_DEFINITIONS, DEFAULT_PARAMETERS,
│                        HTML_TO_CANONICAL_PARAMETER_MAP,
│                        normalize_parameters()
├── derive.py            compute_derived(), build_tube_path(),
│                        CONSTRAINT_LABELS, check_constraints()
├── descriptors.py       build_fixed_geometry_descriptors(),
│                        build_fluid_geometry_descriptors()
├── case.py              create_case_file(), create_geometry_snapshot(),
│                        default_*_config() helpers
├── io.py                write_json(), stable_hash()
└── cli.py               (unchanged)
```

`__init__.py` re-exports every name currently in `core.py` so that existing imports
(`from services.geometry.core import ...`) continue to work during transition.

### Benefit

- Each file is ≤150 lines and has a single responsibility.
- `parameters.py` can be imported by the web-schema package without pulling in `math`.
- Unit tests can target `derive.py` directly without the case-file plumbing.

---

## R2 — Remove `_clamped_sqrt` and make constraint violations explicit  *(Medium impact / Low risk)*

### Problem

`_clamped_sqrt` silently returns `0.0` when the discriminant is negative.  This means
`compute_derived` always succeeds, even for geometrically invalid parameters.
Constraint checks then catch the issue, but `X2`–`X5` will have wrong values in the
returned dict when constraints fail.  Tests only call `check_constraints` after
`compute_derived`, so an invalid geometry still produces a snapshot with plausible-
looking numbers.

### Proposal

```python
# derive.py

class GeometryConstraintError(ValueError):
    """Raised when a sqrt discriminant is negative (geometry is infeasible)."""

def _require_nonneg(value: float, name: str) -> float:
    if value < 0:
        raise GeometryConstraintError(
            f"Discriminant '{name}' = {value:.6g} < 0 — geometry is infeasible."
        )
    return value
```

Replace the four `_clamped_sqrt` calls in `compute_derived` with
`math.sqrt(_require_nonneg(arg, "argN"))`.  Callers that intentionally explore
infeasible space (e.g., the web configurator) should catch `GeometryConstraintError`
and present the constraint list rather than derived values.

Store the raw `sqrtArgs` values before the guard so `check_constraints` can still
report which discriminant failed.

### Benefit

- Invalid parameters can no longer produce silently wrong derived values.
- The distinction between "failed constraint" and "derived value" is explicit.

---

## R3 — Separate `create_case_file` from `create_geometry_snapshot`  *(Medium impact / Low risk)*

### Problem

`create_case_file` calls `create_geometry_snapshot` internally, then discards the
snapshot object.  Callers that need both a snapshot and a case file call both
functions separately, computing derived values twice.

```python
# current usage pattern in viewer_data/mock.py
snapshot = create_geometry_snapshot(case_file["parameters"])   # 1st compute
...
case_file = create_case_file(raw)   # internally calls create_geometry_snapshot again
```

### Proposal

```python
def create_case_file(
    raw: dict[str, Any] | None = None,
    *,
    snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if snapshot is None:
        snapshot = create_geometry_snapshot(raw)
    ...
```

Callers that already have a snapshot pass it in and avoid the double computation.

---

## R4 — Replace bare `dict` for geometry descriptors with typed dataclasses  *(Medium impact / Medium effort)*

### Problem

Functions return nested plain dicts whose shapes are undocumented in the type system.
The web configurator, orchestrator, and viewer-data modules all pattern-match on string
keys like `"type"`, `"center"`, `"size"`.  A typo is only caught at runtime.

### Proposal

Define lightweight dataclasses (or `TypedDict`s) in `descriptors.py`:

```python
from typing import TypedDict, Literal

class BoxDescriptor(TypedDict):
    type: Literal["box"]
    name: str
    center: tuple[float, float, float]
    size: tuple[float, float, float]

class TubeDescriptor(TypedDict):
    type: Literal["tube"]
    name: str
    path: list[tuple[float, float, float]]
    outerRadius: float
    innerRadius: float
    wallThickness: float

class HolderDescriptor(TypedDict):
    type: Literal["holder"]
    name: str
    center: tuple[float, float, float]
    pointHeight: float
    baseY: float
    alpha: float
    hw: float
    ht: float
    plateThickness: float
    tubeRadius: float

class FixedGeometry(TypedDict):
    container: list[BoxDescriptor]
    tube: list[TubeDescriptor]
    holders: list[HolderDescriptor]
    columns: list[BoxDescriptor]
```

JSON serialisation is unaffected because `TypedDict` values are plain dicts at runtime.

### Benefit

- Type checkers (mypy / pyright) catch structural errors at development time.
- Self-documenting — downstream code can see the exact keys available.

---

## R5 — Extract `analyze_series` rolling-window logic into a helper  *(Low impact / Low risk)*

### Problem

`events.py:analyze_series` computes the rolling-window derivative inline at every
timestep.  The derivative computation is a 12-line block inside an already complex
loop, making the steady-state logic harder to read.

### Proposal

```python
def _rolling_rms_dhdt(
    times: list[float],
    heights: list[float],
    window_indices: list[int],
) -> float:
    derivatives = [
        (heights[i] - heights[i - 1]) / (times[i] - times[i - 1])
        for i in window_indices[1:]
        if times[i] - times[i - 1] > 0
    ]
    if not derivatives:
        return 0.0
    return math.sqrt(sum(d * d for d in derivatives) / len(derivatives))
```

The main loop body shrinks by ~10 lines and each concern is independently testable.

---

## R6 — Remove `numpy` dependency from core geometry path  *(Low impact / Low risk)*

### Problem

`pyproject.toml` lists `numpy>=2.2` as a required dependency, but `numpy` is not
imported anywhere in `services/geometry/core.py` or `services/orchestrator/`.  It is
used only in `services/viewer_data/mock.py` and (presumably) in optional extras.

### Proposal

Move `numpy` to `[project.optional-dependencies]` under a `"mock"` or `"viewer"` key:

```toml
[project.optional-dependencies]
geometry = ["meshio>=5.3", "trimesh>=4.6"]
boolean  = ["shapely>=2.0", "manifold3d>=2.5"]
mock     = ["numpy>=2.2"]
dev      = ["pytest>=8.3", "numpy>=2.2"]
```

This keeps the install footprint small for environments that only need geometry
generation (e.g. a CI job that just validates constraints).

> **Note**: verify that `services/viewer_data/mock.py` actually calls numpy before
> making this change.  A quick `grep -r "import numpy"` confirms scope.

---

## R7 — Replace the `orchestrator/cli.py` fallback string with a logged warning  *(Low impact / Low risk)*

### Problem

`run_case` in `orchestrator/cli.py` silently falls through to mock data when
OpenFOAM/Docker are absent.  There is no indication in the CLI output or the
`runStatus` field of the case JSON that the result is synthetic.

### Proposal

1. Print a clearly labelled warning:
   ```
   WARNING: OpenFOAM/Docker not found — falling back to synthetic mock data.
   ```
2. Set `case_file["runStatus"]["state"] = "mock"` before writing back.
3. Document the fallback in `docs/assumptions.md`.

The manifest already sets `"status": "mock"` in `create_mock_run`, so this is a
consistency fix more than a behaviour change.

---

## R8 — Add `__all__` to each public module  *(Low impact / Low risk)*

### Problem

Wildcard imports from `services.geometry.core` would expose internal helpers
(`_round`, `_clamped_sqrt`, `_window_indices`, etc.).  There is no explicit public API
boundary.

### Proposal

After R1 splits the module, add `__all__` to each new file listing only the intended
exports.  The `__init__.py` re-export list doubles as the public API contract.

---

## Summary Table

| # | Title | Impact | Effort | Risk |
|---|-------|--------|--------|------|
| R1 | Split `core.py` into focused modules | High | Medium | Low |
| R2 | Explicit constraint violation errors | Medium | Low | Low |
| R3 | Snapshot reuse in `create_case_file` | Medium | Low | Low |
| R4 | TypedDict for geometry descriptors | Medium | Medium | Low |
| R5 | Extract rolling-window helper | Low | Low | Low |
| R6 | Move numpy to optional dependency | Low | Low | Low |
| R7 | Warn + tag mock fallback explicitly | Low | Low | Low |
| R8 | Add `__all__` to public modules | Low | Low | Low |

Recommended sequence: **R1 → R2 → R3 → R6 → R7**, then R4/R5/R8 as bandwidth allows.
R1 is the prerequisite for most of the others because it establishes the module
boundaries that the rest of the proposals reference.
