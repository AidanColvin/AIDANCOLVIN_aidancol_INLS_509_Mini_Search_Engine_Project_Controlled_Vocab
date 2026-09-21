"""Frozen dataclasses shared by every stage of the pipeline."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class Partition:
    """One bulk download file listed in the openFDA manifest."""

    url: str
    display_name: str
    size_mb: float
    records: int


@dataclass(frozen=True)
class Label:
    """One openFDA drug label with its text fields and openfda block."""

    label_id: str
    set_id: str
    version: str
    effective_time: str
    text_fields: Mapping[str, tuple[str, ...]]
    openfda: Mapping[str, tuple[str, ...]]


@dataclass(frozen=True)
class LabelSummary:
    """The small part of a label needed to choose the newest per ingredient set."""

    label_id: str
    set_id: str
    version: str
    effective_time: str
    ingredient_set: tuple[str, ...]
    brand_names: tuple[str, ...]
    generic_names: tuple[str, ...]


@dataclass(frozen=True)
class TermEvidence:
    """Why one PDLA term was assigned to one label."""

    term_id: str
    field_name: str
    sentence: str
    rule_version: str


@dataclass(frozen=True)
class TagRecord:
    """Every PDLA term assigned to one label, with evidence."""

    label_id: str
    set_id: str
    effective_time: str
    rule_version: str
    evidence: tuple[TermEvidence, ...]


@dataclass(frozen=True)
class MedEntry:
    """One parsed line of a free-text medication list."""

    raw_text: str
    name_text: str
    strength_value: float | None
    strength_unit: str | None
    times_per_day: float | None
    daily_total: float | None
    notes: tuple[str, ...]


@dataclass(frozen=True)
class NameMatch:
    """How a typed drug name was resolved to an ingredient set."""

    query: str
    status: str
    matched_name: str | None
    ingredient_set: tuple[str, ...]
    chain: tuple[str, ...]
    candidates: tuple[str, ...]
    score: float
    reason: str


@dataclass(frozen=True)
class AlertEvidence:
    """The label sentence behind one member of an alert."""

    drug_name: str
    set_id: str
    effective_time: str
    section: str
    sentence: str
    dailymed_url: str


@dataclass(frozen=True)
class Alert:
    """One group, pair, or duplication alert with its heuristic tier."""

    kind: str
    risk: str
    title: str
    tier: int | None
    tier_name: str
    members: tuple[AlertEvidence, ...]
    note: str


@dataclass(frozen=True)
class SearchHit:
    """One ranked search result."""

    set_id: str
    brand_name: str
    generic_name: str
    snippet: str
    tags: tuple[str, ...]
    effective_time: str
    score: float
