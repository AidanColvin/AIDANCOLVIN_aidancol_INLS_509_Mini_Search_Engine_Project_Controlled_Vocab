"""Pure sentence splitting and sentence search over label text."""

from __future__ import annotations

import re
from collections.abc import Iterable

_WHITESPACE = re.compile(r"\s+")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(\[\"'])")
_ABBREVIATIONS = ("e.g.", "i.e.", "vs.", "approx.", "etc.", "mg.", "no.", "dr.", "fig.", "spp.")


def collapse_whitespace(text: str) -> str:
    """
    Takes any text.
    Replaces runs of whitespace with one space and trims the ends.
    Gives the collapsed text, empty for blank input.
    """
    return _WHITESPACE.sub(" ", text).strip()


def protect_abbreviations(text: str, abbreviations: tuple[str, ...]) -> str:
    """
    Takes text and a tuple of lowercase abbreviations that end in a period.
    Replaces the period in each abbreviation with a placeholder so it is not treated as a sentence end.
    Gives the protected text.
    """
    protected = text
    for abbreviation in abbreviations:
        protected = re.sub(
            re.escape(abbreviation),
            lambda match: match.group(0)[:-1] + "․",
            protected,
            flags=re.IGNORECASE,
        )
    return protected


def restore_abbreviations(text: str) -> str:
    """
    Takes text in which abbreviation periods were replaced by a placeholder.
    Puts the periods back.
    Gives the restored text.
    """
    return text.replace("․", ".")


def split_sentences(text: str) -> tuple[str, ...]:
    """
    Takes a block of label text.
    Splits it into sentences at periods, question marks, or exclamation marks followed by a capital, digit, or bracket.
    Gives the tuple of non-empty sentences, empty for blank text.
    """
    collapsed = collapse_whitespace(text)
    if not collapsed:
        return ()
    protected = protect_abbreviations(collapsed, _ABBREVIATIONS)
    pieces = _SENTENCE_END.split(protected)
    return tuple(restore_abbreviations(piece).strip() for piece in pieces if piece.strip())


def sentences_matching(sentences: Iterable[str], pattern: re.Pattern[str]) -> tuple[str, ...]:
    """
    Takes sentences and a compiled regular expression.
    Keeps the sentences in which the pattern occurs.
    Gives the tuple of matching sentences in order, empty when none match.
    """
    return tuple(sentence for sentence in sentences if pattern.search(sentence))


def first_sentence_matching(sentences: Iterable[str], pattern: re.Pattern[str]) -> str | None:
    """
    Takes sentences and a compiled regular expression.
    Finds the first sentence in which the pattern occurs.
    Gives that sentence, or None when no sentence matches.
    """
    for sentence in sentences:
        if pattern.search(sentence):
            return sentence
    return None
