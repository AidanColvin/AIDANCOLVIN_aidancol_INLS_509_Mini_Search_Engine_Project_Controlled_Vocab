"""Pure per-label tagging that combines every rule function and the hierarchy."""

from __future__ import annotations

from rx_label_search.records import Label, TagRecord, TermEvidence
from rx_label_search.text.fields import label_from_record
from rx_label_search.vocabulary.dea import tag_t07_controlled_substance, tag_t10_schedule_ii_controlled_substance
from rx_label_search.vocabulary.dosing import tag_t06_renal_dose_adjustment, tag_t12_hepatic_dose_adjustment
from rx_label_search.vocabulary.hierarchy import broadened_evidence
from rx_label_search.vocabulary.interaction import (
    tag_t14_serotonin_syndrome_risk,
    tag_t15_cns_depression_risk,
    tag_t16_qt_prolongation_risk,
    tag_t17_contraindicated_combination,
)
from rx_label_search.vocabulary.patient_info import tag_t05_medication_guide
from rx_label_search.vocabulary.population import tag_t03_pediatric_indication
from rx_label_search.vocabulary.product import tag_t08_single_active_ingredient, tag_t09_brand_name_product
from rx_label_search.vocabulary.route import tag_t02_oral_route
from rx_label_search.vocabulary.safety import tag_t01_boxed_warning, tag_t04_high_frequency_adverse_effect
from rx_label_search.vocabulary.terms import RULE_VERSION

SIMPLE_RULES = (
    tag_t01_boxed_warning,
    tag_t02_oral_route,
    tag_t03_pediatric_indication,
    tag_t04_high_frequency_adverse_effect,
    tag_t05_medication_guide,
    tag_t06_renal_dose_adjustment,
    tag_t07_controlled_substance,
    tag_t08_single_active_ingredient,
    tag_t09_brand_name_product,
    tag_t10_schedule_ii_controlled_substance,
    tag_t12_hepatic_dose_adjustment,
    tag_t14_serotonin_syndrome_risk,
    tag_t15_cns_depression_risk,
    tag_t16_qt_prolongation_risk,
)


def run_simple_rules(label: Label) -> tuple[TermEvidence, ...]:
    """
    Takes a Label.
    Runs every rule function that needs only the label.
    Gives the tuple of evidence the rules assigned, empty when none applied.
    """
    return tuple(evidence for rule in SIMPLE_RULES if (evidence := rule(label)) is not None)


def tag_label(label: Label, class_gazetteer: frozenset[str]) -> TagRecord:
    """
    Takes a Label and the collection-wide class gazetteer T17 needs.
    Runs every rule function, adds T17, then expands the broader terms.
    Gives the label's TagRecord with every term's evidence.
    """
    evidence = run_simple_rules(label)
    t17 = tag_t17_contraindicated_combination(label, class_gazetteer)
    if t17 is not None:
        evidence = (*evidence, t17)
    return TagRecord(label.label_id, label.set_id, label.effective_time, RULE_VERSION, broadened_evidence(evidence))


def tag_record(record: dict, class_gazetteer: frozenset[str]) -> TagRecord:
    """
    Takes a raw openFDA label record and the class gazetteer.
    Converts the record to a Label and tags it.
    Gives the TagRecord.
    """
    return tag_label(label_from_record(record), class_gazetteer)
