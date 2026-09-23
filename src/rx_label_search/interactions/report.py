"""Pure formatting of the checker's output into the Section 3.5 report shape."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from rx_label_search.interactions.grades import GRADE_ORDER, grade_fields
from rx_label_search.interactions.totals import total_mme
from rx_label_search.interactions.tiers import tier_name as lookup_tier_name
from rx_label_search.records import Alert, MedEntry
from rx_label_search.vocabulary.hierarchy import term_ids
from rx_label_search.vocabulary.terms import TERMS_BY_ID

NOTICE_TEMPLATE = (
    'Results reflect FDA label text as of {build_date}. "No warning found" does not mean a combination is safe. '
    "This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database."
)
NO_WARNING_TEXT = "No warning found in the labels checked."


def build_notice(build_date: str) -> str:
    """
    Takes the build date.
    Fills it into the fixed notice template.
    Gives the notice text.
    """
    return NOTICE_TEMPLATE.format(build_date=build_date)


def not_listed_or(values: Sequence[str]) -> str:
    """
    Takes a field's values.
    Joins them, or gives the fixed "Not listed on label" text when the field is empty.
    Gives the joined string.
    """
    return ", ".join(values) if values else "Not listed on label."


def medication_table_row(entry: MedEntry, drug: Mapping[str, Any] | None) -> dict[str, Any]:
    """
    Takes one parsed entry and its resolved drug, or None when the entry was not resolved.
    Builds one medication-table row with every Section 3.5 A column.
    Gives the row dictionary, with "Not resolved" fields when the entry has no resolved drug.
    """
    if drug is None:
        return {
            "as_entered": entry.raw_text,
            "matched_name": None,
            "generic": [],
            "base_ingredients": [],
            "brand": [],
            "fda_class": "Not listed on label.",
            "route": [],
            "dea_schedule": None,
            "strength": entry.strength_value,
            "times_per_day": entry.times_per_day,
            "daily_total": entry.daily_total,
            "daily_total_unit": entry.strength_unit,
            "pdla_tags": [],
            "label_notes": [],
            **entry_detail(entry),
        }
    record = drug["record"]
    tags = tuple(sorted(term_ids(tuple(_evidence_tuples(record["evidence"])))))
    return {
        "as_entered": entry.raw_text,
        "matched_name": drug["match"].chain,
        "generic": list(record.get("generic_names", ())),
        "base_ingredients": list(record.get("base_ingredients", ())),
        "brand": list(record.get("brand_names", ())),
        "fda_class": not_listed_or(record.get("pharm_class_epc", ())),
        "route": list(record.get("route", ())),
        "dea_schedule": record.get("schedule"),
        "strength": entry.strength_value,
        "times_per_day": entry.times_per_day,
        "daily_total": entry.daily_total,
        "daily_total_unit": entry.strength_unit,
        "pdla_tags": [{"term_id": term_id, "name": TERMS_BY_ID[term_id].name if term_id in TERMS_BY_ID else term_id} for term_id in tags],
        "label_notes": label_notes(record["evidence"]),
        "no_label": bool(record.get("no_label")),
        "profile": drug.get("profile"),
        "set_id": record.get("set_id", ""),
        **entry_detail(entry),
    }


def entry_detail(entry: MedEntry) -> dict[str, Any]:
    """
    Takes one parsed entry.
    Collects what the prescriber wrote beyond the name: brand, components with their strengths, schedule, as-needed use, release form, route, and the stated total.
    Gives the fields as a dictionary for the medication row.
    """
    return {
        "brand_typed": entry.brand_text,
        "components": [{"name": name, "strength": value, "unit": unit} for name, (value, unit) in zip(entry.components, entry.component_strengths)],
        "dose_count": entry.dose_count,
        "days_per_week": entry.days_per_week,
        "schedule_text": entry.schedule_text,
        "as_needed": entry.as_needed,
        "stated_total": entry.stated_total,
        "release_form": entry.release_form,
        "route_typed": entry.route,
    }


# The label sentences worth showing on a medication card: the boxed warning,
# the most frequent adverse reaction, dose adjustments, and the interaction
# warnings. Route, form, guide, and DEA evidence add nothing a reader needs.
LABEL_NOTE_TERM_IDS: frozenset[str] = frozenset({"T01", "T04", "T06", "T12", "T14", "T15", "T16", "T17"})


def label_notes(evidence_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, str]]:
    """
    Takes a checker record's evidence rows.
    Keeps the rows for the terms a reader wants to see on the medication card, each with its term name, the label field it came from, and its sentence.
    Gives the list of note dictionaries in evidence order, empty when none of those terms has evidence.
    """
    notes: list[dict[str, str]] = []
    for row in evidence_rows:
        term_id = row["term_id"]
        if term_id not in LABEL_NOTE_TERM_IDS or not row.get("sentence"):
            continue
        notes.append({
            "term_id": term_id,
            "name": TERMS_BY_ID[term_id].name if term_id in TERMS_BY_ID else term_id,
            "field_name": row["field_name"],
            "sentence": row["sentence"],
        })
    return notes


def _evidence_tuples(rows: Sequence[Mapping[str, Any]]) -> list[Any]:
    """
    Takes a checker record's evidence rows.
    Converts them into TermEvidence records for term_ids to read.
    Gives the list of TermEvidence.
    """
    from rx_label_search.records import TermEvidence

    return [TermEvidence(row["term_id"], row["field_name"], row["sentence"], row["rule_version"]) for row in rows]


def alert_to_dict(alert: Alert) -> dict[str, Any]:
    """
    Takes one Alert.
    Converts it to a JSON-ready dictionary with its tier name looked up and its A-to-E grade attached.
    Gives the dictionary.
    """
    return {
        **grade_fields(alert),
        "kind": alert.kind,
        "risk": alert.risk,
        "title": alert.title,
        "tier": alert.tier,
        "tier_name": alert.tier_name if alert.tier_name else lookup_tier_name(alert.tier),
        "members": [member.__dict__ for member in alert.members],
        "note": alert.note,
        "category": alert.category,
        "family": alert.family,
        "mechanism": alert.mechanism,
        "action": alert.action,
        "rulebook_rows": list(alert.rulebook_rows),
        "references": [{"label": label, "url": url} for label, url in alert.references],
        "includes": list(alert.includes),
        "rule_id": alert.rule_id,
    }


def build_check_report(check_result: Mapping[str, Any], build_date: str) -> dict[str, Any]:
    """
    Takes the checker's raw result and the build date.
    Assembles the medication table, alerts, unresolved entries, and notice.
    Gives the full report dictionary, ready for JSON or the API.
    """
    drugs_by_entry = {id(drug["entry"]): drug for drug in check_result["resolved_drugs"]}
    table = [medication_table_row(entry, drugs_by_entry.get(id(entry))) for entry in check_result["entries"]]
    alerts = sorted((alert_to_dict(alert) for alert in check_result["alerts"]), key=lambda alert: -GRADE_ORDER.index(alert["grade"]))
    totals = list(check_result.get("molecule_totals", ()))
    return {
        "build_date": build_date,
        "medication_table": table,
        "molecule_totals": totals,
        "total_mme": total_mme(totals),
        "alerts": alerts,
        "unresolved_entries": check_result["unresolved_entries"],
        "no_warning_text": NO_WARNING_TEXT,
        "notice": build_notice(build_date),
    }
