"""Jobs that build the search index and run one query against it."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rx_label_search.records import SearchHit
from rx_label_search.search.index import IndexedDocument, average_document_length, build_document_frequencies, build_indexed_document
from rx_label_search.search.query import run_query
from rx_label_search.storage.read_jsonl import iter_jsonl
from rx_label_search.storage.write_json import write_json
from rx_label_search.search.index import tags_from_evidence_rows

INDEX_STATS_FILE = "index_stats.json"


def load_indexed_documents(build_dir: Path) -> list[IndexedDocument]:
    """
    Takes the build directory.
    Reads the collection and its tags together and builds one indexed document per label.
    Gives the list of indexed documents, empty when the collection or tags file is missing.
    """
    tags_by_set_id = {row["set_id"]: tags_from_evidence_rows(row["evidence"]) for row in iter_jsonl(build_dir / "tags.jsonl")}
    return [
        build_indexed_document(record, tags_by_set_id.get(str(record.get("set_id", "")), frozenset()))
        for record in iter_jsonl(build_dir / "collection.jsonl")
    ]


def write_index_stats(build_dir: Path, documents: list[IndexedDocument]) -> dict[str, Any]:
    """
    Takes the build directory and the indexed documents.
    Writes a small stats file with the document count and average length.
    Gives the stats dictionary written.
    """
    stats = {"documents": len(documents), "average_length": average_document_length(documents)}
    write_json(build_dir / INDEX_STATS_FILE, stats)
    return stats


def search(
    query_text: str,
    term_ids: tuple[str, ...],
    operator: str,
    documents: list[IndexedDocument],
) -> tuple[SearchHit, ...]:
    """
    Takes the query text, selected PDLA term ids, the join operator, and the indexed documents.
    Computes the document frequencies and average length, then runs the query.
    Gives the tuple of hits.
    """
    document_frequency = build_document_frequencies(documents)
    average_length = average_document_length(documents)
    return run_query(query_text, term_ids, operator, documents, document_frequency, len(documents), average_length)
