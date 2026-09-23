"""Drug profiles for the medication card: the drug's class explained in plain language (from data/reference/drug_classes.json) and its FDA-approved uses, dosing, maximum, and duration statements quoted from its own label."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from rx_label_search.storage.read_json import read_json
from rx_label_search.storage.write_json import write_json
from rx_label_search.text.fields import field_values
from rx_label_search.text.sentences import split_sentences

PROFILES_DIR = "profiles"
MAX_SENTENCE_CHARS = 420
MAX_INDICATION_CHARS = 900
STUDY_WORDS = re.compile(r"\b(?:stud(?:y|ies)|trials?|patients treated|placebo)\b", re.IGNORECASE)
FRAGMENT = re.compile(r"^[\[(]|^\W*$")
CROSS_REFERENCE = re.compile(r"\s*\[\s*see[^\]]*\]|\(\s*\d+(?:\.\d+)*\s*\)", re.IGNORECASE)
SECTION_HEADER = re.compile(r"^\s*(?:\d+(?:\.\d+)*\s+)?(?:INDICATIONS\s*(?:AND|&)\s*USAGE|DOSAGE\s*(?:AND|&)\s*ADMINISTRATION|MECHANISM\s+OF\s+ACTION|CLINICAL\s+PHARMACOLOGY)\s*", re.IGNORECASE)
NUMBERED_HEADING = re.compile(r"^\s*\d+(?:\.\d+)+\s+(?=[A-Z])")
STRENGTH = re.compile(r"\d+(?:\.\d+)?\s*(?:mg|mcg|g|units?|mEq)\b", re.IGNORECASE)
RECOMMENDED = re.compile(r"\b(?:recommended|usual|starting|initial)\b[^.]*\b(?:dose|dosage)\b|\b(?:dose|dosage)\b[^.]*\b(?:recommended|usual)\b", re.IGNORECASE)
MAXIMUM = re.compile(r"\bmaximum\b|\bnot (?:to )?exceed\b|\bshould not exceed\b|\bup to a (?:total|maximum)\b", re.IGNORECASE)
DURATION = re.compile(
    r"\bshort[- ]term\b|\bshortest (?:possible )?duration\b|\blimit(?:ed)? (?:the )?(?:use|duration|treatment)\b"
    r"|\b(?:longer|more) than (?:\w+ )?\(?\d*\)? ?(?:days?|weeks?|months?)\b|\bfor (?:up to |no more than )?\d+(?: to \d+)? (?:days?|weeks?)\b"
    r"|\bperiodically re-?(?:assess|evaluate)\b|\bgradually (?:taper|reduce)\b|\btaper\b",
    re.IGNORECASE,
)


def clean_sentence(sentence: str) -> str:
    """
    Takes one label sentence.
    Drops a leading section header or number ("1 INDICATIONS AND USAGE", "2.1 ") and extra spaces.
    Gives the cleaned sentence.
    """
    text = SECTION_HEADER.sub("", sentence.strip())
    text = NUMBERED_HEADING.sub("", text)
    text = CROSS_REFERENCE.sub("", text).replace("•", ";")
    text = " ".join(text.split()).replace(" ;", ";").replace(":;", ":")
    return re.sub(r"\s+([.,;:])", r"\1", text)


def section_sentences(record: Mapping[str, Any], fields: Sequence[str], max_chars: int = MAX_SENTENCE_CHARS) -> list[str]:
    """
    Takes one raw label record, the fields to read in order, and the longest sentence worth quoting.
    Splits each field into cleaned sentences, dropping cross-reference fragments.
    Gives the sentences, empty when the fields are absent.
    """
    found: list[str] = []
    for name in fields:
        for text in field_values(record, name):
            for sentence in split_sentences(text):
                cleaned = clean_sentence(sentence)
                if 20 <= len(cleaned) <= max_chars and not FRAGMENT.match(cleaned):
                    found.append(cleaned)
    return found


def first_matching(sentences: Iterable[str], pattern: re.Pattern[str], limit: int, need_strength: bool = False) -> list[str]:
    """
    Takes sentences, a pattern, how many to keep, and whether a sentence must also state an amount.
    Keeps the first distinct matches in order.
    Gives up to limit sentences.
    """
    kept: list[str] = []
    for sentence in sentences:
        if pattern.search(sentence) and (not need_strength or STRENGTH.search(sentence)) and sentence not in kept:
            kept.append(sentence)
        if len(kept) == limit:
            break
    return kept


def label_profile(record: Mapping[str, Any]) -> dict[str, Any]:
    """
    Takes one raw openFDA label record.
    Quotes what the label says the drug is approved for, how it works, its recommended and maximum doses, and how long it is meant to be used.
    Gives the profile dictionary; a missing section gives an empty value.
    """
    indications = section_sentences(record, ("indications_and_usage",), MAX_INDICATION_CHARS)
    mechanism = section_sentences(record, ("mechanism_of_action",)) or [s for s in section_sentences(record, ("clinical_pharmacology",)) if re.search(r"mechanism|acts|binds|inhibit|block", s, re.IGNORECASE)]
    dosing = section_sentences(record, ("dosage_and_administration",))
    duration_pool = [*dosing, *indications, *section_sentences(record, ("boxed_warning", "warnings_and_cautions", "warnings"))]
    block = record.get("openfda") or {}
    return {
        "indications": indications[:3],
        "mechanism": mechanism[:2],
        "dose_recommended": first_matching((sentence for sentence in dosing if not MAXIMUM.search(sentence)), RECOMMENDED, 2, need_strength=True),
        "dose_maximum": first_matching(dosing, MAXIMUM, 2),
        "duration": first_matching((sentence for sentence in duration_pool if not STUDY_WORDS.search(sentence)), DURATION, 2),
        "pharm_class_epc": list(field_values(block, "pharm_class_epc")),
        "pharm_class_moa": list(field_values(block, "pharm_class_moa")),
    }


def write_profiles(records: Iterable[Mapping[str, Any]], build_dir: Path) -> int:
    """
    Takes the raw label records and the build directory.
    Writes one small profile file per label under build_dir/profiles, so a check reads only the labels on the list.
    Gives the number of profiles written.
    """
    folder = build_dir / PROFILES_DIR
    folder.mkdir(parents=True, exist_ok=True)
    count = 0
    for record in records:
        set_id = str(record.get("set_id", ""))
        if not set_id or "/" in set_id:
            continue
        write_json(folder / f"{set_id}.json", label_profile(record))
        count += 1
    return count


def read_profile(build_dir: Path, set_id: str) -> dict[str, Any]:
    """
    Takes the build directory and a label's set id.
    Reads that label's profile file.
    Gives the profile, or an empty dictionary when there is no label or no file.
    """
    path = build_dir / PROFILES_DIR / f"{set_id}.json"
    if not set_id or "/" in set_id or not path.is_file():
        return {}
    return read_json(path)


def classes_for(bases: Sequence[str], table: Mapping[str, Any]) -> list[dict[str, Any]]:
    """
    Takes a drug's base ingredients and the drug-class table.
    Finds every class that lists one of the ingredients (a member also matches a longer salt name, so lithium matches lithium carbonate).
    Gives the matching classes in table order, each with its name, uses, how it works, duration note, and sources.
    """
    found: list[dict[str, Any]] = []
    for entry in table.get("classes", ()):
        members = {member.lower() for member in entry["members"]}
        if any(base in members or any(base.startswith(member + " ") for member in members) for base in bases):
            found.append({key: entry[key] for key in ("id", "name", "what", "how", "duration", "sources") if key in entry})
    return found


def drug_profile(build_dir: Path, record: Mapping[str, Any], table: Mapping[str, Any], ceilings: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    """
    Takes the build directory, a resolved drug's checker record, the drug-class table, and the dose-ceiling table.
    Joins the plain-language class explanation, the StatPearls page for each ingredient, the label's own quoted statements, and the labeled daily maximum when the ceiling table has one.
    Gives the profile for the medication card.
    """
    bases = [base.lower() for base in record.get("base_ingredients", ())]
    by_ingredient = table.get("statpearls_by_ingredient", {})
    references = [by_ingredient[base] for base in bases if base in by_ingredient]
    maximum = [{"ingredient": base, "max_mg_per_day": ceilings[base]["max_mg_per_day"], "note": ceilings[base].get("note", "")} for base in bases if base in ceilings]
    return {
        "classes": classes_for(bases, table),
        "ingredient_references": references,
        "label": read_profile(build_dir, str(record.get("set_id", ""))),
        "ceilings": maximum,
    }
