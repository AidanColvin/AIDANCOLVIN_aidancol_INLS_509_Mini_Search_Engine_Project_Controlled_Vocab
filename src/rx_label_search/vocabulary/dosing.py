"""Rules for T06 Renal Dose Adjustment and T12 Hepatic Dose Adjustment."""

from __future__ import annotations

import re

from rx_label_search.records import Label, TermEvidence
from rx_label_search.text.fields import label_text
from rx_label_search.text.negation import is_negated
from rx_label_search.text.sentences import split_sentences
from rx_label_search.vocabulary.terms import RULE_VERSION

DOSE_ADJUSTMENT_FIELDS = ("dosage_and_administration", "use_in_specific_populations", "precautions")
_RENAL_CUE = re.compile(r"renal impair|kidney|creatinine clearance|\bcrcl\b|\begfr\b|dialysis|end-stage renal", re.IGNORECASE)
_HEPATIC_CUE = re.compile(r"hepatic impair|liver impair|child-?pugh|hepatic insufficiency", re.IGNORECASE)
_DOSE_CHANGE_CUE = re.compile(
    r"dos(?:e|age) adjustment|adjust(?:ed|ing)? (?:the )?dose|reduce (?:the )?(?:daily )?dose|"
    r"lower (?:the )?(?:maximum )?dose|decrease (?:the )?dose|extend(?:ed)? (?:the )?(?:dosing )?interval|"
    r"increase (?:the )?interval|maximum (?:daily )?dose of|\d+(?:\.\d+)?\s*mg|"
    r"dosage is recommended|dosing recommendations|titrat",
    re.IGNORECASE,
)
_AVOID_ONLY_CUE = re.compile(r"\bavoid\b|contraindicat", re.IGNORECASE)


def dose_adjustment_sentence(sentences: tuple[str, ...], function_cue: re.Pattern[str]) -> str | None:
    """
    Takes the sentences of one field and the organ-function cue pattern to match.
    Finds a sentence that ties the organ-function cue to a real dose change, skipping negated or avoid-only sentences.
    Gives that sentence, or None when no sentence qualifies.
    """
    for sentence in sentences:
        if not function_cue.search(sentence) or not _DOSE_CHANGE_CUE.search(sentence):
            continue
        if is_negated(sentence):
            continue
        if _AVOID_ONLY_CUE.search(sentence) and not re.search(r"\d+(?:\.\d+)?\s*mg|adjustment|reduce|lower|decrease|extend|interval", sentence, re.IGNORECASE):
            continue
        return sentence
    return None


def tag_organ_dose_adjustment(label: Label, term_id: str, function_cue: re.Pattern[str]) -> TermEvidence | None:
    """
    Takes a Label, the term id to assign, and the organ-function cue pattern.
    Searches the dose-adjustment fields in order for a qualifying sentence.
    Gives evidence naming the field and the sentence, or None when no field has one.
    """
    for field_name in DOSE_ADJUSTMENT_FIELDS:
        text = label_text(label, field_name)
        if not text:
            continue
        sentence = dose_adjustment_sentence(split_sentences(text), function_cue)
        if sentence is not None:
            return TermEvidence(term_id, field_name, sentence, RULE_VERSION)
    return None


def tag_t06_renal_dose_adjustment(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Searches for a sentence tying a kidney function level to a real dose change.
    Gives evidence naming the field and the sentence, or None when no such sentence exists.
    """
    return tag_organ_dose_adjustment(label, "T06", _RENAL_CUE)


def tag_t12_hepatic_dose_adjustment(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Searches for a sentence tying a liver function level to a real dose change.
    Gives evidence naming the field and the sentence, or None when no such sentence exists.
    """
    return tag_organ_dose_adjustment(label, "T12", _HEPATIC_CUE)
