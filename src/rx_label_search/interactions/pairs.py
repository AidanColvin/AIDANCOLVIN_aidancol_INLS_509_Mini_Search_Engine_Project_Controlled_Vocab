"""Pure pair-alert detection: drug A carries T17, and another listed drug matches its named class or drug."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from rx_label_search.interactions.evidence import dailymed_url, evidence_for_term
from rx_label_search.interactions.tiers import tier_for_field, tier_name as lookup_tier_name
from rx_label_search.records import Alert, AlertEvidence, TermEvidence


def drug_own_names(drug: Mapping[str, Any]) -> frozenset[str]:
    """
    Takes one resolved drug's checker record.
    Reads its lowercase brand, generic, and substance names, plus its base ingredient names so a plain-name mention like "fluvoxamine" matches even when the label's own name carries a salt suffix.
    Gives the frozenset of names, empty when the record carries none.
    """
    record = drug["record"]
    names = (*record.get("brand_names", ()), *record.get("generic_names", ()), *record.get("ingredient_set", ()), *record.get("base_ingredients", ()))
    return frozenset(name.lower() for name in names if name)


def sentence_mentions_drug(sentence: str, other: Mapping[str, Any]) -> bool:
    """
    Takes a T17 evidence sentence and another listed drug's checker record.
    Checks whether the sentence names that drug or one of its pharmacologic classes.
    Gives True when it does, False otherwise.
    """
    lowered = sentence.lower()
    if any(name in lowered for name in drug_own_names(other)):
        return True
    return any(pharm_class.lower() in lowered for pharm_class in other["record"].get("pharm_class_epc", ()))


def t17_evidence(drug: Mapping[str, Any]) -> TermEvidence | None:
    """
    Takes one resolved drug's checker record.
    Reads its T17 evidence, if any.
    Gives the TermEvidence, or None when the drug carries no T17 tag.
    """
    for row in drug["record"]["evidence"]:
        if row["term_id"] == "T17":
            return TermEvidence(row["term_id"], row["field_name"], row["sentence"], row["rule_version"])
    return None


def build_pair_alert(source: Mapping[str, Any], other: Mapping[str, Any]) -> Alert | None:
    """
    Takes one resolved drug carrying T17 and one other listed drug.
    Checks whether the other drug matches a drug or class named in the source drug's contraindication sentence.
    Gives the Alert, or None when the sentence does not name the other drug or its class.
    """
    evidence = t17_evidence(source)
    if evidence is None or not sentence_mentions_drug(evidence.sentence, other):
        return None
    source_record, other_record = source["record"], other["record"]
    member_source = evidence_for_term(source["display_name"], source_record["set_id"], source_record["effective_time"], evidence)
    member_other = AlertEvidence(
        drug_name=other["display_name"],
        set_id=other_record["set_id"],
        effective_time=other_record["effective_time"],
        section="",
        sentence="",
        dailymed_url=dailymed_url(other_record["set_id"]),
    )
    tier = tier_for_field(evidence.field_name)
    return Alert(
        kind="pair",
        risk="T17",
        title=f"{other['display_name']} matches a contraindication named in {source['display_name']}'s label",
        tier=tier,
        tier_name=f"{lookup_tier_name(tier)} (heuristic)",
        members=(member_source, member_other),
        note="",
    )


def build_pair_alerts(drugs: Sequence[Mapping[str, Any]]) -> tuple[Alert, ...]:
    """
    Takes the resolved drugs on a medication list.
    Checks every drug carrying T17 against every other listed drug.
    Gives the tuple of pair alerts, empty when no listed drug matches another's contraindication.
    """
    alerts: list[Alert] = []
    for source in drugs:
        for other in drugs:
            if source is other:
                continue
            alert = build_pair_alert(source, other)
            if alert is not None:
                alerts.append(alert)
    return tuple(alerts)
