"""Pure construction, validation, and editing of the hand-labeled gold set."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from rx_label_search.vocabulary.terms import TERMS_BY_ID

GOLD_SCHEMA_VERSION = 1
PLACEHOLDER_RATIONALE = "PLACEHOLDER: replace with your own rationale before this label counts as real."


def build_gold_template(set_ids: Iterable[str], rationale: str) -> dict[str, Any]:
    """
    Takes the set ids to include and the rationale text to fill every cell with.
    Builds one entry per set id and per PDLA term, each holding gold, and the rationale.
    Gives the gold document with schema_version and labels, empty labels for no set ids.
    """
    labels: dict[str, dict[str, Any]] = {}
    for set_id in set_ids:
        labels[set_id] = {term_id: {"gold": False, "rationale": rationale} for term_id in TERMS_BY_ID}
    return {"schema_version": GOLD_SCHEMA_VERSION, "labels": labels}


def validate_gold_document(document: Mapping[str, Any]) -> tuple[str, ...]:
    """
    Takes a decoded gold document.
    Checks its schema version and that every entry names a real term with a boolean gold value.
    Gives the tuple of problem messages, empty when the document is well formed.
    """
    problems: list[str] = []
    if document.get("schema_version") != GOLD_SCHEMA_VERSION:
        problems.append(f"schema_version must be {GOLD_SCHEMA_VERSION}")
    labels = document.get("labels", {})
    for set_id, terms in labels.items():
        for term_id, cell in terms.items():
            if term_id not in TERMS_BY_ID:
                problems.append(f"{set_id}: unknown term {term_id}")
            elif not isinstance(cell.get("gold"), bool):
                problems.append(f"{set_id}/{term_id}: gold value must be true or false")
    return tuple(problems)


def set_gold_label(document: Mapping[str, Any], set_id: str, term_id: str, gold: bool, rationale: str) -> dict[str, Any]:
    """
    Takes a gold document, the set id and term id to update, the gold value, and the rationale.
    Writes the cell for that set id and term without mutating the input document.
    Gives a new gold document with the cell set.
    """
    labels = {sid: dict(terms) for sid, terms in document.get("labels", {}).items()}
    entry = dict(labels.get(set_id, {}))
    entry[term_id] = {"gold": gold, "rationale": rationale}
    labels[set_id] = entry
    return {"schema_version": document.get("schema_version", GOLD_SCHEMA_VERSION), "labels": labels}


def gold_cells(document: Mapping[str, Any]) -> tuple[tuple[str, str, bool], ...]:
    """
    Takes a gold document.
    Lists every set id and term id pair with its gold value, skipping unfilled placeholder rationale cells.
    Gives the tuple of (set_id, term_id, gold) triples, empty when nothing is filled in.
    """
    filled: list[tuple[str, str, bool]] = []
    for set_id, terms in document.get("labels", {}).items():
        for term_id, cell in terms.items():
            if cell.get("rationale") != PLACEHOLDER_RATIONALE:
                filled.append((set_id, term_id, bool(cell.get("gold", False))))
    return tuple(filled)
