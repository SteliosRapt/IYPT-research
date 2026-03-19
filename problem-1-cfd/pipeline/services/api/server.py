"""HTTP API for browser-triggered case creation and run execution."""

from __future__ import annotations

from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Lock, Thread
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from services.geometry.core import (
    create_case_file,
    default_event_thresholds,
    default_forcing_config,
    default_meshing_config,
    default_solver_config,
    default_transport_config,
)
from services.orchestrator.case import generate_case
from services.orchestrator.runtime import command_exists, run_case
from services.utils import write_json
from services.viewer_data.mock import create_mock_run
from services.viewer_data.real import create_real_run

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_API_STATE_DIR = ROOT_DIR / "tmp" / "api"
MOCK_RUN_MODE = "mock"
REAL_RUN_MODE = "real"
AUTO_RUN_MODE = "auto"


def _utc_now_iso() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _as_object(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


class ApiState:
    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = (root_dir or DEFAULT_API_STATE_DIR).resolve()
        self.cases_dir = self.root_dir / "cases"
        self.runs_dir = self.root_dir / "runs"
        self._lock = Lock()
        self.cases_dir.mkdir(parents=True, exist_ok=True)
        self.runs_dir.mkdir(parents=True, exist_ok=True)

    def create_case(self, payload: dict[str, Any]) -> dict[str, Any]:
        raw_parameters = _as_object(payload.get("parameters")) or None
        display_name = payload.get("displayName")
        normalized_display_name = (
            display_name.strip() if isinstance(display_name, str) and display_name.strip() else "Default fixed-geometry case"
        )
        transport = {
            **default_transport_config(),
            **_as_object(payload.get("transport")),
        }
        forcing = {
            **default_forcing_config(),
            **_as_object(payload.get("forcing")),
        }
        solver = {
            **default_solver_config(),
            **_as_object(payload.get("solver")),
        }
        event_thresholds = {
            **default_event_thresholds(),
            **_as_object(payload.get("eventThresholds")),
        }
        meshing = {
            **default_meshing_config(),
            **_as_object(payload.get("meshing")),
        }
        meshing_preset = payload.get("meshingPreset", meshing.get("preset"))
        if meshing_preset in {"coarse", "medium", "fine"}:
            meshing["preset"] = meshing_preset

        case_file = create_case_file(
            raw_parameters,
            display_name=normalized_display_name,
            transport=transport,
            forcing=forcing,
            solver=solver,
            event_thresholds=event_thresholds,
            meshing=meshing,
        )

        case_root = self.cases_dir / case_file["caseId"]
        case_root.mkdir(parents=True, exist_ok=True)
        write_json(case_root / "case.json", case_file)
        return case_file

    def load_case(self, case_id: str) -> dict[str, Any]:
        case_path = self.cases_dir / case_id / "case.json"
        if not case_path.exists():
            raise FileNotFoundError(f"Case '{case_id}' was not found.")
        return json.loads(case_path.read_text(encoding="utf-8"))

    def start_run(self, case_id: str, mode: str = AUTO_RUN_MODE) -> dict[str, Any]:
        case_file = self.load_case(case_id)
        resolved_mode = self._resolve_run_mode(case_file, mode)

        run_id = f"run-{uuid4().hex[:12]}"
        run_root = self.runs_dir / run_id
        run_root.mkdir(parents=True, exist_ok=True)
        now = _utc_now_iso()
        status_payload = {
            "runId": run_id,
            "caseId": case_id,
            "mode": resolved_mode,
            "state": "queued",
            "createdAt": now,
            "updatedAt": now,
            "startedAt": None,
            "completedAt": None,
            "statusUrl": f"/api/runs/{run_id}/status",
            "manifestUrl": f"/api/runs/{run_id}/viewer/manifest.json",
            "error": None,
        }
        self._write_status(run_id, status_payload)

        worker = Thread(
            target=self._execute_run,
            args=(run_id, case_id, resolved_mode),
            daemon=True,
            name=f"browser-run-{run_id}",
        )
        worker.start()
        return status_payload

    def get_run_status(self, run_id: str) -> dict[str, Any]:
        status_path = self._status_path(run_id)
        if not status_path.exists():
            raise FileNotFoundError(f"Run '{run_id}' was not found.")
        return json.loads(status_path.read_text(encoding="utf-8"))

    def get_run_file(self, run_id: str, relative_path: str) -> Path:
        run_root = (self.runs_dir / run_id).resolve()
        viewer_root = (run_root / "viewer").resolve()
        file_path = (run_root / relative_path).resolve()
        if not file_path.is_relative_to(run_root):
            raise PermissionError("Asset path escapes the run directory.")
        if not file_path.exists() or not file_path.is_file():
            file_path = (viewer_root / relative_path).resolve()
        if not file_path.is_relative_to(viewer_root) and not file_path.is_relative_to(run_root):
            raise PermissionError("Asset path escapes the run directory.")
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"Run asset '{relative_path}' was not found for '{run_id}'.")
        return file_path

    def _execute_run(self, run_id: str, case_id: str, mode: str) -> None:
        started_at = _utc_now_iso()
        self._update_status(run_id, state="running", startedAt=started_at, updatedAt=started_at)

        try:
            case_file = self.load_case(case_id)
            case_path = self.cases_dir / case_id / "case.json"
            run_root = self.runs_dir / run_id
            openfoam_case_dir = generate_case(case_file, run_root / "openfoam-case")
            if mode == REAL_RUN_MODE:
                run_case(openfoam_case_dir)
                create_real_run(openfoam_case_dir, run_root / "viewer")
            else:
                create_mock_run(case_path, run_root / "viewer")
        except Exception as exc:
            completed_at = _utc_now_iso()
            self._update_status(
                run_id,
                state="failed",
                completedAt=completed_at,
                updatedAt=completed_at,
                error=str(exc),
            )
            return

        completed_at = _utc_now_iso()
        self._update_status(
            run_id,
            state="done",
            completedAt=completed_at,
            updatedAt=completed_at,
        )

    def _resolve_run_mode(self, case_file: dict[str, Any], requested_mode: str) -> str:
        if requested_mode == MOCK_RUN_MODE:
            return MOCK_RUN_MODE
        solver_name = case_file["solver"]["solver"]
        solver_available = command_exists(solver_name)
        if requested_mode == AUTO_RUN_MODE:
            return REAL_RUN_MODE if solver_available else MOCK_RUN_MODE
        if requested_mode == REAL_RUN_MODE:
            if not solver_available:
                raise ValueError(
                    f"Solver '{solver_name}' is not available on PATH, so a real API run cannot be started."
                )
            return REAL_RUN_MODE
        raise ValueError("Run mode must be 'auto', 'mock', or 'real'.")

    def _status_path(self, run_id: str) -> Path:
        return self.runs_dir / run_id / "status.json"

    def _write_status(self, run_id: str, payload: dict[str, Any]) -> None:
        with self._lock:
            status_path = self._status_path(run_id)
            status_path.parent.mkdir(parents=True, exist_ok=True)
            write_json(status_path, payload)

    def _update_status(self, run_id: str, **fields: Any) -> dict[str, Any]:
        with self._lock:
            payload = self.get_run_status(run_id)
            payload.update(fields)
            write_json(self._status_path(run_id), payload)
            return payload


class ApiServer(ThreadingHTTPServer):
    api_state: ApiState


class ApiRequestHandler(BaseHTTPRequestHandler):
    server: ApiServer
    server_version = "FixedGeometryApi/0.1"

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        parts = [part for part in path.split("/") if part]

        try:
            if parts == ["api", "health"]:
                self._send_json(HTTPStatus.OK, {"status": "ok"})
                return

            if len(parts) == 3 and parts[:2] == ["api", "cases"]:
                self._send_json(HTTPStatus.OK, self.server.api_state.load_case(parts[2]))
                return

            if len(parts) == 4 and parts[:2] == ["api", "runs"] and parts[3] == "status":
                self._send_json(HTTPStatus.OK, self.server.api_state.get_run_status(parts[2]))
                return

            if len(parts) == 4 and parts[:2] == ["api", "runs"] and parts[3] in {"manifest", "manifest.json"}:
                self._send_file(self.server.api_state.get_run_file(parts[2], "manifest.json"))
                return

            if len(parts) >= 4 and parts[:2] == ["api", "runs"]:
                relative_path = "/".join(parts[3:])
                self._send_file(self.server.api_state.get_run_file(parts[2], relative_path))
                return
        except FileNotFoundError as exc:
            self._send_error_json(HTTPStatus.NOT_FOUND, str(exc))
            return
        except PermissionError as exc:
            self._send_error_json(HTTPStatus.FORBIDDEN, str(exc))
            return

        self._send_error_json(HTTPStatus.NOT_FOUND, f"Unhandled route: {path}")

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        parts = [part for part in path.split("/") if part]

        try:
            payload = self._read_json_body()
            if parts == ["api", "cases"]:
                case_file = self.server.api_state.create_case(payload)
                self._send_json(
                    HTTPStatus.CREATED,
                    {
                        "caseId": case_file["caseId"],
                        "caseUrl": f"/api/cases/{case_file['caseId']}",
                        "caseFile": case_file,
                    },
                )
                return

            if len(parts) == 4 and parts[:2] == ["api", "cases"] and parts[3] == "run":
                status_payload = self.server.api_state.start_run(
                    parts[2],
                    str(payload.get("mode", AUTO_RUN_MODE)),
                )
                self._send_json(HTTPStatus.ACCEPTED, status_payload)
                return
        except json.JSONDecodeError as exc:
            self._send_error_json(HTTPStatus.BAD_REQUEST, f"Invalid JSON body: {exc.msg}")
            return
        except FileNotFoundError as exc:
            self._send_error_json(HTTPStatus.NOT_FOUND, str(exc))
            return
        except ValueError as exc:
            self._send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return

        self._send_error_json(HTTPStatus.NOT_FOUND, f"Unhandled route: {path}")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        payload = self.rfile.read(length)
        if not payload:
            return {}
        decoded = json.loads(payload.decode("utf-8"))
        if not isinstance(decoded, dict):
            raise ValueError("JSON request bodies must be objects.")
        return decoded

    def _send_json(self, status: HTTPStatus, payload: dict[str, Any]) -> None:
        encoded = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self._send_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_file(self, file_path: Path) -> None:
        data = file_path.read_bytes()
        content_type = "application/json; charset=utf-8" if file_path.suffix == ".json" else "text/plain; charset=utf-8"
        self.send_response(HTTPStatus.OK)
        self._send_cors_headers()
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_error_json(self, status: HTTPStatus, message: str) -> None:
        self._send_json(status, {"error": message})

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")


def create_server(host: str = "127.0.0.1", port: int = 8000, state: ApiState | None = None) -> ApiServer:
    server = ApiServer((host, port), ApiRequestHandler)
    server.api_state = state or ApiState()
    return server


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Browser-triggered run API server")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind.")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind.")
    args = parser.parse_args()

    server = create_server(args.host, args.port)
    print(f"Serving browser run API on http://{args.host}:{args.port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
