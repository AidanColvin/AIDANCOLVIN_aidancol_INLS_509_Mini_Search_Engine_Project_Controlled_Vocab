"""Vercel entry point for GET /api/search. Parses the query string and delegates to pure logic."""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rx_label_search.serve.api_search import available_terms, build_search_response, load_build_date  # noqa: E402

BUILD_DIR = Path(__file__).resolve().parent.parent / "data" / "build"


def handle_search_request(query_string: str) -> dict[str, object]:
    """
    Takes the raw query string of a GET /api/search request.
    Parses it and builds the search response.
    Gives the JSON-ready response dictionary.
    """
    params = parse_qs(query_string)
    build_date = load_build_date(BUILD_DIR)
    if params.get("terms_only") == ["1"]:
        return {"build_date": build_date, "available_terms": available_terms()}
    return build_search_response(BUILD_DIR, params, build_date)


class handler(BaseHTTPRequestHandler):
    """Handles GET requests for the search API."""

    def do_GET(self) -> None:
        """
        Takes no arguments.
        Reads the request's query string, builds the search response, and writes it as JSON.
        Gives nothing.
        """
        parsed = urlparse(self.path)
        try:
            body = json.dumps(handle_search_request(parsed.query)).encode("utf-8")
            status = 200
        except FileNotFoundError as error:
            body = json.dumps({"error": f"search data not built yet: {error}"}).encode("utf-8")
            status = 503
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)
