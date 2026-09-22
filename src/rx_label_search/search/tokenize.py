"""Pure tokenization of query and document text: lowercase, strip punctuation, keep numbers."""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[a-z0-9]+(?:[.'][a-z0-9]+)*")


def tokenize(text: str) -> tuple[str, ...]:
    """
    Takes any text.
    Lowercases it and splits it into tokens of letters and digits, keeping an internal apostrophe or decimal point.
    Gives the tuple of tokens in order, empty for text with no tokens.
    """
    return tuple(_TOKEN.findall(text.lower()))
