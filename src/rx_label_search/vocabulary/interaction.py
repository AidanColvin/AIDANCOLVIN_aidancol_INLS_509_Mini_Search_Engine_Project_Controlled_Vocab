"""Rules for the four interaction-risk terms T14 to T17."""

from __future__ import annotations

import re
from collections.abc import Iterable

from rx_label_search.records import Label, TermEvidence
from rx_label_search.text.fields import label_text, openfda_values
from rx_label_search.text.negation import is_negated
from rx_label_search.text.sentences import split_sentences
from rx_label_search.vocabulary.terms import RULE_VERSION

T14_FIELDS = ("boxed_warning", "warnings_and_cautions", "warnings", "precautions", "drug_interactions", "contraindications")
T15_FIELDS = ("boxed_warning", "warnings_and_cautions", "warnings", "precautions", "drug_interactions")
T16_FIELDS = ("boxed_warning", "warnings_and_cautions", "warnings", "precautions", "contraindications", "drug_interactions")
T17_FIELDS = ("contraindications",)

_T14_PATTERN = re.compile(r"serotonin syndrome|serotonin toxicity", re.IGNORECASE)
_T15_PATTERN = re.compile(
    r"additive (?:cns depress|sedat|effects? (?:on|with) (?:the )?cns)|"
    r"additional (?:cns depress|sedat)|"
    r"(?:other |additional )?cns depressants?|central nervous system depressants?|"
    r"respiratory depression",
    re.IGNORECASE,
)
_T16_PATTERN = re.compile(r"qtc? prolongation|prolongs? the qt interval|torsades de pointes", re.IGNORECASE)
_T17_CONTRAINDICATION_CUE = re.compile(
    r"\bis contraindicated\b|\bare contraindicated\b|\bmust not be (?:used|combined|given|taken)\b|"
    r"\bshould not be (?:used|administered|combined|taken)\b|"
    r"\b(?:must|should) not (?:take|use|combine|administer)\b",
    re.IGNORECASE,
)
_T17_CLASS_SIGNAL = re.compile(r"\binhibitors?\b|\binducers?\b|\bantagonists?\b|\bagonists?\b|\bmaois?\b", re.IGNORECASE)
_T17_SELF_REFERENCE_ONLY = re.compile(
    r"\bin common with other\b|\bother members of\b|\bknown\s+\S+\s+sensitivity\b|"
    r"\bhistory of\s+\S+\s+(?:sensitivity|allergy)\b|\bhypersensitivity to\b",
    re.IGNORECASE,
)
_T17_COMBINATION_SIGNAL = re.compile(
    r"\bco-?administ\w*|\bconcomitant\w*|\bconcurrent\w*|\bcombin\w*|\btaking,?\s*or\b|"
    r"\bwithin\s+\d+\s+days\b|\bmaois?\b",
    re.IGNORECASE,
)


def matching_sentence(fields: Iterable[str], label: Label, pattern: re.Pattern[str]) -> tuple[str, str] | None:
    """
    Takes the fields to search in order, a Label, and a compiled pattern.
    Finds the first non-negated sentence in those fields that the pattern matches.
    Gives (field name, sentence), or None when no field has a qualifying sentence.
    """
    for field_name in fields:
        text = label_text(label, field_name)
        if not text:
            continue
        for sentence in split_sentences(text):
            if pattern.search(sentence) and not is_negated(sentence):
                return field_name, sentence
    return None


def tag_t14_serotonin_syndrome_risk(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Searches the interaction-relevant fields for a stated serotonin syndrome or toxicity risk.
    Gives evidence naming the field and the sentence, or None when no field states one.
    """
    found = matching_sentence(T14_FIELDS, label, _T14_PATTERN)
    if found is None:
        return None
    return TermEvidence("T14", found[0], found[1], RULE_VERSION)


def tag_t15_cns_depression_risk(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Searches the interaction-relevant fields for a stated added CNS depression or respiratory depression risk.
    Gives evidence naming the field and the sentence, or None when no field states one.
    """
    found = matching_sentence(T15_FIELDS, label, _T15_PATTERN)
    if found is None:
        return None
    return TermEvidence("T15", found[0], found[1], RULE_VERSION)


def tag_t16_qt_prolongation_risk(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Searches the interaction-relevant fields for a stated QT prolongation or torsades de pointes risk.
    Gives evidence naming the field and the sentence, or None when no field states one.
    """
    found = matching_sentence(T16_FIELDS, label, _T16_PATTERN)
    if found is None:
        return None
    return TermEvidence("T16", found[0], found[1], RULE_VERSION)


def own_drug_names(label: Label) -> frozenset[str]:
    """
    Takes a Label.
    Reads its own lowercase brand, generic, and substance names.
    Gives the frozenset of those names, empty when openfda names none.
    """
    names = (*openfda_values(label, "brand_name"), *openfda_values(label, "generic_name"), *openfda_values(label, "substance_name"))
    return frozenset(name.lower() for name in names if name)


def is_class_reference_sentence(sentence: str, class_gazetteer: frozenset[str]) -> bool:
    """
    Takes one contraindications sentence and a set of lowercase known drug or class names, excluding this label's own names.
    Checks whether the sentence names a known class or carries a generic class-word signal.
    Gives True when either check matches, False otherwise.
    """
    lowered = sentence.lower()
    if any(name in lowered for name in class_gazetteer):
        return True
    return bool(_T17_CLASS_SIGNAL.search(sentence))


def is_self_reference_only(sentence: str) -> bool:
    """
    Takes one contraindications sentence.
    Checks whether it only describes the drug's own class or a known sensitivity to it, with no combination signal.
    Gives True when it is self-referential and carries no combination signal, False otherwise.
    """
    return bool(_T17_SELF_REFERENCE_ONLY.search(sentence)) and not _T17_COMBINATION_SIGNAL.search(sentence)


def contraindicated_combination_sentence(text: str, class_gazetteer: frozenset[str]) -> str | None:
    """
    Takes the contraindications field text and the class gazetteer, with this label's own names already removed.
    Finds a non-negated sentence that states a contraindication and names a drug or class as a combination partner.
    Gives the sentence, or None when no sentence qualifies.
    """
    for sentence in split_sentences(text):
        if not _T17_CONTRAINDICATION_CUE.search(sentence) or is_negated(sentence):
            continue
        if is_self_reference_only(sentence):
            continue
        if is_class_reference_sentence(sentence, class_gazetteer):
            return sentence
    return None


def tag_t17_contraindicated_combination(label: Label, class_gazetteer: frozenset[str]) -> TermEvidence | None:
    """
    Takes a Label and the collection-wide set of known drug and class names.
    Removes the label's own names from the gazetteer, then searches contraindications for a combination partner.
    Gives evidence naming the field and the sentence, or None when no such sentence exists.
    """
    text = label_text(label, "contraindications")
    if not text:
        return None
    other_names_gazetteer = class_gazetteer - own_drug_names(label)
    sentence = contraindicated_combination_sentence(text, other_names_gazetteer)
    if sentence is None:
        return None
    return TermEvidence("T17", "contraindications", sentence, RULE_VERSION)


def extract_class_mentions(sentence: str, class_gazetteer: frozenset[str]) -> tuple[str, ...]:
    """
    Takes one contraindications sentence and the class gazetteer.
    Lists every gazetteer name that appears in the sentence.
    Gives the sorted tuple of matched names, empty when none appear.
    """
    lowered = sentence.lower()
    return tuple(sorted(name for name in class_gazetteer if name in lowered))
