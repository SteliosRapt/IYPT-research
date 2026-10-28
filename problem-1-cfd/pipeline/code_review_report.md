> Superseded by `docs/remediation-roadmap.md`.
> Retained for historical context only.

# Code Review — Fixed-Geometry CFD Pipeline

**Reviewer:** Claude (automated review)
**Date:** March 2026
**Scope:** Full codebase review against `technical_documentation.md` and `refactoring_proposal.md`
**Baseline:** `refactoring_proposal.md` documents R-01 through R-10. This report confirms those findings, updates their status based on direct code inspection, and identifies six new issues not previously captured.

---

## Summary

The codebase is well-structured for an MVP. The Python service layer is clean, the TypeScript shared-schema package is correctly typed, and the test suite covers the happy path thoroughly. The existing `refactoring_proposal.md` identifies the most important architectural risks accurately. This review confirms all ten of those findings by tracing them to specific source lines, and adds six new issues found during code-level inspection — two of which are correctness bugs that will produce wrong OpenFOAM inputs silently.

| # | Issue | Severity | Status vs. Proposal |
|---|-------|----------|---------------------|
| R-01 | Dual geometry implementation (Python + TypeScript) | 🔴 HIGH | Confirmed |
| R-02 | Incompatible hash algorithms break case-ID parity | 🔴 HIGH | Confirmed + details added |
| R-03 | `generate_case()` mutates its input dict | 🟡 MEDIUM | Confirmed |
| R-04 | Magic numbers in mock time-series generator | 🟡 MEDIUM | Confirmed |
| R-05 | `sqrtArgs` stored in Python but absent from TS `DerivedGeometry` | 🟡 MEDIUM | Confirmed |
| R-06 | `wallThicknessRatio` hardcoded in multiple places | 🟡 MEDIUM | Extended — 5 locations, not 4 |
| R-07 | Utility functions in wrong modules | 🔵 LOW | Confirmed |
| R-08 | `SOURCE_FILES` list duplicated | 🔵 LOW | Confirmed |
| R-09 | Missing test coverage for orchestrator and viewer-data | 🔴 HIGH | Confirmed |
| R-10 | No API layer for browser-triggered runs | 🔵 LOW | Confirmed |
| **N-01** | **Inflow velocity hardcoded in `0/U` — ignores forcing config** | 🔴 **HIGH** | **New** |
| **N-02** | **`create_case_file()` omits `transport` config entirely** | 🟡 **MEDIUM** | **New** |
| **N-03** | **`runStatus` state values inconsistent across layers** | 🟡 **MEDIUM** | **New** |
| **N-04** | **`wallThicknessRatio = 0.2` has a 5th hardcoded location** | 🟡 **MEDIUM** | **New (extends R-06)** |
| **N-05** | **O(n²) `_window_indices` — will be slow on real CFD output** | 🔵 **LOW** | **New** |
| **N-06** | **Latent IndexError in `q_window` slicing** | 🔵 **LOW** | **New** |

---

## Confirmed Existing Issues

### R-01 — Dual Geometry Implementation `[HIGH]`

**Location:** `services/geometry/core.py` (≈ 450 lines of logic) vs `packages/shared-schema/src/geometry.ts` (≈ 450 lines of logic)

Direct comparison of the two implementations confirms they are independent, manually-maintained copies. The TypeScript `computeDerived` (geometry.ts:156–227) and Python `compute_derived` (core.py:175–242) are structurally identical and pass the same numeric fixture in their respective test suites, but there is no automated cross-language contract test.

The risk is not the duplication itself but the absence of a guard against drift. Key examples of where drift could silently occur:

- `clampSqrt` / `_clamped_sqrt` — identical logic today but tested only within their own languages.
- The `build_tube_path` / `buildTubePath` Bezier arc loop uses `1 / arcSegments` in the denominator; if one implementation changes `arcSegments` from 24 to a different value, the polylines diverge with no test failure.
- `CONSTRAINT_LABELS` is declared in both languages. Adding or reordering a constraint in one file would silently produce mismatched constraint results for the same geometry.

**Confirmed recommended fix:** cross-language contract tests with shared JSON fixtures (Python writes expected values, TypeScript test reads them and asserts equality to `1e-10`).

---

### R-02 — Incompatible Hash Algorithms `[HIGH]`

**Python (`core.py:506–508`):**
```python
def stable_hash(parameters: dict[str, Any]) -> str:
    payload = json.dumps(parameters, sort_keys=True).encode("utf-8")
    return sha256(payload).hexdigest()[:10]
```

**TypeScript (`geometry.ts:443–450`):**
```typescript
export function stableStringHash(value: string): string {
  let hash = 2166136261;
  for (let index = 0; index < value.length; index += 1) {
    hash ^= value.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return Math.abs(hash >>> 0).toString(16).padStart(8, "0");
}
```

And in `createDefaultCase` (geometry.ts:507):
```typescript
const parameterHash = stableStringHash(JSON.stringify(snapshot.parameters));
```

Three independent differences:

1. **Algorithm:** SHA-256 (Python) vs FNV-1a 32-bit (TypeScript).
2. **Key sorting:** Python uses `sort_keys=True`; TypeScript uses `JSON.stringify` with JavaScript's default object key insertion order (generally insertion order in V8, but not guaranteed by the spec to match Python's sorted output).
3. **Output length:** 10 hex characters (Python) vs 8 hex characters (TypeScript).

A browser-exported case file will have `caseId: "case-XXXXXXXX"` (8 chars) while a CLI-generated file will have `caseId: "case-YYYYYYYYYY"` (10 chars) for identical input parameters. The `parameterHash` field in `provenance` and `metadata` will also differ.

---

### R-03 — `generate_case()` Mutates Its Input Dict `[MEDIUM]`

**Location:** `services/orchestrator/case.py:341–344`

```python
def generate_case(case_file: dict[str, Any], output_dir: Path) -> Path:
    snapshot = create_geometry_snapshot(case_file["parameters"])
    meshing = mesh_preset(...)
    case_file["meshing"] = meshing                           # ← mutates caller's dict
    case_file["solver"]  = {**default_solver_config(), ...} # ← mutates caller's dict
    case_file["forcing"] = {**default_forcing_config(), ...}# ← mutates caller's dict
    case_file["eventThresholds"] = {...}                     # ← mutates caller's dict
```

The mutation is harmless in `test_smoke.py` because the dict is loaded from disk each time (line 16: `json.loads(case_json.read_text(...))`), but any refactor that calls `generate_case()` twice on the same object — for example to regenerate with different mesh presets — will produce incorrect behaviour on the second call because `meshing` will already be set to the first call's value.

Fix is one line at the top of the function: `case_file = copy.deepcopy(case_file)`.

---

### R-04 — Magic Numbers in Mock Time-Series Generator `[MEDIUM]`

**Location:** `services/viewer_data/mock.py:38–44`

```python
steady_height = h0 + 0.0075
height = steady_height - (steady_height - h_initial) * math.exp(-0.8 * time)
damping = 0.0025 * math.exp(-1.1 * max(time - 2.0, 0)) * math.sin(4.0 * max(time - 2.0, 0))
q_out_value = max(0.0, 0.00035 * (1 - math.exp(-0.7 * max(time - 1.6, 0))) * math.exp(-0.06 * max(time - 5.0, 0)))
q_in_value = 0.00042 if time < 8.0 else 0.00018
```

And in the frame loop (mock.py:141–142):
```python
plume_length = outlet_x0 + q_out_value * 180
```

Eight distinct unnamed numeric parameters. The constant `180` is particularly opaque — it appears to be a visual scaling factor mapping volumetric flow rate (m³/s) to plume length (m), which would give it units of m/(m³/s) = s/m², but this is never stated.

---

### R-05 — `sqrtArgs` Absent from TypeScript `DerivedGeometry` `[MEDIUM]`

**Python:** `compute_derived` returns `"sqrtArgs": {"arg1": ..., "arg2": ..., "arg3": ..., "arg4": ...}` (core.py:241), and `check_constraints` reads them from `derived["sqrtArgs"]` (core.py:265–268).

**TypeScript:** The `DerivedGeometry` interface (`types/index.ts:70–96`) has no `sqrtArgs` field. `checkConstraints` (geometry.ts:229–260) recomputes `arg1`–`arg4` from scratch:

```typescript
const arg1 = parameters.L1 * parameters.L1 - (derived.h2 - parameters.h1) * (derived.h2 - parameters.h1);
// ... etc.
```

This means:
1. A Python-generated case JSON that includes `derived.sqrtArgs` will be rejected by TypeScript if any consumer validates it against the `DerivedGeometry` interface (unexpected properties are flagged in strict mode).
2. Any future correction to how the args are computed in Python does not automatically propagate to the TypeScript constraint checks.

---

### R-06 — `wallThicknessRatio` Hardcoded `[MEDIUM]` — Extended to 5 locations

The refactoring proposal identified 4 locations. Code inspection reveals a 5th:

| # | File | Line | Location |
|---|------|------|----------|
| 1 | `services/geometry/core.py` | 120 | `normalize_parameters()` injects `'wallThicknessRatio': 0.2` |
| 2 | `services/geometry/core.py` | 529 | `default_solver_config()` → `'tubeWallThicknessRatio': 0.2` |
| 3 | `packages/shared-schema/src/geometry.ts` | 92 | `normalizeParameters()` injects `wallThicknessRatio: 0.2` |
| 4 | `packages/shared-schema/src/geometry.ts` | 497 | `defaultSolverConfig()` → `tubeWallThicknessRatio: 0.2` |
| **5** | **`apps/web/src/lib/sceneBuilder.ts`** | **141** | **`buildFluidInteriorGroup()` uses `derived.r * (1 - 0.2)` directly** |

The 5th occurrence in `sceneBuilder.ts` is particularly fragile because it is in the frontend scene builder, not the shared-schema package, so it would be missed by a refactor that only touches `geometry.ts`.

---

### R-07 — Utility Functions in Wrong Modules `[LOW]`

**Confirmed:** `write_json()` is defined in `services/geometry/core.py` (line 576) and imported by `services/viewer_data/mock.py` (line 15) and `services/orchestrator/case.py` (line 17). `write_text()` is defined locally in `services/orchestrator/case.py` (line 39) and not shared with any other module.

`stable_hash()` is defined in `core.py` (line 506) and imported by `mock.py` (line 14), creating a viewer-data → geometry import dependency that should not be necessary for a function with no geometry logic.

---

### R-08 — `SOURCE_FILES` Duplicated `[LOW]`

**Confirmed in three locations:**

1. `services/geometry/core.py:13` — `SOURCE_FILES = ["experimental_setup.md", "setup_3d (2).html"]`
2. `services/viewer_data/mock.py:183` — `"sourceFiles": ["experimental_setup.md", "setup_3d (2).html"]` (hardcoded in manifest dict, not imported from core)
3. `packages/shared-schema/src/geometry.ts:533` — `sourceFiles: ["experimental_setup.md", "setup_3d (2).html"]`

---

### R-09 — Missing Test Coverage for Orchestrator and Viewer-Data `[HIGH]`

The smoke test (`test_smoke.py`) verifies that files are created but does not test the content of those files or the internal logic of the builder functions. There are no tests for:

- `mesh_preset()` — the `backgroundCellSize` formula `domain_span / divisor` is untested; a regression would not be caught.
- `build_block_mesh_dict()` — the margin calculation and vertex/cell counts are untested.
- `generate_case()` input non-mutation (the R-03 mutation bug is not caught by any test).
- `build_transport_properties()` reading from `case_file["transport"]` rather than falling back to hardcoded values (the N-02 bug below means this test would reveal that Python-generated cases don't include transport data).
- `create_time_series()` range and length assertions.
- `write_legacy_vtk()` format validation.
- `run_case()` error paths when the solver is not on PATH.

---

### R-10 — No API Layer `[LOW]`

Confirmed. The web app exports a case JSON file which must then be run manually through the CLI. The `ConfigurePage` has no mechanism to submit a run. This is an acceptable MVP limitation.

---

## New Issues

### N-01 — Inflow Velocity Hardcoded in `0/U` Boundary File `[HIGH]`

**Location:** `services/orchestrator/case.py:375–380`

```python
velocity_boundary = """
    walls { type fixedValue; value uniform (0 0 0); }
    topAtmosphere { type pressureInletOutletVelocity; value uniform (0 0 0); }
    topInflow { type fixedValue; value uniform (0 -0.02 0); }   # ← hardcoded
    tubeOutlet { type pressureInletOutletVelocity; value uniform (0 0 0); }
    """
```

The `0/U` boundary condition for the `topInflow` patch is hardcoded to `(0 -0.02 0)` m/s. The case file's `forcing["inflowVelocity"]` parameter (default `0.02`) is never read when generating this file. If a user sets `inflowVelocity` to any other value through the configurator and exports a case JSON, the generated OpenFOAM case will always apply 0.02 m/s inflow regardless.

This is a **silent correctness failure**: no error is raised, the case runs, but the physics do not match the user's configuration. The `inflowVelocity` value is correctly stored in `case.json`, correctly shown in the browser configurator, and correctly used in `build_fluid_geometry_descriptors()` for the inflow patch geometry — but ignored when the actual boundary condition file is written.

**Fix:** Replace the hardcoded velocity with an f-string interpolation:
```python
inflow_vel = case_file["forcing"].get("inflowVelocity", 0.02)
# then in the f-string:
topInflow {{ type fixedValue; value uniform (0 {-abs(inflow_vel)} 0); }}
```

---

### N-02 — `create_case_file()` Omits `transport` Config `[MEDIUM]`

**Location:** `services/geometry/core.py:548–573`

`create_case_file()` returns a dict with `solver`, `forcing`, `meshing`, and `eventThresholds` sections but no `transport` section:

```python
return {
    "schemaVersion": "1.0.0",
    "caseId": ...,
    "parameters": ...,
    "derived": ...,
    "meshing": default_meshing_config(),
    "solver": default_solver_config(),
    "forcing": forcing,
    "eventThresholds": default_event_thresholds(),
    # ← "transport" is missing entirely
    ...
}
```

The TypeScript `CaseFile` interface (`types/index.ts:208–232`) requires `transport: TransportConfig`. Any TypeScript consumer that validates a Python-CLI-generated case file against this interface will fail.

Downstream, `generate_case()` calls `build_transport_properties(case_file)`, which does:
```python
t = case_file.get("transport", {})
water_nu = t.get("waterNu", 1e-6)  # silently falls back to hardcoded default
```
So no runtime error occurs — the OpenFOAM case is generated with correct default transport values — but the transport configuration is not persisted in the case JSON and cannot be recovered from it. Any user who changes transport parameters in the web app, exports a case JSON, and then runs the CLI will silently get default transport properties in the OpenFOAM case, not their customised values.

**Fix:** Add `"transport": default_transport_config()` (a new function mirroring the TypeScript `defaultTransportConfig()`) to the dict returned by `create_case_file()`.

---

### N-03 — `runStatus.state` Values Inconsistent Across Layers `[MEDIUM]`

Three independent enumerations of valid state values exist and they do not agree:

| Source | Values |
|--------|--------|
| `technical_documentation.md` (§7.1) | `'not_started'` \| `'running'` \| `'done'` \| `'error'` |
| TypeScript `CaseFile` interface (`types/index.ts:228`) | `"not_started"` \| `"generated"` \| `"running"` \| `"done"` \| `"failed"` |
| Python `create_case_file()` (core.py:567) | only ever writes `"not_started"` |
| TypeScript `RunManifest.status` (`types/index.ts:258`) | `"mock"` \| `"solver_generated"` |
| Python `create_mock_run()` (mock.py:149) | writes `"mock"` |
| Docs (§7.2, manifest status) | `'mock'` \| `'real'` \| `'running'` \| `'error'` |

The mismatch between `"error"` (Python docs) and `"failed"` (TypeScript), and between `"real"` (Python docs) and `"solver_generated"` (TypeScript manifest type), means that any system parsing `status` or `runStatus.state` values will need inconsistent handling.

**Fix:** Agree on a single canonical set of values, document them in `case.schema.json` and `run-manifest.schema.json` as JSON Schema `enum` constraints, and update all consuming code.

---

### N-04 — Fifth Location of `wallThicknessRatio = 0.2` `[MEDIUM]`

**Location:** `apps/web/src/lib/sceneBuilder.ts:141`

```typescript
const innerRadius = Math.max(derived.r * (1 - 0.2), derived.r * 0.1);
```

This is inside `buildFluidInteriorGroup()`, which renders the fluid domain preview in the 3D scene. It is not in `packages/shared-schema/src/geometry.ts` and would therefore be missed by any refactor limited to the shared-schema package. If `wallThicknessRatio` is ever promoted to a parameter or changed, the fluid interior preview will show incorrect geometry while all other geometry uses the updated value.

This extends the refactoring proposal's R-06 from 4 locations to 5.

---

### N-05 — O(n²) Complexity in `_window_indices` `[LOW]`

**Location:** `services/orchestrator/events.py:25–27`

```python
def _window_indices(times: list[float], center_index: int, window_seconds: float) -> list[int]:
    window_start = times[center_index] - window_seconds
    return [index for index, value in enumerate(times[: center_index + 1]) if value >= window_start]
```

This is called once per timestep inside the main loop of `analyze_series`. Each call creates an O(center_index) slice and then scans it linearly. For a series of N timesteps the total complexity is O(N²).

For the current 121-step mock this is imperceptible. For a real interFoam run writing at `writeInterval = 0.1` s over 15 s (150 steps) to several hundred seconds (thousands of steps), this becomes measurable. An O(N) alternative would maintain a two-pointer or deque, sliding the window start forward as the loop advances.

---

### N-06 — Latent IndexError in `q_window` Index Slicing `[LOW]`

**Location:** `services/orchestrator/events.py:81–82`

```python
q_window = window[-min(len(window), len(q_in), len(q_out)) :]
q_balance = max(abs(q_in[i] - q_out[i]) for i in q_window)
```

`window` is a list of integer *indices* into the `times` array (values ranging from 0 to `center_index`). The slicing guard `min(len(window), len(q_in), len(q_out))` correctly limits how many window entries are used, but it does not ensure that the index values themselves are within the bounds of `q_in` and `q_out`. If `q_in` and `q_out` have fewer elements than `times`, the `q_in[i]` access will raise `IndexError` for indices beyond `len(q_in) - 1`.

In the current codebase, `analyze_series` is always called with `q_in` and `q_out` at the same length as `times`, so the bug is latent. Any future caller that provides a shorter flow-rate array (e.g. coarser monitoring resolution) will encounter an unhandled exception.

---

## What Looks Good

The codebase has significant strengths that should be preserved:

**Geometric correctness.** The `build_tube_path` / `buildTubePath` Bezier arc implementation is carefully crafted with proper clamping, degenerate-case handling (zero-length segments, straight segments), and the `_clamped_sqrt` / `clampSqrt` guard ensures that the constraint-check architecture never crashes on invalid geometry. The 12-decimal rounding convention is applied consistently to ensure numerical stability in hash comparisons.

**Event-detection state machine.** The `analyze_series` function is clean, handles empty input gracefully, correctly interpolates the h0 crossing time, and separates the detection logic from the output structure. The `EventSummary` dataclass is a good API boundary.

**Shared JSON Schema approach.** Using `case.schema.json`, `parameters.schema.json`, and `run-manifest.schema.json` as the authoritative contract (validated in `test_schema_and_examples.py`) is the right architectural pattern. Expanding the schema's `enum` constraints (e.g. for `runStatus.state`) would strengthen this.

**Test-fixture approach in `test_source_truth_parity.py`.** Parsing the HTML source-of-truth to assert that Python defaults match is an excellent guard against accidental parameter drift.

**`build_snappy_hex_mesh_dict` interior point.** The `locationInMesh` computation (case.py:99–100) correctly places the seed point at the geometric centre of the container at half `h0`, which is a robust choice for `snappyHexMesh` — much better than a hardcoded coordinate.

**`integrate_series` trapezoidal integration** is numerically correct and the `strict=True` zip in frame generation (mock.py:136) correctly guards against mismatched array lengths.

---

## Recommended Implementation Order

Building on the proposal's wave structure and adding the new findings:

### Wave 1 — Under 3 hours, highest correctness risk

| Issue | Fix | Effort |
|-------|-----|--------|
| **N-01** | Replace hardcoded `(0 -0.02 0)` in `0/U` with `case_file["forcing"]["inflowVelocity"]` | 15 min |
| R-02 | Align TypeScript `stableStringHash` to SHA-256 with sorted keys; add regression test | 1 hour |
| R-03 | `copy.deepcopy(case_file)` at top of `generate_case()` | 5 min |
| **N-02** | Add `"transport": default_transport_config()` to `create_case_file()` return dict | 15 min |
| R-06 / **N-04** | Define `TUBE_WALL_THICKNESS_RATIO = 0.2` in Python; `TUBE_WALL_THICKNESS_RATIO` constant in TypeScript; update all 5 locations | 30 min |
| R-08 | Import `SOURCE_FILES` from `core.py` in `mock.py`; export from `geometry.ts` | 15 min |

### Wave 2 — Half a day, maintainability

| Issue | Fix | Effort |
|-------|-----|--------|
| **N-03** | Agree on canonical `runStatus.state` / `status` enum values; add `enum` to both schemas | 1 hour |
| R-04 | Extract named constants for mock time-series tuning parameters | 1 hour |
| R-07 | Create `services/utils.py` with `write_json`, `write_text`, `stable_hash` | 1 hour |
| R-05 | Add `sqrtArgs` to TypeScript `DerivedGeometry` interface; populate in `computeDerived`; read in `checkConstraints` | 1 hour |

### Wave 3 — Focused effort, highest long-term impact

| Issue | Fix | Effort |
|-------|-----|--------|
| R-09 | Add `test_case_generation.py`, `test_viewer_data.py`, `test_orchestrator_cli.py` | 1–2 days |
| R-01 | Cross-language contract test suite with shared JSON fixtures | 3–5 days |
| **N-05** | Replace O(n²) `_window_indices` with a two-pointer or `deque`-based window | 2 hours |
| **N-06** | Add bounds assertion or guard for `q_in`/`q_out` length in `analyze_series` | 30 min |

### Wave 4 — New feature, post-MVP

| Issue | Fix | Effort |
|-------|-----|--------|
| R-10 | FastAPI / Flask API layer between browser and Python services | 3–5 days |

---

## Critical Issues Table

| # | File | Line | Issue | Severity |
|---|------|------|-------|----------|
| N-01 | `services/orchestrator/case.py` | 379 | Inflow velocity hardcoded to 0.02 m/s regardless of forcing config | 🔴 Critical |
| R-02 | `packages/shared-schema/src/geometry.ts` | 443–507 | FNV-1a hash vs SHA-256; unsorted serialisation; 8 vs 10 char output | 🔴 Critical |
| R-03 | `services/orchestrator/case.py` | 341–344 | `generate_case()` mutates caller's `case_file` dict | 🟡 Medium |
| N-02 | `services/geometry/core.py` | 548–573 | `create_case_file()` returns dict with no `"transport"` key | 🟡 Medium |
| N-03 | `types/index.ts`, `core.py`, docs | multiple | `runStatus.state` enum values disagree across Python, TypeScript, and docs | 🟡 Medium |
| R-05 | `packages/shared-schema/src/geometry.ts` | 229–260 | `DerivedGeometry` missing `sqrtArgs`; constraints recompute them independently | 🟡 Medium |
| R-06/N-04 | `sceneBuilder.ts:141` + 4 others | multiple | `wallThicknessRatio = 0.2` at 5 separate locations | 🟡 Medium |
| N-05 | `services/orchestrator/events.py` | 25–27 | O(n²) `_window_indices` for long time series | 🔵 Low |
| N-06 | `services/orchestrator/events.py` | 81–82 | Latent IndexError if `q_in`/`q_out` shorter than `times` | 🔵 Low |
| R-07 | `core.py`, `case.py`, `mock.py` | multiple | `write_json`, `write_text`, `stable_hash` in wrong modules | 🔵 Low |
| R-08 | `core.py:13`, `mock.py:183`, `geometry.ts:533` | multiple | `SOURCE_FILES` list duplicated verbatim in three places | 🔵 Low |
| R-09 | `tests/python/` | — | No unit tests for `case.py`, `mock.py`, `cli.py` | 🔴 Critical (debt) |

---

## Verdict

**Request Changes.** Two correctness bugs (N-01 and N-02) silently produce wrong OpenFOAM inputs and must be fixed before the pipeline is used for real simulation runs. The hash incompatibility (R-02) must be fixed before browser-exported cases are correlated with CLI-generated cases. The remaining items are low-risk and can be addressed iteratively. Wave 1 items total under 3 hours and eliminate all three correctness risks simultaneously.
