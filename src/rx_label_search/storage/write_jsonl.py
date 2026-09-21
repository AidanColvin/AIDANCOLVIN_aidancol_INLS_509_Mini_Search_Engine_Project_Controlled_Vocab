"""Writes JSON Lines files to disk atomically."""

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from rx_label_search.storage.write_json import ensure_parent_dir


def write_jsonl(path: Path, rows: Iterable[Any]) -> int:
    """
    Takes a destination path and an iterable of JSON-serializable values.
    Writes one compact JSON document per line through a temporary file that replaces the destination.
    Gives the number of lines written, 0 for an empty iterable.
    """
    ensure_parent_dir(path)
    temp_path = path.with_name(path.name + ".tmp")
    count = 0
    with temp_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")
            count += 1
    os.replace(temp_path, path)
    return count
