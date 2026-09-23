"""Local HTTP server that serves public/ as static files and routes the two API paths to the Vercel function handlers.

The handlers in api/search.py and api/check.py are loaded from their files and called
directly, so a request to this server runs exactly the code the deployed functions run.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import ModuleType
from typing import Any
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
API_DIR = REPO_ROOT / "api"
DEFAULT_PUBLIC_DIR = REPO_ROOT / "public"
DEFAULT_PORT = 8000
SEARCH_PATH_PREFIX = "/api/search"
CHECK_PATH = "/api/check"


def load_api_module(module_stem: str) -> ModuleType:
    """
    Takes the stem of a file under api/, such as "check" or "search".
    Imports that file as a module under a private name so its "handler" class can be reused.
    Gives the loaded module, or raises FileNotFoundError when the file is missing.
    """
    source_path = API_DIR / f"{module_stem}.py"
    if not source_path.is_file():
        raise FileNotFoundError(f"missing Vercel function file: {source_path}")
    spec = importlib.util.spec_from_file_location(f"vercel_function_{module_stem}", source_path)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f"cannot build an import spec for {source_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def request_path(raw_path: str) -> str:
    """
    Takes the raw request target from the request line, which may carry a query string.
    Strips the query string and fragment.
    Gives the path part alone, "/" for an empty target.
    """
    return urlparse(raw_path).path or "/"


def build_handler_class(
    public_dir: Path,
    search_handler: type[BaseHTTPRequestHandler],
    check_handler: type[BaseHTTPRequestHandler],
) -> type[SimpleHTTPRequestHandler]:
    """
    Takes the static directory and the two Vercel handler classes.
    Builds one request handler class that sends GET /api/search* to the search handler, POST /api/check to the check handler, and every other GET to the static files.
    Gives the handler class, ready for an HTTP server.
    """

    class DevHandler(SimpleHTTPRequestHandler):
        """Serves public/ and delegates the two API paths to the Vercel function handlers."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            """
            Takes the positional and keyword arguments the HTTP server passes to a handler.
            Pins the static directory before the base class handles the request.
            Gives nothing.
            """
            super().__init__(*args, directory=str(public_dir), **kwargs)

        def do_GET(self) -> None:
            """
            Takes no arguments.
            Routes GET /api/search* to the search function's do_GET and everything else to the static file server.
            Gives nothing.
            """
            if request_path(self.path).startswith(SEARCH_PATH_PREFIX):
                search_handler.do_GET(self)
                return
            super().do_GET()

        def do_POST(self) -> None:
            """
            Takes no arguments.
            Routes POST /api/check to the check function's do_POST and answers 404 for any other path.
            Gives nothing.
            """
            if request_path(self.path) == CHECK_PATH:
                check_handler.do_POST(self)
                return
            self.send_error(404, "only POST /api/check is served")

        def log_message(self, format_string: str, *args: Any) -> None:
            """
            Takes the log format string and its arguments.
            Writes one access-log line to stderr with the client address stripped, so no request body is ever logged.
            Gives nothing.
            """
            sys.stderr.write(f"{self.log_date_time_string()} {format_string % args}\n")

    return DevHandler


def parse_args(argv: list[str]) -> argparse.Namespace:
    """
    Takes the command-line arguments without the program name.
    Parses the port and public directory flags.
    Gives the parsed namespace, or exits with usage text on a bad flag.
    """
    parser = argparse.ArgumentParser(description="Serve public/ and the two API routes locally.")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port to listen on (default {DEFAULT_PORT})")
    parser.add_argument("--public-dir", type=Path, default=DEFAULT_PUBLIC_DIR, help="directory of static files to serve")
    return parser.parse_args(argv)


def serve(port: int, public_dir: Path) -> None:
    """
    Takes the port and the static directory.
    Loads both Vercel function modules, changes into the repository root so their relative data paths resolve, and serves until interrupted.
    Gives nothing, or raises FileNotFoundError when the public directory or a function file is missing.
    """
    if not public_dir.is_dir():
        raise FileNotFoundError(f"public directory not found: {public_dir}")
    os.chdir(REPO_ROOT)
    search_module = load_api_module("search")
    check_module = load_api_module("check")
    handler_class = build_handler_class(public_dir.resolve(), search_module.handler, check_module.handler)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler_class)
    sys.stderr.write(f"serving {public_dir} on http://127.0.0.1:{server.server_port}\n")
    sys.stderr.flush()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("stopping\n")
    finally:
        server.server_close()


def main(argv: list[str]) -> int:
    """
    Takes the command-line arguments without the program name.
    Parses them and runs the server.
    Gives 0 on a clean stop, or 1 when a required file or directory is missing.
    """
    args = parse_args(argv)
    try:
        serve(args.port, args.public_dir)
    except FileNotFoundError as error:
        sys.stderr.write(f"error: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
