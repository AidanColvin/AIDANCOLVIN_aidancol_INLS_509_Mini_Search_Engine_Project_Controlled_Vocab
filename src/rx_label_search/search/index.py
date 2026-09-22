"""Pure construction of the inverted index and document store from the collection."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from rx_label_search.records import TermEvidence
from rx_label_search.search.tokenize import tokenize
from rx_label_search.text.fields import display_brand_name, display_generic_name, field_values, label_from_record
from rx_label_search.vocabulary.hierarchy import term_ids

INDEXED_FIELDS = (
    "indications_and_usage",
    "adverse_reactions",
    "warnings_and_cautions",
    "warnings",
    "boxed_warning",
    "contraindications",
    "drug_interactions",
    "dosage_and_administration",
    "precautions",
    "use_in_specific_populations",
)


@dataclass(frozen=True)
class IndexedDocument:
    """One label's tokenized text, term ids, and display fields, ready for BM25 and facets."""

    set_id: str
    effective_time: str
    brand_name: str
    generic_name: str
    tokens: tuple[str, ...]
    term_frequencies: Mapping[str, int]
    length: int
    tags: frozenset[str]
    body_text: str


def document_text(record: Mapping[str, Any]) -> str:
    """
    Takes a raw label record.
    Joins its indexed text fields and openfda brand, generic, and substance names into one string.
    Gives the joined text, empty when the record has none of those fields.
    """
    block = record.get("openfda") or {}
    pieces = [" ".join(field_values(record, field)) for field in INDEXED_FIELDS]
    pieces.append(" ".join(field_values(block, "brand_name")))
    pieces.append(" ".join(field_values(block, "generic_name")))
    pieces.append(" ".join(field_values(block, "substance_name")))
    return " ".join(piece for piece in pieces if piece)


def tags_from_evidence_rows(evidence_rows: Iterable[Mapping[str, Any]]) -> frozenset[str]:
    """
    Takes a tagged label's evidence rows, as read from tags.jsonl.
    Converts them to TermEvidence and reads the distinct term ids.
    Gives the frozenset of term ids, empty for no evidence.
    """
    evidence = tuple(TermEvidence(row["term_id"], row["field_name"], row["sentence"], row["rule_version"]) for row in evidence_rows)
    return term_ids(evidence)


def build_indexed_document(record: Mapping[str, Any], tags: frozenset[str]) -> IndexedDocument:
    """
    Takes a raw label record and its tag set.
    Tokenizes the indexed text and reads the display fields.
    Gives the IndexedDocument.
    """
    label = label_from_record(record)
    text = document_text(record)
    tokens = tokenize(text)
    return IndexedDocument(
        set_id=label.set_id,
        effective_time=label.effective_time,
        brand_name=display_brand_name(label),
        generic_name=display_generic_name(label),
        tokens=tokens,
        term_frequencies=Counter(tokens),
        length=len(tokens),
        tags=tags,
        body_text=text,
    )


def build_document_frequencies(documents: Iterable[IndexedDocument]) -> Counter[str]:
    """
    Takes the indexed documents.
    Counts, for each token, the number of documents it appears in.
    Gives the Counter, empty for no documents.
    """
    frequencies: Counter[str] = Counter()
    for document in documents:
        frequencies.update(document.term_frequencies.keys())
    return frequencies


def average_document_length(documents: Iterable[IndexedDocument]) -> float:
    """
    Takes the indexed documents.
    Averages their token counts.
    Gives the average length, 0.0 for no documents.
    """
    lengths = [document.length for document in documents]
    return sum(lengths) / len(lengths) if lengths else 0.0
