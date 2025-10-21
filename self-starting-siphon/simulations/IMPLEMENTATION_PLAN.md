# Comprehensive Code Improvement Plan

## Overview
This plan addresses all 20 identified issues across 6 phases, organized by priority and dependencies. Estimated total effort: 15-20 hours.

---

## **PHASE 1: Fix Critical Bugs** (Priority: CRITICAL)
**Estimated Time**: 4-5 hours

### Task 1.1: Fix Pressure Calculation in Ideal Model
**Files**: `simulations/ideal.py`

**Current Issue** (Line 141-143):
```python
pressure = config.fluid.atmospheric_pressure + config.fluid.density * config.fluid.gravity * (
    config.reservoir.outlet_height - result.height
)
```

**Action Plan**:
1. Determine the intended reference point for pressure calculation
2. Options:
   - **Option A**: Pressure at tube outlet (should be atmospheric)
   - **Option B**: Pressure at crest/highest point (for cavitation check)
   - **Option C**: Gauge pressure at reservoir bottom

**Recommended Fix** (pressure at crest/highest point):
```python
# Calculate pressure at the crest (highest point in siphon)
# Assuming crest is at entry_height or can be specified
crest_height = config.tube.entry_height if hasattr(config.tube, 'entry_height') else config.reservoir.initial_height
pressure = config.fluid.atmospheric_pressure + config.fluid.density * config.fluid.gravity * (
    result.height - crest_height  # Head from surface to crest
) - config.fluid.density * config.fluid.gravity * result.velocity**2 / (2 * config.fluid.gravity)  # Dynamic head
```

**Alternative**: Document current formula explaining it's gauge pressure at a specific point.

**Testing**:
- Verify pressure decreases as reservoir drains
- Ensure minimum pressure is compared correctly to vapor pressure
- Update annotation text to clarify what pressure is being shown

---

### Task 1.2: Add Comprehensive Multi-Segment Tests
**Files**: `test_simulations.py` (add ~300 lines)

**New Test Classes to Add**:

#### 1.2.1 TestTubeSegment
```python
@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestTubeSegment(unittest.TestCase):
    """Test TubeSegment dataclass."""

    def test_basic_construction(self):
        # Test segment creation with valid parameters

    def test_area_calculation(self):
        # Verify cross-sectional area formula

    def test_relative_roughness(self):
        # Test roughness ratio calculation

    def test_elevation_change_positive(self):
        # Test upward slope (angle > 0)

    def test_elevation_change_negative(self):
        # Test downward slope (angle < 0)

    def test_elevation_change_horizontal(self):
        # Test flat segment (angle = 0)

    def test_validation_negative_length(self):
        # Ensure ValueError for length <= 0

    def test_validation_negative_diameter(self):
        # Ensure ValueError for diameter <= 0
```

#### 1.2.2 TestSegmentedTube
```python
@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestSegmentedTube(unittest.TestCase):
    """Test SegmentedTube assembly and validation."""

    def test_basic_construction(self):
        # Test multi-segment tube creation

    def test_node_heights_calculation(self):
        # Verify cumulative elevation calculation

    def test_crest_detection_single_crest(self):
        # Test identifying one local maximum

    def test_crest_detection_multiple_crests(self):
        # Test identifying multiple peaks

    def test_crest_detection_no_crests(self):
        # Test monotonic descent (no peaks)

    def test_area_ratio(self):
        # Test k = A_tube / A_reservoir

    def test_validation_mismatched_outlet(self):
        # Ensure error when segments don't sum to outlet_height

    def test_validation_mixed_diameters(self):
        # Ensure error when diameters differ

    def test_loss_breakdown_zero_velocity(self):
        # Test loss calculation at v=0

    def test_loss_breakdown_laminar_flow(self):
        # Test with Re < 2000

    def test_loss_breakdown_turbulent_flow(self):
        # Test with Re > 2000

    def test_pressure_profile(self):
        # Verify backward-march pressure calculation
```

#### 1.2.3 TestMultiSegmentSolver
```python
@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestMultiSegmentSolver(unittest.TestCase):
    """Test multi-segment solver functions."""

    def test_solve_velocity_zero_head(self):
        # Test with no driving head

    def test_solve_velocity_convergence(self):
        # Verify bisection converges

    def test_crest_pressures_identification(self):
        # Test extracting pressures at crests

    def test_compute_initial_state(self):
        # Integration test for primed state

    def test_metadata_serialization(self):
        # Verify JSON output format

    def test_describe_state_output(self):
        # Test human-readable formatting
```

**Files to Create**:
- Add above test classes to `test_simulations.py` starting at line 718

**Coverage Goal**: Achieve >90% coverage for multi_segment*.py modules

---

### Task 1.3: Add TubeGeometry.entry_height Field
**Files**: `simulations/common.py`

**Issue**: Pressure calculation needs to know crest height, but simple TubeGeometry doesn't track this.

**Solution**: Add optional entry_height to TubeGeometry for simple configurations:
```python
@dataclass(frozen=True)
class TubeGeometry:
    """Geometric description of the siphon tube."""

    length: float  # m
    diameter: float  # m
    minor_loss_coefficients: Sequence[float] = field(default_factory=tuple)
    friction_factor: float | None = None
    roughness: float | None = None  # m, absolute roughness for turbulent models
    entry_height: float | None = None  # m, height where tube enters (for crest pressure calc)

    # ... rest of class unchanged
```

**Impact**: Allows ideal/constant/variable models to calculate crest pressure correctly.

---

## **PHASE 2: Refactor Duplicated Code** (Priority: HIGH)
**Estimated Time**: 3-4 hours

### Task 2.1: Consolidate Plotting Functions
**Files**: `simulations/common.py`, `simulations/ideal.py`, `simulations/constant_losses.py`, `simulations/variable_losses.py`

#### Step 2.1.1: Create Common Plotting Utility
Add to `simulations/common.py`:

```python
from typing import Tuple, Callable
import matplotlib.pyplot as plt

def plot_series(
    x: np.ndarray,
    y: np.ndarray,
    xlabel: str,
    ylabel: str,
    title: str,
    annotation: str,
    output_path: Path,
    color: str = "tab:blue",
    facecolor: str = "white",
    extra_lines: Tuple[Tuple[float, dict], ...] | None = None,
) -> None:
    """Plot a time series with annotation box.

    Parameters
    ----------
    x : np.ndarray
        X-axis data (typically time)
    y : np.ndarray
        Y-axis data
    xlabel : str
        Label for x-axis
    ylabel : str
        Label for y-axis
    title : str
        Plot title
    annotation : str
        Text for annotation box
    output_path : Path
        Where to save the plot
    color : str, default="tab:blue"
        Line color
    facecolor : str, default="white"
        Annotation box background color
    extra_lines : tuple of (value, kwargs) tuples, optional
        Horizontal reference lines to add
    """
    plt.figure(figsize=(8, 6))
    plt.plot(x, y, color=color, linewidth=2)
    if extra_lines:
        for value, kwargs in extra_lines:
            plt.axhline(value, **kwargs)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.text(
        0.02,
        0.98,
        annotation,
        transform=plt.gca().transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="left",
        bbox=dict(boxstyle="round", facecolor=facecolor, alpha=0.85),
    )
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
```

#### Step 2.1.2: Update All Simulation Modules
In `ideal.py`, `constant_losses.py`, `variable_losses.py`:

1. Remove local `_plot_series` functions (lines 63-95 in ideal.py, etc.)
2. Update imports:
   ```python
   from .common import (
       # ... existing imports ...
       plot_series,
   )
   ```
3. Replace all calls:
   ```python
   # OLD
   _plot_series(...)

   # NEW
   plot_series(..., facecolor="wheat")  # or "lightyellow", "lavender"
   ```

**Savings**: Removes ~90 lines of duplicated code

---

### Task 2.2: Consolidate Validation Functions
**Files**: `simulations/common.py`, `simulations/ideal.py`, `simulations/constant_losses.py`, `simulations/variable_losses.py`, `simulations/multi_segment.py`

#### Step 2.2.1: Add to common.py
```python
def validate_area_ratio(k: float) -> None:
    """Validate that area ratio is in valid range (0, 1).

    Parameters
    ----------
    k : float
        Tube-to-reservoir area ratio

    Raises
    ------
    ValueError
        If k <= 0 or k >= 1
    """
    if k <= 0 or k >= 1:
        raise ValueError("The tube-to-reservoir area ratio must lie between 0 and 1.")


def validate_head(head: float) -> None:
    """Validate that hydraulic head is positive.

    Parameters
    ----------
    head : float
        Hydraulic head (height difference)

    Raises
    ------
    ValueError
        If head <= 0
    """
    if head <= 0:
        raise ValueError("The reservoir surface must remain above the outlet height.")
```

#### Step 2.2.2: Update All Modules
Replace `_validate_area_ratio` and `_validate_head` with imports from common.

**Files to Update**:
- `simulations/ideal.py`: Remove lines 24-26, import from common
- `simulations/constant_losses.py`: Remove lines 24-31, import from common
- `simulations/variable_losses.py`: Remove lines 23-30, import from common
- `simulations/multi_segment.py`: Remove lines 21-23, import from common

---

### Task 2.3: Consolidate Darcy Friction Factor
**Files**: `simulations/common.py`, `simulations/variable_losses.py`, `simulations/multi_segment_physics.py`

The `_darcy_friction_factor` function is identical in two files.

#### Step 2.3.1: Move to common.py
```python
def darcy_friction_factor(reynolds: float, relative_roughness: float) -> float:
    """Calculate Darcy-Weisbach friction factor.

    Uses laminar formula for Re < 2000, Swamee-Jain approximation for turbulent.

    Parameters
    ----------
    reynolds : float
        Reynolds number (ρvD/μ)
    relative_roughness : float
        Pipe relative roughness (ε/D)

    Returns
    -------
    float
        Darcy friction factor f

    Notes
    -----
    - Laminar (Re < 2000): f = 64/Re
    - Turbulent (Re >= 2000): Swamee-Jain explicit approximation
    """
    if reynolds <= 0:
        return 0.0
    if reynolds < 2000.0:
        return 64.0 / reynolds
    # Swamee–Jain explicit approximation for turbulent flow
    return 0.25 / (
        np.log10(relative_roughness / 3.7 + 5.74 / reynolds**0.9) ** 2
    )
```

#### Step 2.3.2: Update Modules
- `variable_losses.py`: Remove lines 33-40, import from common, update calls
- `multi_segment_physics.py`: Remove lines 14-24, import from common, update calls

---

## **PHASE 3: Add Constants and Improve Code Quality** (Priority: MEDIUM)
**Estimated Time**: 2-3 hours

### Task 3.1: Define Module-Level Constants
**Files**: `simulations/constants.py` (new file)

Create new file with all magic numbers:

```python
"""Physical and numerical constants for siphon simulations."""

# Numerical solver parameters
BISECTION_MAX_ITERATIONS: int = 80
"""Maximum iterations for bisection velocity solver."""

BISECTION_TOLERANCE: float = 1e-8
"""Convergence tolerance for bisection solver (m/s)."""

# Time-stepping parameters
ADAPTIVE_TIME_STEP_SAFETY_FACTOR: float = 0.5
"""Safety factor for adaptive time step (Courant-like condition)."""

MIN_TIME_STEP_FACTOR: float = 0.1
"""Minimum time step as fraction of requested dt."""

DEFAULT_TIME_STEP: float = 0.05
"""Default time step for variable-loss simulations (seconds)."""

MAX_SIMULATION_TIME: float = 3600.0
"""Maximum simulation duration (seconds)."""

# Flow regime thresholds
REYNOLDS_LAMINAR_THRESHOLD: float = 2000.0
"""Reynolds number below which flow is laminar."""

REYNOLDS_MINIMUM: float = 1.0
"""Minimum Reynolds number for friction calculations."""

# Plotting parameters
DEFAULT_FIGURE_SIZE: tuple[int, int] = (8, 6)
"""Default figure dimensions (width, height) in inches."""

COMPARISON_FIGURE_SIZE: tuple[int, int] = (9, 6)
"""Figure dimensions for comparison plots."""

DEFAULT_DPI: int = 150
"""Default resolution for saved plots."""

DEFAULT_NUM_POINTS: int = 400
"""Default number of time points for analytical solutions."""

GRID_ALPHA: float = 0.3
"""Alpha transparency for plot grid lines."""

ANNOTATION_FONTSIZE: int = 9
"""Font size for plot annotation boxes."""

# Physical validation thresholds
MAX_REASONABLE_REYNOLDS: float = 1e6
"""Reynolds number above which flow assumptions may break down."""

MAX_REASONABLE_RELATIVE_ROUGHNESS: float = 0.05
"""Relative roughness above which pipe is very rough."""

CAVITATION_WARNING_MARGIN: float = 0.1
"""Pressure margin (as fraction of P_vapor) for cavitation warnings."""

# Numerical stability
HEIGHT_COMPARISON_TOLERANCE: float = 1e-6
"""Tolerance for comparing heights (meters)."""

AREA_COMPARISON_TOLERANCE: float = 1e-6
"""Tolerance for comparing areas (m²)."""
```

### Task 3.2: Update All Files to Use Constants
**Files**: All simulation modules

Replace hardcoded values:

**Example** in `variable_losses.py`:
```python
# OLD
for _ in range(80):  # Line 65

# NEW
from .constants import BISECTION_MAX_ITERATIONS
for _ in range(BISECTION_MAX_ITERATIONS):
```

**Files requiring updates**:
- `simulations/variable_losses.py`: ~8 constants
- `simulations/multi_segment_physics.py`: ~5 constants
- `simulations/ideal.py`: ~3 constants
- `simulations/constant_losses.py`: ~3 constants
- `simulations/comparison.py`: ~2 constants
- `simulations/multi_segment.py`: ~2 constants

---

### Task 3.3: Add Comprehensive Docstrings
**Files**: All simulation modules

Add/enhance docstrings for all private functions following NumPy style:

**Example transformation**:
```python
# BEFORE
def _solve_velocity(config: SimulationConfig, head: float) -> Tuple[float, float]:
    if head <= 0:
        return 0.0, config.tube.minor_losses
    # ...

# AFTER
def _solve_velocity(config: SimulationConfig, head: float) -> Tuple[float, float]:
    """Solve for velocity using bisection with Reynolds-dependent friction.

    Iteratively determines the velocity that satisfies the energy balance
    equation when friction factor depends on the velocity itself (via Reynolds
    number). Uses bisection search between 0 and ideal velocity.

    Parameters
    ----------
    config : SimulationConfig
        Complete simulation configuration including geometry and fluid properties
    head : float
        Available hydraulic head (m), i.e., height difference driving the flow

    Returns
    -------
    velocity : float
        Tube velocity satisfying energy balance (m/s)
    loss_coefficient : float
        Total head-loss coefficient Λ at the computed velocity

    Notes
    -----
    The solver finds v such that:
        v²(1 - k² + Λ(v)) = 2gh

    where Λ(v) includes both major losses (Darcy-Weisbach with Re-dependent f)
    and minor losses.

    If head <= 0, returns (0.0, minor_losses_only).

    Convergence typically occurs within 20-30 iterations with tolerance 1e-8.
    """
    if head <= 0:
        return 0.0, config.tube.minor_losses
    # ...
```

**Priority Functions**:
1. All `_validate_*` functions
2. All `_solve_*` functions
3. All `_plot_*` or `plot_*` functions
4. All `_darcy_*` or `_loss_*` helper functions

---

### Task 3.4: Update Deprecated datetime Usage
**Files**: `simulations/common.py`

```python
# OLD (line 120)
from datetime import datetime
timestamp = datetime.utcnow().isoformat(timespec="seconds")

# NEW
from datetime import datetime, timezone
timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
```

---

## **PHASE 4: Add Logging and Validation Warnings** (Priority: MEDIUM)
**Estimated Time**: 3-4 hours

### Task 4.1: Implement Logging Framework
**Files**: `simulations/logging_config.py` (new), all simulation modules

#### Step 4.1.1: Create Logging Configuration
```python
"""Logging configuration for siphon simulations."""

import logging
import sys
from typing import Optional

def configure_logging(
    level: int = logging.INFO,
    filename: Optional[str] = None,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Configure logging for simulation package.

    Parameters
    ----------
    level : int, default=logging.INFO
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    filename : str, optional
        If provided, log to file in addition to console
    format_string : str, optional
        Custom log format string

    Returns
    -------
    logging.Logger
        Configured logger instance
    """
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    logger = logging.getLogger('simulations')
    logger.setLevel(level)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(console_handler)

    # File handler (optional)
    if filename:
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module.

    Parameters
    ----------
    name : str
        Module name (typically __name__)

    Returns
    -------
    logging.Logger
        Logger instance
    """
    return logging.getLogger(f'simulations.{name}')
```

#### Step 4.1.2: Add Logging to Simulations

**In `variable_losses.py`**:
```python
from .logging_config import get_logger

logger = get_logger(__name__)

def simulate(
    config: SimulationConfig,
    time_step: float = 0.05,
    max_time: float = 3600.0,
) -> Tuple[SimulationResult, np.ndarray]:
    """..."""

    logger.info(f"Starting variable-loss simulation (dt={time_step}s)")
    logger.debug(f"Configuration: k={config.area_ratio:.4f}, head={config.reservoir.initial_head:.3f}m")

    # ... simulation loop ...

    iteration_count = 0
    while height > config.reservoir.outlet_height and time < max_time:
        iteration_count += 1

        if iteration_count % 100 == 0:
            logger.debug(f"t={time:.2f}s, h={height:.3f}m, v={velocity:.3f}m/s, Re={reynolds:.0f}")

        # ... rest of loop ...

    logger.info(f"Simulation completed: {iteration_count} iterations, drain_time={time:.2f}s")

    return result, loss_array
```

**Similar additions to**:
- `ideal.py`: Log initial conditions and drain time
- `constant_losses.py`: Log loss coefficient used
- `multi_segment.py`: Log segment count, crest count, convergence

---

### Task 4.2: Add Physical Validation Warnings
**Files**: `simulations/validators.py` (new)

```python
"""Physical validation and sanity checks for simulation parameters."""

import logging
from typing import List
import numpy as np

from .common import SimulationConfig, FluidProperties, TubeGeometry
from .constants import (
    MAX_REASONABLE_REYNOLDS,
    MAX_REASONABLE_RELATIVE_ROUGHNESS,
    CAVITATION_WARNING_MARGIN,
)

logger = logging.getLogger('simulations.validators')


class ValidationWarning:
    """Container for a validation warning."""

    def __init__(self, severity: str, parameter: str, message: str):
        self.severity = severity  # 'INFO', 'WARNING', 'CRITICAL'
        self.parameter = parameter
        self.message = message

    def __str__(self):
        return f"[{self.severity}] {self.parameter}: {self.message}"


def validate_reynolds_number(
    velocity: float,
    diameter: float,
    fluid: FluidProperties,
) -> List[ValidationWarning]:
    """Check if Reynolds number is in reasonable range.

    Parameters
    ----------
    velocity : float
        Flow velocity (m/s)
    diameter : float
        Pipe diameter (m)
    fluid : FluidProperties
        Fluid properties

    Returns
    -------
    list of ValidationWarning
        Any warnings generated
    """
    warnings = []
    reynolds = fluid.density * velocity * diameter / fluid.viscosity

    if reynolds > MAX_REASONABLE_REYNOLDS:
        warnings.append(ValidationWarning(
            'WARNING',
            'Reynolds number',
            f'Re={reynolds:.0f} exceeds typical range for siphons. '
            f'Turbulence model may be inaccurate.'
        ))

    if reynolds < 1.0 and velocity > 0:
        warnings.append(ValidationWarning(
            'WARNING',
            'Reynolds number',
            f'Re={reynolds:.2f} is very low. Flow may be dominated by surface tension.'
        ))

    return warnings


def validate_roughness(tube: TubeGeometry) -> List[ValidationWarning]:
    """Check if roughness is physically reasonable.

    Parameters
    ----------
    tube : TubeGeometry
        Tube geometry specification

    Returns
    -------
    list of ValidationWarning
        Any warnings generated
    """
    warnings = []

    if tube.relative_roughness > MAX_REASONABLE_RELATIVE_ROUGHNESS:
        warnings.append(ValidationWarning(
            'WARNING',
            'Surface roughness',
            f'Relative roughness ε/D={tube.relative_roughness:.4f} is very high. '
            f'Pipe may be severely corroded or this value may be an error.'
        ))

    return warnings


def check_cavitation_risk(
    pressure: float,
    vapor_pressure: float,
    location: str = "crest",
) -> List[ValidationWarning]:
    """Check if pressure is dangerously close to cavitation.

    Parameters
    ----------
    pressure : float
        Absolute pressure (Pa)
    vapor_pressure : float
        Vapor pressure of fluid (Pa)
    location : str, default="crest"
        Description of where pressure is measured

    Returns
    -------
    list of ValidationWarning
        Any warnings generated
    """
    warnings = []

    margin = (pressure - vapor_pressure) / vapor_pressure

    if pressure < vapor_pressure:
        warnings.append(ValidationWarning(
            'CRITICAL',
            f'Cavitation at {location}',
            f'Pressure ({pressure/1000:.1f} kPa) is below vapor pressure '
            f'({vapor_pressure/1000:.1f} kPa). Siphon will break!'
        ))
    elif margin < CAVITATION_WARNING_MARGIN:
        warnings.append(ValidationWarning(
            'WARNING',
            f'Cavitation risk at {location}',
            f'Pressure ({pressure/1000:.1f} kPa) is only {margin*100:.1f}% above '
            f'vapor pressure. Risk of cavitation.'
        ))

    return warnings


def validate_configuration(config: SimulationConfig) -> List[ValidationWarning]:
    """Run all validation checks on a configuration.

    Parameters
    ----------
    config : SimulationConfig
        Configuration to validate

    Returns
    -------
    list of ValidationWarning
        All warnings generated
    """
    warnings = []

    # Check roughness
    warnings.extend(validate_roughness(config.tube))

    # Check area ratio
    k = config.area_ratio
    if k > 0.3:
        warnings.append(ValidationWarning(
            'WARNING',
            'Area ratio',
            f'k={k:.3f} is large. Ideal model assumptions may be violated. '
            f'Consider using variable-loss model.'
        ))

    # Check loss coefficient if available
    if config.tube.friction_factor is not None:
        try:
            lambda_total = config.tube.constant_loss_coefficient()
            if lambda_total > 100:
                warnings.append(ValidationWarning(
                    'WARNING',
                    'Loss coefficient',
                    f'Λ={lambda_total:.1f} is very large. Check tube geometry and minor losses.'
                ))
        except ValueError:
            pass

    # Log all warnings
    for warning in warnings:
        if warning.severity == 'CRITICAL':
            logger.critical(str(warning))
        elif warning.severity == 'WARNING':
            logger.warning(str(warning))
        else:
            logger.info(str(warning))

    return warnings
```

#### Step 4.2.1: Integrate Validators into Simulations

**In `variable_losses.py` simulate function**:
```python
from .validators import validate_configuration, validate_reynolds_number, check_cavitation_risk

def simulate(...):
    # After initial setup
    warnings = validate_configuration(config)

    # During simulation
    while height > config.reservoir.outlet_height and time < max_time:
        # ... compute velocity ...

        # Check Reynolds number occasionally
        if iteration_count % 50 == 0:
            re_warnings = validate_reynolds_number(velocity, config.tube.diameter, config.fluid)
            for w in re_warnings:
                if w not in already_warned:  # Avoid spam
                    logger.warning(str(w))
                    already_warned.add(w)
```

---

### Task 4.3: Add Cavitation Detection to Ideal Model
**Files**: `simulations/ideal.py`

After fixing pressure calculation, add cavitation checks:

```python
from .validators import check_cavitation_risk

def create_plots(...):
    result = simulate(config)

    # Calculate pressure at crest
    # ... (fixed pressure calculation from Phase 1) ...

    # Check for cavitation
    min_pressure = pressure.min()
    cavitation_warnings = check_cavitation_risk(
        min_pressure,
        config.fluid.vapor_pressure,
        location="crest"
    )

    # Add to plot annotation if critical
    if any(w.severity == 'CRITICAL' for w in cavitation_warnings):
        pressure_annotation += "\n⚠️ CAVITATION RISK!"
```

---

## **PHASE 5: Infrastructure Improvements** (Priority: LOW)
**Estimated Time**: 3-4 hours

### Task 5.1: Pin Dependency Versions
**Files**: `requirements.txt`, `pyproject.toml` (new)

#### Step 5.1.1: Update requirements.txt
```txt
# Core dependencies
numpy>=1.24.0,<2.0.0
matplotlib>=3.7.0,<4.0.0

# Optional: Development dependencies
pytest>=7.4.0,<8.0.0
pytest-cov>=4.1.0,<5.0.0
mypy>=1.5.0,<2.0.0
black>=23.7.0,<24.0.0
ruff>=0.0.285,<1.0.0
```

#### Step 5.1.2: Create pyproject.toml
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "siphon-simulations"
version = "1.0.0"
description = "Analytical and numerical siphon drainage models for IYPT"
authors = [{name = "IYPT Team"}]
readme = "README.md"
requires-python = ">=3.11"
dependencies = [
    "numpy>=1.24.0,<2.0.0",
    "matplotlib>=3.7.0,<4.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "mypy>=1.5.0",
    "black>=23.7.0",
    "ruff>=0.0.285",
]

[tool.black]
line-length = 120
target-version = ['py311']

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = false
disallow_incomplete_defs = false
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true

[[tool.mypy.overrides]]
module = "matplotlib.*"
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["test_simulations.py"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=simulations --cov-report=html --cov-report=term"
```

---

### Task 5.2: Add GitHub Actions CI/CD
**Files**: `.github/workflows/test.yml` (new), `.github/workflows/lint.yml` (new)

#### test.yml
```yaml
name: Run Tests

on:
  push:
    branches: [ main, claude/* ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .[dev]

    - name: Run tests with coverage
      run: |
        pytest --cov=simulations --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  test-imports:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Test imports without dependencies
      run: |
        python -c "import sys; sys.path.insert(0, '.'); from simulations import common"
```

#### lint.yml
```yaml
name: Lint Code

on:
  push:
    branches: [ main, claude/* ]
  pull_request:
    branches: [ main ]

jobs:
  lint:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: "3.11"

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install black ruff mypy
        pip install -e .

    - name: Run Black
      run: black --check simulations/ test_simulations.py

    - name: Run Ruff
      run: ruff check simulations/ test_simulations.py

    - name: Run MyPy
      run: mypy simulations/
```

---

### Task 5.3: Add Type Checking Configuration
**Already covered in pyproject.toml above**

Additional: Create `py.typed` marker file for PEP 561:
```bash
touch simulations/py.typed
```

---

### Task 5.4: Fix Crest Detection Logic
**Files**: `simulations/multi_segment_physics.py`

```python
# OLD (line 150)
if heights[idx] >= heights[idx - 1] and heights[idx] >= heights[idx + 1]:
    crests.append(idx)

# NEW - Use strict inequality to avoid flat regions
if heights[idx] > heights[idx - 1] and heights[idx] > heights[idx + 1]:
    crests.append(idx)
elif heights[idx] > heights[idx - 1] and np.isclose(heights[idx], heights[idx + 1], atol=HEIGHT_COMPARISON_TOLERANCE):
    # Peak extends to next node - take first occurrence
    crests.append(idx)
```

**Rationale**: Flat crests should only be counted once, and strict peaks should be clearly identified.

---

## **PHASE 6: Documentation and Final Polish** (Priority: LOW)
**Estimated Time**: 2-3 hours

### Task 6.1: Create Examples Directory
**Files**: `examples/` (new directory)

#### examples/basic_comparison.py
```python
"""Example: Compare all three simulation models."""

from pathlib import Path
from simulations.common import SimulationConfig, TubeGeometry, ReservoirSetup
from simulations.comparison import run_all

def main():
    # Configure a realistic siphon setup
    config = SimulationConfig(
        tube=TubeGeometry(
            length=1.5,           # 1.5m tube
            diameter=0.015,       # 15mm diameter
            friction_factor=0.02, # Smooth pipe
            roughness=1.5e-4,     # ~0.15mm roughness
            minor_loss_coefficients=(0.5, 1.0),  # Entry and exit
        ),
        reservoir=ReservoirSetup(
            surface_area=0.25,    # 50cm x 50cm reservoir
            initial_height=0.6,   # 60cm water depth
            outlet_height=0.0,    # Drain to zero
        ),
        label="Example comparison"
    )

    # Run all three models
    results = run_all(config, output_dir="plots/example_comparison")

    print("\n=== Simulation Results ===")
    for name, result in results.items():
        print(f"{name:15s}: drain time = {result.drain_time:.2f} s")

if __name__ == "__main__":
    main()
```

#### examples/multi_crest_analysis.py
```python
"""Example: Analyze a multi-crest siphon configuration."""

from simulations.multi_segment import (
    MultiSegmentConfig,
    compute_initial_state,
    describe_state,
    save_metadata,
)
from simulations.multi_segment_physics import SegmentedTube, TubeSegment
from simulations.common import ReservoirSetup

def main():
    # Define a siphon with two crests
    tube = SegmentedTube(
        entry_height=0.05,
        outlet_height=0.0,
        segments=[
            # Rise to first crest
            TubeSegment(length=0.3, diameter=0.01, angle_deg=30.0,
                       minor_loss_coefficients=[0.5], roughness=1.5e-4),
            # Descend
            TubeSegment(length=0.4, diameter=0.01, angle_deg=-45.0,
                       minor_loss_coefficients=[0.2], roughness=1.5e-4),
            # Rise to second crest
            TubeSegment(length=0.2, diameter=0.01, angle_deg=40.0,
                       minor_loss_coefficients=[0.3], roughness=1.5e-4),
            # Final descent
            TubeSegment(length=0.3, diameter=0.01, angle_deg=-20.0,
                       minor_loss_coefficients=[1.0], roughness=1.5e-4),
        ],
        entry_minor_losses=(0.5,),
        exit_minor_losses=(1.0,),
    )

    reservoir = ReservoirSetup(
        surface_area=0.2,
        initial_height=0.5,
        outlet_height=0.0,
    )

    config = MultiSegmentConfig(
        reservoir=reservoir,
        tube=tube,
        label="Two-crest example"
    )

    # Compute primed state
    state = compute_initial_state(config)

    # Display results
    print(describe_state(state))

    # Save metadata
    save_metadata(state, "plots/multi_crest/metadata.json")
    print("\nMetadata saved to plots/multi_crest/metadata.json")

if __name__ == "__main__":
    main()
```

---

### Task 6.2: Update README with New Features
**Files**: `README.md`

Add sections:
1. **Logging Configuration** - how to enable debug logging
2. **Validation Warnings** - what warnings mean and how to address them
3. **Examples** - link to examples/ directory
4. **CI Status Badges** - add GitHub Actions badges
5. **Type Checking** - mention mypy support
6. **Development Setup** - how to install dev dependencies

---

### Task 6.3: Create CHANGELOG.md
**Files**: `CHANGELOG.md` (new)

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-10-21

### Added
- Comprehensive logging framework with DEBUG, INFO, WARNING levels
- Physical validation warnings (Reynolds number, roughness, cavitation)
- Module-level constants for all magic numbers
- Comprehensive docstrings for all functions
- Type checking configuration with mypy
- GitHub Actions CI/CD for testing and linting
- Examples directory with sample scripts
- Development dependencies (pytest, black, ruff, mypy)

### Fixed
- Pressure calculation in ideal model now correctly shows crest pressure
- Crest detection logic handles flat peaks correctly
- Missing test coverage for multi-segment modules (added 30+ tests)

### Changed
- Consolidated duplicated plotting code into common.plot_series
- Consolidated validation functions into common module
- Consolidated Darcy friction factor calculation
- Updated deprecated datetime.utcnow() to datetime.now(timezone.utc)
- Pinned dependency versions for reproducibility

### Removed
- Duplicate _plot_series functions from individual modules
- Duplicate _validate_* functions from individual modules
```

---

### Task 6.4: Add Progress Indicators
**Files**: `simulations/variable_losses.py`, `requirements.txt`

#### Optional dependency for progress bars:
```txt
# requirements.txt - add optional
tqdm>=4.65.0,<5.0.0  # Optional: for progress bars
```

#### In variable_losses.py:
```python
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

def simulate(
    config: SimulationConfig,
    time_step: float = 0.05,
    max_time: float = 3600.0,
    show_progress: bool = False,
) -> Tuple[SimulationResult, np.ndarray]:
    """...

    Parameters
    ----------
    ...
    show_progress : bool, default=False
        If True and tqdm is installed, show progress bar
    """

    # ... setup ...

    # Estimate total iterations for progress bar
    estimated_iterations = int(max_time / time_step)

    if show_progress and TQDM_AVAILABLE:
        pbar = tqdm(total=estimated_iterations, desc="Simulating")
    else:
        pbar = None

    while height > config.reservoir.outlet_height and time < max_time:
        # ... simulation step ...

        if pbar:
            pbar.update(1)

    if pbar:
        pbar.close()

    return result, loss_array
```

---

### Task 6.5: Configure Matplotlib for Headless Environments
**Files**: `simulations/__init__.py`

```python
"""Simulation package exposing siphon modelling utilities."""

import os
import sys

# Configure matplotlib backend before importing pyplot
if 'DISPLAY' not in os.environ or os.environ.get('MPLBACKEND') == 'Agg':
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend for headless environments

from .common import (
    FluidProperties,
    ReservoirSetup,
    SimulationConfig,
    SimulationResult,
    TubeGeometry,
    # New exports
    plot_series,
    validate_area_ratio,
    validate_head,
    darcy_friction_factor,
)
# ... rest of imports ...
```

---

## **TESTING STRATEGY**

After each phase, run:

```bash
# 1. Run test suite
python -m pytest test_simulations.py -v

# 2. Check coverage
python -m pytest --cov=simulations --cov-report=html

# 3. Type checking
mypy simulations/

# 4. Linting
black simulations/ test_simulations.py
ruff check simulations/

# 5. Run examples
python examples/basic_comparison.py
python examples/multi_crest_analysis.py

# 6. Manual verification
python -m simulations.ideal
python -m simulations.constant_losses
python -m simulations.variable_losses
python -m simulations.multi_segment
```

---

## **IMPLEMENTATION ORDER & DEPENDENCIES**

### Phase Dependencies:
- **Phase 1** must complete first (critical bugs)
- **Phase 2** can start after Phase 1 Task 1.1 (pressure fix)
- **Phase 3** requires Phase 2 (uses consolidated functions)
- **Phase 4** can run in parallel with Phase 3
- **Phase 5** can start anytime (infrastructure)
- **Phase 6** should be last (documentation of all changes)

### Suggested Order:
1. **Day 1**: Phase 1 (critical bugs) - 4-5 hours
2. **Day 2**: Phase 2 (refactoring) - 3-4 hours
3. **Day 3**: Phase 3 (constants & quality) + Phase 4.1-4.2 (logging) - 4-5 hours
4. **Day 4**: Phase 4.3 (cavitation) + Phase 5 (infrastructure) - 4-5 hours
5. **Day 5**: Phase 6 (documentation & polish) - 2-3 hours

**Total Estimated Time**: 17-22 hours across 5 days

---

## **SUCCESS CRITERIA**

### Phase 1:
- ✅ All tests pass (including new multi-segment tests)
- ✅ Test coverage >90% for all modules
- ✅ Pressure plots show physically correct values

### Phase 2:
- ✅ Zero duplicated plotting code
- ✅ All validation logic in common module
- ✅ All tests still pass

### Phase 3:
- ✅ Zero hardcoded magic numbers
- ✅ All functions have comprehensive docstrings
- ✅ mypy reports no errors

### Phase 4:
- ✅ Logging works at DEBUG, INFO, WARNING levels
- ✅ Physical warnings trigger appropriately
- ✅ Cavitation detection works correctly

### Phase 5:
- ✅ GitHub Actions runs successfully
- ✅ Dependencies pinned and installable
- ✅ Type checking passes

### Phase 6:
- ✅ Examples run without errors
- ✅ README accurately reflects all features
- ✅ CHANGELOG documents all changes

---

## **RISK MITIGATION**

1. **Breaking Changes**: Commit after each phase, test thoroughly
2. **Import Errors**: Update `__init__.py` exports as functions move
3. **Test Failures**: Fix tests before proceeding to next phase
4. **Merge Conflicts**: Work on feature branch, rebase frequently

---

## **SUMMARY OF FILES TO CREATE**

### New Files:
1. `simulations/constants.py` - All magic number constants
2. `simulations/logging_config.py` - Logging utilities
3. `simulations/validators.py` - Physical validation functions
4. `pyproject.toml` - Project configuration
5. `.github/workflows/test.yml` - CI testing
6. `.github/workflows/lint.yml` - CI linting
7. `simulations/py.typed` - Type checking marker
8. `examples/basic_comparison.py` - Example script
9. `examples/multi_crest_analysis.py` - Example script
10. `CHANGELOG.md` - Version history
11. `IMPLEMENTATION_PLAN.md` - This document

### Modified Files:
1. `simulations/common.py` - Add plot_series, validators, darcy_friction_factor, entry_height
2. `simulations/ideal.py` - Fix pressure calc, use common functions, add logging
3. `simulations/constant_losses.py` - Use common functions, add logging
4. `simulations/variable_losses.py` - Use common functions, add logging, progress bars
5. `simulations/multi_segment.py` - Use common validators, add logging
6. `simulations/multi_segment_physics.py` - Fix crest detection, use common darcy
7. `simulations/comparison.py` - Use constants
8. `simulations/__init__.py` - Update exports, configure matplotlib
9. `test_simulations.py` - Add 30+ tests for multi-segment modules
10. `requirements.txt` - Pin versions, add dev dependencies
11. `README.md` - Document new features

---

**End of Implementation Plan**
