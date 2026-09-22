"""Network I/O for the openFDA manifest, bulk files, and single-label spot checks."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from rx_label_search.storage.write_json import ensure_parent_dir

MANIFEST_URL = "https://api.fda.gov/download.json"
LABEL_API_URL = "https://api.fda.gov/drug/label.json"
DEFAULT_TIMEOUT_SECONDS = 120.0
DOWNLOAD_CHUNK_BYTES = 1 << 20


def fetch_json(url: str, timeout: float) -> Any:
    """
    Takes a URL and a timeout in seconds.
    Performs an HTTP GET and decodes the body as JSON.
    Gives the decoded value, or raises urllib.error.URLError or json.JSONDecodeError.
    """
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.load(response)


def download_to_path(url: str, destination: Path, timeout: float) -> Path:
    """
    Takes a URL, a destination path, and a timeout in seconds.
    Streams the response body to a temporary file that then replaces the destination.
    Gives the destination path, or raises urllib.error.URLError on a failed request.
    """
    ensure_parent_dir(destination)
    temp_path = destination.with_name(destination.name + ".part")
    with urllib.request.urlopen(url, timeout=timeout) as response, temp_path.open("wb") as handle:
        while True:
            chunk = response.read(DOWNLOAD_CHUNK_BYTES)
            if not chunk:
                break
            handle.write(chunk)
    os.replace(temp_path, destination)
    return destination


def file_size_bytes(path: Path) -> int | None:
    """
    Takes a file path.
    Reads the size of the file from the filesystem.
    Gives the size in bytes, or None when the file does not exist.
    """
    if not path.is_file():
        return None
    return path.stat().st_size


def label_query_url(search: str, limit: int) -> str:
    """
    Takes an openFDA search expression and a result limit.
    Builds the drug label API URL with those query parameters encoded.
    Gives the full URL string.
    """
    return LABEL_API_URL + "?" + urllib.parse.urlencode({"search": search, "limit": limit})


def fetch_label_by_set_id(set_id: str, timeout: float) -> Any:
    """
    Takes an SPL set id and a timeout in seconds.
    Queries the openFDA label API for that set id.
    Gives the decoded API response, or raises urllib.error.HTTPError when nothing matches.
    """
    return fetch_json(label_query_url(f'set_id:"{set_id}"', 1), timeout)
