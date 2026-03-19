# Fixed-Geometry CFD Pipeline — Refactoring Proposal

**March 2026 · Version 0.1.0**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Review Methodology](#2-review-methodology)
3. [R-01 — Duplicated Geometry Logic](#3-r-01--duplicated-geometry-logic-high)
4. [R-02 — Incompatible Hash Algorithms](#4-r-02--incompatible-hash-algorithms-break-case-id-parity-high)
5. [R-03 — generate_case() Mutates Its Input](#5-r-03--generate_case-mutates-its-input-dict-medium)
6. [R-04 — Magic Numbers in Mock Generator](#6-r-04--magic-numbers-in-mock-time-series-generator-medium)
7. [R-05 — sqrtArgs Stored in Python but Recomputed in TypeScript](#7-r-05--sqrtargs-stored-in-python-but-recomputed-in-typescript-medium)
8. [R-06 — wallThicknessRatio Hardcoded in Multiple Places](#8-r-06--wallthicknessratio-hardcoded-in-multiple-places-medium)
9. [R-07 — Utility Functions in Wrong Modules](#9-r-07--utility-functions-in-wrong-modules-low)
10. [R-08 — SOURCE_FILES List Duplicated](#10-r-08--source_files-list-duplicated-low)
11. [R-09 — Missing Test Coverage](#11-r-09--missing-test-coverage-for-orchestrator-and-viewer-data-high)
12. [R-10 — No API Layer for Browser-Triggered Runs](#12-r-10--no-api-layer-for-browser-triggered-runs-low)
13. [Recommended Implementation Order](#13-recommended-implementation-order)

---

## 1. Executive Summary

A code review of the Fixed-Geometry CFD Pipeline (as of March 2026) identified ten actionable issues across correctness, maintainability, and testability. The most critical item is a dual-implementation of the geometry engine in both Python and TypeScript with an incompatible hashing strategy — this creates a risk of silent case-ID divergence between browser-generated and CLI-generated cases. Seven of the ten issues can be resolved with localised, low-risk changes. Two require modest focused effort. One (adding an API layer) is optional for an MVP but recommended before scaling.

| # | Issue | Severity | Estimated Effort |
|---|-------|----------|-----------------|
| R-01 | Duplicated geometry logic — Python and TypeScript | **HIGH** | 3–5 days (contract tests) |
| R-02 | Incompatible hash algorithms break case-ID parity | **HIGH** | 1 hour |
| R-03 | `generate_case()` mutates its input dict | **MEDIUM** | 30 minutes |
| R-04 | Magic numbers in mock time-series generator | **MEDIUM** | 1–2 hours |
| R-05 | `sqrtArgs` stored in Python but recomputed in TS | **MEDIUM** | 1–2 hours |
| R-06 | `wallThicknessRatio` hardcoded in multiple places | **MEDIUM** | 30 minutes |
| R-07 | Utility functions (`write_json`, `stable_hash`) in wrong modules | **LOW** | 1 hour |
| R-08 | `SOURCE_FILES` list duplicated in three locations | **LOW** | 15 minutes |
| R-09 | Missing test coverage for orchestrator and viewer-data | **HIGH** | 1–2 days |
| R-10 | No API layer — web app cannot trigger backend runs | **LOW** | 3–5 days (new feature) |

---

## 2. Review Methodology

The review examined every non-generated source file in the repository:

- **Python backend:** `services/geometry/core.py`, `orchestrator/case.py`, `orchestrator/events.py`, `orchestrator/cli.py`, `viewer_data/mock.py`.
- **TypeScript shared schema:** `packages/shared-schema/src/geometry.ts`, `types/index.ts`, `metadata/parameterMetadata.ts`.
- **Web app:** `apps/web/src/app/store.ts`, `pages/ConfigurePage.tsx`, `pages/RunsPage.tsx`, `components/*`.
- **Test suite:** `tests/python/*.py`, `packages/shared-schema/src/index.test.ts`.
- **Configuration:** `pyproject.toml`, `package.json`, `compose.yaml`, `tsconfig.base.json`.

Severity levels:

| Severity | Meaning |
|----------|---------|
| **HIGH** | Risk of silent correctness failure, or issue will compound significantly as the codebase grows. |
| **MEDIUM** | Reduces maintainability or debuggability without an immediate correctness risk. |
| **LOW** | Code hygiene or architectural improvement. Low urgency; address when convenient. |

---

## 3. R-01 — Duplicated Geometry Logic `[HIGH]`

### Description

The entire geometry engine — `normalizeParameters` / `normalize_parameters`, `computeDerived` / `compute_derived`, `checkConstraints` / `check_constraints`, `buildFixedGeometryDescriptors` / `build_fixed_geometry_descriptors`, `buildTubePath` / `build_tube_path`, and all default config factories — is implemented independently in both:

- `services/geometry/core.py` (Python)
- `packages/shared-schema/src/geometry.ts` (TypeScript)

The two implementations must produce numerically identical results for the same input parameters, but there is no automated contract test to verify this. Both are maintained by hand. Any future change to the geometry formulae, constraint list, or descriptor structure must be applied to both files simultaneously, with no tooling enforcement.

### Risk

- **Silent drift:** a parameter range, formula, or constraint updated in one language but not the other will cause the browser configurator and the backend CLI to produce different results for the same inputs. This is particularly dangerous for constraint validation — a user might see a green constraint in the browser while the backend CLI rejects the same geometry.
- **Maintenance cost:** the combined geometry code is approximately 800 lines of logic duplicated across two languages. Every feature addition doubles the work.

### Recommended Fix

Introduce a cross-language contract test suite. The test suite should:

1. Generate a representative set of parameter dicts (default, boundary values, a few random seeds).
2. Run `compute_derived` / `computeDerived` on each dict in Python and TypeScript.
3. Assert that all numeric fields are equal up to floating-point rounding (tolerance `1e-10` is achievable because both implementations use the same 12-decimal round helper).

This does not eliminate the duplication but makes drift detectable immediately. A CI step that runs both the Python and TypeScript test suites with shared fixtures enforces parity.

**Longer-term option:** replace the TypeScript `geometry.ts` with a WebAssembly compilation of the Python code, or use a single authoritative JSON specification of formulas with code generation into both languages. Both approaches are significant architectural investments and out of scope for the MVP.

---

## 4. R-02 — Incompatible Hash Algorithms Break Case-ID Parity `[HIGH]`

### Description

Python and TypeScript both compute a stable hash of the parameter dict to generate the `caseId`. The implementations differ in two ways:

| Aspect | Python (`geometry/core.py`) | TypeScript (`geometry.ts`) |
|--------|----------------------------|---------------------------|
| Algorithm | SHA-256 (`hashlib`) | FNV-1a 32-bit (custom) |
| Serialisation | `json.dumps(params, sort_keys=True)` | `JSON.stringify(params)` — no `sort_keys` |
| Output length | First 10 hex chars of 64-char digest | 8 hex chars (zero-padded) |

**Consequence:** the browser's `createDefaultCase()` generates `case-XXXXXXXX` while the Python CLI's `create_case_file()` generates `case-YYYYYYYYYY` for identical parameter inputs. Any system that correlates browser-exported JSON with CLI-generated data by `caseId` will silently fail.

### Recommended Fix

Choose one algorithm and apply it consistently. The simplest path is to align on Python's SHA-256 approach in TypeScript:

```typescript
// Sort keys to match Python's json.dumps(sort_keys=True)
const sorted = Object.fromEntries(
  Object.entries(snapshot.parameters).sort(([a], [b]) => a.localeCompare(b))
);
const bytes = new TextEncoder().encode(JSON.stringify(sorted));
const hashBuffer = await crypto.subtle.digest('SHA-256', bytes);
const hashArray = Array.from(new Uint8Array(hashBuffer));
const hash = hashArray.map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 10);
```

Both outputs should then be truncated to the same length (10 characters). A test in `index.test.ts` that compares against the known Python output for the default parameters will catch any future regression.

---

## 5. R-03 — `generate_case()` Mutates Its Input Dict `[MEDIUM]`

### Description

In `services/orchestrator/case.py`, the `generate_case()` function directly mutates the `case_file` dict passed by the caller:

```python
case_file["meshing"] = meshing
case_file["solver"]  = {**default_solver_config(), **case_file.get("solver", {})}
case_file["forcing"] = {**default_forcing_config(), **case_file.get("forcing", {})}
case_file["eventThresholds"] = {**default_event_thresholds(), **case_file.get("eventThresholds", {})}
```

A caller that holds a reference to the `case_file` dict will see its contents changed after calling `generate_case()`. This side effect is invisible from the function signature. In the current codebase `orchestrator/cli.py` loads the dict from disk and does not reuse it, so the bug is latent. Any refactor that calls `generate_case()` twice on the same case (e.g. for different mesh presets) will introduce a subtle ordering dependency.

### Recommended Fix

Work on a local copy of the input at the top of `generate_case()`:

```python
import copy
case_file = copy.deepcopy(case_file)
```

Alternatively, collect the merged config into local variables without touching the input. Either approach eliminates the mutation with no other changes.

---

## 6. R-04 — Magic Numbers in Mock Time-Series Generator `[MEDIUM]`

### Description

`services/viewer_data/mock.py` contains numerous un-named numeric constants in `create_time_series()` and `create_mock_run()`:

```python
height  = steady_height - (steady_height - h_initial) * math.exp(-0.8 * time)
damping = 0.0025 * math.exp(-1.1 * max(time - 2.0, 0)) * math.sin(4.0 * ...)
q_out_value = max(0.0, 0.00035 * (1 - math.exp(-0.7 * max(time - 1.6, 0))) * ...)
plume_length = outlet_x0 + q_out_value * 180
```

Without accompanying explanations these constants are impossible to reason about during debugging or when adapting the mock for a different test geometry. The value `180` (plume length scaling) has unclear units.

### Recommended Fix

Extract named constants with inline comments at the top of the module:

```python
# Mock time-series tuning parameters
HEIGHT_RISE_RATE   = 0.8     # 1/s  — exponential approach rate to steady state
DAMPING_AMPLITUDE  = 0.0025  # m    — initial surface oscillation amplitude
DAMPING_DECAY_RATE = 1.1     # 1/s  — oscillation decay rate
DAMPING_FREQUENCY  = 4.0     # rad/s — oscillation angular frequency
FLOW_ONSET_TIME    = 1.6     # s    — delay before outlet flow begins
PLUME_LENGTH_SCALE = 180     # m / (m³/s) — visual scaling for outlet plume
```

Add a short docstring on `create_time_series()` noting that the series is synthetic and calibrated to activate the event detector within the 12-second window.

---

## 7. R-05 — `sqrtArgs` Stored in Python but Recomputed in TypeScript `[MEDIUM]`

### Description

In Python, `compute_derived()` stores the four intermediate discriminants (`arg1`…`arg4`) under the key `'sqrtArgs'` in the returned dict. `check_constraints()` reads them from there.

In TypeScript, `computeDerived()` does not include `sqrtArgs` in its return type or value. `checkConstraints()` therefore recomputes `arg1`…`arg4` from scratch. The TypeScript `DerivedGeometry` type therefore does not match the Python `derived` dict structurally.

### Risk

- If a future change corrects the arg computations in one implementation but not the other, constraint checks will silently diverge (related to R-01).
- The TypeScript `DerivedGeometry` type does not match the Python `derived` dict, which means any consumer that validates a case JSON `derived` field against the TypeScript type may reject valid Python-generated objects.

### Recommended Fix

Add `sqrtArgs` to the TypeScript `DerivedGeometry` interface and populate it in `computeDerived()`:

```typescript
// In DerivedGeometry interface
sqrtArgs: { arg1: number; arg2: number; arg3: number; arg4: number };

// In computeDerived()
sqrtArgs: { arg1, arg2, arg3, arg4 }
```

Update `checkConstraints()` to read from `derived.sqrtArgs` rather than recomputing. Add a contract test asserting that `derived.sqrtArgs` values match for the default parameters across both implementations.

---

## 8. R-06 — `wallThicknessRatio` Hardcoded in Multiple Places `[MEDIUM]`

### Description

The value `0.2` for the tube wall thickness ratio appears in four locations:

1. `services/geometry/core.py` → `normalize_parameters()` injects `merged['wallThicknessRatio'] = 0.2`.
2. `services/geometry/core.py` → `default_solver_config()` stores `'tubeWallThicknessRatio': 0.2`.
3. `packages/shared-schema/src/geometry.ts` → `normalizeParameters()` injects `wallThicknessRatio: 0.2`.
4. `packages/shared-schema/src/geometry.ts` → `defaultSolverConfig()` stores `tubeWallThicknessRatio: 0.2`.

There are also two different key names: `wallThicknessRatio` (in the normalised parameter dict used by geometry computation) and `tubeWallThicknessRatio` (in the solver config). If a future user wants to parameterise wall thickness, they must find and update all four locations.

### Recommended Fix

In Python, define a single module-level constant:

```python
TUBE_WALL_THICKNESS_RATIO = 0.2  # Fraction of outer radius used for tube wall
```

Reference it in both `normalize_parameters()` and `default_solver_config()`. Apply the same pattern in TypeScript. Optionally promote `wallThicknessRatio` to a first-class user parameter if the experiment design ever varies tube wall thickness.

---

## 9. R-07 — Utility Functions in Wrong Modules `[LOW]`

### Description

Two utility functions are defined in modules that do not conceptually own them:

- `write_json()` is defined in `services/geometry/core.py` but imported and used by `services/viewer_data/mock.py`. The geometry module should not be the home for I/O utilities.
- `stable_hash()` is defined in `services/geometry/core.py` and also imported by `services/viewer_data/mock.py`. It has no dependency on geometry logic.
- `write_text()` is defined in `services/orchestrator/case.py` (not exported). A parallel `write_json()` exists only in `core.py`, so there is no shared I/O utility module.

### Recommended Fix

Create `services/utils.py` (or `services/io.py`) containing `write_json()`, `write_text()`, and `stable_hash()`. Import from this module in all consumers. This removes the artificial dependency of `viewer_data` on the geometry module.

```
services/
  utils.py          ← write_json, write_text, stable_hash
  geometry/core.py  ← from ..utils import write_json, stable_hash
  orchestrator/case.py ← from ..utils import write_json, write_text
  viewer_data/mock.py  ← from ..utils import write_json, stable_hash
```

---

## 10. R-08 — `SOURCE_FILES` List Duplicated `[LOW]`

### Description

The list `['experimental_setup.md', 'setup_3d (2).html']` appears hardcoded in three places:

1. `services/geometry/core.py` — `SOURCE_FILES` module constant (used in `create_case_file()` provenance).
2. `services/viewer_data/mock.py` — hardcoded again in the manifest dict (line 183).
3. `packages/shared-schema/src/geometry.ts` — hardcoded in `createDefaultCase()` provenance.

If the source file list ever changes (e.g. the HTML file is renamed), all three locations must be updated.

### Recommended Fix

In Python, import `SOURCE_FILES` from `services.geometry.core` in `mock.py` instead of re-declaring it:

```python
# services/viewer_data/mock.py
from services.geometry.core import SOURCE_FILES
```

In TypeScript, define a `SOURCE_FILES` constant at the top of `geometry.ts` and reference it in `createDefaultCase()`. This reduces the list to two authoritative definitions (one per language) and eliminates the cross-module duplication on the Python side entirely.

---

## 11. R-09 — Missing Test Coverage for Orchestrator and Viewer-Data `[HIGH]`

### Description

The existing test suite covers geometry computation (`test_geometry_core.py`), event detection (`test_events.py`), and schema validation (`test_schema_and_examples.py`), plus smoke tests and source-truth parity. However, there are no unit tests for:

- `services/orchestrator/case.py` — none of the builder functions (`build_block_mesh_dict`, `build_control_dict`, `mesh_preset`, `build_run_metadata`, `generate_case`) are tested in isolation.
- `services/viewer_data/mock.py` — `create_time_series()` and `write_legacy_vtk()` have no unit tests.
- `services/orchestrator/cli.py` — `run_case()` error handling (OpenFOAM not present) is untested.

### Risk

- `generate_case()` mutations (R-03) would have been caught by a unit test asserting the input dict is unchanged after the call.
- `build_block_mesh_dict()` contains a margin calculation that has not been numerically verified.
- The OpenFOAM field files (`alpha.water`, `U`, `p_rgh`) are assembled from f-strings with no structural validation. A typo would not be detected until an actual OpenFOAM run.

### Recommended Fix

Add the following test modules:

| Proposed test file | Coverage targets |
|--------------------|-----------------|
| `tests/python/test_case_generation.py` | `mesh_preset()` output for each preset level. `generate_case()` output directory structure. Verify input dict is not mutated. Spot-check `blockMeshDict` vertex count. `build_transport_properties()` reads from `case_file["transport"]`. |
| `tests/python/test_viewer_data.py` | `create_time_series()` length and range assertions. `integrate_series()` trapezoidal accuracy. `write_legacy_vtk()` output format (VTK header, point count). |
| `tests/python/test_orchestrator_cli.py` | `run_case()` raises `RuntimeError` when solver not on PATH. Manifest is written to expected location by `create_mock_run()`. |

---

## 12. R-10 — No API Layer for Browser-Triggered Runs `[LOW]`

### Description

The web application currently calls the Python geometry logic by re-implementing it entirely in TypeScript (see R-01). There is no mechanism for the browser to trigger a backend simulation run, poll its status, or retrieve real CFD results. All simulation management must be done through the CLI. This is acceptable for an MVP but will become a bottleneck as the project grows.

### Recommended Fix

Add a lightweight HTTP API layer (e.g. FastAPI or Flask) between the browser and the Python services:

| Endpoint | Action |
|----------|--------|
| `POST /api/cases` | Accept parameter dict, call `create_case_file()`, return `caseId` + case JSON. |
| `POST /api/cases/{id}/run` | Enqueue a run (mock or real), return run ID. |
| `GET  /api/runs/{id}/status` | Poll run status and return progress. |
| `GET  /api/runs/{id}/manifest` | Return manifest JSON when run is complete. |

This would allow the `ConfigurePage` export buttons to submit runs directly rather than requiring the user to copy the exported JSON and invoke the CLI manually. It would also eliminate the need for the TypeScript geometry re-implementation (R-01), since all computation could be delegated to the Python backend.

---

## 13. Recommended Implementation Order

Based on risk and effort, the following order is recommended:

| Wave | Issue | Effort | Rationale |
|------|-------|--------|-----------|
| 1 | R-02 | 1 hour | Fixes silent case-ID divergence. Zero-risk change confined to one function in TypeScript. |
| 1 | R-03 | 30 min | Prevents a latent mutation bug. One line of Python. |
| 1 | R-06 | 30 min | Eliminates the magic number `0.2` from four locations. |
| 1 | R-08 | 15 min | Import `SOURCE_FILES` from `core.py` instead of re-declaring. |
| 2 | R-04 | 1–2 hours | Improves future debuggability of mock runs. |
| 2 | R-07 | 1 hour | Cleaner module boundaries; removes geometry → io coupling. |
| 2 | R-05 | 1–2 hours | Aligns TypeScript `DerivedGeometry` with Python dict structure. |
| 3 | R-01 | 3–5 days | Contract test suite for cross-language parity. Large but high leverage. |
| 3 | R-09 | 1–2 days | Fills critical coverage gaps in orchestrator and viewer-data. |
| 4 | R-10 | 3–5 days | New feature; deferred until post-MVP. |

**Wave 1** items total under 3 hours of work and address the highest-risk correctness issues immediately. They should be completed before any further feature development. **Wave 3** items require dedicated focused time but have the highest long-term impact on code health.
