"""Vercel entry point for POST /api/check. Reads the JSON body and delegates to pure logic.

The request body (a medication list) is read only to build the response; it is
never written to a file, a log, or any store, and no analytics are recorded.
Each request is handled independently with no state carried between requests.
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rx_label_search.serve.api_check import build_check_response  # noqa: E402

BUILD_DIR = Path(__file__).resolve().parent.parent / "data" / "build"
MAX_REQUEST_BODY_BYTES = 1 << 20


def read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, object]:
    """
    Takes the active request handler.
    Reads its request body up to the maximum size and decodes it as JSON.
    Gives the decoded body, or an empty dictionary when it is missing or not valid JSON.
    """
    length = min(int(handler.headers.get("Content-Length", 0) or 0), MAX_REQUEST_BODY_BYTES)
    if length == 0:
        return {}
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


class handler(BaseHTTPRequestHandler):
    """Handles POST requests for the interaction-check API."""

    def do_POST(self) -> None:
        """
        Takes no arguments.
        Reads the JSON request body, runs the interaction check, and writes the report as JSON.
        Gives nothing.
        """
        body = read_json_body(self)
        try:
            response = json.dumps(build_check_response(BUILD_DIR, body)).encode("utf-8")
            status = 200
        except FileNotFoundError as error:
            response = json.dumps({"error": f"checker data not built yet: {error}"}).encode("utf-8")
            status = 503
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(response)
