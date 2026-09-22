"""Reads one JSON document from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: Path) -> Any:
    """
    Takes a path to a UTF-8 JSON file.
    Reads and decodes the file.
    Gives the decoded value, or raises FileNotFoundError or json.JSONDecodeError.
    """
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
