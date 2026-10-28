"""Runtime helpers for generated solver cases."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess

GENERATED_CASE_MARKER = ".fixed-geometry-generated-case"


def load_json(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def command_exists(name: str) -> bool:
    return shutil.which(name) is not None


def is_generated_case_dir(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    children = {child.name for child in path.iterdir()}
    if GENERATED_CASE_MARKER in children:
        return True
    return bool({"case.json", "system", "constant"} <= children or {"Allrun", "system", "constant"} <= children)


def prepare_generated_case_dir(path: Path) -> Path:
    if path.exists():
        if not path.is_dir():
            raise RuntimeError(f"Generated case target '{path}' exists and is not a directory.")
        if any(path.iterdir()):
            if not is_generated_case_dir(path):
                raise RuntimeError(
                    f"Refusing to overwrite non-generated directory '{path}'. "
                    "Choose an empty directory or a prior generated case directory."
                )
            shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)
    (path / GENERATED_CASE_MARKER).write_text("fixed-geometry generated case\n", encoding="utf-8")
    return path


def run_case(case_dir: Path) -> None:
    case_file = load_json(case_dir / "case.json")
    solver = case_file["solver"]["solver"]
    has_openfoam = command_exists(solver)
    has_docker = command_exists("docker")

    if has_openfoam:
        result = subprocess.run(["bash", "Allrun"], cwd=case_dir, check=False)
        if result.returncode != 0:
            raise RuntimeError(f"Allrun exited with code {result.returncode} in {case_dir}")
        return

    if has_docker:
        raise RuntimeError(
            "Docker is present but no container orchestration is wired. "
            "Run the solver manually via Docker."
        )

    raise RuntimeError(
        f"Solver '{solver}' not found and Docker is not available. "
        "Install OpenFOAM or Docker to run this case."
    )
