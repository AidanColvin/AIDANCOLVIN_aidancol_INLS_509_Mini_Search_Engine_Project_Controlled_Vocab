"""Jobs that build the checker's lookup data and run one check against it."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from rx_label_search.interactions.checker import run_interaction_check
from rx_label_search.interactions.knowledge import Knowledge
from rx_label_search.interactions.knowledge_evidence import build_rule_evidence
from rx_label_search.interactions.lookup import build_ingredient_set_index
from rx_label_search.interactions.report import build_check_report
from rx_label_search.normalize.run import default_fetcher
from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.read_jsonl import iter_jsonl
from rx_label_search.storage.write_json import write_json
from rx_label_search.text.fields import field_values
from rx_label_search.vocabulary.dea import SCHEDULE_PATTERNS
from rx_label_search.vocabulary.terms import TERMS_BY_ID

CHECKER_RECORDS_FILE = "checker_records.json"
RULE_EVIDENCE_FILE = "rule_evidence.json"
KNOWLEDGE_FILE = Path(__file__).resolve().parents[3] / "data" / "reference" / "interaction_knowledge.json"
INGREDIENT_SET_INDEX_FILE = "ingredient_set_index.json"


def label_schedule(controlled_substance_text: str) -> str | None:
    """
    Takes the joined controlled_substance field text.
    Checks it against each DEA schedule pattern, most restrictive first.
    Gives the schedule as "II", "III", "IV", or "V", or None when no schedule pattern matches.
    """
    for schedule in ("II", "III", "IV", "V"):
        if SCHEDULE_PATTERNS[schedule].search(controlled_substance_text):
            return schedule
    return None


def build_checker_record(record: Mapping[str, Any], evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Takes one raw label record and its tagged evidence rows.
    Reads the fields the checker's medication table and alerts need.
    Gives the checker record dictionary.
    """
    block = record.get("openfda") or {}
    controlled_substance_text = " ".join(field_values(record, "controlled_substance"))
    return {
        "set_id": str(record.get("set_id", "")),
        "effective_time": str(record.get("effective_time", "")),
        "brand_names": list(field_values(block, "brand_name")),
        "generic_names": list(field_values(block, "generic_name")),
        "ingredient_set": sorted({name.upper() for name in field_values(block, "substance_name")}),
        "route": list(field_values(block, "route")),
        "pharm_class_epc": list(field_values(block, "pharm_class_epc")),
        "schedule": label_schedule(controlled_substance_text),
        "evidence": evidence_rows,
    }


def build_checker_data(build_dir: Path) -> dict[str, int]:
    """
    Takes the build directory.
    Builds the checker records keyed by set id and the ingredient-set-to-set-id index, and writes both files.
    Gives a summary with the number of records written.
    """
    evidence_by_set_id = {row["set_id"]: row["evidence"] for row in iter_jsonl(build_dir / "tags.jsonl")}
    records: dict[str, dict[str, Any]] = {}
    for raw in iter_jsonl(build_dir / "collection.jsonl"):
        set_id = str(raw.get("set_id", ""))
        records[set_id] = build_checker_record(raw, evidence_by_set_id.get(set_id, []))
    write_json(build_dir / CHECKER_RECORDS_FILE, records)
    summaries = read_json(build_dir / "collection_summaries.json")
    write_json(build_dir / INGREDIENT_SET_INDEX_FILE, build_ingredient_set_index(summaries))
    salt_to_base = read_json(build_dir / "base_ingredients.json") if (build_dir / "base_ingredients.json").is_file() else {}
    evidence = build_rule_evidence(iter_jsonl(build_dir / "collection.jsonl"), Knowledge(read_json(KNOWLEDGE_FILE)), salt_to_base)
    write_json(build_dir / RULE_EVIDENCE_FILE, evidence)
    return {"records": len(records), "rules_with_label_evidence": len(evidence["by_base"])}


def run_check(build_dir: Path, medication_text: str, build_date: str, use_rxnorm: bool) -> dict[str, Any]:
    """
    Takes the build directory, a free-text medication list, the build date, and whether to use the RxNorm fallback.
    Loads every lookup table the checker needs and runs the check.
    Gives the formatted check report.
    """
    dictionary = read_json(build_dir / "name_dictionary.json")
    summaries = read_json(build_dir / "collection_summaries.json")
    salt_to_base = read_json(build_dir / "base_ingredients.json") if (build_dir / "base_ingredients.json").is_file() else {}
    ingredient_index = read_json(build_dir / INGREDIENT_SET_INDEX_FILE)
    checker_records = read_json(build_dir / CHECKER_RECORDS_FILE)
    metabolite_reference = read_json(Path("data/reference/active_metabolites.json"))["pairs"]
    fetch = default_fetcher() if use_rxnorm else None
    knowledge = Knowledge(read_json(KNOWLEDGE_FILE))
    rule_evidence = read_json(build_dir / RULE_EVIDENCE_FILE) if (build_dir / RULE_EVIDENCE_FILE).is_file() else {}
    result = run_interaction_check(medication_text, dictionary, fetch, summaries, salt_to_base, ingredient_index, checker_records, metabolite_reference, knowledge, rule_evidence)
    return build_check_report(result, build_date)
