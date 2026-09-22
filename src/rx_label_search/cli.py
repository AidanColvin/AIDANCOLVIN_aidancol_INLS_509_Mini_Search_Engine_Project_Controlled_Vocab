"""Command-line argument parsing and dispatch."""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import os
import sys
from collections.abc import Sequence
from pathlib import Path

from rx_label_search.collect.fetch import MANIFEST_URL
from rx_label_search.collect.run import build_collection, download_partitions
from rx_label_search.collect.verify import collection_problems
from rx_label_search.normalize.med_line_parser import parse_med_list
from rx_label_search.normalize.run import build_base_ingredient_map, default_fetcher, resolve_name
from rx_label_search.vocabulary.run import run_tagging
from rx_label_search.evaluate.run import add_gold_label, run_ir_evaluation, run_tag_evaluation, write_placeholder_gold
from rx_label_search.interactions.run import build_checker_data, run_check
from rx_label_search.search.facets import OPERATOR_AND
from rx_label_search.search.run import build_search_index_file, load_indexed_documents, load_ranking_documents, search_with_snippets, write_index_stats
from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.read_jsonl import iter_jsonl

DEFAULT_RAW_DIR = Path("data/raw")
DEFAULT_BUILD_DIR = Path("data/build")


def today_string() -> str:
    """
    Takes no arguments.
    Reads today's date from the system clock.
    Gives the date as YYYY-MM-DD.
    """
    return datetime.date.today().isoformat()


def default_workers() -> int:
    """
    Takes no arguments.
    Reads the CPU count from the operating system.
    Gives the CPU count minus one, never below 1.
    """
    return max(1, (os.cpu_count() or 2) - 1)


def build_parser() -> argparse.ArgumentParser:
    """
    Takes no arguments.
    Declares every command and option of the tool.
    Gives the configured argument parser.
    """
    parser = argparse.ArgumentParser(prog="rx-label-search", description="FDA label search, tagging, and interaction checks.")
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("download", help="download the openFDA label bulk files")
    download.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    download.add_argument("--manifest-url", default=MANIFEST_URL)
    collect = commands.add_parser("collect", help="build the filtered collection from the bulk files")
    collect.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    collect.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    collect.add_argument("--workers", type=int, default=default_workers())
    verify = commands.add_parser("verify-collection", help="check the built collection against the scope rules")
    verify.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    bases = commands.add_parser("base-ingredients", help="map every collection substance to its RxNorm base ingredients")
    bases.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    parse = commands.add_parser("parse-meds", help="parse a free-text medication list")
    parse.add_argument("text")
    resolve = commands.add_parser("resolve", help="resolve typed drug names to collection ingredient sets")
    resolve.add_argument("text")
    resolve.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    resolve.add_argument("--no-rxnorm", action="store_true", help="skip the RxNorm fallback")
    tag = commands.add_parser("tag", help="tag every collection label with the PDLA terms")
    tag.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    tag.add_argument("--workers", type=int, default=default_workers())
    gold_template = commands.add_parser("gold-template", help="write the placeholder gold-set template")
    gold_template.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    gold_template.add_argument("--sample-size", type=int, default=20)
    gold_template.add_argument("--output", type=Path, default=Path("data/gold/gold_sample_PLACEHOLDER.json"))
    gold_label = commands.add_parser("gold-label", help="record one hand label in the gold file")
    gold_label.add_argument("--gold-file", type=Path, required=True)
    gold_label.add_argument("--set-id", required=True)
    gold_label.add_argument("--term", required=True, choices=sorted(f"T{n:02d}" for n in range(1, 18)))
    gold_label.add_argument("--value", required=True, choices=("true", "false"))
    gold_label.add_argument("--rationale", required=True)
    evaluate = commands.add_parser("evaluate-tags", help="score the tagger against the gold file")
    evaluate.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    evaluate.add_argument("--gold-file", type=Path, default=Path("data/gold/gold_sample_PLACEHOLDER.json"))
    evaluate.add_argument("--report", type=Path, default=Path("reports/tag_evaluation.md"))
    build_index = commands.add_parser("build-index", help="build the search index stats from the tagged collection")
    build_index.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    query = commands.add_parser("query", help="run one keyword and facet search")
    query.add_argument("text", nargs="?", default="")
    query.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    query.add_argument("--term", action="append", dest="terms", default=[], help="a PDLA term id to filter on; repeat for more")
    query.add_argument("--operator", choices=("AND", "OR"), default=OPERATOR_AND)
    query.add_argument("--limit", type=int, default=10)
    ir_eval = commands.add_parser("evaluate-search", help="score search against a queries and relevance-judgments file")
    ir_eval.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    ir_eval.add_argument("--queries", type=Path, required=True)
    ir_eval.add_argument("--judgments", type=Path, required=True)
    ir_eval.add_argument("--k", type=int, default=10)
    build_checker = commands.add_parser("build-checker-data", help="build the checker's lookup tables from the tagged collection")
    build_checker.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    check = commands.add_parser("check", help="check a free-text medication list for interaction risks")
    check.add_argument("text")
    check.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    check.add_argument("--build-date", default=today_string())
    check.add_argument("--no-rxnorm", action="store_true", help="skip the RxNorm fallback")
    return parser


def run_download(args: argparse.Namespace) -> str:
    """
    Takes parsed download arguments.
    Runs the partition download job.
    Gives a one-line summary of the export date and file count.
    """
    export_date, paths = download_partitions(args.raw_dir, args.manifest_url)
    return f"export {export_date}: {len(paths)} partitions in {args.raw_dir}"


def run_collect(args: argparse.Namespace) -> str:
    """
    Takes parsed collect arguments.
    Reads the export date from the saved manifest and runs the collection build job.
    Gives the stats document as a JSON string.
    """
    manifest = read_json(args.raw_dir / "download_manifest.json")
    export_date = str(manifest["results"]["drug"]["label"]["export_date"])
    stats = build_collection(args.raw_dir, args.build_dir, export_date, today_string(), args.workers)
    return json.dumps(stats, indent=2)


def run_verify_collection(args: argparse.Namespace) -> str:
    """
    Takes parsed verify-collection arguments.
    Streams the built collection through the invariant checks.
    Gives a summary line, or raises SystemExit(1) with the problems listed when any check fails.
    """
    count, problems = collection_problems(iter_jsonl(args.build_dir / "collection.jsonl"))
    if problems:
        raise SystemExit("\n".join([f"{len(problems)} problems in {count} records", *problems[:50]]))
    return f"collection valid: {count} records, one per ingredient set, all human prescription with openfda"


def run_base_ingredients(args: argparse.Namespace) -> str:
    """
    Takes parsed base-ingredients arguments.
    Runs the RxNorm lookup job over the collection summaries.
    Gives a one-line count of substances mapped.
    """
    mapping = build_base_ingredient_map(args.build_dir, default_fetcher(), today_string())
    return f"{len(mapping)} substances mapped to base ingredients in {args.build_dir}"


def run_parse_meds(args: argparse.Namespace) -> str:
    """
    Takes parsed parse-meds arguments.
    Parses the medication list text.
    Gives the entries as a JSON string.
    """
    return json.dumps([dataclasses.asdict(entry) for entry in parse_med_list(args.text)], indent=2)


def run_resolve(args: argparse.Namespace) -> str:
    """
    Takes parsed resolve arguments.
    Parses the medication list and resolves each name through the dictionary and, unless disabled, RxNorm.
    Gives the entries with their matches as a JSON string.
    """
    dictionary = read_json(args.build_dir / "name_dictionary.json")
    summaries = read_json(args.build_dir / "collection_summaries.json")
    salt_to_base = read_json(args.build_dir / "base_ingredients.json") if (args.build_dir / "base_ingredients.json").is_file() else {}
    fetch = None if args.no_rxnorm else default_fetcher()
    rows = []
    for entry in parse_med_list(args.text):
        match = resolve_name(entry.name_text, dictionary, fetch, summaries, salt_to_base)
        rows.append({"entry": dataclasses.asdict(entry), "match": dataclasses.asdict(match)})
    return json.dumps(rows, indent=2)


def run_tag(args: argparse.Namespace) -> str:
    """
    Takes parsed tag arguments.
    Runs the tagging job over the collection.
    Gives a one-line summary of reused, newly tagged, and total records.
    """
    summary = run_tagging(args.build_dir, args.workers)
    return f"tagged {summary['total']} labels ({summary['reused']} reused, {summary['newly_tagged']} new)"


def run_gold_template(args: argparse.Namespace) -> str:
    """
    Takes parsed gold-template arguments.
    Writes the placeholder gold-set template.
    Gives a one-line summary of the path written.
    """
    path = write_placeholder_gold(args.build_dir, args.sample_size, args.output)
    return f"wrote placeholder gold template to {path}"


def run_gold_label(args: argparse.Namespace) -> str:
    """
    Takes parsed gold-label arguments.
    Records one hand label in the gold file.
    Gives a one-line summary of the cell written.
    """
    add_gold_label(args.gold_file, args.set_id, args.term, args.value == "true", args.rationale)
    return f"recorded {args.term}={args.value} for {args.set_id} in {args.gold_file}"


def run_evaluate_tags(args: argparse.Namespace) -> str:
    """
    Takes parsed evaluate-tags arguments.
    Runs the tag evaluation report job.
    Gives the report text.
    """
    return run_tag_evaluation(args.build_dir, args.gold_file, args.report)


def run_build_index(args: argparse.Namespace) -> str:
    """
    Takes parsed build-index arguments.
    Loads the indexed documents, writes the index stats file, and writes the compact search index file the serve function reads.
    Gives a one-line summary of the document count and average length.
    """
    documents = load_indexed_documents(args.build_dir)
    stats = write_index_stats(args.build_dir, documents)
    build_search_index_file(args.build_dir)
    return f"indexed {stats['documents']} documents, average length {stats['average_length']:.1f} tokens"


def run_query_command(args: argparse.Namespace) -> str:
    """
    Takes parsed query arguments.
    Loads the lean ranking documents and runs one search, attaching a real snippet to each returned hit.
    Gives the top hits as a JSON string.
    """
    documents = load_ranking_documents(args.build_dir)
    hits = search_with_snippets(args.build_dir, args.text, tuple(args.terms), args.operator, documents, args.limit)
    return json.dumps([dataclasses.asdict(hit) for hit in hits], indent=2)


def run_evaluate_search(args: argparse.Namespace) -> str:
    """
    Takes parsed evaluate-search arguments.
    Runs the IR evaluation job.
    Gives the scores as a JSON string.
    """
    return json.dumps(run_ir_evaluation(args.build_dir, args.queries, args.judgments, args.k), indent=2)


def run_build_checker_data(args: argparse.Namespace) -> str:
    """
    Takes parsed build-checker-data arguments.
    Runs the checker data build job.
    Gives a one-line summary of the record count.
    """
    summary = build_checker_data(args.build_dir)
    return f"built checker records for {summary['records']} labels in {args.build_dir}"


def run_check_command(args: argparse.Namespace) -> str:
    """
    Takes parsed check arguments.
    Runs the interaction checker on the given medication text.
    Gives the report as a JSON string.
    """
    return json.dumps(run_check(args.build_dir, args.text, args.build_date, not args.no_rxnorm), indent=2)


def main(argv: Sequence[str] | None = None) -> int:
    """
    Takes an optional argument vector, defaulting to sys.argv.
    Parses the arguments and dispatches to the matching command.
    Gives the process exit code, 0 on success.
    """
    args = build_parser().parse_args(argv)
    handlers = {
        "download": run_download,
        "collect": run_collect,
        "verify-collection": run_verify_collection,
        "base-ingredients": run_base_ingredients,
        "parse-meds": run_parse_meds,
        "resolve": run_resolve,
        "tag": run_tag,
        "gold-template": run_gold_template,
        "gold-label": run_gold_label,
        "evaluate-tags": run_evaluate_tags,
        "build-index": run_build_index,
        "query": run_query_command,
        "evaluate-search": run_evaluate_search,
        "build-checker-data": run_build_checker_data,
        "check": run_check_command,
    }
    print(handlers[args.command](args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
