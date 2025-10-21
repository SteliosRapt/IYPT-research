# Code Refactoring Recommendations for IYPT Siphon Simulations

**Date:** 2025-10-21
**Repository:** PastelDev/IYPT
**Branch:** claude/general-refactoring-011CUKnJJ5Po8iNdEvgdr1pC

## Executive Summary

This document outlines comprehensive refactoring recommendations for the IYPT siphon drainage simulation codebase. The code is well-structured and demonstrates good software engineering practices, but contains significant code duplication and opportunities for improved maintainability through better separation of concerns.

**Overall Code Quality:** Good (well-documented, type-annotated, tested)
**Main Issues:** Code duplication, mixed concerns, lack of formal interfaces
**Estimated Impact:** Medium-High improvement in maintainability

---

## Table of Contents

1. [Critical Code Duplication Issues](#1-critical-code-duplication-issues)
2. [Design & Architecture Issues](#2-design--architecture-issues)
3. [Detailed Refactoring Proposals](#3-detailed-refactoring-proposals)
4. [Priority & Impact Assessment](#4-priority--impact-assessment)
5. [Implementation Roadmap](#5-implementation-roadmap)

---

## 1. Critical Code Duplication Issues

### 1.1 Duplicated Plotting Function

**Severity:** High
**Lines of Duplicated Code:** ~35 lines × 3 files = ~105 lines

The `_plot_series()` function appears in three files with nearly identical implementations:

- `simulations/ideal.py:63-96`
- `simulations/constant_losses.py:82-115`
- `simulations/variable_losses.py:159-192`

**Differences:** Only the `facecolor` parameter in the annotation box varies:
- `ideal.py`: `facecolor="wheat"`
- `constant_losses.py`: `facecolor="lightyellow"`
- `variable_losses.py`: `facecolor="lavender"`

**Impact:** Any bug fix or enhancement to plotting must be applied in three places.

**Recommendation:** Extract to `common.py` or create a new `plotting.py` module.

---

### 1.2 Duplicated Validation Functions

**Severity:** High
**Lines of Duplicated Code:** ~9 lines × 4 files = ~36 lines

#### 1.2.1 `_validate_area_ratio()`

Appears identically in:
- `simulations/ideal.py:24-27`
- `simulations/constant_losses.py:24-27`
- `simulations/variable_losses.py:23-26`
- `simulations/multi_segment.py:21-24`

```python
def _validate_area_ratio(k: float) -> None:
    if k <= 0 or k >= 1:
        raise ValueError("The tube-to-reservoir area ratio must lie between 0 and 1.")
```

#### 1.2.2 `_validate_head()`

Appears identically in:
- `simulations/constant_losses.py:29-32`
- `simulations/variable_losses.py:28-31`

```python
def _validate_head(head: float) -> None:
    if head <= 0:
        raise ValueError("The reservoir surface must remain above the outlet height.")
```

**Recommendation:** Move both to `common.py` and make them public or add them to existing dataclass validation.

---

### 1.3 Duplicated Friction Factor Calculation

**Severity:** Medium-High
**Lines of Duplicated Code:** ~13 lines × 2 files = ~26 lines

The `_darcy_friction_factor()` function is duplicated:
- `simulations/variable_losses.py:33-41`
- `simulations/multi_segment_physics.py:14-25`

**Exact same implementation:**
```python
def _darcy_friction_factor(reynolds: float, relative_roughness: float) -> float:
    if reynolds <= 0:
        return 0.0
    if reynolds < 2000:
        return 64.0 / reynolds
    return 0.25 / (
        np.log10(relative_roughness / 3.7 + 5.74 / reynolds**0.9) ** 2
    )
```

**Impact:** This is a critical physics calculation that should have a single source of truth.

**Recommendation:** Move to `common.py` as a public utility function.

---

### 1.4 Duplicated Loss Coefficient Pattern

**Severity:** Low-Medium
**Locations:** Multiple files

The pattern for summing minor loss coefficients appears in several places:

```python
float(np.sum(self.minor_loss_coefficients)) if self.minor_loss_coefficients else 0.0
```

**Found in:**
- `simulations/common.py:47` (TubeGeometry.minor_losses)
- `simulations/multi_segment_physics.py:56` (TubeSegment.minor_losses)
- `simulations/multi_segment_physics.py:157` (SegmentedTube._entry_lambda)
- `simulations/multi_segment_physics.py:160` (SegmentedTube._exit_lambda)

**Recommendation:** Create a helper function `sum_loss_coefficients()` or use consistent property pattern.

---

### 1.5 Duplicated Bisection Solver

**Severity:** Medium
**Lines of Code:** ~15 lines × 2 files = ~30 lines

Similar bisection solver logic appears in:
- `simulations/variable_losses.py:55-76` (`_solve_velocity`)
- `simulations/multi_segment_physics.py:228-271` (`solve_velocity`)

**Commonalities:**
- Both solve for velocity using bisection
- Both iterate up to 80 times
- Both use tolerance of 1e-8
- Similar residual computation pattern

**Differences:**
- Different residual equations (single tube vs. segmented)
- Different return types

**Recommendation:** Extract common bisection algorithm with customizable residual function.

---

## 2. Design & Architecture Issues

### 2.1 Mixed Concerns: Simulation + Plotting

**Severity:** Medium
**Issue:** Each simulation module couples physics calculations with visualization code.

**Current Structure:**
```
ideal.py
├── simulate()          # Physics
├── _plot_series()      # Plotting
└── create_plots()      # Mixed

constant_losses.py
├── simulate()          # Physics
├── _plot_series()      # Plotting
└── create_plots()      # Mixed

variable_losses.py
├── simulate()          # Physics
├── _plot_series()      # Plotting
└── create_plots()      # Mixed
```

**Problems:**
1. Difficult to use simulations without importing matplotlib
2. Testing physics requires dealing with plotting code
3. Cannot easily swap visualization libraries
4. Violates Single Responsibility Principle

**Recommendation:** Separate into:
- `simulations/` - Pure physics calculations
- `visualization/` or `plotting/` - Visualization utilities
- Each module should be importable independently

---

### 2.2 No Formal Simulation Interface

**Severity:** Low-Medium
**Issue:** All simulation modules share similar patterns but no formal contract.

**Common Pattern:**
```python
def simulate(config: SimulationConfig, ...) -> SimulationResult:
    """Run simulation"""

def create_plots(config: SimulationConfig, output_dir: str | Path) -> SimulationResult:
    """Run simulation and create plots"""
```

**Problems:**
1. No guarantee of interface consistency
2. Difficult to write generic code that works with any simulation
3. No IDE support for discovering available simulation types

**Recommendation:** Create a `Protocol` or ABC defining the simulation interface:

```python
from typing import Protocol

class Simulation(Protocol):
    def simulate(self, config: SimulationConfig, **kwargs) -> SimulationResult:
        ...

    def create_plots(self, config: SimulationConfig, output_dir: str | Path) -> SimulationResult:
        ...
```

---

### 2.3 Hardcoded Plot Configuration

**Severity:** Low
**Issue:** Plot styling parameters scattered throughout code.

**Examples:**
- Figure size: `figsize=(8, 6)` and `figsize=(9, 6)`
- DPI: `dpi=150` (hardcoded in 4 places)
- Colors: `"tab:blue"`, `"tab:red"`, etc.
- Font sizes: `fontsize=9`
- Annotation positions: `0.02, 0.98`

**Recommendation:** Create a `PlotConfig` dataclass:

```python
@dataclass(frozen=True)
class PlotConfig:
    figsize: tuple[float, float] = (8, 6)
    dpi: int = 150
    grid_alpha: float = 0.3
    line_width: float = 2.0
    annotation_fontsize: int = 9
    annotation_position: tuple[float, float] = (0.02, 0.98)
    default_colors: dict[str, str] = field(default_factory=...)
```

---

### 2.4 Repeated Metadata Handling

**Severity:** Low
**Issue:** JSON metadata saving is repeated across modules.

**Pattern appears in:**
- `ideal.py:159-162`
- `constant_losses.py:167-170`
- `variable_losses.py:259-262`

```python
metadata_path = directory / "metadata.json"
with metadata_path.open("w", encoding="utf-8") as handle:
    json.dump(result.to_metadata(), handle, indent=2)
```

**Recommendation:** Create a helper function in `common.py`:

```python
def save_metadata(result: SimulationResult | MultiSegmentInitialState,
                  output_path: Path) -> Path:
    """Save simulation metadata as JSON."""
```

---

## 3. Detailed Refactoring Proposals

### Proposal 1: Extract Common Utilities Module

**Priority:** High
**Effort:** Medium (2-3 hours)
**Risk:** Low

**Actions:**

1. **Move validation functions to `common.py`:**
   ```python
   def validate_area_ratio(k: float) -> None:
       """Validate tube-to-reservoir area ratio."""
       if k <= 0 or k >= 1:
           raise ValueError("The tube-to-reservoir area ratio must lie between 0 and 1.")

   def validate_head(head: float) -> None:
       """Validate reservoir head is positive."""
       if head <= 0:
           raise ValueError("The reservoir surface must remain above the outlet height.")

   def darcy_friction_factor(reynolds: float, relative_roughness: float) -> float:
       """Calculate Darcy friction factor using Swamee-Jain approximation."""
       if reynolds <= 0:
           return 0.0
       if reynolds < 2000:
           return 64.0 / reynolds
       return 0.25 / (np.log10(relative_roughness / 3.7 + 5.74 / reynolds**0.9) ** 2)
   ```

2. **Update all simulation modules to import from `common`:**
   ```python
   from .common import validate_area_ratio, validate_head, darcy_friction_factor
   ```

3. **Remove duplicate private functions from:**
   - `ideal.py`
   - `constant_losses.py`
   - `variable_losses.py`
   - `multi_segment.py`
   - `multi_segment_physics.py`

**Benefits:**
- Single source of truth for critical calculations
- Easier testing
- Bug fixes apply everywhere automatically
- Reduced LOC by ~80 lines

---

### Proposal 2: Create Plotting Module

**Priority:** High
**Effort:** Medium-High (3-4 hours)
**Risk:** Medium

**Actions:**

1. **Create `simulations/plotting.py`:**

```python
"""Visualization utilities for siphon simulations."""

from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Sequence

import matplotlib.pyplot as plt
import numpy as np

from .common import SimulationResult


@dataclass(frozen=True)
class PlotStyle:
    """Configuration for plot appearance."""
    color: str = "tab:blue"
    linewidth: float = 2.0
    facecolor: str = "wheat"


@dataclass(frozen=True)
class PlotConfig:
    """Global plotting configuration."""
    figsize: tuple[float, float] = (8, 6)
    comparison_figsize: tuple[float, float] = (9, 6)
    dpi: int = 150
    grid_alpha: float = 0.3
    annotation_fontsize: int = 9
    annotation_position: tuple[float, float] = (0.02, 0.98)


def plot_series(
    x: np.ndarray,
    y: np.ndarray,
    xlabel: str,
    ylabel: str,
    title: str,
    annotation: str,
    output_path: Path,
    style: PlotStyle = PlotStyle(),
    config: PlotConfig = PlotConfig(),
    extra_lines: Sequence[tuple[float, dict]] | None = None,
) -> None:
    """Create and save a line plot with annotation."""
    plt.figure(figsize=config.figsize)
    plt.plot(x, y, color=style.color, linewidth=style.linewidth)

    if extra_lines:
        for value, kwargs in extra_lines:
            plt.axhline(value, **kwargs)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=config.grid_alpha)

    plt.text(
        *config.annotation_position,
        annotation,
        transform=plt.gca().transAxes,
        fontsize=config.annotation_fontsize,
        verticalalignment="top",
        horizontalalignment="left",
        bbox=dict(boxstyle="round", facecolor=style.facecolor, alpha=0.85),
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=config.dpi)
    plt.close()


# Additional specialized plotting functions...
```

2. **Update simulation modules to use new plotting utilities:**
   ```python
   from .plotting import plot_series, PlotStyle, PlotConfig
   ```

3. **Define model-specific styles:**
   ```python
   IDEAL_STYLE = PlotStyle(color="tab:blue", facecolor="wheat")
   CONSTANT_STYLE = PlotStyle(color="tab:red", facecolor="lightyellow")
   VARIABLE_STYLE = PlotStyle(color="tab:green", facecolor="lavender")
   ```

**Benefits:**
- Eliminates ~105 lines of duplication
- Centralized plot styling
- Easier to change appearance globally
- Better separation of concerns
- Can test plotting independently

---

### Proposal 3: Extract Numerical Solvers

**Priority:** Medium
**Effort:** Medium (2-3 hours)
**Risk:** Medium

**Actions:**

1. **Create `simulations/solvers.py`:**

```python
"""Numerical solution algorithms for siphon simulations."""

from __future__ import annotations
from typing import Callable, Tuple

import numpy as np


def bisection_solver(
    residual_fn: Callable[[float], float],
    lower_bound: float,
    upper_bound: float,
    max_iterations: int = 80,
    tolerance: float = 1e-8,
) -> float:
    """
    Solve for root using bisection method.

    Args:
        residual_fn: Function that returns 0 at the solution
        lower_bound: Lower bound of search interval
        upper_bound: Upper bound of search interval
        max_iterations: Maximum number of iterations
        tolerance: Convergence tolerance

    Returns:
        Approximate solution
    """
    lower = lower_bound
    upper = upper_bound

    for _ in range(max_iterations):
        mid = 0.5 * (lower + upper)
        residual = residual_fn(mid)

        if abs(residual) < tolerance:
            return mid

        if residual > 0:
            upper = mid
        else:
            lower = mid

    return 0.5 * (lower + upper)
```

2. **Refactor `variable_losses._solve_velocity()` to use common solver:**

```python
from .solvers import bisection_solver

def _solve_velocity(config: SimulationConfig, head: float) -> Tuple[float, float]:
    if head <= 0:
        return 0.0, config.tube.minor_losses

    g = config.fluid.gravity
    k = config.area_ratio
    ideal_velocity = np.sqrt(2 * g * head / max(1e-12, 1 - k**2))

    def residual(v: float) -> float:
        loss_coeff = _loss_coefficient(config, v)
        return v**2 * (1 - k**2 + loss_coeff) - 2 * g * head

    velocity = bisection_solver(residual, 0.0, ideal_velocity)
    return velocity, _loss_coefficient(config, velocity)
```

3. **Similarly refactor `multi_segment_physics.solve_velocity()`**

**Benefits:**
- Reusable numerical algorithms
- Easier to add other solvers (Newton-Raphson, etc.)
- Better testability of numerical methods
- Reduced code duplication

---

### Proposal 4: Create Simulation Base Protocol

**Priority:** Low-Medium
**Effort:** Low (1-2 hours)
**Risk:** Low

**Actions:**

1. **Add to `common.py`:**

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class SimulationModule(Protocol):
    """Protocol defining the interface for simulation modules."""

    def simulate(self, config: SimulationConfig, **kwargs) -> SimulationResult:
        """Run the simulation and return results."""
        ...

    def create_plots(
        self,
        config: SimulationConfig,
        output_dir: str | Path,
        **kwargs
    ) -> SimulationResult:
        """Run simulation and generate diagnostic plots."""
        ...
```

2. **Update `comparison.py` to leverage the protocol:**

```python
def run_simulation(
    module: SimulationModule,
    config: SimulationConfig,
    **kwargs
) -> SimulationResult:
    """Generic simulation runner."""
    return module.simulate(config, **kwargs)
```

**Benefits:**
- Type safety for generic code
- IDE autocomplete support
- Documentation of expected interface
- Easier to add new simulation types

---

### Proposal 5: Consolidate Metadata Handling

**Priority:** Low
**Effort:** Low (1 hour)
**Risk:** Low

**Actions:**

1. **Add to `common.py`:**

```python
from typing import Protocol

class HasMetadata(Protocol):
    """Protocol for objects that can be serialized to metadata."""
    def to_metadata(self) -> dict:
        ...


def save_simulation_metadata(
    result: HasMetadata,
    output_dir: str | Path,
    filename: str = "metadata.json",
    indent: int = 2,
) -> Path:
    """
    Save simulation metadata to JSON file.

    Args:
        result: Simulation result with to_metadata() method
        output_dir: Directory to save metadata
        filename: Name of JSON file
        indent: JSON indentation level

    Returns:
        Path to saved metadata file
    """
    directory = ensure_output_dir(output_dir)
    metadata_path = directory / filename

    with metadata_path.open("w", encoding="utf-8") as handle:
        json.dump(result.to_metadata(), handle, indent=indent)

    return metadata_path
```

2. **Update all modules to use common function:**

```python
from .common import save_simulation_metadata

# In create_plots():
save_simulation_metadata(result, directory)
```

**Benefits:**
- DRY principle
- Consistent metadata format
- Easier to add compression, validation, etc.

---

## 4. Priority & Impact Assessment

### High Priority (Immediate Implementation Recommended)

| Proposal | Effort | Impact | Risk | ROI |
|----------|--------|--------|------|-----|
| **1. Extract Common Utilities** | Medium | High | Low | **Very High** |
| **2. Create Plotting Module** | Medium-High | High | Medium | **High** |

**Rationale:** These eliminate the most duplication and provide immediate maintenance benefits.

---

### Medium Priority (Implement Soon)

| Proposal | Effort | Impact | Risk | ROI |
|----------|--------|--------|------|-----|
| **3. Extract Numerical Solvers** | Medium | Medium | Medium | **Medium** |
| **4. Simulation Base Protocol** | Low | Medium | Low | **Medium-High** |

**Rationale:** Improve architecture but less critical than eliminating duplication.

---

### Low Priority (Nice to Have)

| Proposal | Effort | Impact | Risk | ROI |
|----------|--------|--------|------|-----|
| **5. Consolidate Metadata Handling** | Low | Low-Medium | Low | **Medium** |

**Rationale:** Minor improvement, implement if time permits.

---

## 5. Implementation Roadmap

### Phase 1: Foundation (Week 1)

**Goal:** Eliminate critical duplication

1. **Day 1-2:** Implement Proposal 1 (Extract Common Utilities)
   - Move validation and friction factor functions
   - Update all imports
   - Run full test suite
   - Commit: "refactor: extract common physics utilities"

2. **Day 3-5:** Implement Proposal 2 (Create Plotting Module)
   - Create `plotting.py` with `plot_series` and configuration
   - Migrate plotting from simulation modules
   - Update all simulation modules
   - Run tests and verify plots unchanged
   - Commit: "refactor: extract plotting utilities to separate module"

**Deliverables:**
- ~180 lines of duplication eliminated
- All tests passing
- No changes to simulation outputs

---

### Phase 2: Architecture (Week 2)

**Goal:** Improve code structure

3. **Day 1-2:** Implement Proposal 3 (Extract Numerical Solvers)
   - Create `solvers.py` with bisection algorithm
   - Refactor `variable_losses` and `multi_segment_physics`
   - Add solver unit tests
   - Commit: "refactor: extract numerical solvers"

4. **Day 3-4:** Implement Proposal 4 (Simulation Protocol)
   - Add `SimulationModule` protocol to `common.py`
   - Update type hints in `comparison.py`
   - Add protocol documentation
   - Commit: "refactor: add simulation module protocol"

5. **Day 5:** Implement Proposal 5 (Metadata Handling)
   - Add `save_simulation_metadata` to `common.py`
   - Update all modules
   - Commit: "refactor: consolidate metadata handling"

**Deliverables:**
- Improved architecture
- Better type safety
- All refactoring complete

---

### Phase 3: Testing & Documentation (Week 3)

**Goal:** Ensure quality and update documentation

6. **Day 1-2:** Update test suite
   - Add tests for new utility functions
   - Add tests for plotting module
   - Verify coverage maintained/improved

7. **Day 3-4:** Update documentation
   - Update README with new module structure
   - Add docstrings to new modules
   - Update physics docs if needed

8. **Day 5:** Final review
   - Code review
   - Performance testing
   - Create summary document

---

## 6. Additional Recommendations

### 6.1 Consider Type Aliases

For improved readability:

```python
# In common.py
from typing import TypeAlias

Meters: TypeAlias = float
Seconds: TypeAlias = float
KilogramsPerCubicMeter: TypeAlias = float
PascalSeconds: TypeAlias = float
```

### 6.2 Add Logging

For debugging and production use:

```python
import logging

logger = logging.getLogger(__name__)

def simulate(config: SimulationConfig, ...) -> SimulationResult:
    logger.info(f"Starting simulation: {config.label}")
    # ...
    logger.info(f"Simulation complete. Drain time: {t_empty:.2f}s")
```

### 6.3 Configuration File Support

Allow users to define simulations in YAML/JSON:

```yaml
# simulation_config.yaml
reservoir:
  surface_area: 0.5
  initial_height: 0.8
  outlet_height: 0.2

tube:
  length: 1.2
  diameter: 0.02
  friction_factor: 0.02
  minor_loss_coefficients: [0.5]
```

### 6.4 CLI Tool

Create a command-line interface:

```bash
python -m simulations run --config simulation_config.yaml --output plots/
python -m simulations compare --configs config1.yaml config2.yaml
```

---

## Conclusion

The IYPT siphon simulation codebase is well-written but contains significant opportunities for refactoring. The proposed changes will:

- **Reduce code duplication by ~180 lines** (8% of total codebase)
- **Improve maintainability** through better separation of concerns
- **Enhance testability** with isolated, reusable components
- **Increase type safety** with formal interfaces
- **Preserve functionality** - all changes are refactoring only

**Recommended Approach:** Implement Phase 1 (High Priority items) immediately for maximum impact with minimal risk. Phase 2 and 3 can follow as time permits.

**Estimated Total Effort:** 2-3 weeks for complete implementation
**Risk Level:** Low to Medium (with good test coverage)
**Expected ROI:** High (significant maintenance improvements)

---

## Appendix: Code Metrics

### Current State
- **Total Python LOC:** ~2,220
- **Duplicate Code:** ~180 lines (8.1%)
- **Number of Modules:** 10
- **Test Coverage:** Comprehensive (53 tests)

### After Refactoring (Estimated)
- **Total Python LOC:** ~2,100 (5% reduction)
- **Duplicate Code:** <20 lines (<1%)
- **Number of Modules:** 12 (+plotting, +solvers)
- **Test Coverage:** Enhanced (60+ tests)

### Complexity Metrics
- **Current:** Some functions with cyclomatic complexity >10
- **After:** Most functions <10 complexity
- **Maintainability Index:** Expected improvement of 10-15%

---

**Document Version:** 1.0
**Author:** Claude (AI Assistant)
**Last Updated:** 2025-10-21
