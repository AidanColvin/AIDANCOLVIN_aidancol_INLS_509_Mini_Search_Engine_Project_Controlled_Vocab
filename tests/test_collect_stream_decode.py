"""Tests for the incremental JSON array decoder."""

from __future__ import annotations

import json

from rx_label_search.collect.stream_decode import find_array_start, iter_array_objects, skip_separators


def chunked(text: str, size: int) -> list[str]:
    """
    Takes a text and a chunk size.
    Splits the text into consecutive pieces of that size.
    Gives the list of pieces, empty for empty text.
    """
    return [text[i : i + size] for i in range(0, len(text), size)]


def test_find_array_start_and_missing() -> None:
    """
    Takes no arguments.
    Finds the results array in a small document and in one without it.
    Gives nothing, or fails if either index is wrong.
    """
    assert find_array_start('{"meta": {}, "results": [', '"results"') == 25
    assert find_array_start('{"meta": {}}', '"results"') == -1


def test_skip_separators() -> None:
    """
    Takes no arguments.
    Skips whitespace and commas before the next token.
    Gives nothing, or fails if the index is wrong.
    """
    assert skip_separators(" , ,x", 0) == 4
    assert skip_separators("", 0) == 0


def test_iter_array_objects_across_chunk_boundaries() -> None:
    """
    Takes no arguments.
    Decodes a document split into tiny chunks that cut through objects.
    Gives nothing, or fails if the decoded objects differ from the originals.
    """
    rows = [{"id": str(i), "text": ["a, b]", "c"]} for i in range(5)]
    document = json.dumps({"meta": {"x": 1}, "results": rows})
    assert list(iter_array_objects(chunked(document, 7), '"results"')) == rows


def test_iter_array_objects_empty_document() -> None:
    """
    Takes no arguments.
    Decodes chunks with no results key and a document with an empty array.
    Gives nothing, or fails if anything is yielded.
    """
    assert list(iter_array_objects(["{}"], '"results"')) == []
    assert list(iter_array_objects(['{"results": []}'], '"results"')) == []
