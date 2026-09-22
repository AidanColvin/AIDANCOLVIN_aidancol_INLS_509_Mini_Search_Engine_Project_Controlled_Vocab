"""Jobs that build gold templates, edit gold labels, and run the evaluation report."""

from __future__ import annotations

from pathlib import Path

from rx_label_search.evaluate.gold import PLACEHOLDER_RATIONALE, build_gold_template, gold_cells, set_gold_label, validate_gold_document
from rx_label_search.evaluate.report import format_tag_evaluation_report
from rx_label_search.evaluate.tag_metrics import all_term_metrics
from rx_label_search.records import TermEvidence
from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.read_jsonl import iter_jsonl
from rx_label_search.storage.write_json import write_json
from rx_label_search.vocabulary.hierarchy import term_ids
from rx_label_search.vocabulary.terms import TERMS_BY_ID

PLACEHOLDER_GOLD_FILE = Path("data/gold/gold_sample_PLACEHOLDER.json")


def write_placeholder_gold(build_dir: Path, sample_size: int, output_path: Path) -> Path:
    """
    Takes the build directory, how many labels to sample, and the placeholder file path.
    Builds a gold template from the first sample_size tagged set ids, with obviously fake rationale text.
    Gives the path written.
    """
    set_ids = [row["set_id"] for row in iter_jsonl(build_dir / "tags.jsonl")][:sample_size]
    return write_json(output_path, build_gold_template(set_ids, PLACEHOLDER_RATIONALE))


def predicted_terms_by_set_id(build_dir: Path) -> dict[str, frozenset[str]]:
    """
    Takes the build directory.
    Reads every tagged label's term ids, keyed by set id.
    Gives the mapping, empty when no tags file exists yet.
    """
    tags_path = build_dir / "tags.jsonl"
    if not tags_path.is_file():
        return {}
    predicted: dict[str, frozenset[str]] = {}
    for row in iter_jsonl(tags_path):
        evidence = tuple(TermEvidence(e["term_id"], e["field_name"], e["sentence"], e["rule_version"]) for e in row["evidence"])
        predicted[row["set_id"]] = term_ids(evidence)
    return predicted


def add_gold_label(gold_path: Path, set_id: str, term_id: str, gold: bool, rationale: str) -> Path:
    """
    Takes the gold file path, a set id, a term id, the gold value, and the rationale.
    Reads the file, sets the one cell, and writes the file back.
    Gives the path written, or raises FileNotFoundError when the gold file does not exist yet.
    """
    document = set_gold_label(read_json(gold_path), set_id, term_id, gold, rationale)
    return write_json(gold_path, document)


def run_tag_evaluation(build_dir: Path, gold_path: Path, report_path: Path) -> str:
    """
    Takes the build directory, the gold file path, and the report output path.
    Validates the gold file, computes every term's metrics against the tagger's output, and writes the report.
    Gives the report text, or raises ValueError when the gold file fails validation.
    """
    document = read_json(gold_path)
    problems = validate_gold_document(document)
    if problems:
        raise ValueError("; ".join(problems))
    cells = gold_cells(document)
    predicted = predicted_terms_by_set_id(build_dir)
    metrics = all_term_metrics(tuple(TERMS_BY_ID), cells, predicted)
    report = format_tag_evaluation_report(metrics, len(cells))
    write_json(report_path.with_suffix(".json"), [m.__dict__ | {"precision": m.precision, "recall": m.recall, "f1": m.f1} for m in metrics])
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report
