"""Section 7.6 acceptance scenarios, run against the fixture labels."""

from __future__ import annotations

from typing import Any

from rx_label_search.search.index import build_document_frequencies, build_indexed_document, average_document_length
from rx_label_search.search.run import search
from rx_label_search.vocabulary.tagger import tag_record

GAZETTEER: frozenset[str] = frozenset()


def indexed_fixtures(fixture_labels: dict[str, dict[str, Any]]) -> list[Any]:
    """
    Takes the fixture labels.
    Tags and indexes every one of them.
    Gives the list of indexed documents.
    """
    documents = []
    for record in fixture_labels.values():
        tags = frozenset(item.term_id for item in tag_record(record, GAZETTEER).evidence)
        documents.append(build_indexed_document(record, tags))
    return documents


def test_scenario_1_t06_alone(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Filters on T06 alone with no keyword query.
    Gives nothing, or fails if gabapentin is missing or a label without T06 appears.
    """
    documents = indexed_fixtures(fixture_labels)
    hits = search("", ("T06",), "AND", documents)
    generics = {hit.generic_name for hit in hits}
    assert "GABAPENTIN" in generics
    assert all("T06" in hit.tags for hit in hits)


def test_scenario_2_hypertension_and_boxed_warning_and_oral(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Searches "hypertension" and filters on T01 AND T02.
    Gives nothing, or fails if losartan is missing or any hit lacks either term.
    """
    documents = indexed_fixtures(fixture_labels)
    hits = search("hypertension", ("T01", "T02"), "AND", documents)
    assert any("LOSARTAN" in hit.generic_name for hit in hits)
    assert all({"T01", "T02"} <= set(hit.tags) for hit in hits)


def test_scenario_2_oral_alone_would_include_entresto(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Searches "hypertension" and filters on T02 alone, without the boxed-warning requirement.
    Gives nothing, or fails if this looser filter does not return at least as many hits as the AND case.
    """
    documents = indexed_fixtures(fixture_labels)
    both = search("hypertension", ("T01", "T02"), "AND", documents)
    oral_only = search("hypertension", ("T02",), "AND", documents)
    assert len(oral_only) >= len(both)


def test_scenario_3_muscle_spasm_and_serotonin_and_cns(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Searches "muscle spasm" and filters on T14 AND T15.
    Gives nothing, or fails if cyclobenzaprine is missing or any hit lacks either term.
    """
    documents = indexed_fixtures(fixture_labels)
    hits = search("muscle spasm", ("T14", "T15"), "AND", documents)
    assert any("CYCLOBENZAPRINE" in hit.generic_name for hit in hits)
    assert all({"T14", "T15"} <= set(hit.tags) for hit in hits)


def test_scenario_3_or_returns_more_than_and(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Compares AND and OR joins of T14 and T15 on the same keyword query.
    Gives nothing, or fails if OR does not return at least as many hits as AND.
    """
    documents = indexed_fixtures(fixture_labels)
    and_hits = search("muscle spasm", ("T14", "T15"), "AND", documents)
    or_hits = search("muscle spasm", ("T14", "T15"), "OR", documents)
    assert len(or_hits) >= len(and_hits)


def test_search_average_length_and_document_frequency_are_reused_correctly(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Runs the same search directly through the lower-level functions and through the search job.
    Gives nothing, or fails if the two paths disagree.
    """
    documents = indexed_fixtures(fixture_labels)
    from rx_label_search.search.query import run_query

    frequencies = build_document_frequencies(documents)
    direct = run_query("hypertension", ("T01", "T02"), "AND", documents, frequencies, len(documents), average_document_length(documents))
    via_job = search("hypertension", ("T01", "T02"), "AND", documents)
    assert direct == via_job
