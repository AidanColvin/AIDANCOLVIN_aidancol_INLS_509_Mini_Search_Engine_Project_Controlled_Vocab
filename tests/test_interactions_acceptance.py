"""Section 3.6 acceptance test, built entirely from fixture labels and saved RxNorm responses."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from rx_label_search.collect.filters import summarize_record
from rx_label_search.collect.run import summary_to_json
from rx_label_search.interactions.checker import run_interaction_check
from rx_label_search.interactions.lookup import build_ingredient_set_index
from rx_label_search.interactions.report import build_check_report
from rx_label_search.interactions.run import build_checker_record
from rx_label_search.normalize.name_dictionary import build_name_dictionary
from rx_label_search.normalize.run import lookup_bases_for_substance, salt_to_base_map, unique_substances
from rx_label_search.storage.read_json import read_json
from rx_label_search.vocabulary.tagger import tag_record

FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "labels"
RXNORM_DIR = Path(__file__).resolve().parent / "fixtures" / "rxnorm"
ACCEPTANCE_FIXTURES = (
    "olanzapine_zyprexa",
    "adderall_xr",
    "zolpidem_ambien",
    "trazodone",
    "desvenlafaxine",
    "cyclobenzaprine",
    "pregabalin_lyrica",
    "venlafaxine",
    "dextroamphetamine",
)
TEST_INPUT = (
    "10 mg Zyprexa X 1 daily , 20 mg adderall X 3 daily , 10 mg ambien X daily , trazdone 50 mg X 1 daily , "
    "desvenlafaxine 50 mg X 1 daily , Flexril 10 mg X 3 times daily , Lyrica 100 mg X 3 daily"
)


def fixture_fetch(url: str) -> Any:
    """
    Takes a full RxNav URL.
    Serves the saved response whose source_url matches, so no network is used.
    Gives the response, or raises KeyError when no fixture was saved for the URL.
    """
    for path in RXNORM_DIR.glob("*.json"):
        document = read_json(path)
        if document["source_url"] == url:
            return document["response"]
    raise KeyError(url)


@pytest.fixture(scope="module")
def acceptance_context() -> dict[str, Any]:
    """
    Takes no arguments.
    Builds every lookup table the checker needs from only the nine acceptance fixtures.
    Gives a dictionary with the dictionary, summaries, salt-to-base map, ingredient index, checker records, and metabolite reference.
    """
    records = {name: read_json(FIXTURE_DIR / f"{name}.json")["label"] for name in ACCEPTANCE_FIXTURES}
    summaries = [summarize_record(record) for record in records.values()]
    summary_docs = [summary_to_json(summary) for summary in summaries]
    cache = {substance: lookup_bases_for_substance(substance, fixture_fetch) for substance in unique_substances(summary_docs)}
    gazetteer = frozenset({"mao inhibitors", "monoamine oxidase inhibitors"})
    checker_records = {}
    for record in records.values():
        tag = tag_record(record, gazetteer)
        evidence_rows = [{"term_id": e.term_id, "field_name": e.field_name, "sentence": e.sentence, "rule_version": e.rule_version} for e in tag.evidence]
        checker_records[str(record["set_id"])] = build_checker_record(record, evidence_rows)
    return {
        "dictionary": build_name_dictionary(summaries),
        "summaries": summary_docs,
        "salt_to_base": salt_to_base_map(cache),
        "ingredient_index": build_ingredient_set_index(summary_docs),
        "checker_records": checker_records,
        "metabolite_reference": read_json(Path("data/reference/active_metabolites.json"))["pairs"],
    }


def run_acceptance_check(context: dict[str, Any], text: str) -> dict[str, Any]:
    """
    Takes the acceptance context and a medication-list text.
    Runs the checker and formats its report.
    Gives the report dictionary.
    """
    result = run_interaction_check(
        text,
        context["dictionary"],
        fixture_fetch,
        context["summaries"],
        context["salt_to_base"],
        context["ingredient_index"],
        context["checker_records"],
        context["metabolite_reference"],
    )
    return build_check_report(result, "2026-09-21")


def test_seven_entries_parse_with_correct_daily_totals(acceptance_context: dict[str, Any]) -> None:
    """
    Takes the acceptance context.
    Runs the checker on the exact Section 3.1 test input.
    Gives nothing, or fails if the entry count or any daily total is wrong.
    """
    report = run_acceptance_check(acceptance_context, TEST_INPUT)
    totals = [row["daily_total"] for row in report["medication_table"]]
    assert len(report["medication_table"]) == 7
    assert totals == [10.0, 60.0, 10.0, 50.0, 50.0, 30.0, 300.0]


def test_typos_resolve_with_the_mapping_shown(acceptance_context: dict[str, Any]) -> None:
    """
    Takes the acceptance context.
    Checks the "trazdone" and "Flexril" entries.
    Gives nothing, or fails if either mapping chain does not show the resolution path.
    """
    report = run_acceptance_check(acceptance_context, TEST_INPUT)
    by_entry = {row["as_entered"]: row for row in report["medication_table"]}
    trazodone_row = by_entry["trazdone 50 mg X 1 daily"]
    assert trazodone_row["matched_name"][0] == "trazdone"
    assert "TRAZODONE" in trazodone_row["generic"][0].upper()
    flexril_row = by_entry["Flexril 10 mg X 3 times daily"]
    assert flexril_row["matched_name"] == ("Flexril", "Flexeril", "cyclobenzaprine", "CYCLOBENZAPRINE HYDROCHLORIDE")


def test_ambien_entry_notes_frequency_read_from_x_daily() -> None:
    """
    Takes no arguments.
    Parses the "10 mg ambien X daily" entry on its own.
    Gives nothing, or fails if the once-daily note is missing.
    """
    from rx_label_search.normalize.med_line_parser import parse_med_list

    entry = parse_med_list("10 mg ambien X daily")[0]
    assert any("once daily" in note for note in entry.notes)


def test_adderall_rolls_up_to_amphetamine_and_dextroamphetamine(acceptance_context: dict[str, Any]) -> None:
    """
    Takes the acceptance context.
    Checks the Adderall entry's base ingredients.
    Gives nothing, or fails if they are not exactly amphetamine and dextroamphetamine.
    """
    report = run_acceptance_check(acceptance_context, TEST_INPUT)
    adderall_row = next(row for row in report["medication_table"] if row["as_entered"].startswith("20 mg adderall"))
    assert sorted(adderall_row["base_ingredients"]) == ["amphetamine", "dextroamphetamine"]


def test_schedules_match_the_fixture_labels(acceptance_context: dict[str, Any]) -> None:
    """
    Takes the acceptance context.
    Checks the DEA schedule shown for the amphetamine, zolpidem, and pregabalin entries, and that the other four show none.
    Gives nothing, or fails if any schedule is wrong.
    """
    report = run_acceptance_check(acceptance_context, TEST_INPUT)
    schedules = {row["as_entered"]: row["dea_schedule"] for row in report["medication_table"]}
    assert schedules["20 mg adderall X 3 daily"] == "II"
    assert schedules["10 mg ambien X daily"] == "IV"
    assert schedules["Lyrica 100 mg X 3 daily"] == "V"
    for entry in ("10 mg Zyprexa X 1 daily", "trazdone 50 mg X 1 daily", "desvenlafaxine 50 mg X 1 daily", "Flexril 10 mg X 3 times daily"):
        assert schedules[entry] is None, entry


def test_expected_group_alerts_fire(acceptance_context: dict[str, Any]) -> None:
    """
    Takes the acceptance context.
    Checks for the serotonin syndrome and CNS depression group alerts.
    Gives nothing, or fails if either alert is missing or has fewer than four members.
    """
    report = run_acceptance_check(acceptance_context, TEST_INPUT)
    by_risk = {alert["risk"]: alert for alert in report["alerts"] if alert["kind"] == "group"}
    assert "T14" in by_risk
    assert len(by_risk["T14"]["members"]) >= 4
    assert "T15" in by_risk
    assert len(by_risk["T15"]["members"]) >= 4


def test_no_duplication_flags_for_the_main_list(acceptance_context: dict[str, Any]) -> None:
    """
    Takes the acceptance context.
    Checks that the seven-entry list raises no duplication flag.
    Gives nothing, or fails if one is present.
    """
    report = run_acceptance_check(acceptance_context, TEST_INPUT)
    assert [alert for alert in report["alerts"] if alert["kind"] == "duplication"] == []


def test_venlafaxine_and_desvenlafaxine_give_a_metabolite_flag(acceptance_context: dict[str, Any]) -> None:
    """
    Takes the acceptance context.
    Checks venlafaxine with desvenlafaxine on a two-drug list.
    Gives nothing, or fails if no metabolite duplication flag fires.
    """
    report = run_acceptance_check(acceptance_context, "venlafaxine 75 mg daily, desvenlafaxine 50 mg daily")
    flags = [alert for alert in report["alerts"] if alert["kind"] == "duplication" and alert["risk"] == "active_metabolite"]
    assert len(flags) == 1


def test_adderall_and_dextroamphetamine_give_an_ingredient_flag(acceptance_context: dict[str, Any]) -> None:
    """
    Takes the acceptance context.
    Checks Adderall with a dextroamphetamine-only product on a two-drug list.
    Gives nothing, or fails if no shared-ingredient duplication flag fires.
    """
    report = run_acceptance_check(acceptance_context, "adderall 20 mg daily, dextroamphetamine sulfate 10 mg daily")
    flags = [alert for alert in report["alerts"] if alert["kind"] == "duplication" and alert["risk"] == "shared_ingredient"]
    assert len(flags) == 1


def test_notice_and_no_warning_text_are_verbatim(acceptance_context: dict[str, Any]) -> None:
    """
    Takes the acceptance context.
    Checks the notice and no-warning text on a report.
    Gives nothing, or fails if either differs from the exact required wording.
    """
    report = run_acceptance_check(acceptance_context, TEST_INPUT)
    assert report["notice"] == (
        'Results reflect FDA label text as of 2026-09-21. "No warning found" does not mean a combination is safe. '
        "This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database."
    )
    assert report["no_warning_text"] == "No warning found in the labels checked."
