"""Rule for T03 Pediatric Indication."""

from __future__ import annotations

import re

from rx_label_search.records import Label, TermEvidence
from rx_label_search.text.fields import label_text
from rx_label_search.text.negation import is_negated
from rx_label_search.text.sentences import split_sentences
from rx_label_search.vocabulary.terms import RULE_VERSION

_ESTABLISHED = re.compile(
    r"safety and (?:effectiveness|efficacy) (?:of [^.]*?)?(?:have|has) been established in\s+"
    r"(?:pediatric|children)",
    re.IGNORECASE,
)
_INDICATED_FOR_PEDIATRIC = re.compile(r"indicated for\s+.{0,80}?\bpediatric patients\b", re.IGNORECASE)
_NOT_ESTABLISHED = re.compile(
    r"safety and (?:effectiveness|efficacy)[^.]*?have not been established|"
    r"have not been established in pediatric|contraindicat\w* in (?:children|pediatric)",
    re.IGNORECASE,
)


def pediatric_sentence(sentences: tuple[str, ...]) -> str | None:
    """
    Takes the sentences of one field.
    Finds a sentence that states an established pediatric indication and is not itself negated.
    Gives that sentence, or None when no sentence qualifies.
    """
    for sentence in sentences:
        if _NOT_ESTABLISHED.search(sentence) or is_negated(sentence):
            continue
        if _ESTABLISHED.search(sentence) or _INDICATED_FOR_PEDIATRIC.search(sentence):
            return sentence
    return None


def tag_t03_pediatric_indication(label: Label) -> TermEvidence | None:
    """
    Takes a Label.
    Searches indications_and_usage and pediatric_use for a stated established pediatric indication.
    Gives evidence naming the field and the sentence, or None when neither field states one.
    """
    for field_name in ("pediatric_use", "indications_and_usage"):
        text = label_text(label, field_name)
        if not text:
            continue
        sentence = pediatric_sentence(split_sentences(text))
        if sentence is not None:
            return TermEvidence("T03", field_name, sentence, RULE_VERSION)
    return None
