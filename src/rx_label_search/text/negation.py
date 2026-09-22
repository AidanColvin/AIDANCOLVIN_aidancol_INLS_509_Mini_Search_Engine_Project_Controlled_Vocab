"""Pure negation detection so sentences that deny a risk never fire a tag or alert."""

from __future__ import annotations

import re

NEGATION_CUES: tuple[str, ...] = (
    r"\bno clinically (?:significant|meaningful|relevant|important)\b",
    r"\bnot clinically (?:significant|meaningful|relevant|important)\b",
    r"\bno (?:significant|meaningful|relevant) (?:effect|interaction|change|increase|prolongation)",
    r"\bno (?:dose|dosage) adjustment(?:s)? (?:is|are|was|were)? ?(?:needed|necessary|required|recommended)",
    r"\bdoes not (?:require|need) (?:a )?(?:dose|dosage) adjustment",
    r"\bno (?:evidence|reports?|cases?) of\b",
    r"\bnot (?:been )?(?:associated|observed|reported|seen|expected)\b",
    r"\bdid not (?:prolong|increase|affect|alter|result in|cause)\b",
    r"\bdoes not (?:prolong|increase|affect|alter|cause)\b",
    r"\bis not (?:a )?(?:controlled|scheduled)\b",
    r"\bnot a controlled substance\b",
    r"\bnot (?:expected|known|likely) to\b",
    r"\bwithout (?:clinically )?(?:significant|meaningful)\b",
    r"\bwas not (?:observed|seen|reported|detected|found)\b",
    r"\bwere not (?:observed|seen|reported|detected|found)\b",
    r"\bunlikely to\b",
    r"\bno interaction",
)
_NEGATION = re.compile("|".join(NEGATION_CUES), re.IGNORECASE)
_WINDOW_CHARS = 120


def negation_cue(sentence: str) -> str | None:
    """
    Takes one sentence.
    Searches it for a negation cue from the cue list.
    Gives the matched cue text, or None when the sentence has no cue.
    """
    match = _NEGATION.search(sentence)
    return match.group(0) if match else None


def is_negated(sentence: str) -> bool:
    """
    Takes one sentence.
    Checks whether it contains a negation cue anywhere.
    Gives True when a cue is present, False otherwise.
    """
    return negation_cue(sentence) is not None


def is_negated_near(sentence: str, position: int, window: int = _WINDOW_CHARS) -> bool:
    """
    Takes a sentence, a character position inside it, and a window size.
    Checks whether a negation cue occurs within the window before the position.
    Gives True when a cue sits in that window, False otherwise.
    """
    start = max(0, position - window)
    return _NEGATION.search(sentence[start:position]) is not None
