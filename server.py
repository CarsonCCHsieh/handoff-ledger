"""Loopback-only review workspace for HANDOFF Ledger's real local agent."""

from __future__ import annotations

import argparse
import json
import mimetypes
import sys
import threading
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
FIXTURE = ROOT / "fixtures" / "sample-project"
OUTPUT = ROOT / "artifacts" / "run.json"
sys.path.insert(0, str(ROOT / "src"))

_lock = threading.Lock()
_state: dict = {"phase": "idle", "started_at": None, "run": None}


def load_saved_run() -> dict | None:
    if not OUTPUT.is_file() or OUTPUT.stat().st_size > 4_000_000:
        return None
    try:
        value = json.loads(OUTPUT.read_text(encoding="utf-8-sig"))
        return value if isinstance(value, dict) else None
    except (OSError, ValueError):
        return None


def execute_review() -> None:
    try:
        from handoff_ledger.runner import run_handoff

        result = run_handoff(
            FIXTURE, output_path=OUTPUT, timeout_seconds=180.0
        )
        if not isinstance(result, dict):
            raise TypeError("Agent returned an invalid review envelope")
    except Exception as exc:
        result = {
            "status": "failed",
            "error": {"type": type(exc).__name__, "message": "Local review failed. Inspect the local agent run log."},
            "typed_output_valid": False,
        }
    with _lock:
        _state.update(phase=result.get("status", "failed"), run=result)


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "HandoffLedger/0.1"

    def log_message(self, format: str, *args: object) -> None:
        # Keep local request logs free of query strings or request bodies.
        return

    def send_bytes(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; connect-src 'self'; style-src 'self'; script-src 'self'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(payload)

    def send_json(self, status: int, value: object) -> None:
        self.send_bytes(status, json.dumps(value, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        route = urlsplit(self.path).path
        if route == "/api/state":
            with _lock:
                value = dict(_state)
            if value["phase"] == "idle":
                value["run"] = load_saved_run()
                if value["run"]:
                    value["phase"] = value["run"].get("status", "failed")
            self.send_json(HTTPStatus.OK, value)
            return
        if route == "/api/evidence":
            files = []
            if FIXTURE.is_dir():
                for source in sorted(FIXTURE.rglob("*")):
                    if len(files) >= 32:
                        break
                    if not source.is_file() or source.is_symlink() or source.suffix not in {".md", ".txt", ".json", ".jsonl", ".log"}:
                        continue
                    if not source.resolve().is_relative_to(FIXTURE.resolve()) or source.stat().st_size > 80_000:
                        continue
                    try:
                        files.append({"path": source.relative_to(FIXTURE).as_posix(), "text": source.read_text(encoding="utf-8-sig")})
                    except (OSError, UnicodeError):
                        continue
            self.send_json(HTTPStatus.OK, {"label": "Original synthetic release fixture", "files": files})
            return
        static_files = {"/": "index.html", "/index.html": "index.html", "/app.js": "app.js", "/styles.css": "styles.css"}
        if route not in static_files:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        target = WEB / static_files[route]
        try:
            data = target.read_bytes()
        except OSError:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Asset not found"})
            return
        kind = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
        self.send_bytes(HTTPStatus.OK, data, kind + "; charset=utf-8")

    def do_POST(self) -> None:
        if urlsplit(self.path).path != "/api/run":
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        origin = self.headers.get("Origin")
        allowed = {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}
        if origin not in allowed:
            self.send_json(HTTPStatus.FORBIDDEN, {"error": "Open the local workspace to start a review"})
            return
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            self.send_json(HTTPStatus.UNSUPPORTED_MEDIA_TYPE, {"error": "JSON body required"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 0 or length > 256:
                raise ValueError
            body = json.loads(self.rfile.read(length) or b"{}")
            if body != {}:
                raise ValueError
        except (ValueError, TypeError):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "This demo accepts only its fixed synthetic fixture"})
            return
        with _lock:
            if _state["phase"] == "running":
                self.send_json(HTTPStatus.CONFLICT, {"error": "A review is already running"})
                return
            _state.update(phase="running", started_at=datetime.now(timezone.utc).isoformat(), run=None)
        threading.Thread(target=execute_review, name="handoff-review", daemon=True).start()
        self.send_json(HTTPStatus.ACCEPTED, {"phase": "running"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=31931)
    args = parser.parse_args()
    server = ThreadingHTTPServer(("127.0.0.1", args.port), ReviewHandler)
    print(f"HANDOFF Ledger: http://127.0.0.1:{server.server_port}/", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
