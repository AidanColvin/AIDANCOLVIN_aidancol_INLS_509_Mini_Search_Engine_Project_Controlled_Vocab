"""Runs the blind interaction-screen fixture through POST /api/check and scores the answers against its key.

Standard library only. Every request, its exact text, and its raw response are kept in the
JSON sidecar; the markdown report shows the scored view. Nothing is fabricated: an HTTP or
network failure is recorded as the result for that request.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_KEY = REPO_ROOT / "data" / "reference" / "drug_interaction_screen_fixture.json"
DEFAULT_OUT_MD = REPO_ROOT / "docs" / "interaction-validation.md"
DEFAULT_OUT_JSON = REPO_ROOT / "docs" / "interaction-validation.json"
CHECK_PATH = "/api/check"
DEFAULT_DELAY_SECONDS = 0.25
DEFAULT_TIMEOUT_SECONDS = 60.0
PRIMARY_VARIANT = "newline"
VARIANTS: tuple[tuple[str, str, bool], ...] = (
    ("newline", "\n", False),
    ("comma", ", ", False),
    ("semicolon", "; ", False),
    ("newline_reversed", "\n", True),
)

# Fixture category -> alert risks that count as the equivalent category.
CATEGORY_MAP: dict[str, tuple[str, ...]] = {
    "serotonin syndrome": ("T14",),
    "CNS depression": ("T15",),
    "respiratory depression": ("T15",),
    "QT prolongation": ("T16",),
    "duplicate entry": ("shared_ingredient", "active_metabolite"),
    "duplicate therapy": ("shared_ingredient", "active_metabolite"),
}
CONTRAINDICATED_RISK = "T17"
RISK_LABELS: dict[str, str] = {
    "T14": "serotonin syndrome risk (T14)",
    "T15": "CNS depression risk (T15)",
    "T16": "QT prolongation risk (T16)",
    "T17": "contraindicated combination (T17)",
    "shared_ingredient": "shared ingredient (duplicate entry / duplicate therapy)",
    "active_metabolite": "active metabolite pair (duplicate therapy)",
}
# Alert tier -> fixture severity. None is the tier of every duplication flag.
SEVERITY_BY_TIER: dict[int | None, str] = {1: "contraindicated", 2: "major", 3: "major", 4: "moderate", None: "minor"}
SEVERITY_BY_GRADE: dict[str, str] = {"E": "contraindicated", "D": "major", "C": "moderate", "B": "moderate", "A": "minor"}
SEVERITY_ORDER: tuple[str, ...] = ("contraindicated", "major", "moderate", "minor")
SEVERITY_RANK: dict[str, int] = {"contraindicated": 0, "major": 1, "moderate": 2, "minor": 3}
MODERATE_RANK = SEVERITY_RANK["moderate"]

CAUSE_UNSUPPORTED = "category outside the checker's rules"
CAUSE_UNRESOLVED = "drug unresolved"
CAUSE_NO_ALERT = "drugs resolved but no alert"
RESULT_HIT = "HIT"
RESULT_PARTIAL = "PARTIAL"
RESULT_MISS = "MISS"

RELEASE_FORM_WORDS = frozenset({"er", "ir", "xr", "xl", "sr", "dr", "cr", "la", "cd", "mixed", "salts"})
NAME_PUNCTUATION = re.compile(r"[#()\[\],;:]+")
GENERIC_PART_SPLIT = re.compile(r"\s*(?:,|\band\b|/)\s*", re.IGNORECASE)
AMOUNT = re.compile(r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(mcg/h|mcg|mg|g|meq|units?)\b", re.IGNORECASE)
UNIT_NAMES: dict[str, str] = {"mcg/h": "mcg/h", "mcg": "mcg", "mg": "mg", "g": "g", "meq": "mEq", "unit": "units", "units": "units"}
MASS_TO_MG: dict[str, float] = {"mcg": 0.001, "mg": 1.0, "g": 1000.0}
NOT_COMPARABLE_MARKERS = ("per week", "/week", "no single daily number", "per episode", "moiety")
PARENTHETICAL = re.compile(r"\([^)]*\)")
PER_COMPONENT_AMOUNTS = re.compile(r"^\s*[\d,.]+\s*[a-zA-Z/]+\s*/\s*[\d,.]+", re.IGNORECASE)
SNF_SEVERITY_SUFFIX = re.compile(r"\bat moderate or above\b", re.IGNORECASE)
SNF_PAIR_SPLIT = re.compile(r"\s+(?:with|\+|and)\s+", re.IGNORECASE)
SENTENCE_PREVIEW_CHARS = 180


@dataclass(frozen=True)
class RequestResult:
    """One POST /api/check call: what was sent and exactly what came back."""

    variant: str
    text: str
    http_status: int | None
    elapsed_seconds: float
    error: str | None
    response: dict[str, Any] | None


@dataclass(frozen=True)
class MemberNames:
    """One alert member with every name the medication table gives it."""

    drug_name: str
    section: str
    sentence: str
    names: tuple[str, ...]


@dataclass
class ExpectedScore:
    """How one expected item scored against the primary variant's alerts."""

    drugs: list[str]
    category: str
    severity: str
    why: str
    supported: bool
    allowed_risks: list[str]
    result: str
    cause: str | None
    resolved: bool
    unresolved_drugs: list[str]
    alert_title: str | None = None
    alert_risk: str | None = None
    alert_tier: int | None = None
    alert_severity: str | None = None
    alert_grade: str | None = None
    label_sentence: str | None = None
    source_drug: str | None = None
    source_section: str | None = None
    covering_alerts: list[str] = field(default_factory=list)


def read_json_file(path: Path) -> Any:
    """
    Takes a file path.
    Reads and decodes it as UTF-8 JSON.
    Gives the decoded value, or raises FileNotFoundError or json.JSONDecodeError.
    """
    return json.loads(path.read_text(encoding="utf-8"))


def medication_entry_text(medication: dict[str, Any]) -> str:
    """
    Takes one fixture medication with brand, generic, strength, and frequency.
    Writes it the way a US prescriber types a line: brand when present, else the generic as written, then the strength, then the frequency as written.
    Gives the entry text with single spaces between the parts.
    """
    brand = medication.get("brand")
    label_text = str(brand) if brand else str(medication.get("generic", ""))
    parts = [label_text, str(medication.get("strength", "")), str(medication.get("frequency", ""))]
    return " ".join(part for part in parts if part.strip())


def variant_text(entries: list[str], separator: str, reverse: bool) -> str:
    """
    Takes the per-medication entry texts, the separator to join them with, and whether to reverse their order.
    Joins them into one request body text.
    Gives the medication text for one variant.
    """
    ordered = list(reversed(entries)) if reverse else list(entries)
    return separator.join(ordered)


def error_text(error: BaseException) -> str:
    """
    Takes an exception raised while requesting or decoding.
    Names its class and message.
    Gives a one-line description.
    """
    return f"{error.__class__.__name__}: {error}"


def post_check(base_url: str, text: str, timeout_seconds: float, variant: str) -> RequestResult:
    """
    Takes the API base URL, the medication text, the timeout, and the variant name.
    Sends POST /api/check with use_rxnorm true and decodes the JSON reply.
    Gives a RequestResult carrying the response, or the HTTP status and error text when the request or decoding fails.
    """
    body = json.dumps({"medications": text, "use_rxnorm": True}).encode("utf-8")
    request = urllib.request.Request(base_url.rstrip("/") + CHECK_PATH, data=body, headers={"Content-Type": "application/json"}, method="POST")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as reply:
            payload = json.loads(reply.read().decode("utf-8"))
            return RequestResult(variant, text, reply.status, time.monotonic() - started, None, payload)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        return RequestResult(variant, text, error.code, time.monotonic() - started, f"HTTP {error.code}: {detail}", None)
    except (urllib.error.URLError, OSError, ValueError) as error:
        return RequestResult(variant, text, None, time.monotonic() - started, error_text(error), None)


def run_variants(base_url: str, entries: list[str], delay_seconds: float, timeout_seconds: float) -> dict[str, RequestResult]:
    """
    Takes the API base URL, one list's entry texts, the pause between requests, and the timeout.
    Sends the four separator and order variants one after another with the pause between them.
    Gives the results keyed by variant name.
    """
    results: dict[str, RequestResult] = {}
    for index, (variant, separator, reverse) in enumerate(VARIANTS):
        if index > 0:
            time.sleep(delay_seconds)
        results[variant] = post_check(base_url, variant_text(entries, separator, reverse), timeout_seconds, variant)
    return results


def normalize_token(text: str) -> tuple[str, ...]:
    """
    Takes a drug name from the fixture or the checker.
    Lowercases it, strips punctuation, and drops release-form words such as ER, XR, and "mixed salts".
    Gives the remaining words as a tuple, empty for a blank name.
    """
    cleaned = NAME_PUNCTUATION.sub(" ", text.lower())
    return tuple(word for word in cleaned.split() if word not in RELEASE_FORM_WORDS)


def tokens_match(first: tuple[str, ...], second: tuple[str, ...]) -> bool:
    """
    Takes two normalized word tuples.
    Checks whether they are equal or one is a leading-word prefix of the other, so "lithium" matches "lithium carbonate" and "naproxen sodium" matches "naproxen".
    Gives True on a match, False when either is empty or neither is a prefix of the other.
    """
    if not first or not second:
        return False
    shorter, longer = (first, second) if len(first) <= len(second) else (second, first)
    return longer[: len(shorter)] == shorter


def expected_components(drug: str) -> tuple[str, ...]:
    """
    Takes one expected drug string, which may be a combination written "a/b".
    Splits it on the slash.
    Gives the trimmed components, one for a plain drug.
    """
    return tuple(part.strip() for part in drug.split("/") if part.strip())


def drug_matches_names(drug: str, names: tuple[str, ...]) -> bool:
    """
    Takes one expected drug string and a checker name list.
    Checks whether any component of the drug matches any checker name under the token rule.
    Gives True when at least one component matches, False otherwise.
    """
    component_tokens = [normalize_token(component) for component in expected_components(drug)]
    name_tokens = [normalize_token(candidate) for candidate in names]
    return any(tokens_match(component, candidate) for component in component_tokens for candidate in name_tokens)


def split_generic_parts(text: str) -> tuple[str, ...]:
    """
    Takes a label generic name such as "DEXTROAMPHETAMINE SACCHARATE, AMPHETAMINE ASPARTATE AND AMPHETAMINE SULFATE".
    Splits it at commas, the word "and", and slashes.
    Gives the trimmed parts, one part for a single-ingredient name.
    """
    return tuple(part.strip() for part in GENERIC_PART_SPLIT.split(text) if part.strip())


def row_names(row: dict[str, Any]) -> tuple[str, ...]:
    """
    Takes one medication-table row.
    Collects its entered text, matched-name chain, generic parts, base ingredients, and brands.
    Gives the tuple of names, lowercased and de-duplicated.
    """
    chain = row.get("matched_name") or []
    collected: list[str] = [str(row.get("as_entered", ""))]
    collected.extend(str(link) for link in chain)
    for link in chain:
        collected.extend(split_generic_parts(str(link)))
    for generic in row.get("generic") or []:
        collected.extend(split_generic_parts(str(generic)))
    collected.extend(str(base) for base in row.get("base_ingredients") or [])
    collected.extend(str(brand) for brand in row.get("brand") or [])
    return tuple(dict.fromkeys(candidate.lower() for candidate in collected if candidate.strip()))


def resolved_rows(response: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Takes one check response.
    Keeps the medication-table rows whose entry resolved to a label.
    Gives the list of resolved rows, empty when nothing resolved.
    """
    return [row for row in response.get("medication_table", []) if row.get("matched_name")]


def rows_for_member(member: dict[str, Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Takes one alert member and the resolved medication-table rows.
    Finds the rows whose matched-name chain, entered text, brand, or generic carries the member's drug name.
    Gives the matching rows, empty when the member's name is not in the table.
    """
    wanted = str(member.get("drug_name", "")).lower()
    found: list[dict[str, Any]] = []
    for row in rows:
        chain = [str(link).lower() for link in row.get("matched_name") or []]
        direct = [str(row.get("as_entered", "")).lower(), *chain]
        direct.extend(str(brand).lower() for brand in row.get("brand") or [])
        direct.extend(str(generic).lower() for generic in row.get("generic") or [])
        if wanted in direct:
            found.append(row)
    return found


def member_names(member: dict[str, Any], rows: list[dict[str, Any]]) -> MemberNames:
    """
    Takes one alert member and the resolved medication-table rows.
    Attaches every name the table knows for that member's drug, plus the member's own name.
    Gives the MemberNames record.
    """
    names: list[str] = [str(member.get("drug_name", "")).lower()]
    for row in rows_for_member(member, rows):
        names.extend(row_names(row))
    return MemberNames(str(member.get("drug_name", "")), str(member.get("section", "")), str(member.get("sentence", "")), tuple(dict.fromkeys(names)))


def alert_members(alert: dict[str, Any], rows: list[dict[str, Any]]) -> tuple[MemberNames, ...]:
    """
    Takes one alert and the resolved medication-table rows.
    Builds the MemberNames for each of its members.
    Gives the tuple in member order.
    """
    return tuple(member_names(member, rows) for member in alert.get("members", []))


def assign_members(drugs: list[str], members: tuple[MemberNames, ...], used: frozenset[int]) -> bool:
    """
    Takes the expected drugs still to cover, the alert's members, and the member indexes already used.
    Tries to give every remaining drug its own distinct matching member, backtracking as needed.
    Gives True when every drug can be covered by a distinct member, False otherwise.
    """
    if not drugs:
        return True
    first, rest = drugs[0], drugs[1:]
    for index, member in enumerate(members):
        if index in used or not drug_matches_names(first, member.names):
            continue
        if assign_members(rest, members, used | {index}):
            return True
    return False


def alert_covers(drugs: list[str], members: tuple[MemberNames, ...]) -> bool:
    """
    Takes the expected drugs of one item and an alert's members.
    Checks whether distinct members cover every listed drug, counting a repeated drug once per repeat.
    Gives True when the alert covers the item, False otherwise.
    """
    return assign_members(list(drugs), members, frozenset())


def alert_severity(alert: dict[str, Any]) -> str:
    """
    Takes one alert.
    Maps its A-to-E grade to the fixture severity scale, falling back to its tier when the response predates grades.
    Gives the severity word, "minor" for an ungraded alert with a null tier.
    """
    grade = alert.get("grade")
    if isinstance(grade, str) and grade in SEVERITY_BY_GRADE:
        return SEVERITY_BY_GRADE[grade]
    return SEVERITY_BY_TIER.get(alert.get("tier"), "minor")


def allowed_risks_for(category: str, severity: str) -> tuple[str, ...]:
    """
    Takes an expected item's category and severity.
    Looks up the equivalent alert risks, adding T17 when the item is contraindicated.
    Gives the tuple of risks, empty when the category is outside the checker's rules and the item is not contraindicated.
    """
    risks = list(CATEGORY_MAP.get(category, ()))
    if severity == "contraindicated":
        risks.append(CONTRAINDICATED_RISK)
    return tuple(risks)


def drug_is_resolved(drug: str, rows: list[dict[str, Any]]) -> bool:
    """
    Takes one expected drug string and the resolved medication-table rows.
    Checks whether any resolved row carries a name matching the drug.
    Gives True when the drug resolved, False otherwise.
    """
    return any(drug_matches_names(drug, row_names(row)) for row in rows)


def drug_fully_matches_row(drug: str, row: dict[str, Any]) -> bool:
    """
    Takes one expected drug string and one resolved medication-table row.
    Checks whether every component of the drug, not just one, matches a name on the row.
    Gives True for a full match, False otherwise.
    """
    names = row_names(row)
    return all(drug_matches_names(component, names) for component in expected_components(drug))


def assign_rows(drugs: list[str], rows: list[dict[str, Any]], full_only: bool, taken: set[int]) -> set[int]:
    """
    Takes the expected drugs, the resolved rows, whether only full matches count, and the row indexes already taken.
    Gives each drug in order the first free row that matches it, taking that row.
    Gives the set of drug indexes that received a row.
    """
    covered: set[int] = set()
    for drug_index, drug in enumerate(drugs):
        for row_index, row in enumerate(rows):
            if row_index in taken:
                continue
            if drug_fully_matches_row(drug, row) or (not full_only and drug_matches_names(drug, row_names(row))):
                taken.add(row_index)
                covered.add(drug_index)
                break
    return covered


def unresolved_expected_drugs(drugs: list[str], rows: list[dict[str, Any]]) -> list[str]:
    """
    Takes the expected drugs of one item and the resolved medication-table rows.
    Gives each drug its own distinct resolved row, full matches first so "fluoxetine" claims the Prozac row before "olanzapine/fluoxetine" can borrow it, then any-component matches.
    Gives the drugs left without a row, in order, empty when every drug has one.
    """
    taken: set[int] = set()
    covered = assign_rows(drugs, rows, True, taken)
    remaining = [(index, drug) for index, drug in enumerate(drugs) if index not in covered]
    second = assign_rows([drug for _, drug in remaining], rows, False, taken)
    return [drug for position, (_, drug) in enumerate(remaining) if position not in second]


def evidence_member(members: tuple[MemberNames, ...]) -> MemberNames | None:
    """
    Takes an alert's members.
    Finds the first member that cites a label sentence.
    Gives that member, or None when no member carries a sentence.
    """
    for member in members:
        if member.sentence:
            return member
    return None


def attach_alert(score: ExpectedScore, alert: dict[str, Any], members: tuple[MemberNames, ...]) -> None:
    """
    Takes an expected score, the alert chosen for it, and that alert's members.
    Copies the alert's title, risk, tier, severity, and first cited sentence onto the score.
    Gives nothing.
    """
    score.alert_title = str(alert.get("title", ""))
    score.alert_risk = str(alert.get("risk", ""))
    score.alert_tier = alert.get("tier")
    score.alert_severity = alert_severity(alert)
    grade = alert.get("grade")
    score.alert_grade = grade if isinstance(grade, str) else None
    cited = evidence_member(members)
    if cited is None:
        return
    score.label_sentence = cited.sentence
    score.source_drug = cited.drug_name
    score.source_section = cited.section


def choose_alert(covering: list[tuple[dict[str, Any], tuple[MemberNames, ...]]], allowed: tuple[str, ...], severity: str) -> tuple[str, dict[str, Any], tuple[MemberNames, ...]]:
    """
    Takes the alerts covering an item's drugs, the allowed risks, and the expected severity.
    Picks a HIT when one alert has an allowed risk at the expected severity or higher, else a PARTIAL preferring an allowed risk.
    Gives (result, alert, members).
    """
    for alert, members in covering:
        if alert.get("risk") in allowed and SEVERITY_RANK[alert_severity(alert)] <= SEVERITY_RANK[severity]:
            return RESULT_HIT, alert, members
    for alert, members in covering:
        if alert.get("risk") in allowed:
            return RESULT_PARTIAL, alert, members
    alert, members = covering[0]
    return RESULT_PARTIAL, alert, members


def score_expected_item(item: dict[str, Any], response: dict[str, Any]) -> ExpectedScore:
    """
    Takes one expected item from the answer key and the primary variant's check response.
    Applies the category map, the member-cover rule, and the severity rule to decide HIT, PARTIAL, or MISS with its cause.
    Gives the ExpectedScore.
    """
    drugs = [str(drug) for drug in item.get("drugs", [])]
    category, severity = str(item.get("category", "")), str(item.get("severity", "")).lower()
    rows = resolved_rows(response)
    allowed = allowed_risks_for(category, severity)
    unresolved = unresolved_expected_drugs(drugs, rows)
    score = ExpectedScore(drugs, category, severity, str(item.get("why", "")), bool(allowed), list(allowed), RESULT_MISS, None, not unresolved, unresolved)
    covering = [(alert, members) for alert in response.get("alerts", []) if alert_covers(drugs, members := alert_members(alert, rows))]
    score.covering_alerts = [f"{alert.get('risk')} {alert_severity(alert)}: {alert.get('title')}" for alert, _ in covering]
    if not allowed:
        score.cause = CAUSE_UNSUPPORTED
        return score
    if covering:
        score.result, alert, members = choose_alert(covering, allowed, severity)
        attach_alert(score, alert, members)
        return score
    score.cause = CAUSE_UNRESOLVED if unresolved else CAUSE_NO_ALERT
    return score


def parse_should_not_flag(entry: str) -> tuple[str, ...]:
    """
    Takes one should_not_flag string such as "atorvastatin", "levothyroxine with ibuprofen", or "any pair at moderate or above; ...".
    Strips parentheticals and the severity phrase, then reads it as the whole list, a pair, or one drug.
    Gives ("*",) for the whole list, two names for a pair, or one name for a single drug.
    """
    cleaned = SNF_SEVERITY_SUFFIX.sub(" ", PARENTHETICAL.sub(" ", entry)).split(";")[0].strip(" .")
    if cleaned.lower().startswith("any pair"):
        return ("*",)
    parts = tuple(part.strip() for part in SNF_PAIR_SPLIT.split(cleaned) if part.strip())
    return parts if len(parts) == 2 else (cleaned,)


def alert_signature(alert: dict[str, Any]) -> str:
    """
    Takes one alert.
    Joins its risk with the sorted lowercase member drug names.
    Gives the signature string used for cross-variant comparison.
    """
    names = sorted(str(member.get("drug_name", "")).lower() for member in alert.get("members", []))
    return f"{alert.get('risk')}|" + ", ".join(names)


def false_positive_reason(alert: dict[str, Any], members: tuple[MemberNames, ...], rules: list[tuple[str, ...]], control_list: bool) -> str | None:
    """
    Takes one moderate-or-higher alert, its members, the parsed should_not_flag rules, and whether the list expects nothing.
    Checks the control rule, then each whole-list, pair, or single-drug rule against the members.
    Gives the rule text that makes the alert a false positive, or None when no rule applies.
    """
    if control_list:
        return "control list: answer key expects nothing"
    for rule in rules:
        if rule == ("*",):
            return "any pair at moderate or above"
        if len(rule) == 2 and len(members) == 2 and alert_covers(list(rule), members):
            return " with ".join(rule)
        if len(rule) == 1 and any(drug_matches_names(rule[0], member.names) for member in members):
            return rule[0]
    return None


def score_false_positives(answer: dict[str, Any], response: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Takes one list's answer key and the primary variant's response.
    Flags every moderate-or-higher alert that a should_not_flag rule or the control-list rule forbids.
    Gives the list of false-positive records with the alert title, severity, and the rule hit.
    """
    rules = [parse_should_not_flag(str(entry)) for entry in answer.get("should_not_flag", [])]
    control_list = not answer.get("expected")
    rows = resolved_rows(response)
    found: list[dict[str, Any]] = []
    for alert in response.get("alerts", []):
        if SEVERITY_RANK[alert_severity(alert)] > MODERATE_RANK:
            continue
        reason = false_positive_reason(alert, alert_members(alert, rows), rules, control_list)
        if reason is not None:
            found.append({"alert_title": alert.get("title"), "risk": alert.get("risk"), "severity": alert_severity(alert), "rule": reason})
    return found


def parse_amounts(text: str) -> list[tuple[float, str]]:
    """
    Takes an answer-key total string such as "1,600 mg / 320 mg" or "100 mcg = 0.1 mg".
    Reads every number-with-unit in order, dropping thousands separators.
    Gives the list of (value, unit) pairs, empty when the text has none.
    """
    return [(float(value.replace(",", "")), UNIT_NAMES[unit.lower()]) for value, unit in AMOUNT.findall(text)]


def rows_for_component(component: str, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Takes one molecule component name and the resolved medication-table rows.
    Finds the rows whose base ingredients or generic parts match the component.
    Gives the matching rows, empty when none match.
    """
    wanted = normalize_token(component)
    found: list[dict[str, Any]] = []
    for row in rows:
        names = [str(base) for base in row.get("base_ingredients") or []]
        for generic in row.get("generic") or []:
            names.extend(split_generic_parts(str(generic)))
        if any(tokens_match(wanted, normalize_token(candidate)) for candidate in names):
            found.append(row)
    return found


def sum_row_totals(rows: list[dict[str, Any]]) -> tuple[float | None, str | None, list[str]]:
    """
    Takes the medication-table rows for one molecule.
    Sums their daily totals, converting mass units to mg when they differ.
    Gives (total, unit, notes), with None values when no row carries a total or the units cannot be reconciled.
    """
    totals = [(float(row["daily_total"]), str(row.get("daily_total_unit") or "")) for row in rows if row.get("daily_total") is not None]
    notes = [f'no daily total for "{row.get("as_entered")}"' for row in rows if row.get("daily_total") is None]
    if not totals:
        return None, None, notes
    units = {unit for _, unit in totals}
    if len(units) == 1:
        return sum(value for value, _ in totals), totals[0][1], notes
    if units <= MASS_TO_MG.keys():
        return sum(value * MASS_TO_MG[unit] for value, unit in totals), "mg", [*notes, "mixed mass units converted to mg"]
    return None, None, [*notes, f"units cannot be reconciled: {sorted(units)}"]


def amounts_equal(expected_value: float, expected_unit: str, actual_value: float, actual_unit: str) -> bool:
    """
    Takes an expected amount with its unit and an actual amount with its unit.
    Compares them, converting between mcg, mg, and g when both are mass units.
    Gives True when they agree within a tiny tolerance, False otherwise.
    """
    if expected_unit in MASS_TO_MG and actual_unit in MASS_TO_MG:
        return abs(expected_value * MASS_TO_MG[expected_unit] - actual_value * MASS_TO_MG[actual_unit]) < 1e-6
    return expected_unit == actual_unit and abs(expected_value - actual_value) < 1e-6


def expected_amount(expected_text: str, amounts: list[tuple[float, str]], index: int) -> tuple[float, str] | None:
    """
    Takes the key's totals text, its parsed amounts, and a component index.
    Picks the index-th amount when the text lists one amount per component as "a / b", otherwise the first amount for every component.
    Gives the (value, unit) pair, or None when the text has no amount.
    """
    if not amounts:
        return None
    if PER_COMPONENT_AMOUNTS.match(expected_text) and index < len(amounts):
        return amounts[index]
    return amounts[0]


def score_total(molecule: str, expected_text: str, response: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Takes one answer-key totals entry and the primary variant's response.
    Compares the checker's summed daily total per molecule component with the expected amount, marking weekly, per-episode, and unnamed-molecule entries as not comparable.
    Gives one record per component with the result match, mismatch, no_total, or not_comparable.
    """
    amounts = parse_amounts(expected_text)
    rows = resolved_rows(response)
    records: list[dict[str, Any]] = []
    for index, component in enumerate(expected_components(molecule)):
        matched_rows = rows_for_component(component, rows)
        actual_value, actual_unit, notes = sum_row_totals(matched_rows)
        expected = expected_amount(expected_text, amounts, index)
        record: dict[str, Any] = {"molecule": molecule, "component": component, "expected_text": expected_text, "expected": expected, "checker_total": actual_value, "checker_unit": actual_unit, "rows": [row.get("as_entered") for row in matched_rows], "notes": notes}
        if any(marker in expected_text.lower() for marker in NOT_COMPARABLE_MARKERS) or expected is None:
            record["result"] = "not_comparable"
        elif not matched_rows:
            record["result"] = "no_total"
            record["notes"] = [*notes, "no resolved row matches this molecule"]
        elif actual_value is None:
            record["result"] = "no_total"
        else:
            record["result"] = "match" if amounts_equal(expected[0], expected[1], actual_value, actual_unit or "") else "mismatch"
        records.append(record)
    return records


def score_totals(answer: dict[str, Any], response: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Takes one list's answer key and the primary variant's response.
    Scores every totals entry.
    Gives the flat list of per-component total records, empty when the key has no totals.
    """
    records: list[dict[str, Any]] = []
    for molecule, expected_text in (answer.get("totals") or {}).items():
        records.extend(score_total(str(molecule), str(expected_text), response))
    return records


def variant_consistency(results: dict[str, RequestResult]) -> dict[str, Any]:
    """
    Takes the four variant results for one list.
    Compares each variant's alert signature set with the primary variant's.
    Gives a record with identical_across_variants and, per variant, the missing and extra signatures or the request error.
    """
    primary = results[PRIMARY_VARIANT]
    primary_set = {alert_signature(alert) for alert in (primary.response or {}).get("alerts", [])} if primary.response else set()
    per_variant: dict[str, Any] = {}
    identical = primary.response is not None
    for variant, result in results.items():
        if result.response is None:
            per_variant[variant] = {"identical": False, "error": result.error, "missing": [], "extra": []}
            identical = False
            continue
        current = {alert_signature(alert) for alert in result.response.get("alerts", [])}
        per_variant[variant] = {"identical": current == primary_set, "error": None, "missing": sorted(primary_set - current), "extra": sorted(current - primary_set)}
        identical = identical and current == primary_set
    return {"identical_across_variants": identical, "primary_signatures": sorted(primary_set), "variants": per_variant}


def unresolved_lines(response: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Takes one check response.
    Reads its unresolved entries with their reasons and candidates.
    Gives the list of records, empty when everything resolved.
    """
    return [{"raw_text": entry.get("raw_text"), "status": entry.get("status"), "reason": entry.get("reason"), "candidates": entry.get("candidates", [])} for entry in response.get("unresolved_entries", [])]


def score_list(medication_list: dict[str, Any], answer: dict[str, Any], results: dict[str, RequestResult]) -> dict[str, Any]:
    """
    Takes one fixture list, its answer key, and its four request results.
    Scores the expected items, false positives, totals, and cross-variant consistency against the primary variant.
    Gives the per-list record, with only the request results when the primary request failed.
    """
    primary = results[PRIMARY_VARIANT]
    record: dict[str, Any] = {
        "id": medication_list["id"],
        "theme": answer.get("theme", ""),
        "requests": {variant: asdict(result) for variant, result in results.items()},
        "primary_error": primary.error,
        "expected": [],
        "false_positives": [],
        "totals": [],
        "unresolved": [],
        "consistency": variant_consistency(results),
    }
    if primary.response is None:
        return record
    record["expected"] = [asdict(score_expected_item(item, primary.response)) for item in answer.get("expected", [])]
    record["false_positives"] = score_false_positives(answer, primary.response)
    record["totals"] = score_totals(answer, primary.response)
    record["unresolved"] = unresolved_lines(primary.response)
    return record


def graded_pairs(lists: list[dict[str, Any]]) -> list[tuple[str, str]]:
    """
    Takes every scored list record.
    Collects (expected severity, tool severity) for each expected item an alert covered with a supported category.
    Gives the list of pairs, empty when no item was covered.
    """
    return [
        (item["severity"], item["alert_severity"])
        for record in lists
        for item in record["expected"]
        if item["result"] in (RESULT_HIT, RESULT_PARTIAL) and item["severity"] in SEVERITY_RANK and item["alert_severity"] in SEVERITY_RANK
    ]


def cohen_kappa(pairs: list[tuple[str, str]], labels: tuple[str, ...]) -> float | None:
    """
    Takes (rater one, rater two) label pairs and the label set.
    Computes Cohen's kappa: observed agreement corrected for the agreement expected by chance from each rater's marginals.
    Gives kappa, or None when there are no pairs or chance agreement is total.
    """
    if not pairs:
        return None
    total = len(pairs)
    observed = sum(first == second for first, second in pairs) / total
    chance = sum((sum(first == label for first, _ in pairs) / total) * (sum(second == label for _, second in pairs) / total) for label in labels)
    if chance >= 1.0:
        return None
    return (observed - chance) / (1.0 - chance)


def severity_agreement(lists: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Takes every scored list record.
    Cross-tabulates the key's severity against the tool's graded severity for covered items, with exact agreement, agreement within one level, and Cohen's kappa.
    Gives the agreement dictionary.
    """
    pairs = graded_pairs(lists)
    matrix = {expected: {tool: sum(pair == (expected, tool) for pair in pairs) for tool in SEVERITY_ORDER} for expected in SEVERITY_ORDER}
    within_one = sum(abs(SEVERITY_RANK[first] - SEVERITY_RANK[second]) <= 1 for first, second in pairs)
    kappa = cohen_kappa(pairs, SEVERITY_ORDER)
    return {
        "items": len(pairs),
        "exact": sum(first == second for first, second in pairs),
        "within_one_level": within_one,
        "tool_more_severe": sum(SEVERITY_RANK[second] < SEVERITY_RANK[first] for first, second in pairs),
        "tool_less_severe": sum(SEVERITY_RANK[second] > SEVERITY_RANK[first] for first, second in pairs),
        "cohen_kappa": None if kappa is None else round(kappa, 3),
        "matrix": matrix,
    }


def build_summary(lists: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Takes every scored list record.
    Counts expected items, hits, partials, misses by cause, false positives, totals outcomes, variant differences, and request errors.
    Gives the summary dictionary.
    """
    expected = [item for record in lists for item in record["expected"]]
    totals = [entry for record in lists for entry in record["totals"]]
    return {
        "lists": len(lists),
        "expected_items": len(expected),
        "hits": sum(item["result"] == RESULT_HIT for item in expected),
        "partials": sum(item["result"] == RESULT_PARTIAL for item in expected),
        "misses": sum(item["result"] == RESULT_MISS for item in expected),
        "misses_by_cause": {cause: sum(item["result"] == RESULT_MISS and item["cause"] == cause for item in expected) for cause in (CAUSE_UNSUPPORTED, CAUSE_UNRESOLVED, CAUSE_NO_ALERT)},
        "false_positives": sum(len(record["false_positives"]) for record in lists),
        "totals": {outcome: sum(entry["result"] == outcome for entry in totals) for outcome in ("match", "mismatch", "no_total", "not_comparable")},
        "lists_with_variant_differences": sum(not record["consistency"]["identical_across_variants"] for record in lists),
        "request_errors": sum(result["error"] is not None for record in lists for result in record["requests"].values()),
        "lists_with_unresolved_entries": sum(bool(record["unresolved"]) for record in lists),
        "severity_agreement": severity_agreement(lists),
    }


def build_date_of(lists: list[dict[str, Any]]) -> str | None:
    """
    Takes every scored list record.
    Reads the build_date from the first successful response.
    Gives the build date, or None when every request failed.
    """
    for record in lists:
        for result in record["requests"].values():
            if result["response"] is not None:
                return str(result["response"].get("build_date"))
    return None


def markdown_cell(text: Any) -> str:
    """
    Takes any cell value.
    Renders it as one-line markdown-safe text with pipes and newlines escaped.
    Gives the cell text, an empty string for None.
    """
    if text is None:
        return ""
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def preview(text: str | None) -> str:
    """
    Takes a label sentence, possibly long.
    Shortens it to the preview length with an ellipsis.
    Gives the preview, empty for None.
    """
    if not text:
        return ""
    return text if len(text) <= SENTENCE_PREVIEW_CHARS else text[: SENTENCE_PREVIEW_CHARS - 1] + "…"


def expected_row(item: dict[str, Any]) -> str:
    """
    Takes one scored expected item.
    Formats it as a markdown table row with the result, cause, alert, sentence, and source.
    Gives the row text.
    """
    result = item["result"] if item["cause"] is None else f"{item['result']} ({item['cause']})"
    if item["result"] == RESULT_PARTIAL:
        result = f"PARTIAL (got {item['alert_risk']} at {item['alert_severity']})"
    if item["result"] == RESULT_MISS and item["unresolved_drugs"] and item["cause"] != CAUSE_UNSUPPORTED:
        result += f": {', '.join(item['unresolved_drugs'])}"
    source = f"{item['source_drug']} / {item['source_section']}" if item["source_drug"] else ""
    cells = [", ".join(item["drugs"]), item["category"], item["severity"], result, item["alert_title"], preview(item["label_sentence"]), source]
    return "| " + " | ".join(markdown_cell(cell) for cell in cells) + " |"


def list_section(record: dict[str, Any]) -> list[str]:
    """
    Takes one scored list record.
    Writes its markdown section: text sent, expected-item table, unresolved line, false positives, totals, and variant consistency.
    Gives the section lines.
    """
    lines = [f"## {record['id']}: {markdown_cell(record['theme'])}", "", "Text sent (newline variant):", "", "```"]
    lines.extend(record["requests"][PRIMARY_VARIANT]["text"].splitlines())
    lines.extend(["```", ""])
    if record["primary_error"]:
        lines.extend([f"Primary request failed: {markdown_cell(record['primary_error'])}", ""])
        return lines
    lines.extend(["| Drugs | Category | Severity | Result | Alert fired | Label sentence | Source drug / section |", "| --- | --- | --- | --- | --- | --- | --- |"])
    lines.extend(expected_row(item) for item in record["expected"])
    if not record["expected"]:
        lines.append("| (control list: nothing expected) | | | | | | |")
    unresolved = "; ".join(f"{markdown_cell(entry['raw_text'])} ({entry['status']}: {markdown_cell(entry['reason'])})" for entry in record["unresolved"])
    lines.extend(["", f"Unresolved entries: {unresolved or 'none'}"])
    fps = "; ".join(f"{markdown_cell(fp['alert_title'])} [{fp['severity']}, rule: {markdown_cell(fp['rule'])}]" for fp in record["false_positives"])
    lines.append(f"False positives: {fps or 'none'}")
    for entry in record["totals"]:
        actual = f"{entry['checker_total']:g} {entry['checker_unit']}" if entry["checker_total"] is not None else "none"
        lines.append(f"Total {entry['component']}: {entry['result']} (expected {markdown_cell(entry['expected_text'])}; checker {actual})")
    consistency = record["consistency"]
    if consistency["identical_across_variants"]:
        lines.append("Variants: identical alert sets across newline, comma, semicolon, and reversed order")
    else:
        for variant, detail in consistency["variants"].items():
            if detail["identical"]:
                continue
            what = detail["error"] or f"missing {detail['missing']}; extra {detail['extra']}"
            lines.append(f"Variant {variant} differs: {markdown_cell(what)}")
    lines.append("")
    return lines


def summary_lines(summary: dict[str, Any]) -> list[str]:
    """
    Takes the summary counts.
    Writes them as markdown bullet lines.
    Gives the lines.
    """
    causes = summary["misses_by_cause"]
    totals = summary["totals"]
    return [
        f"- Lists run: {summary['lists']}",
        f"- Expected items: {summary['expected_items']}",
        f"- Hits: {summary['hits']}",
        f"- Partials: {summary['partials']}",
        f"- Misses: {summary['misses']} (unsupported category {causes[CAUSE_UNSUPPORTED]}; drug unresolved {causes[CAUSE_UNRESOLVED]}; drugs resolved but no alert {causes[CAUSE_NO_ALERT]})",
        f"- False positives: {summary['false_positives']}",
        f"- Totals: matched {totals['match']}, mismatched {totals['mismatch']}, no checker total {totals['no_total']}, not comparable {totals['not_comparable']}",
        f"- Lists with variant differences: {summary['lists_with_variant_differences']}",
        f"- Lists with unresolved entries: {summary['lists_with_unresolved_entries']}",
        f"- Request errors: {summary['request_errors']}",
        *agreement_lines(summary.get("severity_agreement")),
    ]


def agreement_lines(agreement: dict[str, Any] | None) -> list[str]:
    """
    Takes the severity-agreement dictionary, or None for an older summary.
    Writes the agreement counts and the key-by-tool severity matrix as markdown.
    Gives the lines, empty when there is no agreement data.
    """
    if not agreement:
        return []
    items = agreement["items"]
    lines = [
        "",
        "### Severity agreement (covered items)",
        "",
        f"- Items where an alert covered the expected drugs in a supported category: {items}",
        f"- Exact severity agreement: {agreement['exact']} of {items}",
        f"- Within one level: {agreement['within_one_level']} of {items}",
        f"- Tool more severe than the key: {agreement['tool_more_severe']}; less severe: {agreement['tool_less_severe']}",
        f"- Cohen's kappa: {agreement['cohen_kappa']}",
        "",
        "| Key severity \\ Tool severity | " + " | ".join(SEVERITY_ORDER) + " |",
        "| --- | " + " | ".join("---" for _ in SEVERITY_ORDER) + " |",
    ]
    lines.extend(f"| {expected} | " + " | ".join(str(agreement["matrix"][expected][tool]) for tool in SEVERITY_ORDER) + " |" for expected in SEVERITY_ORDER)
    return lines


def rules_lines() -> list[str]:
    """
    Takes no arguments.
    Writes the category map, the severity map, and the scoring rules as markdown.
    Gives the lines.
    """
    lines = ["### Category map", "", "| Fixture category | Counts as |", "| --- | --- |"]
    lines.extend(f"| {category} | {', '.join(RISK_LABELS[risk] for risk in risks)} |" for category, risks in CATEGORY_MAP.items())
    lines.append(f"| any category at severity contraindicated | also {RISK_LABELS[CONTRAINDICATED_RISK]} |")
    lines.append("| every other fixture category | unsupported by this checker's rule set; scored as a miss with cause \"category outside the checker's rules\" |")
    lines.extend(["", "### Severity map (alert grade to fixture severity)", "", "| Grade | Severity |", "| --- | --- |"])
    lines.extend(f"| {grade} | {severity} |" for grade, severity in SEVERITY_BY_GRADE.items())
    lines.append("")
    lines.append("Grades follow the correspondence Pinkoh et al. (2023) give between Lexicomp and a four-level scale: X contraindicated, D major, C moderate, B minor. This tool's E, D, C and B, and A line up with Lexicomp X, D, C, and B. A response without grades falls back to the tier map: 1 contraindicated, 2 and 3 major, 4 moderate, none minor.")
    lines.extend([
        "",
        "### Scoring rules",
        "",
        "- Scoring uses the newline-separated, key-order variant. The other three variants are compared to it for consistency only.",
        "- HIT: one alert's members cover every expected drug (a repeated drug needs a distinct member per repeat) under an equivalent category at the expected severity or higher.",
        "- Drug names match on lowercase generic, base-ingredient, brand, and matched-name-chain names from the medication table. Release-form words (ER, XR, IR, SR, DR, CR, LA, CD, XL, \"mixed salts\") are dropped, and a name matches when it equals the other or is a leading-word prefix of it, so \"lithium\" matches \"lithium carbonate\". A combination \"a/b\" is satisfied by either component.",
        "- PARTIAL: an alert covers every expected drug but its category or severity differs; the actual risk and severity are shown.",
        "- MISS causes, in order: category outside the checker's rules; drug unresolved (a listed drug has no resolved medication-table row); drugs resolved but no alert.",
        "- FALSE POSITIVE: a moderate-or-higher alert whose two members are exactly a should_not_flag pair, a moderate-or-higher alert that includes a single should_not_flag drug, any moderate-or-higher alert when should_not_flag says \"any pair\", and any moderate-or-higher alert on a list whose expected list is empty.",
        "- Totals: the checker's daily_total is summed across resolved rows sharing the molecule and compared with the first amount in the key's text, or with the matching amount when the key writes one per component as \"a / b\" (mcg, mg, and g are interconverted). Weekly, per-episode, moiety, \"no single daily number\" entries, and a key total with no amount this rule can parse (for example a unit outside mcg/h, mcg, mg, g, mEq, units, such as \"about 70 MME\") are recorded as not comparable.",
        "",
    ])
    return lines


def render_markdown(report: dict[str, Any]) -> str:
    """
    Takes the full report dictionary.
    Writes the markdown document: header, rules, summary, and one section per list.
    Gives the markdown text.
    """
    lines = [
        "# Interaction checker validation",
        "",
        f"- Run label: {markdown_cell(report['label'])}",
        f"- Base URL: {report['base_url']}",
        f"- Build date reported: {report['build_date'] or 'none (every request failed)'}",
        f"- Timestamp: {report['timestamp']}",
        f"- Key: {report['key_path']} ({markdown_cell(report['key_fixture'])})",
        "",
        "## Rules",
        "",
        *rules_lines(),
        "## Summary",
        "",
        *summary_lines(report["summary"]),
        "",
    ]
    for record in report["lists"]:
        lines.extend(list_section(record))
    return "\n".join(lines).rstrip() + "\n"


def run_harness(key: dict[str, Any], base_url: str, delay_seconds: float, timeout_seconds: float, only: frozenset[str]) -> list[dict[str, Any]]:
    """
    Takes the fixture, the API base URL, the pause between requests, the timeout, and an optional set of list ids to keep.
    Sends every list in its four variants and scores it, printing one progress line per list.
    Gives the scored list records in fixture order.
    """
    answers = key.get("answer_key", {})
    scored: list[dict[str, Any]] = []
    for medication_list in key.get("lists", []):
        list_id = str(medication_list["id"])
        if only and list_id not in only:
            continue
        entries = [medication_entry_text(medication) for medication in medication_list.get("medications", [])]
        results = run_variants(base_url, entries, delay_seconds, timeout_seconds)
        record = score_list(medication_list, answers.get(list_id, {}), results)
        counts = {result: sum(item["result"] == result for item in record["expected"]) for result in (RESULT_HIT, RESULT_PARTIAL, RESULT_MISS)}
        sys.stderr.write(f"{list_id}: {counts} error={record['primary_error']}\n")
        sys.stderr.flush()
        scored.append(record)
        time.sleep(delay_seconds)
    return scored


def build_report(key: dict[str, Any], key_path: Path, base_url: str, label: str, lists: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Takes the fixture, its path, the base URL, the run label, and the scored lists.
    Assembles the report with the rules, summary, and timestamp.
    Gives the report dictionary that both output files are written from.
    """
    return {
        "label": label,
        "base_url": base_url,
        "build_date": build_date_of(lists),
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "key_path": str(key_path),
        "key_fixture": str(key.get("fixture", "")),
        "category_map": {category: list(risks) for category, risks in CATEGORY_MAP.items()},
        "contraindicated_also_matches": CONTRAINDICATED_RISK,
        "severity_map": dict(SEVERITY_BY_GRADE),
        "summary": build_summary(lists),
        "lists": lists,
    }


def write_outputs(report: dict[str, Any], out_md: Path, out_json: Path) -> None:
    """
    Takes the report and the two output paths.
    Writes the markdown report and the JSON sidecar, creating parent directories.
    Gives nothing.
    """
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(report), encoding="utf-8")
    out_json.write_text(json.dumps(report, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args(argv: list[str]) -> argparse.Namespace:
    """
    Takes the command-line arguments without the program name.
    Parses the key, base URL, output paths, label, delay, timeout, and optional list filter.
    Gives the parsed namespace, or exits with usage text on a bad flag.
    """
    parser = argparse.ArgumentParser(description="Validate POST /api/check against the interaction-screen fixture.")
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY, help="fixture with lists and answer_key")
    parser.add_argument("--base-url", required=True, help="API origin, e.g. http://127.0.0.1:8000")
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD, help="markdown report path")
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON, help="JSON sidecar path")
    parser.add_argument("--label", default="unlabeled run", help="free text naming the run")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS, help="seconds to pause between requests")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS, help="per-request timeout in seconds")
    parser.add_argument("--only", default="", help="comma-separated list ids to run, all when empty")
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    """
    Takes the command-line arguments without the program name.
    Loads the key, runs every list, scores it, and writes both outputs.
    Gives 0 when the outputs were written, or 1 when the key cannot be read.
    """
    args = parse_args(argv)
    try:
        key = read_json_file(args.key)
    except (FileNotFoundError, json.JSONDecodeError) as error:
        sys.stderr.write(f"error: cannot read key {args.key}: {error_text(error)}\n")
        return 1
    only = frozenset(part.strip() for part in args.only.split(",") if part.strip())
    lists = run_harness(key, args.base_url, args.delay, args.timeout, only)
    report = build_report(key, args.key, args.base_url, args.label, lists)
    write_outputs(report, args.out_md, args.out_json)
    sys.stderr.write(json.dumps(report["summary"], indent=1) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
