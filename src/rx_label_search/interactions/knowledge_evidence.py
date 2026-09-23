"""Build-time search for the FDA label sentence behind each interaction rule, so an alert can quote the label rather than paraphrase it."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

from rx_label_search.interactions.knowledge import Knowledge, member_matches
from rx_label_search.normalize.rollup import base_ingredients
from rx_label_search.text.fields import field_values
from rx_label_search.text.sentences import split_sentences

SECTION_ORDER: tuple[str, ...] = ("contraindications", "boxed_warning", "warnings_and_cautions", "warnings", "precautions", "drug_interactions")
MAX_SENTENCE_CHARS = 600
FAMILY_WORDS: dict[str, str] = {
    "cns": r"respiratory depression|CNS depress|central nervous system depress|sedation",
    "serotonin": r"serotonin syndrome|serotonergic",
    "qt": r"\bQT\b|torsade",
    "electrolyte": r"hypokalemia|hypomagnesemia|potassium",
    "bleeding": r"bleeding|hemorrhage",
    "hyperkalemia": r"hyperkalemia|serum potassium",
    "kidney": r"renal (?:function|failure|impairment|toxicity)|kidney injury|nephrotoxic",
    "hypotension": r"hypotension|blood pressure",
    "bradycardia": r"bradycardia|heart block|AV block|atrioventricular",
    "hypoglycemia": r"hypoglycemia|blood glucose",
    "anticholinergic": r"anticholinergic",
    "antagonism": r"anticholinergic|cholinergic",
    "seizure": r"seizure",
    "sodium": r"hyponatremia|SIADH",
}
CLASS_SYNONYMS: dict[str, tuple[str, ...]] = {
    "maoi_nonselective": ("MAOI", "MAO inhibitor", "monoamine oxidase inhibitor"),
    "mao_b_inhibitor": ("MAO-B",),
    "reuptake_inhibitor": ("SSRI", "SNRI", "serotonin reuptake inhibitor", "serotonin and norepinephrine reuptake", "antidepressant"),
    "ssri": ("SSRI", "selective serotonin reuptake"),
    "snri": ("SNRI",),
    "tca": ("tricyclic",),
    "triptan": ("triptan", "5-HT1"),
    "sympathomimetic": ("sympathomimetic", "amphetamine", "stimulant", "pressor"),
    "benzodiazepine": ("benzodiazepine",),
    "opioid": ("opioid",),
    "opioid_3a4_substrate": ("opioid",),
    "gabapentinoid": ("gabapentin", "pregabalin"),
    "opioid_antagonist": ("naltrexone", "opioid antagonist"),
    "cyp3a4_inhibitor": ("CYP3A4 inhibitor", "CYP3A inhibitor", "inhibitors of CYP3A"),
    "strong_cyp3a4_inhibitor": ("strong CYP3A4 inhibitor", "strong CYP3A inhibitor", "potent CYP3A4 inhibitor", "strong inhibitors of CYP3A"),
    "moderate_cyp3a4_inhibitor": ("moderate CYP3A4 inhibitor", "moderate CYP3A inhibitor", "CYP3A4 inhibitor"),
    "strong_cyp3a4_inducer": ("CYP3A4 inducer", "CYP3A inducer", "strong inducer", "enzyme-inducing", "enzyme inducer"),
    "cyp3a4_inducer": ("CYP3A4 inducer", "CYP3A inducer", "inducer"),
    "strong_cyp2d6_inhibitor": ("CYP2D6 inhibitor", "strong CYP2D6", "inhibitors of CYP2D6"),
    "cyp2d6_inhibitor": ("CYP2D6 inhibitor", "inhibitors of CYP2D6"),
    "cyp1a2_strong_inhibitor": ("CYP1A2 inhibitor", "inhibitors of CYP1A2"),
    "pgp_inhibitor": ("P-gp inhibitor", "P-glycoprotein inhibitor", "P-gp"),
    "nsaid": ("NSAID", "nonsteroidal anti-inflammatory"),
    "raas_blocker": ("ACE inhibitor", "angiotensin", "renin-angiotensin"),
    "thiazide": ("thiazide", "diuretic"),
    "loop_diuretic": ("loop diuretic", "diuretic"),
    "nitrate": ("nitrate", "nitric oxide donor"),
    "pde5_inhibitor": ("PDE5", "PDE-5", "phosphodiesterase"),
    "beta_blocker": ("beta-blocker", "beta-adrenergic blocker", "beta blocker"),
    "nondhp_ccb": ("calcium channel blocker", "calcium-channel blocker"),
    "polyvalent_cation": ("antacid", "calcium", "iron", "magnesium", "aluminum", "zinc", "multivalent cation", "sucralfate"),
    "levothyroxine_binder": ("calcium", "iron", "antacid", "bile acid sequestrant", "sucralfate"),
    "hormonal_contraceptive": ("contracepti", "estrogen", "ethinyl estradiol"),
    "d2_blocker": ("dopamine antagonist", "dopamine receptor antagonist", "antipsychotic", "neuroleptic"),
    "systemic_corticosteroid": ("corticosteroid",),
    "carbapenem": ("carbapenem",),
    "penicillin": ("penicillin",),
    "ppi": ("proton pump inhibitor",),
    "statin": ("HMG-CoA", "statin"),
    "sulfonylurea": ("sulfonylurea",),
    "glp1_agonist": ("oral medication", "gastric emptying"),
    "stimulant": ("stimulant",),
    "sedating_antipsychotic": ("antipsychotic",),
}


def side_items(rule: Mapping[str, Any], which: str) -> list[str]:
    """
    Takes a pair rule and "a" or "b".
    Reads that side's class and ingredient names.
    Gives the list as written in the rule.
    """
    return list(rule[which])


def partner_pattern(rule: Mapping[str, Any], knowledge: Knowledge) -> re.Pattern[str]:
    """
    Takes a pair rule and the knowledge table.
    Builds one case-insensitive pattern for the partner side: every member ingredient's name, plus class phrases such as "CYP3A4 inhibitor" or "MAOI".
    Gives the compiled pattern.
    """
    partner = "b" if rule.get("label_side", "a") == "a" else "a"
    items = side_items(rule, partner)
    words: set[str] = set(knowledge.of(items))
    for item in items:
        words.update(CLASS_SYNONYMS.get(item, ()))
    alternatives = sorted((re.escape(word) for word in words if len(word) > 3), key=len, reverse=True)
    return re.compile(r"\b(?:" + "|".join(alternatives) + r")", re.IGNORECASE)


def group_pattern(group: Mapping[str, Any]) -> re.Pattern[str]:
    """
    Takes a group rule.
    Builds the pattern for its syndrome, taken with another drug ("concomitant", "with other", "combination").
    Gives the compiled pattern.
    """
    syndrome = FAMILY_WORDS.get(group.get("family", ""), re.escape(group.get("category", "")))
    return re.compile(rf"(?=.*(?:{syndrome}))(?=.*(?:concomitant|with other|combination|coadminist|co-administ|together|taking))", re.IGNORECASE)


def rule_patterns(knowledge: Knowledge) -> list[tuple[str, frozenset[str], re.Pattern[str]]]:
    """
    Takes the knowledge table.
    Pairs each pair and group rule with the ingredients whose labels should hold its sentence and the pattern that finds it.
    Gives (rule id, label-side members, pattern) triples.
    """
    triples: list[tuple[str, frozenset[str], re.Pattern[str]]] = []
    for rule in knowledge.table.get("pairs", ()):
        side = "a" if rule.get("label_side", "a") == "a" else "b"
        triples.append((rule["id"], knowledge.of(side_items(rule, side)), partner_pattern(rule, knowledge)))
    for group in knowledge.table.get("groups", ()):
        triples.append((group["id"], knowledge.of([group.get("label_side", group["classes"][0])]), group_pattern(group)))
    return triples


def first_hit(record: Mapping[str, Any], pattern: re.Pattern[str]) -> tuple[str, str] | None:
    """
    Takes one raw label record and a pattern.
    Searches the interaction-relevant sections in order of weight, contraindications first, sentence by sentence.
    Gives (section, sentence) for the first match, or None.
    """
    for section in SECTION_ORDER:
        for text in field_values(record, section):
            for sentence in split_sentences(text):
                if len(sentence) <= MAX_SENTENCE_CHARS and pattern.search(sentence):
                    return section, sentence
    return None


def build_rule_evidence(records: Iterable[Mapping[str, Any]], knowledge: Knowledge, salt_to_base: Mapping[str, Iterable[str]]) -> dict[str, Any]:
    """
    Takes the raw label records, the knowledge table, and the salt-to-base map.
    Finds, for every rule and every label on its label side, the first sentence that names the partner drug or class (or, for a group, the syndrome with co-use).
    Gives {"by_set": {rule: {set_id: hit}}, "by_base": {rule: {base: hit}}}, each hit holding the section, sentence, and set id.
    """
    triples = rule_patterns(knowledge)
    by_set: dict[str, dict[str, dict[str, str]]] = {}
    by_base: dict[str, dict[str, dict[str, str]]] = {}
    for record in records:
        substances = field_values(record.get("openfda") or {}, "substance_name")
        bases = base_ingredients(tuple(name.upper() for name in substances), {key: tuple(value) for key, value in salt_to_base.items()})
        set_id = str(record.get("set_id", ""))
        for rule_id, side, pattern in triples:
            on_side = [base for base in bases if member_matches(base, side)]
            if not on_side:
                continue
            hit = first_hit(record, pattern)
            if hit is None:
                continue
            entry = {"section": hit[0], "sentence": hit[1], "set_id": set_id}
            by_set.setdefault(rule_id, {})[set_id] = entry
            for base in on_side:
                by_base.setdefault(rule_id, {}).setdefault(base, entry)
    return {"by_set": by_set, "by_base": by_base}
