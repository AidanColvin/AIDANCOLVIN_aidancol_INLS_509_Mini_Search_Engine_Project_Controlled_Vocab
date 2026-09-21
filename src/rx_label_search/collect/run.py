"""Jobs that compose the collect stage: download partitions, then build the collection."""

from __future__ import annotations

import time
import urllib.error
from collections import Counter
from collections.abc import Iterator, Mapping
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from rx_label_search.collect.dedupe import newest_per_ingredient_set, winner_ids
from rx_label_search.collect.fetch import (
    DEFAULT_TIMEOUT_SECONDS,
    MANIFEST_URL,
    download_to_path,
    fetch_json,
    file_size_bytes,
)
from rx_label_search.collect.filters import summarize_record
from rx_label_search.collect.manifest import label_export_date, label_partitions, partition_filename
from rx_label_search.collect.partition_reader import iter_partition_records
from rx_label_search.collect.stats import build_stats, cumulative_counts, scan_records
from rx_label_search.normalize.name_dictionary import build_name_dictionary
from rx_label_search.records import LabelSummary, Partition
from rx_label_search.storage.write_json import write_json
from rx_label_search.storage.write_jsonl import write_jsonl

DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_RETRY_WAIT_SECONDS = 120.0
COLLECTION_FILE = "collection.jsonl"
STATS_FILE = "collection_stats.json"
NAME_DICTIONARY_FILE = "name_dictionary.json"
MANIFEST_FILE = "download_manifest.json"


def partition_path(raw_dir: Path, partition: Partition) -> Path:
    """
    Takes the raw data directory and a partition record.
    Joins the directory with the partition's file name.
    Gives the local path where the partition is stored.
    """
    return raw_dir / partition_filename(partition.url)


def is_complete_download(path: Path, expected_mb: float) -> bool:
    """
    Takes a local file path and the manifest's size in megabytes.
    Compares the file's size on disk with the expected size, allowing one percent of slack.
    Gives True when the file exists and is at least that large, False otherwise.
    """
    size = file_size_bytes(path)
    if size is None:
        return False
    return size >= expected_mb * 1_000_000 * 0.99


def download_with_retries(url: str, destination: Path, attempts: int, wait_seconds: float) -> Path:
    """
    Takes a URL, a destination path, the number of attempts, and the wait between attempts.
    Downloads the file, retrying after network errors with the given wait.
    Gives the destination path, or raises urllib.error.URLError after the last failed attempt.
    """
    last_error: urllib.error.URLError | None = None
    for attempt in range(attempts):
        try:
            return download_to_path(url, destination, DEFAULT_TIMEOUT_SECONDS)
        except urllib.error.URLError as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(wait_seconds)
    raise last_error if last_error is not None else urllib.error.URLError("no attempts made")


def download_partitions(raw_dir: Path, manifest_url: str) -> tuple[str, list[Path]]:
    """
    Takes the raw data directory and the manifest URL.
    Fetches the manifest, saves it, and downloads every label partition not already complete on disk.
    Gives the export date and the list of local partition paths in manifest order.
    """
    manifest = fetch_json(manifest_url, DEFAULT_TIMEOUT_SECONDS)
    write_json(raw_dir / MANIFEST_FILE, manifest)
    paths: list[Path] = []
    for partition in label_partitions(manifest):
        destination = partition_path(raw_dir, partition)
        if not is_complete_download(destination, partition.size_mb):
            download_with_retries(partition.url, destination, DOWNLOAD_ATTEMPTS, DOWNLOAD_RETRY_WAIT_SECONDS)
        paths.append(destination)
    return label_export_date(manifest), paths


def scan_partition_file(path: Path) -> tuple[Counter[str], list[LabelSummary]]:
    """
    Takes a path to one zipped partition.
    Streams its records through the scope filters.
    Gives the stage counter and the summaries of records that passed every filter.
    """
    return scan_records(iter_partition_records(path))


def iter_kept_records(path: Path, keep_ids: frozenset[str]) -> Iterator[Mapping[str, Any]]:
    """
    Takes a partition path and the set of label ids to keep.
    Streams the partition and passes through only the records whose id is in the set.
    Gives an iterator of raw records, empty when none match.
    """
    for record in iter_partition_records(path):
        if str(record.get("id", "")) in keep_ids:
            yield record


def write_kept_records(path: Path, keep_ids: frozenset[str], out_path: Path) -> int:
    """
    Takes a partition path, the ids to keep, and an output JSON Lines path.
    Writes the kept records of that partition to the output file.
    Gives the number of records written.
    """
    return write_jsonl(out_path, iter_kept_records(path, keep_ids))


def concatenate_files(parts: list[Path], out_path: Path) -> int:
    """
    Takes ordered part file paths and a destination path.
    Appends the parts' bytes into the destination and removes each part.
    Gives the total number of bytes written.
    """
    total = 0
    with out_path.open("wb") as handle:
        for part in parts:
            data = part.read_bytes()
            handle.write(data)
            total += len(data)
            part.unlink()
    return total


def summaries_by_id(summaries: list[LabelSummary], keep_ids: frozenset[str]) -> list[LabelSummary]:
    """
    Takes label summaries and the ids of the winners.
    Keeps only the summaries whose id is a winner, sorted by set id.
    Gives the filtered list, empty when nothing matches.
    """
    return sorted((s for s in summaries if s.label_id in keep_ids), key=lambda s: s.set_id)


def summary_to_json(summary: LabelSummary) -> dict[str, Any]:
    """
    Takes a label summary.
    Converts it to a JSON-ready dictionary.
    Gives the dictionary with tuples turned into lists.
    """
    return {
        "id": summary.label_id,
        "set_id": summary.set_id,
        "version": summary.version,
        "effective_time": summary.effective_time,
        "ingredient_set": list(summary.ingredient_set),
        "brand_names": list(summary.brand_names),
        "generic_names": list(summary.generic_names),
    }


def build_collection(raw_dir: Path, build_dir: Path, export_date: str, build_date: str, workers: int) -> dict[str, Any]:
    """
    Takes the raw and build directories, the openFDA export date, the build date, and a worker count.
    Runs both passes over the partitions and writes the collection, stats, name dictionary, and kept summaries.
    Gives the stats document, or raises FileNotFoundError when no partitions exist.
    """
    paths = sorted(raw_dir.glob("drug-label-*.json.zip"))
    if not paths:
        raise FileNotFoundError(f"no partitions found in {raw_dir}")
    reached: Counter[str] = Counter()
    summaries: list[LabelSummary] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for counts, found in pool.map(scan_partition_file, paths):
            reached.update(counts)
            summaries.extend(found)
    newest = newest_per_ingredient_set(summaries)
    keep = winner_ids(newest)
    build_dir.mkdir(parents=True, exist_ok=True)
    part_paths = [build_dir / f"collection.part-{index:04d}.jsonl" for index in range(len(paths))]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        list(pool.map(write_kept_records, paths, [keep] * len(paths), part_paths))
    concatenate_files(part_paths, build_dir / COLLECTION_FILE)
    write_json(build_dir / NAME_DICTIONARY_FILE, build_name_dictionary(summaries))
    write_json(build_dir / "collection_summaries.json", [summary_to_json(s) for s in summaries_by_id(summaries, keep)])
    stats = build_stats(cumulative_counts(reached, len(newest)), export_date, build_date, len(paths))
    write_json(build_dir / STATS_FILE, stats)
    return stats


def save_fixture(set_id: str, name: str, dest_dir: Path, fetch_date: str) -> Path:
    """
    Takes an SPL set id, a fixture name, a destination directory, and the fetch date.
    Fetches the label from the openFDA API and saves it with its fetch metadata.
    Gives the written path, or raises urllib.error.HTTPError when the set id is unknown.
    """
    from rx_label_search.collect.fetch import fetch_label_by_set_id, label_query_url

    response = fetch_label_by_set_id(set_id, DEFAULT_TIMEOUT_SECONDS)
    record = response["results"][0]
    document = {
        "fetched_on": fetch_date,
        "source_url": label_query_url(f'set_id:"{set_id}"', 1),
        "fixture_name": name,
        "label": record,
    }
    return write_json(dest_dir / f"{name}.json", document)
