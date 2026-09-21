"""Reads JSON Lines files from disk."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


def iter_jsonl(path: Path) -> Iterator[Any]:
    """
    Takes a path to a UTF-8 JSON Lines file.
    Yields one decoded value per non-empty line as the file is read.
    Gives an iterator of values, or raises FileNotFoundError or json.JSONDecodeError.
    """
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield json.loads(stripped)


def read_jsonl(path: Path) -> list[Any]:
    """
    Takes a path to a UTF-8 JSON Lines file.
    Reads every line into memory.
    Gives the list of decoded values, empty for an empty file.
    """
    return list(iter_jsonl(path))
