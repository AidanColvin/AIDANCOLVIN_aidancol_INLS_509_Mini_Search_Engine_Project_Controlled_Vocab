"""Pure pair-alert detection: drug A carries T17, and another listed drug matches its named class or drug."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from typing import Any

from rx_label_search.interactions.evidence import dailymed_url, evidence_for_term
from rx_label_search.interactions.tiers import tier_for_field, tier_name as lookup_tier_name
from rx_label_search.records import Alert, AlertEvidence, TermEvidence
from rx_label_search.vocabulary.interaction import is_self_reference_only

_BULLET_SPLIT = re.compile(r"•")


def drug_own_names(drug: Mapping[str, Any]) -> frozenset[str]:
    """
    Takes one resolved drug's checker record.
    Reads its lowercase brand, generic, and substance names, plus its base ingredient names so a plain-name mention like "fluvoxamine" matches even when the label's own name carries a salt suffix.
    Gives the frozenset of names, empty when the record carries none.
    """
    record = drug["record"]
    names = (*record.get("brand_names", ()), *record.get("generic_names", ()), *record.get("ingredient_set", ()), *record.get("base_ingredients", ()))
    return frozenset(name.lower() for name in names if name)


def combination_clauses(sentence: str) -> tuple[str, ...]:
    """
    Takes a T17 evidence sentence, which may bundle several bullet-separated clauses into one string.
    Splits it on bullet markers and drops any clause that only states a hypersensitivity or self-reference, keeping only clauses about taking drugs together.
    Gives the tuple of remaining clauses, the whole sentence alone when it has no bullets and is not itself self-reference-only.
    """
    parts = tuple(part.strip() for part in _BULLET_SPLIT.split(sentence) if part.strip())
    if len(parts) <= 1:
        return () if is_self_reference_only(sentence) else (sentence,)
    return tuple(part for part in parts if not is_self_reference_only(part))


def name_appears(text: str, name: str) -> bool:
    """
    Takes lowercase text and a lowercase name.
    Checks whether the name appears as whole words, not as a substring inside a longer name such as "venlafaxine" inside "desvenlafaxine".
    Gives True when it does, False otherwise.
    """
    return re.search(rf"\b{re.escape(name)}\b", text) is not None


def sentence_mentions_drug(sentence: str, other: Mapping[str, Any]) -> bool:
    """
    Takes a T17 evidence sentence and another listed drug's checker record.
    Checks the sentence's combination clauses, not any hypersensitivity clause, for that drug's name or pharmacologic class as whole words.
    Gives True when a combination clause names the drug or its class, False otherwise.
    """
    own_names = drug_own_names(other)
    pharm_classes = tuple(name.lower() for name in other["record"].get("pharm_class_epc", ()) if name)
    for clause in combination_clauses(sentence):
        lowered = clause.lower()
        if any(name_appears(lowered, name) for name in own_names):
            return True
        if any(name_appears(lowered, pharm_class) for pharm_class in pharm_classes):
            return True
    return False


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


def shares_base_ingredient(source: Mapping[str, Any], other: Mapping[str, Any]) -> bool:
    """
    Takes two resolved drugs.
    Checks whether any base ingredient of one is also a base ingredient of the other, as with Synthroid and levothyroxine, or Symbyax and Prozac.
    Gives True when they share one, False otherwise or when either lists none.
    """
    first = {name.lower() for name in source["record"].get("base_ingredients", ()) if name}
    second = {name.lower() for name in other["record"].get("base_ingredients", ()) if name}
    return bool(first & second)


def build_pair_alert(source: Mapping[str, Any], other: Mapping[str, Any]) -> Alert | None:
    """
    Takes one resolved drug carrying T17 and one other listed drug.
    Checks whether the other drug matches a drug or class named in the source drug's contraindication sentence, skipping a drug that shares the source's own ingredient, since a label naming its own ingredient is not a contraindicated combination and the duplication flag already covers it.
    Gives the Alert, or None when the sentence does not name the other drug or its class, or the two share an ingredient.
    """
    evidence = t17_evidence(source)
    if evidence is None or shares_base_ingredient(source, other) or not sentence_mentions_drug(evidence.sentence, other):
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
