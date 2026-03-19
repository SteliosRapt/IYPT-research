from __future__ import annotations

import json
from pathlib import Path
from threading import Thread
import time
from unittest.mock import patch
from urllib.request import Request, urlopen

from services.api.server import ApiState, create_server


def _request(base_url: str, method: str, path: str, payload: dict | None = None) -> tuple[int, object]:
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"{base_url}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data is not None else {},
    )
    with urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
        if response.headers.get_content_type() == "application/json":
            return response.status, json.loads(body)
        return response.status, body


def _start_server(tmp_path: Path) -> tuple[object, Thread, str]:
    server = create_server("127.0.0.1", 0, state=ApiState(tmp_path / "api-state"))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    return server, thread, f"http://{host}:{port}"


def _write_fake_solver_outputs(case_dir: Path) -> None:
    post_processing = case_dir / "postProcessing"
    (post_processing / "containerWaterVolume" / "0").mkdir(parents=True, exist_ok=True)
    (post_processing / "tubeOutletFlow" / "0").mkdir(parents=True, exist_ok=True)
    (post_processing / "topInflowFlow" / "0").mkdir(parents=True, exist_ok=True)
    (case_dir / "VTK").mkdir(exist_ok=True)
    (case_dir / "VTK" / "mesh.vtk").write_text("# vtk\n", encoding="utf-8")
    (post_processing / "containerWaterVolume" / "0" / "volFieldValue.dat").write_text(
        "# Time volume\n0.0 0.0252\n0.1 0.0273\n0.2 0.0294\n",
        encoding="utf-8",
    )
    (post_processing / "tubeOutletFlow" / "0" / "surfaceFieldValue.dat").write_text(
        "# Time phi\n0.0 -0.00011\n0.1 -0.00012\n0.2 -0.00013\n",
        encoding="utf-8",
    )
    (post_processing / "topInflowFlow" / "0" / "surfaceFieldValue.dat").write_text(
        "# Time phi\n0.0 -0.00014\n0.1 -0.00014\n0.2 -0.00014\n",
        encoding="utf-8",
    )


def test_api_creates_case_and_serves_mock_run_assets(tmp_path: Path) -> None:
    server, thread, base_url = _start_server(tmp_path)

    try:
        health_status, health_payload = _request(base_url, "GET", "/api/health")
        assert health_status == 200
        assert health_payload == {"status": "ok"}

        case_status, case_payload = _request(
            base_url,
            "POST",
            "/api/cases",
            {
                "parameters": {"h0": 0.31},
                "meshingPreset": "fine",
                "transport": {"sigma": 0.081},
            },
        )
        assert case_status == 201
        assert isinstance(case_payload, dict)
        case_id = case_payload["caseId"]
        assert case_payload["caseFile"]["parameters"]["h0"] == 0.31
        assert case_payload["caseFile"]["meshing"]["preset"] == "fine"
        assert case_payload["caseFile"]["transport"]["sigma"] == 0.081

        lookup_status, lookup_payload = _request(base_url, "GET", f"/api/cases/{case_id}")
        assert lookup_status == 200
        assert lookup_payload["caseId"] == case_id

        run_status_code, run_payload = _request(
            base_url,
            "POST",
            f"/api/cases/{case_id}/run",
            {"mode": "mock"},
        )
        assert run_status_code == 202
        assert isinstance(run_payload, dict)
        run_id = run_payload["runId"]

        final_status: dict | None = None
        for _ in range(50):
            time.sleep(0.1)
            _, current_status = _request(base_url, "GET", f"/api/runs/{run_id}/status")
            assert isinstance(current_status, dict)
            if current_status["state"] in {"done", "failed"}:
                final_status = current_status
                break

        assert final_status is not None
        assert final_status["state"] == "done"

        manifest_status, manifest_payload = _request(base_url, "GET", f"/api/runs/{run_id}/manifest.json")
        assert manifest_status == 200
        assert isinstance(manifest_payload, dict)
        assert manifest_payload["status"] == "mock"

        height_status, height_payload = _request(base_url, "GET", f"/api/runs/{run_id}/series/height.json")
        assert height_status == 200
        assert isinstance(height_payload, list)
        assert height_payload[0]["time"] == 0.0
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_api_runs_real_solver_post_processing_when_requested(tmp_path: Path) -> None:
    with patch("services.api.server.command_exists", return_value=True), patch(
        "services.api.server.run_case",
        side_effect=lambda case_dir: _write_fake_solver_outputs(case_dir),
    ):
        server, thread, base_url = _start_server(tmp_path)

        try:
            _, case_payload = _request(base_url, "POST", "/api/cases", {})
            assert isinstance(case_payload, dict)
            case_id = case_payload["caseId"]

            run_status_code, run_payload = _request(
                base_url,
                "POST",
                f"/api/cases/{case_id}/run",
                {"mode": "real"},
            )
            assert run_status_code == 202
            assert isinstance(run_payload, dict)
            assert run_payload["mode"] == "real"
            run_id = run_payload["runId"]

            final_status: dict | None = None
            for _ in range(50):
                time.sleep(0.1)
                _, current_status = _request(base_url, "GET", f"/api/runs/{run_id}/status")
                assert isinstance(current_status, dict)
                if current_status["state"] in {"done", "failed"}:
                    final_status = current_status
                    break

            assert final_status is not None
            assert final_status["state"] == "done"
            assert final_status["manifestUrl"].endswith("/viewer/manifest.json")

            manifest_status, manifest_payload = _request(base_url, "GET", final_status["manifestUrl"])
            assert manifest_status == 200
            assert isinstance(manifest_payload, dict)
            assert manifest_payload["status"] == "done"
            assert manifest_payload["paraview"]["foamFile"] == "../openfoam-case/.foam"
            assert manifest_payload["paraview"]["vtkDir"] == "../openfoam-case/VTK"

            height_status, height_payload = _request(base_url, "GET", f"/api/runs/{run_id}/series/height.json")
            assert height_status == 200
            assert isinstance(height_payload, list)
            assert height_payload[0]["value"] == 0.24

            foam_status, foam_payload = _request(base_url, "GET", f"/api/runs/{run_id}/openfoam-case/.foam")
            assert foam_status == 200
            assert isinstance(foam_payload, str)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
