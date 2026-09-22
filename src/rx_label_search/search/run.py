"""Jobs that build the search index and run one query against it.

The full body text of every label totals over 100 MB, too large to load into
memory on every serverless cold start. build_search_index_file therefore
splits the index: search_ranking.json holds everything BM25 and facets need
except body text, and one small file per label under snippets/ holds only
its body text. A query ranks against the lean ranking file, then reads a
snippet shard only for the handful of results it actually returns.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

from rx_label_search.records import SearchHit
from rx_label_search.search.index import IndexedDocument, average_document_length, build_document_frequencies, build_indexed_document
from rx_label_search.search.query import run_query
from rx_label_search.search.snippets import SNIPPET_RADIUS_CHARS, build_snippet
from rx_label_search.search.tokenize import tokenize
from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.read_jsonl import iter_jsonl
from rx_label_search.storage.write_json import write_json
from rx_label_search.search.index import tags_from_evidence_rows

INDEX_STATS_FILE = "index_stats.json"
SEARCH_RANKING_FILE = "search_ranking.json"
SNIPPET_SHARD_DIR = "snippets"


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


def document_to_ranking_json(document: IndexedDocument) -> dict[str, Any]:
    """
    Takes one indexed document.
    Converts it to a compact JSON-ready dictionary without the raw token list or body text.
    Gives the dictionary, keeping only what BM25 ranking and facets need.
    """
    return {
        "set_id": document.set_id,
        "effective_time": document.effective_time,
        "brand_name": document.brand_name,
        "generic_name": document.generic_name,
        "term_frequencies": dict(document.term_frequencies),
        "length": document.length,
        "tags": sorted(document.tags),
    }


def ranking_document_from_json(row: dict[str, Any]) -> IndexedDocument:
    """
    Takes one compact ranking-file row.
    Rebuilds the IndexedDocument with an empty body text, deriving its token tuple from the term frequencies.
    Gives the IndexedDocument.
    """
    return IndexedDocument(
        set_id=row["set_id"],
        effective_time=row["effective_time"],
        brand_name=row["brand_name"],
        generic_name=row["generic_name"],
        tokens=tuple(row["term_frequencies"]),
        term_frequencies=row["term_frequencies"],
        length=row["length"],
        tags=frozenset(row["tags"]),
        body_text="",
    )


def snippet_shard_path(build_dir: Path, set_id: str) -> Path:
    """
    Takes the build directory and a set id.
    Builds the path to that label's snippet shard file.
    Gives the path.
    """
    return build_dir / SNIPPET_SHARD_DIR / f"{set_id}.json"


def build_search_index_file(build_dir: Path) -> int:
    """
    Takes the build directory.
    Loads every indexed document, writes the lean ranking file, and writes one snippet shard per label.
    Gives the number of documents written.
    """
    documents = load_indexed_documents(build_dir)
    write_json(build_dir / SEARCH_RANKING_FILE, [document_to_ranking_json(document) for document in documents])
    for document in documents:
        write_json(snippet_shard_path(build_dir, document.set_id), {"body_text": document.body_text})
    return len(documents)


def load_ranking_documents(build_dir: Path) -> list[IndexedDocument]:
    """
    Takes the build directory.
    Reads the lean ranking file written by build_search_index_file.
    Gives the list of indexed documents, each with an empty body text.
    """
    return [ranking_document_from_json(row) for row in read_json(build_dir / SEARCH_RANKING_FILE)]


def load_body_text(build_dir: Path, set_id: str) -> str:
    """
    Takes the build directory and a set id.
    Reads that label's snippet shard.
    Gives its body text, or an empty string when the shard is missing.
    """
    path = snippet_shard_path(build_dir, set_id)
    if not path.is_file():
        return ""
    return read_json(path)["body_text"]


def attach_snippet(build_dir: Path, query_text: str, hit: SearchHit) -> SearchHit:
    """
    Takes the build directory, the original query text, and one ranked hit with no snippet yet.
    Reads that hit's snippet shard and builds its real snippet.
    Gives a new SearchHit with the snippet filled in.
    """
    body_text = load_body_text(build_dir, hit.set_id)
    snippet = build_snippet(body_text, tokenize(query_text), SNIPPET_RADIUS_CHARS)
    return dataclasses.replace(hit, snippet=snippet)


def search_with_snippets(
    build_dir: Path,
    query_text: str,
    term_ids: tuple[str, ...],
    operator: str,
    documents: list[IndexedDocument],
    limit: int,
) -> tuple[SearchHit, ...]:
    """
    Takes the build directory, the query text, selected PDLA term ids, the join operator, the lean documents, and a result limit.
    Ranks against the lean documents, then reads a snippet shard only for the top limit hits.
    Gives the tuple of hits, each with its real snippet filled in.
    """
    hits = search(query_text, term_ids, operator, documents)[:limit]
    return tuple(attach_snippet(build_dir, query_text, hit) for hit in hits)
