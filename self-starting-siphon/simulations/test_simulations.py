"""Unit tests for siphon simulation modules."""

import unittest
import sys
from pathlib import Path

# Check if numpy and matplotlib are available
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    print("Warning: numpy not available, skipping tests that require it", file=sys.stderr)

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available, skipping plotting tests", file=sys.stderr)


class TestImports(unittest.TestCase):
    """Test that modules can be imported."""

    def test_common_import(self):
        """Test that common module can be imported."""
        if not NUMPY_AVAILABLE:
            self.skipTest("numpy not available")
        from simulations import common
        self.assertIsNotNone(common)

    def test_ideal_import(self):
        """Test that ideal module can be imported."""
        if not NUMPY_AVAILABLE:
            self.skipTest("numpy not available")
        from simulations import ideal
        self.assertIsNotNone(ideal)

    def test_constant_losses_import(self):
        """Test that constant_losses module can be imported."""
        if not NUMPY_AVAILABLE:
            self.skipTest("numpy not available")
        from simulations import constant_losses
        self.assertIsNotNone(constant_losses)

    def test_variable_losses_import(self):
        """Test that variable_losses module can be imported."""
        if not NUMPY_AVAILABLE:
            self.skipTest("numpy not available")
        from simulations import variable_losses
        self.assertIsNotNone(variable_losses)


@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestFluidProperties(unittest.TestCase):
    """Test FluidProperties dataclass."""

    def setUp(self):
        from simulations.common import FluidProperties
        self.FluidProperties = FluidProperties

    def test_default_values(self):
        """Test default fluid property values."""
        fluid = self.FluidProperties()
        self.assertEqual(fluid.density, 998.0)
        self.assertEqual(fluid.viscosity, 1.0e-3)
        self.assertEqual(fluid.gravity, 9.81)
        self.assertEqual(fluid.atmospheric_pressure, 101300.0)
        self.assertEqual(fluid.vapor_pressure, 2300.0)

    def test_custom_values(self):
        """Test custom fluid property values."""
        fluid = self.FluidProperties(
            density=1000.0,
            viscosity=2.0e-3,
            gravity=9.80,
        )
        self.assertEqual(fluid.density, 1000.0)
        self.assertEqual(fluid.viscosity, 2.0e-3)
        self.assertEqual(fluid.gravity, 9.80)

    def test_immutability(self):
        """Test that FluidProperties is immutable."""
        fluid = self.FluidProperties()
        with self.assertRaises(AttributeError):
            fluid.density = 1000.0


@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestTubeGeometry(unittest.TestCase):
    """Test TubeGeometry dataclass."""

    def setUp(self):
        from simulations.common import TubeGeometry
        self.TubeGeometry = TubeGeometry

    def test_basic_construction(self):
        """Test basic tube geometry construction."""
        tube = self.TubeGeometry(length=1.0, diameter=0.02)
        self.assertEqual(tube.length, 1.0)
        self.assertEqual(tube.diameter, 0.02)

    def test_area_calculation(self):
        """Test tube cross-sectional area calculation."""
        tube = self.TubeGeometry(length=1.0, diameter=0.02)
        expected_area = np.pi * (0.01)**2
        self.assertAlmostEqual(tube.area, expected_area, places=10)

    def test_relative_roughness(self):
        """Test relative roughness calculation."""
        tube = self.TubeGeometry(length=1.0, diameter=0.02, roughness=1.5e-4)
        expected = 1.5e-4 / 0.02
        self.assertAlmostEqual(tube.relative_roughness, expected, places=10)

    def test_relative_roughness_none(self):
        """Test relative roughness when roughness is None."""
        tube = self.TubeGeometry(length=1.0, diameter=0.02)
        self.assertEqual(tube.relative_roughness, 0.0)

    def test_minor_losses(self):
        """Test minor loss coefficient calculation."""
        tube = self.TubeGeometry(
            length=1.0,
            diameter=0.02,
            minor_loss_coefficients=(0.5, 0.3, 0.2),
        )
        self.assertAlmostEqual(tube.minor_losses, 1.0, places=10)

    def test_minor_losses_empty(self):
        """Test minor loss coefficient when none specified."""
        tube = self.TubeGeometry(length=1.0, diameter=0.02)
        self.assertEqual(tube.minor_losses, 0.0)

    def test_constant_loss_coefficient(self):
        """Test constant loss coefficient calculation."""
        tube = self.TubeGeometry(
            length=1.2,
            diameter=0.02,
            friction_factor=0.02,
            minor_loss_coefficients=(0.5,),
        )
        expected = 0.02 * (1.2 / 0.02) + 0.5
        self.assertAlmostEqual(tube.constant_loss_coefficient(), expected, places=10)

    def test_constant_loss_coefficient_override(self):
        """Test constant loss coefficient with override friction factor."""
        tube = self.TubeGeometry(
            length=1.2,
            diameter=0.02,
            friction_factor=0.02,
            minor_loss_coefficients=(0.5,),
        )
        expected = 0.03 * (1.2 / 0.02) + 0.5
        result = tube.constant_loss_coefficient(friction_factor=0.03)
        self.assertAlmostEqual(result, expected, places=10)

    def test_constant_loss_coefficient_no_friction(self):
        """Test constant loss coefficient raises error when no friction factor."""
        tube = self.TubeGeometry(length=1.2, diameter=0.02)
        with self.assertRaises(ValueError):
            tube.constant_loss_coefficient()


@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestReservoirSetup(unittest.TestCase):
    """Test ReservoirSetup dataclass."""

    def setUp(self):
        from simulations.common import ReservoirSetup
        self.ReservoirSetup = ReservoirSetup

    def test_basic_construction(self):
        """Test basic reservoir setup construction."""
        reservoir = self.ReservoirSetup(
            surface_area=0.5,
            initial_height=0.8,
            outlet_height=0.2,
        )
        self.assertEqual(reservoir.surface_area, 0.5)
        self.assertEqual(reservoir.initial_height, 0.8)
        self.assertEqual(reservoir.outlet_height, 0.2)

    def test_initial_head(self):
        """Test initial head calculation."""
        reservoir = self.ReservoirSetup(
            surface_area=0.5,
            initial_height=0.8,
            outlet_height=0.2,
        )
        self.assertAlmostEqual(reservoir.initial_head, 0.6, places=10)

    def test_validate_positive_area(self):
        """Test validation requires positive surface area."""
        reservoir = self.ReservoirSetup(
            surface_area=-0.5,
            initial_height=0.8,
            outlet_height=0.2,
        )
        with self.assertRaises(ValueError) as ctx:
            reservoir.validate()
        self.assertIn("positive", str(ctx.exception).lower())

    def test_validate_zero_area(self):
        """Test validation rejects zero surface area."""
        reservoir = self.ReservoirSetup(
            surface_area=0.0,
            initial_height=0.8,
            outlet_height=0.2,
        )
        with self.assertRaises(ValueError):
            reservoir.validate()

    def test_validate_height_order(self):
        """Test validation requires initial height above outlet."""
        reservoir = self.ReservoirSetup(
            surface_area=0.5,
            initial_height=0.2,
            outlet_height=0.8,
        )
        with self.assertRaises(ValueError) as ctx:
            reservoir.validate()
        self.assertIn("above", str(ctx.exception).lower())

    def test_validate_equal_heights(self):
        """Test validation rejects equal initial and outlet heights."""
        reservoir = self.ReservoirSetup(
            surface_area=0.5,
            initial_height=0.5,
            outlet_height=0.5,
        )
        with self.assertRaises(ValueError):
            reservoir.validate()


@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestSimulationConfig(unittest.TestCase):
    """Test SimulationConfig dataclass."""

    def setUp(self):
        from simulations.common import SimulationConfig, TubeGeometry, ReservoirSetup
        self.SimulationConfig = SimulationConfig
        self.TubeGeometry = TubeGeometry
        self.ReservoirSetup = ReservoirSetup

    def test_basic_construction(self):
        """Test basic simulation config construction."""
        tube = self.TubeGeometry(length=1.2, diameter=0.02)
        reservoir = self.ReservoirSetup(
            surface_area=0.5,
            initial_height=0.8,
            outlet_height=0.2,
        )
        config = self.SimulationConfig(tube=tube, reservoir=reservoir)
        self.assertEqual(config.tube, tube)
        self.assertEqual(config.reservoir, reservoir)

    def test_area_ratio(self):
        """Test area ratio calculation."""
        tube = self.TubeGeometry(length=1.2, diameter=0.02)
        reservoir = self.ReservoirSetup(
            surface_area=0.5,
            initial_height=0.8,
            outlet_height=0.2,
        )
        config = self.SimulationConfig(tube=tube, reservoir=reservoir)
        expected = tube.area / reservoir.surface_area
        self.assertAlmostEqual(config.area_ratio, expected, places=10)

    def test_validation_on_construction(self):
        """Test validation runs on construction."""
        tube = self.TubeGeometry(length=1.2, diameter=0.02)
        reservoir = self.ReservoirSetup(
            surface_area=0.5,
            initial_height=0.2,
            outlet_height=0.8,
        )
        with self.assertRaises(ValueError):
            self.SimulationConfig(tube=tube, reservoir=reservoir)

    def test_validation_negative_diameter(self):
        """Test validation rejects negative diameter."""
        tube = self.TubeGeometry(length=1.2, diameter=-0.02)
        reservoir = self.ReservoirSetup(
            surface_area=0.5,
            initial_height=0.8,
            outlet_height=0.2,
        )
        with self.assertRaises(ValueError) as ctx:
            self.SimulationConfig(tube=tube, reservoir=reservoir)
        self.assertIn("diameter", str(ctx.exception).lower())

    def test_validation_negative_length(self):
        """Test validation rejects negative tube length."""
        tube = self.TubeGeometry(length=-1.2, diameter=0.02)
        reservoir = self.ReservoirSetup(
            surface_area=0.5,
            initial_height=0.8,
            outlet_height=0.2,
        )
        with self.assertRaises(ValueError) as ctx:
            self.SimulationConfig(tube=tube, reservoir=reservoir)
        self.assertIn("length", str(ctx.exception).lower())


@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestCommonHelpers(unittest.TestCase):
    """Test helper functions in common module."""

    def setUp(self):
        from simulations import common
        self.common = common

    def test_time_grid_normal(self):
        """Test time grid generation."""
        grid = self.common.time_grid(10.0, 100)
        self.assertEqual(len(grid), 100)
        self.assertAlmostEqual(grid[0], 0.0, places=10)
        self.assertAlmostEqual(grid[-1], 10.0, places=10)

    def test_time_grid_zero_duration(self):
        """Test time grid with zero duration."""
        grid = self.common.time_grid(0.0, 100)
        self.assertEqual(len(grid), 1)
        self.assertEqual(grid[0], 0.0)

    def test_time_grid_negative_duration(self):
        """Test time grid with negative duration."""
        grid = self.common.time_grid(-5.0, 100)
        self.assertEqual(len(grid), 1)
        self.assertEqual(grid[0], 0.0)

    def test_mass_flow_rate(self):
        """Test mass flow rate calculation."""
        flow_rate = np.array([0.001, 0.002, 0.003])
        fluid = self.common.FluidProperties(density=1000.0)
        mass_flow = self.common.mass_flow_rate(flow_rate, fluid)
        expected = np.array([1.0, 2.0, 3.0])
        np.testing.assert_array_almost_equal(mass_flow, expected)

    def test_ensure_output_dir(self):
        """Test output directory creation."""
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()
        try:
            test_path = Path(temp_dir) / "test_output" / "nested"
            result = self.common.ensure_output_dir(test_path)
            self.assertTrue(result.exists())
            self.assertTrue(result.is_dir())
        finally:
            shutil.rmtree(temp_dir)


@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestIdealSimulation(unittest.TestCase):
    """Test ideal siphon simulation."""

    def setUp(self):
        from simulations import ideal
        from simulations.common import SimulationConfig, TubeGeometry, ReservoirSetup
        self.ideal = ideal
        self.SimulationConfig = SimulationConfig
        self.TubeGeometry = TubeGeometry
        self.ReservoirSetup = ReservoirSetup

    def get_example_config(self):
        """Create example configuration."""
        return self.SimulationConfig(
            tube=self.TubeGeometry(
                length=1.2,
                diameter=0.02,
                minor_loss_coefficients=(0.5, 0.5),
            ),
            reservoir=self.ReservoirSetup(
                surface_area=0.5,
                initial_height=0.8,
                outlet_height=0.2,
            ),
            label="Test ideal",
        )

    def test_simulate_basic(self):
        """Test basic ideal simulation."""
        config = self.get_example_config()
        result = self.ideal.simulate(config, num_points=100)

        self.assertEqual(len(result.time), 100)
        self.assertEqual(len(result.height), 100)
        self.assertEqual(len(result.velocity), 100)
        self.assertEqual(len(result.flow_rate), 100)

    def test_simulate_initial_conditions(self):
        """Test initial conditions of ideal simulation."""
        config = self.get_example_config()
        result = self.ideal.simulate(config)

        # First height should be initial height
        self.assertAlmostEqual(result.height[0], config.reservoir.initial_height, places=6)

        # Final height should be outlet height
        self.assertAlmostEqual(result.height[-1], config.reservoir.outlet_height, places=6)

        # Final velocity should be zero
        self.assertAlmostEqual(result.velocity[-1], 0.0, places=6)

    def test_simulate_monotonic_decrease(self):
        """Test that height and velocity decrease monotonically."""
        config = self.get_example_config()
        result = self.ideal.simulate(config)

        # Height should decrease monotonically
        height_diff = np.diff(result.height)
        self.assertTrue(np.all(height_diff <= 1e-10))

        # Velocity should decrease monotonically
        velocity_diff = np.diff(result.velocity)
        self.assertTrue(np.all(velocity_diff <= 1e-10))

    def test_simulate_invalid_area_ratio_zero(self):
        """Test that area ratio of zero raises error."""
        config = self.SimulationConfig(
            tube=self.TubeGeometry(length=1.2, diameter=0.0001),
            reservoir=self.ReservoirSetup(
                surface_area=10000.0,
                initial_height=0.8,
                outlet_height=0.2,
            ),
        )
        # Area ratio should be essentially zero
        self.assertLess(config.area_ratio, 1e-6)
        with self.assertRaises(ValueError):
            self.ideal.simulate(config)

    def test_simulate_invalid_area_ratio_one(self):
        """Test that area ratio of one raises error."""
        config = self.SimulationConfig(
            tube=self.TubeGeometry(length=1.2, diameter=1.0),
            reservoir=self.ReservoirSetup(
                surface_area=np.pi * 0.25,  # Same area as tube
                initial_height=0.8,
                outlet_height=0.2,
            ),
        )
        # Area ratio should be 1.0
        self.assertAlmostEqual(config.area_ratio, 1.0, places=6)
        with self.assertRaises(ValueError):
            self.ideal.simulate(config)

    def test_metadata_generation(self):
        """Test metadata generation."""
        config = self.get_example_config()
        result = self.ideal.simulate(config)
        metadata = result.to_metadata()

        self.assertIn("timestamp", metadata)
        self.assertIn("label", metadata)
        self.assertIn("drain_time_s", metadata)
        self.assertIn("config", metadata)
        self.assertIn("summary", metadata)
        self.assertEqual(metadata["summary"]["loss_coefficient"], 0.0)


@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestConstantLossesSimulation(unittest.TestCase):
    """Test constant losses siphon simulation."""

    def setUp(self):
        from simulations import constant_losses
        from simulations.common import SimulationConfig, TubeGeometry, ReservoirSetup
        self.constant_losses = constant_losses
        self.SimulationConfig = SimulationConfig
        self.TubeGeometry = TubeGeometry
        self.ReservoirSetup = ReservoirSetup

    def get_example_config(self):
        """Create example configuration."""
        return self.SimulationConfig(
            tube=self.TubeGeometry(
                length=1.2,
                diameter=0.02,
                friction_factor=0.02,
                minor_loss_coefficients=(0.5,),
            ),
            reservoir=self.ReservoirSetup(
                surface_area=0.5,
                initial_height=0.8,
                outlet_height=0.2,
            ),
            label="Test constant losses",
        )

    def test_simulate_basic(self):
        """Test basic constant losses simulation."""
        config = self.get_example_config()
        result = self.constant_losses.simulate(config, num_points=100)

        self.assertEqual(len(result.time), 100)
        self.assertEqual(len(result.height), 100)
        self.assertEqual(len(result.velocity), 100)

    def test_simulate_initial_conditions(self):
        """Test initial conditions."""
        config = self.get_example_config()
        result = self.constant_losses.simulate(config)

        self.assertAlmostEqual(result.height[0], config.reservoir.initial_height, places=6)
        self.assertAlmostEqual(result.height[-1], config.reservoir.outlet_height, places=6)
        self.assertAlmostEqual(result.velocity[-1], 0.0, places=6)

    def test_simulate_custom_loss_coefficient(self):
        """Test simulation with custom loss coefficient."""
        config = self.get_example_config()
        result = self.constant_losses.simulate(config, loss_coefficient=2.0)

        self.assertEqual(result.summary["loss_coefficient"], 2.0)

    def test_simulate_negative_loss_coefficient(self):
        """Test that negative loss coefficient raises error."""
        config = self.get_example_config()
        with self.assertRaises(ValueError):
            self.constant_losses.simulate(config, loss_coefficient=-1.0)

    def test_slower_than_ideal(self):
        """Test that losses result in slower drainage than ideal."""
        from simulations import ideal

        config = self.get_example_config()
        ideal_result = ideal.simulate(config)
        constant_result = self.constant_losses.simulate(config)

        # With losses, drain time should be longer
        self.assertGreater(constant_result.drain_time, ideal_result.drain_time)


@unittest.skipUnless(NUMPY_AVAILABLE, "requires numpy")
class TestVariableLossesSimulation(unittest.TestCase):
    """Test variable losses siphon simulation."""

    def setUp(self):
        from simulations import variable_losses
        from simulations.common import SimulationConfig, TubeGeometry, ReservoirSetup
        self.variable_losses = variable_losses
        self.SimulationConfig = SimulationConfig
        self.TubeGeometry = TubeGeometry
        self.ReservoirSetup = ReservoirSetup

    def get_example_config(self):
        """Create example configuration."""
        return self.SimulationConfig(
            tube=self.TubeGeometry(
                length=1.2,
                diameter=0.02,
                roughness=1.5e-4,
                minor_loss_coefficients=(0.5,),
            ),
            reservoir=self.ReservoirSetup(
                surface_area=0.5,
                initial_height=0.8,
                outlet_height=0.2,
            ),
            label="Test variable losses",
        )

    def test_simulate_basic(self):
        """Test basic variable losses simulation."""
        config = self.get_example_config()
        result, loss_array = self.variable_losses.simulate(config, time_step=0.1)

        self.assertGreater(len(result.time), 0)
        self.assertEqual(len(result.time), len(result.height))
        self.assertEqual(len(result.time), len(loss_array))

    def test_simulate_initial_conditions(self):
        """Test initial conditions."""
        config = self.get_example_config()
        result, _ = self.variable_losses.simulate(config)

        self.assertAlmostEqual(result.height[0], config.reservoir.initial_height, places=6)
        self.assertAlmostEqual(result.height[-1], config.reservoir.outlet_height, places=5)

    def test_simulate_final_velocity_zero(self):
        """Test that final velocity is zero."""
        config = self.get_example_config()
        result, _ = self.variable_losses.simulate(config)

        self.assertAlmostEqual(result.velocity[-1], 0.0, places=10)

    def test_darcy_friction_factor_laminar(self):
        """Test Darcy friction factor in laminar regime."""
        reynolds = 1000.0
        relative_roughness = 0.0
        f = self.variable_losses._darcy_friction_factor(reynolds, relative_roughness)
        expected = 64.0 / reynolds
        self.assertAlmostEqual(f, expected, places=6)

    def test_darcy_friction_factor_turbulent(self):
        """Test Darcy friction factor in turbulent regime."""
        reynolds = 10000.0
        relative_roughness = 0.001
        f = self.variable_losses._darcy_friction_factor(reynolds, relative_roughness)
        # Should be positive and reasonable
        self.assertGreater(f, 0.0)
        self.assertLess(f, 1.0)

    def test_darcy_friction_factor_zero_reynolds(self):
        """Test Darcy friction factor with zero Reynolds number."""
        f = self.variable_losses._darcy_friction_factor(0.0, 0.0)
        self.assertEqual(f, 0.0)

    def test_loss_coefficient_evolution(self):
        """Test that loss coefficient varies during simulation."""
        config = self.get_example_config()
        result, loss_array = self.variable_losses.simulate(config)

        # Loss coefficient should vary
        self.assertIn("loss_coefficient_min", result.summary)
        self.assertIn("loss_coefficient_max", result.summary)
        self.assertIn("loss_coefficient_mean", result.summary)

        # Min should be less than or equal to mean
        self.assertLessEqual(
            result.summary["loss_coefficient_min"],
            result.summary["loss_coefficient_mean"]
        )


@unittest.skipUnless(NUMPY_AVAILABLE and MATPLOTLIB_AVAILABLE, "requires numpy and matplotlib")
class TestPlotGeneration(unittest.TestCase):
    """Test plot generation functions."""

    def setUp(self):
        from simulations import ideal, constant_losses, variable_losses
        from simulations.common import SimulationConfig, TubeGeometry, ReservoirSetup
        self.ideal = ideal
        self.constant_losses = constant_losses
        self.variable_losses = variable_losses
        self.SimulationConfig = SimulationConfig
        self.TubeGeometry = TubeGeometry
        self.ReservoirSetup = ReservoirSetup

    def get_example_config(self):
        """Create example configuration."""
        return self.SimulationConfig(
            tube=self.TubeGeometry(
                length=1.2,
                diameter=0.02,
                friction_factor=0.02,
                roughness=1.5e-4,
                minor_loss_coefficients=(0.5,),
            ),
            reservoir=self.ReservoirSetup(
                surface_area=0.5,
                initial_height=0.8,
                outlet_height=0.2,
            ),
        )

    def test_ideal_create_plots(self):
        """Test ideal simulation plot creation."""
        import tempfile
        import shutil

        config = self.get_example_config()
        temp_dir = tempfile.mkdtemp()
        try:
            result = self.ideal.create_plots(config, temp_dir)

            # Check that plots were created
            self.assertTrue((Path(temp_dir) / "velocity_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "height_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "flow_rate_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "metadata.json").exists())

            # Check metadata file is valid JSON
            import json
            with open(Path(temp_dir) / "metadata.json") as f:
                metadata = json.load(f)
            self.assertIn("timestamp", metadata)
        finally:
            shutil.rmtree(temp_dir)

    def test_constant_losses_create_plots(self):
        """Test constant losses simulation plot creation."""
        import tempfile
        import shutil

        config = self.get_example_config()
        temp_dir = tempfile.mkdtemp()
        try:
            result = self.constant_losses.create_plots(config, temp_dir)

            self.assertTrue((Path(temp_dir) / "velocity_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "height_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "flow_rate_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "metadata.json").exists())
        finally:
            shutil.rmtree(temp_dir)

    def test_variable_losses_create_plots(self):
        """Test variable losses simulation plot creation."""
        import tempfile
        import shutil

        config = self.get_example_config()
        temp_dir = tempfile.mkdtemp()
        try:
            result = self.variable_losses.create_plots(config, temp_dir, time_step=0.1)

            self.assertTrue((Path(temp_dir) / "velocity_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "height_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "flow_rate_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "loss_coefficient_vs_time.png").exists())
            self.assertTrue((Path(temp_dir) / "metadata.json").exists())
        finally:
            shutil.rmtree(temp_dir)


def run_tests():
    """Run all tests and return the result."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
