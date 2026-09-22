"""Writes one JSON document to disk atomically."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def ensure_parent_dir(path: Path) -> Path:
    """
    Takes a file path.
    Creates the parent directory of the path if it does not exist.
    Gives the same path back.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_json(path: Path, data: Any) -> Path:
    """
    Takes a destination path and a JSON-serializable value.
    Writes the value as indented UTF-8 JSON through a temporary file that replaces the destination.
    Gives the destination path, or raises TypeError when the value is not serializable.
    """
    ensure_parent_dir(path)
    temp_path = path.with_name(path.name + ".tmp")
    with temp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    os.replace(temp_path, path)
    return path
