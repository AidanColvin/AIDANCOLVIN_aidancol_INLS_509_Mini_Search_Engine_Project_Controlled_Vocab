"""Tests for T02 and T05."""

from __future__ import annotations

from rx_label_search.records import Label
from rx_label_search.vocabulary.patient_info import tag_t05_medication_guide
from rx_label_search.vocabulary.route import tag_t02_oral_route


def test_t02_assigns_when_oral_is_among_routes() -> None:
    """
    Takes no arguments.
    Checks a label with ORAL among two routes and a label with no ORAL route.
    Gives nothing, or fails if either result is wrong.
    """
    with_oral = Label("i", "s", "1", "20250101", {}, {"route": ("ORAL", "INTRAVENOUS")})
    without_oral = Label("i", "s", "1", "20250101", {}, {"route": ("TOPICAL",)})
    assert tag_t02_oral_route(with_oral) is not None
    assert tag_t02_oral_route(without_oral) is None


def test_t02_missing_route_field() -> None:
    """
    Takes no arguments.
    Checks a label with no route field at all.
    Gives nothing, or fails if evidence is returned.
    """
    assert tag_t02_oral_route(Label("i", "s", "1", "20250101", {}, {})) is None


def test_t05_assigns_when_medguide_has_text() -> None:
    """
    Takes no arguments.
    Checks a label with medguide text and one without.
    Gives nothing, or fails if either result is wrong.
    """
    with_guide = Label("i", "s", "1", "20250101", {"spl_medguide": ("Medication Guide text.",)}, {})
    without_guide = Label("i", "s", "1", "20250101", {}, {})
    assert tag_t05_medication_guide(with_guide) is not None
    assert tag_t05_medication_guide(without_guide) is None
