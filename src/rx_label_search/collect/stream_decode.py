"""Pure incremental decoding of a large JSON document's results array from text chunks."""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from typing import Any

RESULTS_KEY = '"results"'
_DECODER = json.JSONDecoder()


def find_array_start(text: str, key: str) -> int:
    """
    Takes a text buffer and a quoted JSON key such as "results".
    Finds the index of the opening bracket of the array that follows the key.
    Gives the index just past the bracket, or -1 when the key or bracket is not yet present.
    """
    key_index = text.find(key)
    if key_index < 0:
        return -1
    bracket = text.find("[", key_index + len(key))
    if bracket < 0:
        return -1
    return bracket + 1


def skip_separators(text: str, index: int) -> int:
    """
    Takes a text buffer and a start index.
    Advances past whitespace and commas.
    Gives the first index that is neither whitespace nor a comma, or len(text) at the end.
    """
    while index < len(text) and (text[index].isspace() or text[index] == ","):
        index += 1
    return index


def iter_array_objects(chunks: Iterable[str], key: str) -> Iterator[Any]:
    """
    Takes an iterable of text chunks forming one JSON document and the quoted key of an array in it.
    Decodes the array's elements one at a time while holding only unparsed text in memory.
    Gives an iterator of decoded elements, empty when the key never appears.
    """
    buffer = ""
    index = -1
    source = iter(chunks)
    while index < 0:
        chunk = next(source, None)
        if chunk is None:
            return
        buffer += chunk
        index = find_array_start(buffer, key)
    buffer = buffer[index:]
    while True:
        position = skip_separators(buffer, 0)
        if position < len(buffer) and buffer[position] == "]":
            return
        try:
            value, end = _DECODER.raw_decode(buffer, position)
        except json.JSONDecodeError:
            chunk = next(source, None)
            if chunk is None:
                return
            buffer += chunk
            continue
        yield value
        buffer = buffer[end:]
