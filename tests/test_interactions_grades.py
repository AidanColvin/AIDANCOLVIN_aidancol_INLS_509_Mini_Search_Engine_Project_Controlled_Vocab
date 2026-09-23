"""Tests for the A-to-E severity grade in interactions/grades.py."""

from __future__ import annotations

from rx_label_search.interactions.grades import (
    GRADES,
    action_phrase,
    avoid_together_phrase,
    grade_alert,
    grade_fields,
    grade_member,
)
from rx_label_search.records import Alert, AlertEvidence


def member(section: str, sentence: str, drug_name: str = "Drug A") -> AlertEvidence:
    """
    Takes a label section, a sentence, and an optional drug name.
    Builds one alert member carrying that evidence.
    Gives the AlertEvidence.
    """
    return AlertEvidence(drug_name=drug_name, set_id="set", effective_time="20260101", section=section, sentence=sentence, dailymed_url="https://dailymed.nlm.nih.gov/x")


def alert(kind: str, risk: str, members: tuple[AlertEvidence, ...]) -> Alert:
    """
    Takes an alert kind, a risk id, and its members.
    Builds an Alert with a placeholder title and tier.
    Gives the Alert.
    """
    return Alert(kind=kind, risk=risk, title="t", tier=None, tier_name="", members=members, note="")


def test_pair_contraindication_is_grade_e() -> None:
    """
    Takes no arguments.
    Grades a pair alert whose sentence comes from the contraindications section.
    Gives nothing; asserts grade E.
    """
    graded = grade_member(member("contraindications", "Do not use with MAOIs."), "pair")
    assert graded is not None and graded.letter == "E"


def test_boxed_warning_is_grade_d() -> None:
    """
    Takes no arguments.
    Grades a group member from the boxed warning.
    Gives nothing; asserts grade D and a basis naming the boxed warning.
    """
    graded = grade_member(member("boxed_warning", "Concomitant use of benzodiazepines and opioids may result in profound sedation.", "Xanax"), "group")
    assert graded is not None and graded.letter == "D" and "boxed warning" in graded.basis


def test_avoid_counts_only_when_about_using_drugs_together() -> None:
    """
    Takes no arguments.
    Checks an avoid statement about concomitant use against one about the patient.
    Gives nothing; asserts only the concomitant-use sentence is read as avoid-together.
    """
    assert avoid_together_phrase("Avoid concomitant use with CNS depressants.") == "Avoid"
    assert avoid_together_phrase("Avoid use in patients at risk of TdP.") is None


def test_warning_section_is_grade_c_and_avoid_together_raises_it_to_d() -> None:
    """
    Takes no arguments.
    Grades two warnings-section sentences, one with an avoid-together statement.
    Gives nothing; asserts C for the plain warning and D for the avoid-together one.
    """
    plain = grade_member(member("warnings_and_cautions", "QT prolongation has been seen."), "group")
    avoid = grade_member(member("precautions", "CNS depressants should be avoided when taken with this combination product."), "group")
    assert plain is not None and plain.letter == "C"
    assert avoid is not None and avoid.letter == "D"


def test_drug_interactions_section_is_b_with_an_action_and_a_without() -> None:
    """
    Takes no arguments.
    Grades drug-interactions sentences with and without an instruction.
    Gives nothing; asserts B with "monitor" and A without an action.
    """
    assert action_phrase("Monitor patients closely for sedation.") == "Monitor"
    with_action = grade_member(member("drug_interactions", "Monitor patients closely for sedation."), "group")
    without = grade_member(member("drug_interactions", "Concomitant use may result in serotonin syndrome."), "group")
    assert with_action is not None and with_action.letter == "B"
    assert without is not None and without.letter == "A"


def test_alert_takes_its_most_severe_member_and_duplication_is_c() -> None:
    """
    Takes no arguments.
    Grades a group alert with an A member and a D member, and a duplication alert.
    Gives nothing; asserts D for the group and C for the duplication.
    """
    group = alert("group", "T15", (member("drug_interactions", "May add sedation."), member("boxed_warning", "Profound sedation.")))
    assert grade_alert(group).letter == "D"
    duplicate = alert("duplication", "shared_ingredient", (member("", ""), member("", "")))
    assert grade_alert(duplicate).letter == "C"


def test_grade_fields_spell_out_the_grade_with_its_lexicomp_level() -> None:
    """
    Takes no arguments.
    Builds the API fields for a pair contraindication.
    Gives nothing; asserts every field and the X Lexicomp level.
    """
    fields = grade_fields(alert("pair", "T17", (member("contraindications", "Contraindicated with pimozide."), member("", ""))))
    assert fields["grade"] == "E"
    assert fields["grade_name"] == GRADES["E"].name
    assert fields["grade_lexicomp"] == "X"
    assert fields["grade_basis"]
