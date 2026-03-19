from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

from services.geometry.core import create_case_file
from services.orchestrator.case import generate_case
from services.orchestrator.runtime import run_case


def _generated_case_dir(tmp_path):
    return generate_case(create_case_file(), tmp_path / "generated")


def test_run_case_reports_missing_solver_and_docker(tmp_path) -> None:
    case_dir = _generated_case_dir(tmp_path)

    with patch("services.orchestrator.runtime.command_exists", return_value=False):
        try:
            run_case(case_dir)
        except RuntimeError as exc:
            assert "Docker is not available" in str(exc)
        else:
            raise AssertionError("run_case() should fail when neither the solver nor Docker is available.")


def test_run_case_executes_allrun_when_solver_is_available(tmp_path) -> None:
    case_dir = _generated_case_dir(tmp_path)

    with patch(
        "services.orchestrator.runtime.command_exists",
        side_effect=lambda name: name == "interFoam",
    ), patch(
        "services.orchestrator.runtime.subprocess.run",
        return_value=SimpleNamespace(returncode=0),
    ) as run_mock:
        run_case(case_dir)

    run_mock.assert_called_once_with(["bash", "Allrun"], cwd=case_dir, check=False)


def test_run_case_surfaces_allrun_failures(tmp_path) -> None:
    case_dir = _generated_case_dir(tmp_path)

    with patch(
        "services.orchestrator.runtime.command_exists",
        side_effect=lambda name: name == "interFoam",
    ), patch(
        "services.orchestrator.runtime.subprocess.run",
        return_value=SimpleNamespace(returncode=3),
    ):
        try:
            run_case(case_dir)
        except RuntimeError as exc:
            assert "Allrun exited with code 3" in str(exc)
        else:
            raise AssertionError("run_case() should fail when Allrun returns a non-zero code.")
