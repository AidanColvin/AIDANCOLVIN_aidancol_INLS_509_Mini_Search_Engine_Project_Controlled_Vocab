"""Jobs that build gold templates, edit gold labels, and run the evaluation report."""

from __future__ import annotations

from pathlib import Path

from rx_label_search.evaluate.gold import PLACEHOLDER_RATIONALE, build_gold_template, gold_cells, set_gold_label, validate_gold_document
from rx_label_search.evaluate.report import format_tag_evaluation_report
from rx_label_search.evaluate.ir_metrics import mean_average_precision, normalized_discounted_cumulative_gain, precision_at_k, recall_at_k
from rx_label_search.evaluate.tag_metrics import all_term_metrics
from rx_label_search.records import TermEvidence
from rx_label_search.search.run import load_indexed_documents, search
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


def read_queries_file(path: Path) -> dict[str, str]:
    """
    Takes a path to a queries file, one "query_id\\tquery_text" line per query.
    Reads every non-blank line into a mapping.
    Gives the mapping from query id to query text, empty for an empty file.
    """
    queries: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        query_id, _, query_text = line.partition("\t")
        queries[query_id] = query_text
    return queries


def read_judgments_file(path: Path) -> dict[str, dict[str, float]]:
    """
    Takes a path to a relevance-judgments file, one "query_id\\tset_id\\trelevance" line per judgment.
    Reads every non-blank line into a mapping of query id to a mapping of set id to relevance grade.
    Gives the nested mapping, empty for an empty file.
    """
    judgments: dict[str, dict[str, float]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        query_id, set_id, relevance = line.split("\t")
        judgments.setdefault(query_id, {})[set_id] = float(relevance)
    return judgments


def run_ir_evaluation(build_dir: Path, queries_path: Path, judgments_path: Path, k: int) -> dict[str, float]:
    """
    Takes the build directory, the queries file path, the judgments file path, and the cutoff k.
    Runs every query against the index and averages precision@k, recall@k, and nDCG@k, plus MAP over all ranks.
    Gives a dictionary of the four averaged scores, all 0.0 when the queries file is empty.
    """
    documents = load_indexed_documents(build_dir)
    queries = read_queries_file(queries_path)
    judgments = read_judgments_file(judgments_path)
    if not queries:
        return {"precision_at_k": 0.0, "recall_at_k": 0.0, "map": 0.0, "ndcg_at_k": 0.0}
    all_ranked: list[list[str]] = []
    all_relevant: list[frozenset[str]] = []
    precisions: list[float] = []
    recalls: list[float] = []
    ndcgs: list[float] = []
    for query_id, query_text in queries.items():
        hits = search(query_text, (), "AND", documents)
        ranked = [hit.set_id for hit in hits]
        relevance = judgments.get(query_id, {})
        relevant = frozenset(set_id for set_id, grade in relevance.items() if grade > 0)
        all_ranked.append(ranked)
        all_relevant.append(relevant)
        precisions.append(precision_at_k(ranked, relevant, k))
        recalls.append(recall_at_k(ranked, relevant, k))
        ndcgs.append(normalized_discounted_cumulative_gain(ranked, relevance, k))
    return {
        "precision_at_k": sum(precisions) / len(precisions),
        "recall_at_k": sum(recalls) / len(recalls),
        "map": mean_average_precision(all_ranked, all_relevant),
        "ndcg_at_k": sum(ndcgs) / len(ndcgs),
    }
