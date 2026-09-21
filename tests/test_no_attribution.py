"""Fails if either forbidden vendor name appears in any file this project creates or edits."""

from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN_FRAGMENTS: tuple[tuple[str, str], ...] = (("Cla", "ude"), ("Anthro", "pic"))
EXEMPT_PREFIXES: tuple[str, ...] = (
    "notes/",
    "rubrics/",
    "document_collection_part_1/",
    "MiniVocab_Aidan_Colvin_aidancol.md",
    "LICENSE",
)
BINARY_SUFFIXES = frozenset({".zip", ".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".woff", ".woff2"})


def forbidden_strings(fragments: tuple[tuple[str, str], ...]) -> tuple[str, ...]:
    """
    Takes pairs of string fragments.
    Joins each pair into one lowercase search string.
    Gives the tuple of search strings, empty when no pairs are given.
    """
    return tuple((left + right).lower() for left, right in fragments)


def list_repo_files(root: Path) -> list[str]:
    """
    Takes the repository root.
    Asks git for every tracked and untracked file that is not ignored.
    Gives the list of repository-relative paths, or raises CalledProcessError when git fails.
    """
    completed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    return [entry for entry in completed.stdout.decode("utf-8").split("\0") if entry]


def is_exempt(relative_path: str, prefixes: tuple[str, ...]) -> bool:
    """
    Takes a repository-relative path and the exempt path prefixes.
    Checks whether the path starts with any exempt prefix.
    Gives True when the path is exempt, False otherwise.
    """
    return any(relative_path.startswith(prefix) for prefix in prefixes)


def is_binary_name(relative_path: str, suffixes: frozenset[str]) -> bool:
    """
    Takes a repository-relative path and a set of binary file suffixes.
    Checks whether the path ends with one of those suffixes.
    Gives True for a binary name, False otherwise.
    """
    return Path(relative_path).suffix.lower() in suffixes


def read_text_or_none(path: Path) -> str | None:
    """
    Takes a file path.
    Reads the file as UTF-8 text.
    Gives the text, or None when the file is missing or not valid UTF-8.
    """
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, UnicodeDecodeError):
        return None


def find_matches(text: str, needles: tuple[str, ...]) -> list[str]:
    """
    Takes a text and lowercase search strings.
    Finds which search strings occur in the text, ignoring case.
    Gives the list of matched search strings, empty when none occur.
    """
    lowered = text.lower()
    return [needle for needle in needles if needle in lowered]


def scan_repository(root: Path, prefixes: tuple[str, ...], needles: tuple[str, ...]) -> list[str]:
    """
    Takes the repository root, exempt prefixes, and lowercase search strings.
    Scans every non-exempt text file for the search strings.
    Gives a list of "path: match" strings, empty when the repository is clean.
    """
    hits: list[str] = []
    for relative_path in list_repo_files(root):
        if is_exempt(relative_path, prefixes) or is_binary_name(relative_path, BINARY_SUFFIXES):
            continue
        text = read_text_or_none(root / relative_path)
        if text is None:
            continue
        hits.extend(f"{relative_path}: {match}" for match in find_matches(text, needles))
    return hits


def test_forbidden_strings_joins_fragments() -> None:
    """
    Takes no arguments.
    Joins the configured fragments into search strings.
    Gives nothing, or fails if the count or casing is wrong.
    """
    needles = forbidden_strings(FORBIDDEN_FRAGMENTS)
    assert len(needles) == 2
    assert all(needle == needle.lower() for needle in needles)


def test_forbidden_strings_empty_input() -> None:
    """
    Takes no arguments.
    Joins an empty tuple of fragments.
    Gives nothing, or fails if the result is not empty.
    """
    assert forbidden_strings(()) == ()


def test_find_matches_is_case_insensitive() -> None:
    """
    Takes no arguments.
    Searches mixed-case text for a lowercase needle.
    Gives nothing, or fails if the needle is not found.
    """
    assert find_matches("Hello WORLD", ("world",)) == ["world"]


def test_find_matches_empty_text() -> None:
    """
    Takes no arguments.
    Searches an empty text.
    Gives nothing, or fails if any match is reported.
    """
    assert find_matches("", ("x",)) == []


def test_is_exempt_matches_prefix() -> None:
    """
    Takes no arguments.
    Checks an exempt and a non-exempt path against the prefixes.
    Gives nothing, or fails if either answer is wrong.
    """
    assert is_exempt("notes/a.md", EXEMPT_PREFIXES)
    assert not is_exempt("src/x.py", EXEMPT_PREFIXES)


def test_repository_has_no_forbidden_names() -> None:
    """
    Takes no arguments.
    Scans every non-exempt repository file for the forbidden names.
    Gives nothing, or fails listing every file and match.
    """
    hits = scan_repository(ROOT, EXEMPT_PREFIXES, forbidden_strings(FORBIDDEN_FRAGMENTS))
    assert not hits, "\n" + "\n".join(hits)
