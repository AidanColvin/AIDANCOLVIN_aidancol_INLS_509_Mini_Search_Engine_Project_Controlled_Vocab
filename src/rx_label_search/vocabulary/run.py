"""The parallel, cached tagging job over the whole collection."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from rx_label_search.records import TagRecord, TermEvidence
from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.read_jsonl import iter_jsonl
from rx_label_search.storage.write_json import write_json
from rx_label_search.storage.write_jsonl import write_jsonl
from rx_label_search.vocabulary.gazetteer import build_class_gazetteer
from rx_label_search.vocabulary.tagger import tag_record
from rx_label_search.vocabulary.terms import RULE_VERSION

TAGS_FILE = "tags.jsonl"
CACHE_KEY_LENGTH = 16
_GAZETTEER: frozenset[str] = frozenset()


def cache_key(label_id: str, set_id: str, effective_time: str, rule_version: str) -> str:
    """
    Takes a label's id, set id, effective time, and the rule version that would tag it.
    Hashes the four values together.
    Gives a short hex digest that changes whenever any input changes.
    """
    joined = "|".join((label_id, set_id, effective_time, rule_version))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:CACHE_KEY_LENGTH]


def evidence_to_json(evidence: TermEvidence) -> dict[str, str]:
    """
    Takes one TermEvidence.
    Converts it to a JSON-ready dictionary.
    Gives the dictionary.
    """
    return {"term_id": evidence.term_id, "field_name": evidence.field_name, "sentence": evidence.sentence, "rule_version": evidence.rule_version}


def tag_record_to_json(tag: TagRecord) -> dict[str, Any]:
    """
    Takes one TagRecord.
    Converts it to a JSON-ready dictionary, keyed by cache_key for lookup.
    Gives the dictionary.
    """
    return {
        "cache_key": cache_key(tag.label_id, tag.set_id, tag.effective_time, tag.rule_version),
        "label_id": tag.label_id,
        "set_id": tag.set_id,
        "effective_time": tag.effective_time,
        "rule_version": tag.rule_version,
        "evidence": [evidence_to_json(item) for item in tag.evidence],
    }


def _tag_one(record: dict[str, Any]) -> dict[str, Any]:
    """
    Takes one raw label record.
    Tags it with the module-level gazetteer set by init_worker_gazetteer.
    Gives the JSON-ready tag document.
    """
    return tag_record_to_json(tag_record(record, _GAZETTEER))


def init_worker_gazetteer(gazetteer: frozenset[str]) -> None:
    """
    Takes the class gazetteer.
    Stores it in this worker process's module-level slot for _tag_one to read.
    Gives nothing.
    """
    global _GAZETTEER
    _GAZETTEER = gazetteer


def cached_keys(build_dir: Path) -> frozenset[str]:
    """
    Takes the build directory.
    Reads the cache keys already present in the tags file, if one exists.
    Gives the frozenset of keys, empty when no tags file exists yet.
    """
    tags_path = build_dir / TAGS_FILE
    if not tags_path.is_file():
        return frozenset()
    return frozenset(row["cache_key"] for row in iter_jsonl(tags_path))


def load_collection_records(build_dir: Path) -> Iterable[dict[str, Any]]:
    """
    Takes the build directory.
    Streams the collection's raw label records.
    Gives an iterator of records.
    """
    return iter_jsonl(build_dir / "collection.jsonl")


def uncached_records(records: Iterable[dict[str, Any]], cached: frozenset[str], rule_version: str) -> list[dict[str, Any]]:
    """
    Takes the collection records, the already-cached keys, and the current rule version.
    Filters out records whose cache key is already present.
    Gives the list of records that still need tagging.
    """
    return [record for record in records if cache_key(str(record.get("id", "")), str(record.get("set_id", "")), str(record.get("effective_time", "")), rule_version) not in cached]


def run_tagging(build_dir: Path, workers: int) -> dict[str, int]:
    """
    Takes the build directory and a worker count.
    Tags every collection label not already cached under the current rule version and merges the results.
    Gives a summary with the counts of records reused, newly tagged, and total.
    """
    gazetteer = build_class_gazetteer(load_collection_records(build_dir), read_json(Path("data/reference/fda_enzyme_table.json")))
    cached = cached_keys(build_dir)
    to_tag = uncached_records(load_collection_records(build_dir), cached, RULE_VERSION)
    with ProcessPoolExecutor(max_workers=workers, initializer=init_worker_gazetteer, initargs=(gazetteer,)) as pool:
        fresh = list(pool.map(_tag_one, to_tag))
    tags_path = build_dir / TAGS_FILE
    existing = list(iter_jsonl(tags_path)) if tags_path.is_file() else []
    write_jsonl(tags_path, [*existing, *fresh])
    write_json(build_dir / "class_gazetteer.json", sorted(gazetteer))
    return {"reused": len(existing), "newly_tagged": len(fresh), "total": len(existing) + len(fresh)}
