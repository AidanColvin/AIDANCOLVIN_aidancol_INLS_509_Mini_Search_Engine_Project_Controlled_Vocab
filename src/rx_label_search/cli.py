"""Command-line argument parsing and dispatch."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from rx_label_search.collect.fetch import MANIFEST_URL
from rx_label_search.collect.run import build_collection, download_partitions
from rx_label_search.storage.read_json import read_json

DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_BUILD_DIR = Path("data/build")


def today_string() -> str:
    """
    Takes no arguments.
    Reads today's date from the system clock.
    Gives the date as YYYY-MM-DD.
    """
    return datetime.date.today().isoformat()


def default_workers() -> int:
    """
    Takes no arguments.
    Reads the CPU count from the operating system.
    Gives the CPU count minus one, never below 1.
    """
    return max(1, (os.cpu_count() or 2) - 1)


def build_parser() -> argparse.ArgumentParser:
    """
    Takes no arguments.
    Declares every command and option of the tool.
    Gives the configured argument parser.
    """
    parser = argparse.ArgumentParser(prog="rx-label-search", description="FDA label search, tagging, and interaction checks.")
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("download", help="download the openFDA label bulk files")
    download.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    download.add_argument("--manifest-url", default=MANIFEST_URL)
    collect = commands.add_parser("collect", help="build the filtered collection from the bulk files")
    collect.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    collect.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    collect.add_argument("--workers", type=int, default=default_workers())
    return parser


def run_download(args: argparse.Namespace) -> str:
    """
    Takes parsed download arguments.
    Runs the partition download job.
    Gives a one-line summary of the export date and file count.
    """
    export_date, paths = download_partitions(args.raw_dir, args.manifest_url)
    return f"export {export_date}: {len(paths)} partitions in {args.raw_dir}"


def run_collect(args: argparse.Namespace) -> str:
    """
    Takes parsed collect arguments.
    Reads the export date from the saved manifest and runs the collection build job.
    Gives the stats document as a JSON string.
    """
    manifest = read_json(args.raw_dir / "download_manifest.json")
    export_date = str(manifest["results"]["drug"]["label"]["export_date"])
    stats = build_collection(args.raw_dir, args.build_dir, export_date, today_string(), args.workers)
    return json.dumps(stats, indent=2)


def main(argv: Sequence[str] | None = None) -> int:
    """
    Takes an optional argument vector, defaulting to sys.argv.
    Parses the arguments and dispatches to the matching command.
    Gives the process exit code, 0 on success.
    """
    args = build_parser().parse_args(argv)
    handlers = {"download": run_download, "collect": run_collect}
    print(handlers[args.command](args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
