"""Tests for T14 to T17, including negation exclusions and the T17 class check."""

from __future__ import annotations

from typing import Any

from rx_label_search.records import Label
from rx_label_search.text.fields import label_from_record
from rx_label_search.vocabulary.interaction import (
    extract_class_mentions,
    is_class_reference_sentence,
    tag_t14_serotonin_syndrome_risk,
    tag_t15_cns_depression_risk,
    tag_t16_qt_prolongation_risk,
    tag_t17_contraindicated_combination,
)

GAZETTEER = frozenset({"mao inhibitors", "strong cyp3a inhibitors"})


def test_t14_on_cyclobenzaprine_and_gabapentin(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks the serotonin syndrome rule on a label that warns of it and one that does not.
    Gives nothing, or fails if either result is wrong.
    """
    assert tag_t14_serotonin_syndrome_risk(label_from_record(fixture_labels["cyclobenzaprine"])) is not None
    assert tag_t14_serotonin_syndrome_risk(label_from_record(fixture_labels["gabapentin"])) is None


def test_t14_omits_when_mentioned_only_in_mechanism_of_action() -> None:
    """
    Takes no arguments.
    Checks a label that mentions serotonin only in mechanism_of_action, a field T14 does not search.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"mechanism_of_action": ("This drug inhibits serotonin reuptake.",)}, {})
    assert tag_t14_serotonin_syndrome_risk(label) is None


def test_t15_on_cyclobenzaprine_and_omits_on_driving_only_warning(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks the CNS depression rule on cyclobenzaprine and a driving-only drowsiness warning.
    Gives nothing, or fails if either result is wrong.
    """
    assert tag_t15_cns_depression_risk(label_from_record(fixture_labels["cyclobenzaprine"])) is not None
    label = Label("i", "s", "1", "20250101", {"warnings": ("This drug may cause drowsiness; use caution when driving or operating machinery.",)}, {})
    assert tag_t15_cns_depression_risk(label) is None


def test_t16_on_trazodone_and_negated_qt(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks the QT rule on trazodone and a sentence that denies a QT effect.
    Gives nothing, or fails if either result is wrong.
    """
    assert tag_t16_qt_prolongation_risk(label_from_record(fixture_labels["trazodone"])) is not None
    label = Label("i", "s", "1", "20250101", {"drug_interactions": ("The drug did not prolong the QT interval in a thorough QT study.",)}, {})
    assert tag_t16_qt_prolongation_risk(label) is None


def test_t16_assigns_on_torsades_mention() -> None:
    """
    Takes no arguments.
    Checks a sentence naming torsades de pointes.
    Gives nothing, or fails if evidence is missing.
    """
    label = Label("i", "s", "1", "20250101", {"warnings": ("Cases of torsades de pointes have been reported.",)}, {})
    assert tag_t16_qt_prolongation_risk(label) is not None


def test_is_class_reference_sentence_uses_gazetteer_and_generic_signal() -> None:
    """
    Takes no arguments.
    Checks a sentence matched only by the gazetteer, one matched only by the generic signal, and one matched by neither.
    Gives nothing, or fails if any case is wrong.
    """
    assert is_class_reference_sentence("Contraindicated with MAO inhibitors.", GAZETTEER)
    assert is_class_reference_sentence("Contraindicated with strong CYP3A4 inhibitors.", frozenset())
    assert not is_class_reference_sentence("Contraindicated in patients with hypersensitivity.", frozenset())


def test_t17_on_trazodone_and_gabapentin(fixture_labels: dict[str, dict[str, Any]]) -> None:
    """
    Takes the fixture labels.
    Checks the contraindicated-combination rule on trazodone's MAOI contraindication and gabapentin's label.
    Gives nothing, or fails if either result is wrong.
    """
    assert tag_t17_contraindicated_combination(label_from_record(fixture_labels["trazodone"]), GAZETTEER) is not None
    assert tag_t17_contraindicated_combination(label_from_record(fixture_labels["gabapentin"]), GAZETTEER) is None


def test_t17_omits_on_condition_only_contraindication() -> None:
    """
    Takes no arguments.
    Checks a contraindication that names only a condition or allergy, with no drug or class.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"contraindications": ("This drug is contraindicated in patients with hypersensitivity to any component of the formulation.",)}, {})
    assert tag_t17_contraindicated_combination(label, frozenset()) is None


def test_t17_omits_on_self_referential_class_mention() -> None:
    """
    Takes no arguments.
    Checks a sentence that names the drug's own class or a known sensitivity to it, with no combination partner.
    Gives nothing, or fails if evidence is returned for either case.
    """
    phenothiazine = Label(
        "i", "s", "1", "20250101",
        {"contraindications": ("In common with other phenothiazines, this drug is contraindicated in severe central nervous system depression.",)},
        {},
    )
    barbiturate = Label("i", "s", "1", "20250101", {"contraindications": ("Barbiturates are contraindicated in patients with known barbiturate sensitivity.",)}, {})
    assert tag_t17_contraindicated_combination(phenothiazine, frozenset({"phenothiazine"})) is None
    assert tag_t17_contraindicated_combination(barbiturate, frozenset({"barbiturate"})) is None


def test_t17_self_reference_pattern_still_fires_with_a_combination_signal() -> None:
    """
    Takes no arguments.
    Checks a sentence that has a self-reference phrase but also states a genuine combination signal.
    Gives nothing, or fails if evidence is not returned.
    """
    label = Label(
        "i", "s", "1", "20250101",
        {"contraindications": ("This drug is contraindicated with known hypersensitivity to MAOIs when taken concomitantly with other agents.",)},
        {},
    )
    assert tag_t17_contraindicated_combination(label, frozenset()) is not None


def test_t17_omits_when_gazetteer_hit_is_only_the_drugs_own_name() -> None:
    """
    Takes no arguments.
    Checks a contraindication sentence that repeats the drug's own name for an unrelated condition.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label(
        "i", "s", "1", "20250101",
        {"contraindications": ("Phenobarbital is contraindicated in patients with acute intermittent porphyria.",)},
        {"generic_name": ("PHENOBARBITAL",), "substance_name": ("PHENOBARBITAL",)},
    )
    assert tag_t17_contraindicated_combination(label, frozenset({"phenobarbital"})) is None


def test_t17_still_fires_on_a_different_drugs_gazetteer_name() -> None:
    """
    Takes no arguments.
    Checks a contraindication sentence naming a different drug from the gazetteer as a combination partner.
    Gives nothing, or fails if evidence is missing.
    """
    label = Label(
        "i", "s", "1", "20250101",
        {"contraindications": ("Concomitant use with pimozide is contraindicated.",)},
        {"generic_name": ("CLARITHROMYCIN",), "substance_name": ("CLARITHROMYCIN",)},
    )
    assert tag_t17_contraindicated_combination(label, frozenset({"pimozide"})) is not None


def test_t17_omits_on_avoid_or_not_recommended_wording() -> None:
    """
    Takes no arguments.
    Checks a weaker "avoid" statement, which Appendix C excludes from T17.
    Gives nothing, or fails if evidence is returned.
    """
    label = Label("i", "s", "1", "20250101", {"contraindications": ("Concomitant use with strong CYP3A4 inhibitors is not recommended.",)}, {})
    assert tag_t17_contraindicated_combination(label, frozenset()) is None


def test_extract_class_mentions() -> None:
    """
    Takes no arguments.
    Extracts gazetteer names from a sentence with one match and one with none.
    Gives nothing, or fails if either result is wrong.
    """
    assert extract_class_mentions("Contraindicated with MAO inhibitors.", GAZETTEER) == ("mao inhibitors",)
    assert extract_class_mentions("Contraindicated in pregnancy.", GAZETTEER) == ()


def test_own_drug_names_reads_all_three_fields_and_lowercases() -> None:
    """
    Takes no arguments.
    Reads the own-names set from a label with brand, generic, and substance names.
    Gives nothing, or fails if any name is missing or not lowercased.
    """
    from rx_label_search.vocabulary.interaction import own_drug_names

    label = Label("i", "s", "1", "20250101", {}, {"brand_name": ("OxyContin",), "generic_name": ("OXYCODONE HYDROCHLORIDE",), "substance_name": ("OXYCODONE HYDROCHLORIDE",)})
    assert own_drug_names(label) == frozenset({"oxycontin", "oxycodone hydrochloride"})
    assert own_drug_names(Label("i", "s", "1", "20250101", {}, {})) == frozenset()
