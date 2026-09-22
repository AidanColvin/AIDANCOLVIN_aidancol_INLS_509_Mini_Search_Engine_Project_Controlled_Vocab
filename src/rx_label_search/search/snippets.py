"""Pure extraction of a query-term-containing snippet from a document's body text."""

from __future__ import annotations

from rx_label_search.search.tokenize import tokenize

SNIPPET_RADIUS_CHARS = 80
SNIPPET_ELLIPSIS = "…"


def find_first_query_word_position(body_text: str, query_terms: tuple[str, ...]) -> int | None:
    """
    Takes the document's body text and the query terms.
    Finds the character position of the first query term's first occurrence, case-insensitively.
    Gives that position, or None when no query term appears in the text.
    """
    lowered = body_text.lower()
    positions = [lowered.find(term) for term in query_terms if lowered.find(term) >= 0]
    return min(positions) if positions else None


def build_snippet(body_text: str, query_terms: tuple[str, ...], radius: int) -> str:
    """
    Takes the document's body text, the query terms, and the character radius around the first match.
    Extracts the text around the first query term occurrence, or the start of the text when none is found.
    Gives the snippet with an ellipsis marking a cut edge, empty for empty body text.
    """
    if not body_text:
        return ""
    position = find_first_query_word_position(body_text, query_terms)
    if position is None:
        start, end = 0, min(len(body_text), radius * 2)
    else:
        start, end = max(0, position - radius), min(len(body_text), position + radius)
    prefix = SNIPPET_ELLIPSIS if start > 0 else ""
    suffix = SNIPPET_ELLIPSIS if end < len(body_text) else ""
    return f"{prefix}{body_text[start:end].strip()}{suffix}"


def snippet_for_query(body_text: str, query_text: str) -> str:
    """
    Takes a document's body text and the original query text.
    Tokenizes the query and builds the snippet around its first match.
    Gives the snippet, empty for empty body text.
    """
    return build_snippet(body_text, tokenize(query_text), SNIPPET_RADIUS_CHARS)
