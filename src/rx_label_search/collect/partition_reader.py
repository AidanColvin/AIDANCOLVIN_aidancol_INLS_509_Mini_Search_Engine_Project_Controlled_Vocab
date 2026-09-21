"""File I/O that streams label records out of a zipped openFDA partition."""

from __future__ import annotations

import io
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from rx_label_search.collect.stream_decode import RESULTS_KEY, iter_array_objects

READ_CHUNK_CHARS = 1 << 20


def iter_zip_text_chunks(path: Path, chunk_chars: int) -> Iterator[str]:
    """
    Takes a path to a .json.zip partition and a chunk size in characters.
    Opens the first member of the zip and reads it as UTF-8 text in chunks.
    Gives an iterator of text chunks, or raises zipfile.BadZipFile or FileNotFoundError.
    """
    with zipfile.ZipFile(path) as archive:
        member = archive.namelist()[0]
        with archive.open(member) as raw, io.TextIOWrapper(raw, encoding="utf-8") as text:
            while True:
                chunk = text.read(chunk_chars)
                if not chunk:
                    return
                yield chunk


def iter_partition_records(path: Path) -> Iterator[Any]:
    """
    Takes a path to a .json.zip openFDA partition.
    Streams the records of its results array without loading the whole file.
    Gives an iterator of decoded label records, empty when the file has no results.
    """
    return iter_array_objects(iter_zip_text_chunks(path, READ_CHUNK_CHARS), RESULTS_KEY)
