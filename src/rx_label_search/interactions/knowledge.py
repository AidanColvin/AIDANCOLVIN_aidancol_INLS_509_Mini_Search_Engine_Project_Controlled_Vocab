"""Pure class-level interaction rules: shared-effect groups, perpetrator-victim pairs, therapeutic duplication, and dose ceilings, each graded A to E with its mechanism, action, and sources."""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

from rx_label_search.interactions.evidence import dailymed_url
from rx_label_search.interactions.grades import GRADE_ORDER, section_name
from rx_label_search.interactions.totals import daily_mg, format_amount
from rx_label_search.records import Alert, AlertEvidence

Drug = Mapping[str, Any]
LABEL_FAMILIES: dict[str, str] = {"T14": "serotonin", "T15": "cns", "T16": "qt"}


def expand_members(classes: Mapping[str, Mapping[str, Any]], items: Sequence[str], seen: frozenset[str] = frozenset()) -> frozenset[str]:
    """
    Takes the class table, a list of class names, "@class" references, or single ingredient names, and the classes already being expanded.
    Expands every class into its members, following "@" references without looping.
    Gives the lowercase ingredient names.
    """
    found: set[str] = set()
    for item in items:
        name = item[1:] if item.startswith("@") else item
        if name in classes and name not in seen:
            found |= expand_members(classes, classes[name]["members"], seen | {name})
        elif not item.startswith("@"):
            found.add(item.lower())
    return frozenset(found)


def member_matches(base: str, members: frozenset[str]) -> bool:
    """
    Takes one base ingredient name and a set of class members.
    Checks for the name itself, or a member it extends by a space (lithium matches lithium carbonate).
    Gives True when the base belongs to the members.
    """
    low = base.lower()
    if low in members:
        return True
    parts = low.split(" ")
    return any(" ".join(parts[:end]) in members for end in range(1, len(parts)))


def drug_bases(drug: Drug) -> tuple[str, ...]:
    """
    Takes one resolved drug.
    Reads its base ingredients.
    Gives the lowercase names.
    """
    return tuple(name.lower() for name in drug["record"].get("base_ingredients", ()))


def matched(drugs: Sequence[Drug], members: frozenset[str]) -> list[tuple[int, str]]:
    """
    Takes the resolved drugs and a set of class members.
    Finds every (drug position, base ingredient) pair where the ingredient belongs to the members.
    Gives the pairs in list order.
    """
    return [(index, base) for index, drug in enumerate(drugs) for base in drug_bases(drug) if member_matches(base, members)]


def molecule_count(hits: Sequence[tuple[int, str]]) -> int:
    """
    Takes (drug position, ingredient) hits for one class.
    Counts separate medicines: ingredients from one entry count once (Adderall's two amphetamines are one drug), and entries that share an ingredient count once (Zoloft and generic sertraline).
    Gives the number of separate medicines.
    """
    clusters: list[set[str]] = []
    by_entry: dict[int, set[str]] = {}
    for index, base in hits:
        by_entry.setdefault(index, set()).add(base)
    for bases in by_entry.values():
        joined = [cluster for cluster in clusters if cluster & bases]
        merged = set(bases).union(*joined) if joined else set(bases)
        clusters = [cluster for cluster in clusters if not cluster & bases] + [merged]
    return len(clusters)


def distinct_sides(sides: Sequence[frozenset[str]], ingredients: Sequence[str]) -> bool:
    """
    Takes class member sets and the distinct ingredients present.
    Tries to give each side its own different ingredient.
    Gives True when every side gets one.
    """
    def assign(index: int, used: frozenset[str]) -> bool:
        """
        Takes the side to fill next and the ingredients already used.
        Tries each unused ingredient that fits this side, then the remaining sides.
        Gives True when all remaining sides can be filled.
        """
        if index == len(sides):
            return True
        return any(assign(index + 1, used | {name}) for name in ingredients if name not in used and member_matches(name, sides[index]))

    return assign(0, frozenset())


class Knowledge:
    """The loaded rule table, with every class expanded once."""

    def __init__(self, table: Mapping[str, Any]) -> None:
        """
        Takes the parsed interaction_knowledge.json table.
        Expands every class and keeps the rules, references, ceilings, and MME factors.
        Gives nothing; the instance holds the expanded table.
        """
        self.table = table
        self.classes: Mapping[str, Mapping[str, Any]] = table["classes"]
        self.members: dict[str, frozenset[str]] = {name: expand_members(self.classes, [name]) for name in self.classes}
        self.references: Mapping[str, Mapping[str, str]] = table.get("references", {})
        self.ceilings: Mapping[str, Mapping[str, Any]] = table.get("dose_ceilings", {})
        self.mme_factors: Mapping[str, float] = table.get("mme_factors", {})

    def of(self, items: Sequence[str]) -> frozenset[str]:
        """
        Takes class names or ingredient names.
        Expands them into one member set.
        Gives the lowercase ingredient names.
        """
        return expand_members(self.classes, items)

    def refs(self, ids: Sequence[str]) -> tuple[tuple[str, str], ...]:
        """
        Takes reference ids.
        Looks each up in the reference table.
        Gives (label, url) pairs for the ids that exist.
        """
        return tuple((self.references[ref]["label"], self.references[ref]["url"]) for ref in ids if ref in self.references)


def max_grade(*grades: str) -> str:
    """
    Takes grade letters.
    Picks the most severe.
    Gives the letter, "A" when none are given.
    """
    present = [grade for grade in grades if grade in GRADE_ORDER]
    return max(present, key=GRADE_ORDER.index) if present else "A"


def evidence_member(drug: Drug, rule_id: str, rule_evidence: Mapping[str, Any], quote: bool) -> AlertEvidence:
    """
    Takes one resolved drug, the rule id, the build-time rule evidence index, and whether this drug's label is the one to quote.
    Finds the label sentence the index holds for this rule and this drug's own label (or, failing that, another label of the same ingredient).
    Gives the AlertEvidence, with the drug's DailyMed link and an empty sentence when nothing is quoted.
    """
    record = drug["record"]
    set_id = record.get("set_id", "")
    name = drug["display_name"]
    url = dailymed_url(set_id, " ".join(drug_bases(drug)))
    if quote:
        by_set = rule_evidence.get("by_set", {}).get(rule_id, {})
        hit = by_set.get(set_id)
        if hit is None:
            by_base = rule_evidence.get("by_base", {}).get(rule_id, {})
            hit = next((by_base[base] for base in drug_bases(drug) if base in by_base), None)
        if hit is not None:
            hit_set = hit.get("set_id", set_id)
            return AlertEvidence(name, hit_set, record.get("effective_time", ""), hit["section"], hit["sentence"], dailymed_url(hit_set))
    return AlertEvidence(name, set_id, record.get("effective_time", ""), "", "", url)


def label_basis(members: Sequence[AlertEvidence], rows: Sequence[int], fallback: str) -> str:
    """
    Takes an alert's members, the rulebook rows it implements, and the rule's own risk text.
    Writes why the grade was given: the label section that states it when one was quoted, and the rulebook row.
    Gives the basis sentence.
    """
    quoted = next((member for member in members if member.sentence and member.section), None)
    row_text = f" Clinical rulebook row {', '.join(str(row) for row in rows)}." if rows else ""
    if quoted is not None:
        return f"The {section_name(quoted.section)} section of the {quoted.drug_name} label addresses this combination: {fallback}.{row_text}"
    return f"Class rule: {fallback}.{row_text}"


def distinct_names(drugs: Sequence[Drug], indexes: Sequence[int]) -> list[int]:
    """
    Takes the resolved drugs and positions.
    Drops repeated positions, keeping list order.
    Gives the unique positions.
    """
    seen: list[int] = []
    for index in indexes:
        if index not in seen:
            seen.append(index)
    return sorted(seen)


def build_alert(drugs: Sequence[Drug], indexes: Sequence[int], rule: Mapping[str, Any], knowledge: Knowledge, rule_evidence: Mapping[str, Any], title: str, grade: str, kind: str, quote_side: frozenset[str]) -> Alert:
    """
    Takes the resolved drugs, the positions in this alert, the rule, the knowledge table, the evidence index, the title, the grade, the alert kind, and the members whose label should be quoted.
    Assembles one graded Alert with a member per drug, the quoted label sentence where one exists, and the rule's mechanism, action, rows, and sources.
    Gives the Alert.
    """
    positions = distinct_names(drugs, indexes)
    members = tuple(evidence_member(drugs[index], rule["id"], rule_evidence, any(member_matches(base, quote_side) for base in drug_bases(drugs[index]))) for index in positions)
    rows = tuple(rule.get("rows", ()))
    return Alert(
        kind=kind,
        risk=rule["id"],
        title=title,
        tier=None,
        tier_name=rule.get("category", ""),
        members=members,
        note="",
        grade=grade,
        basis=label_basis(members, rows, rule.get("risk", "")),
        category=rule.get("category", ""),
        family=rule.get("family", ""),
        mechanism=rule.get("mechanism", ""),
        action=rule.get("action", ""),
        rulebook_rows=rows,
        references=knowledge.refs(rule.get("refs", ())),
        rule_id=rule["id"],
    )


def group_grade(group: Mapping[str, Any], present: Sequence[str], knowledge: Knowledge, count: int) -> str | None:
    """
    Takes one group rule, the distinct ingredients of the list that belong to it, the knowledge table, and the number of separate medicines they come from.
    Checks its requirements (minimum count, required classes, conditions) and works out its grade with any escalations.
    Gives the grade letter, or None when the group does not apply.
    """
    if count < group.get("min_members", 2):
        return None
    if group.get("anchor") and not any(member_matches(name, knowledge.of([group["anchor"]])) for name in present):
        return None
    required = group.get("require_any")
    if required and not any(member_matches(name, knowledge.of(required)) for name in present):
        return None
    need_distinct = group.get("require_all_distinct")
    if need_distinct and not distinct_sides([knowledge.of([name]) for name in need_distinct], present):
        return None
    grade = group.get("grade", "C")
    conditions = group.get("conditions")
    if conditions:
        met = [condition["grade"] for condition in conditions if condition_met(condition, present, knowledge, count)]
        if not met:
            return None
        grade = max_grade(*met)
    for escalation in group.get("escalate", ()):
        if condition_met(escalation, present, knowledge, count):
            grade = max_grade(grade, escalation["grade"])
    return grade


def condition_met(condition: Mapping[str, Any], present: Sequence[str], knowledge: Knowledge, count: int) -> bool:
    """
    Takes one condition ({"has": classes, "min_members": n, "count_of": class, "min": n}), the distinct ingredients present, the knowledge table, and the number of separate medicines.
    Checks each part: every "has" class holds its own ingredient, the total reaches min_members, and the "count_of" class reaches min.
    Gives True when every stated part holds.
    """
    has = condition.get("has")
    if has and not distinct_sides([knowledge.of([name]) for name in has], present):
        return False
    if count < condition.get("min_members", 0):
        return False
    count_of = condition.get("count_of")
    if count_of and sum(member_matches(name, knowledge.of([count_of])) for name in present) < condition.get("min", 0):
        return False
    return True


def group_alerts(drugs: Sequence[Drug], knowledge: Knowledge, rule_evidence: Mapping[str, Any]) -> list[Alert]:
    """
    Takes the resolved drugs, the knowledge table, and the evidence index.
    Applies every shared-effect group rule, counting distinct ingredients so one drug entered twice counts once.
    Gives one alert per group that applies, titled with the count and the risk ("3 CNS depressants: ...").
    """
    alerts: list[Alert] = []
    for group in knowledge.table.get("groups", ()):
        members = knowledge.of(group["classes"])
        hits = matched(drugs, members)
        present = sorted({base for _, base in hits})
        count = molecule_count(hits)
        grade = group_grade(group, present, knowledge, count)
        if grade is None:
            continue
        plural = knowledge.classes.get(group["classes"][0], {}).get("plural", "drugs") if len(group["classes"]) == 1 else "drugs"
        title = f"{count} {plural}: {group['risk']}"
        quote_side = knowledge.of([group.get("label_side", group["classes"][0])])
        alerts.append(build_alert(drugs, [index for index, _ in hits], group, knowledge, rule_evidence, title, grade, "group", quote_side))
    return alerts


def pair_grade(rule: Mapping[str, Any], victim: Drug, perpetrator_base: str, totals: Sequence[Mapping[str, Any]]) -> str:
    """
    Takes one pair rule, the victim drug, the perpetrator ingredient, and the per-ingredient totals.
    Applies the rule's dose caps: a victim above the label's cap for this perpetrator (or any dose when the cap is 0) gets the over-cap grade.
    Gives the grade letter.
    """
    grade = rule["grade"]
    caps = rule.get("dose_caps", {})
    victim_bases = [base for base in drug_bases(victim)]
    victim_dose = next((dose for base in victim_bases if (dose := daily_mg(totals, base)) is not None), None)
    if perpetrator_base in caps:
        cap = caps[perpetrator_base]
        if cap == 0 or (victim_dose is not None and victim_dose > cap):
            return rule.get("over_cap_grade", grade)
    cap_a = rule.get("dose_caps_a")
    if cap_a is not None and victim_dose is not None and victim_dose > cap_a:
        return rule.get("over_cap_grade", grade)
    return grade


def pair_alerts(drugs: Sequence[Drug], knowledge: Knowledge, rule_evidence: Mapping[str, Any], totals: Sequence[Mapping[str, Any]]) -> list[Alert]:
    """
    Takes the resolved drugs, the knowledge table, the evidence index, and the per-ingredient totals.
    Applies every pair rule across different entries and different ingredients, and merges the hits for one victim into a single alert naming every perpetrator.
    Gives the pair alerts.
    """
    alerts: list[Alert] = []
    for rule in knowledge.table.get("pairs", ()):
        side_a = knowledge.of(rule["a"])
        side_b = knowledge.of(rule["b"]) - frozenset(name.lower() for name in rule.get("exclude_b", ()))
        merged: dict[tuple[str, ...], dict[str, Any]] = {}
        for a_index, a_base in matched(drugs, side_a):
            for b_index, b_base in matched(drugs, side_b):
                if a_index == b_index or a_base == b_base or b_base in drug_bases(drugs[a_index]):
                    continue
                key = tuple(sorted(drug_bases(drugs[a_index])))
                slot = merged.setdefault(key, {"a": [], "b": [], "b_bases": [], "grade": "A"})
                slot["a"].append(a_index)
                slot["b"].append(b_index)
                if b_base not in slot["b_bases"]:
                    slot["b_bases"].append(b_base)
                slot["grade"] = max_grade(slot["grade"], pair_grade(rule, drugs[a_index], b_base, totals))
        for slot in merged.values():
            a_name = drugs[slot["a"][0]]["display_name"]
            b_positions = distinct_names(drugs, slot["b"])
            if len(b_positions) == 1:
                title = f"{a_name} with {drugs[b_positions[0]]['display_name']}: {rule['risk']}"
            else:
                title = f"{a_name} with {len(b_positions)} {rule.get('b_plural', 'drugs')}: {rule['risk']}"
            quote_side = side_a if rule.get("label_side", "a") == "a" else side_b
            alerts.append(build_alert(drugs, [*slot["a"], *slot["b"]], rule, knowledge, rule_evidence, title, slot["grade"], "pair", quote_side))
    return alerts


def duplicate_class_alerts(drugs: Sequence[Drug], knowledge: Knowledge, rule_evidence: Mapping[str, Any]) -> list[Alert]:
    """
    Takes the resolved drugs, the knowledge table, and the evidence index.
    Flags two or more different ingredients of one therapeutic class taken from different entries (two SSRIs, two NSAIDs, three antipsychotics).
    Gives one duplicate-therapy alert per class that applies.
    """
    alerts: list[Alert] = []
    for rule in knowledge.table.get("duplicate_classes", ()):
        members = knowledge.of([rule["class"]])
        hits = matched(drugs, members)
        by_ingredient: dict[str, set[int]] = {}
        for index, base in hits:
            by_ingredient.setdefault(base, set()).add(index)
        entries = {index for index, _ in hits}
        if len(by_ingredient) < 2 or len(entries) < 2:
            continue
        if any(len({index for index, base in hits if base != other}) == 0 for other in by_ingredient):
            continue
        required = rule.get("require_any")
        if required and not any(member_matches(base, knowledge.of(required)) for base in by_ingredient):
            continue
        plural = knowledge.classes[rule["class"]]["plural"]
        full = {**rule, "category": "duplicate therapy", "mechanism": f"These are all {plural}: taking more than one is therapeutic duplication.", "rows": []}
        title = f"{len(by_ingredient)} {plural}: {rule['risk']}"
        alerts.append(build_alert(drugs, sorted(entries), full, knowledge, rule_evidence, title, rule["grade"], "duplication", frozenset()))
    return alerts


def ceiling_alerts(drugs: Sequence[Drug], knowledge: Knowledge, totals: Sequence[Mapping[str, Any]]) -> list[Alert]:
    """
    Takes the resolved drugs, the knowledge table, and the per-ingredient totals.
    Compares each ingredient's daily total, added up across entries, with its labeled maximum: above it is flagged at the ceiling's grade, exactly at it at grade A.
    Gives the dose-ceiling alerts.
    """
    alerts: list[Alert] = []
    for row in totals:
        if row["period"] != "day" or row["unit"] != "mg":
            continue
        ceiling = ceiling_for(row["ingredient"], knowledge.ceilings)
        if ceiling is None:
            continue
        limit = float(ceiling["max_mg_per_day"])
        total = float(row["total"])
        if total < limit * 0.995:
            continue
        over = total > limit * 1.005
        grade = ceiling["grade"] if over else "A"
        where = "above" if over else "at"
        amount = format_amount(total, "mg")
        maximum = format_amount(limit, "mg")
        max_word = "maximum" if not row["as_needed"] else "maximum if every as-needed dose is taken"
        title = f"{row['ingredient']} {amount}/day is {where} the labeled maximum of {maximum}/day ({max_word})"
        indexes = [index for index, drug in enumerate(drugs) if any(member_matches(base, frozenset({row["ingredient"]})) or base in row["ingredient"].split("/") for base in drug_bases(drug))]
        members = tuple(AlertEvidence(drugs[index]["display_name"], drugs[index]["record"].get("set_id", ""), drugs[index]["record"].get("effective_time", ""), "", "", dailymed_url(drugs[index]["record"].get("set_id", ""), row["ingredient"])) for index in indexes)
        risk = ceiling["risk"]
        note = f" ({ceiling['note']})" if ceiling.get("note") else ""
        alerts.append(Alert(
            kind="ceiling", risk="dose_ceiling", title=title, tier=None, tier_name="dose ceiling", members=members, note="",
            grade=grade, basis=f"Daily total {amount} against a labeled maximum of {maximum}{note}.",
            category="dose ceiling", family="dose",
            mechanism=f"The total counts every entry of {row['ingredient']}, including combination products. Above the maximum the risk is {risk}." if over else f"The total counts every entry of {row['ingredient']}; it is at the labeled maximum, not over it.",
            action="Lower the total to the labeled maximum or less." if over else "No change needed for the ceiling; do not add more from any source.",
        ))
    return alerts


def ceiling_for(ingredient: str, ceilings: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any] | None:
    """
    Takes an ingredient (or a slash-joined product such as "amphetamine/dextroamphetamine") and the ceiling table.
    Finds the ceiling for the ingredient, or for a product whose parts match a ceiling's combination_of list.
    Gives the ceiling entry, or None.
    """
    if ingredient in ceilings:
        return ceilings[ingredient]
    parts = set(ingredient.split("/"))
    for ceiling in ceilings.values():
        if set(ceiling.get("combination_of", ())) == parts:
            return ceiling
    return None


def alert_drug_indexes(alert: Alert, drugs: Sequence[Drug]) -> frozenset[str]:
    """
    Takes an alert and the resolved drugs.
    Collects the display names of its members.
    Gives the names as a frozenset.
    """
    return frozenset(member.drug_name for member in alert.members)


ABSORBABLE: frozenset[str] = frozenset({"opioid_benzodiazepine", "opioid_gabapentinoid", "clozapine_benzodiazepine", "beta_blocker_nondhp", "alpha_blocker_pde5"})


def dedupe_pairs(alerts: Sequence[Alert]) -> list[Alert]:
    """
    Takes alerts.
    Keeps only the most severe of several pair alerts that name the same drugs for the same syndrome (a booster that is both a strong and a moderate inhibitor fires two rules).
    Gives the alerts without those repeats, in their original order.
    """
    best: dict[tuple[frozenset[str], str], Alert] = {}
    for alert in alerts:
        if alert.kind != "pair":
            continue
        key = (alert_drug_indexes(alert, ()), alert.category)
        if key not in best or GRADE_ORDER.index(alert.grade or "A") > GRADE_ORDER.index(best[key].grade or "A"):
            best[key] = alert
    keep = set(map(id, best.values()))
    return [alert for alert in alerts if alert.kind != "pair" or id(alert) in keep]


def absorb(alerts: Sequence[Alert]) -> list[Alert]:
    """
    Takes the knowledge alerts.
    Folds a pair alert into a group alert of the same family when the group already names all its drugs at the same or a higher grade, keeping the pair's point as an "includes" line.
    Gives the alerts that remain.
    """
    groups = [alert for alert in alerts if alert.kind == "group"]
    kept: list[Alert] = []
    folded: dict[int, list[str]] = {}
    for alert in alerts:
        if alert.kind != "pair":
            continue
        names = alert_drug_indexes(alert, ())
        home = next((position for position, group in enumerate(groups) if group.family == alert.family and (group.category == alert.category or alert.rule_id in ABSORBABLE) and names <= alert_drug_indexes(group, ()) and GRADE_ORDER.index(group.grade or "A") >= GRADE_ORDER.index(alert.grade or "A")), None)
        if home is None:
            kept.append(alert)
        else:
            folded.setdefault(home, []).append(f"{alert.title}. {alert.mechanism}")
    merged_groups = [dataclasses.replace(group, includes=(*group.includes, *folded.get(position, ()))) for position, group in enumerate(groups)]
    others = [alert for alert in alerts if alert.kind not in ("group", "pair")]
    return [*merged_groups, *kept, *others]


def merge_label_alerts(knowledge_alerts: Sequence[Alert], label_alerts: Sequence[Alert], drugs: Sequence[Drug] = ()) -> list[Alert]:
    """
    Takes the knowledge alerts, the label-driven group and pair alerts, and the resolved drugs.
    Moves each label alert's quoted sentences into the rule alert that covers at least two of its drugs for the same syndrome (the rule's grade stands; a label pair with no rule keeps its own grade), drops label alerts about one drug entered twice, and keeps any other label group as a grade A note that both labels mention the risk.
    Gives the combined alert list.
    """
    result = list(knowledge_alerts)
    leftovers: list[Alert] = []
    for label_alert in label_alerts:
        names = alert_drug_indexes(label_alert, ())
        if len(names) < 2 or same_molecule(label_alert, drugs):
            continue
        family = LABEL_FAMILIES.get(label_alert.risk)
        home = next((position for position, alert in enumerate(result) if alert.kind in ("group", "pair") and len(names & alert_drug_indexes(alert, ())) >= 2 and (family is None or alert.family == family) and (family is not None or names <= alert_drug_indexes(alert, ()))), None)
        if home is None:
            leftovers.append(label_alert if label_alert.kind == "pair" else dataclasses.replace(label_alert, grade="A", basis="These labels each mention this risk, but no class rule applies to this combination.", category=label_alert.title, family=family or ""))
            continue
        target = result[home]
        quoted = {member.drug_name: member for member in label_alert.members if member.sentence}
        members = tuple(member if member.sentence else quoted.get(member.drug_name, member) for member in target.members)
        result[home] = dataclasses.replace(target, members=members)
    return [*result, *leftovers]


def same_molecule(alert: Alert, drugs: Sequence[Drug]) -> bool:
    """
    Takes a label alert and the resolved drugs.
    Checks whether all its drugs share one set of ingredients, as with OxyContin and Roxicodone.
    Gives True when they are one molecule.
    """
    names = alert_drug_indexes(alert, ())
    hits = [(index, base) for index, drug in enumerate(drugs) if drug["display_name"] in names for base in drug_bases(drug)]
    return molecule_count(hits) <= 1


def knowledge_alerts(drugs: Sequence[Drug], knowledge: Knowledge, rule_evidence: Mapping[str, Any], totals: Sequence[Mapping[str, Any]]) -> list[Alert]:
    """
    Takes the resolved drugs, the knowledge table, the evidence index, and the per-ingredient totals.
    Runs the group, pair, duplicate-class, and dose-ceiling rules and folds covered pairs into their groups.
    Gives the knowledge alerts.
    """
    found = [
        *group_alerts(drugs, knowledge, rule_evidence),
        *pair_alerts(drugs, knowledge, rule_evidence, totals),
        *duplicate_class_alerts(drugs, knowledge, rule_evidence),
        *ceiling_alerts(drugs, knowledge, totals),
    ]
    return absorb(dedupe_pairs(found))


RELEASE_WORDS = frozenset({"xr", "er", "sr", "xl", "cd", "la", "ds", "ir", "dr", "odt", "ec", "cr"})
DAY_TOKENS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


def typed_name_key(drug: Drug) -> str:
    """
    Takes one resolved drug.
    Reduces the name as typed (brand if given, else generic) to its words without release-form suffixes, so "Xanax" and "Xanax XR" read the same.
    Gives the lowercase key.
    """
    entry = drug["entry"]
    words = (entry.brand_text or entry.name_text or "").lower().replace("-", " ").split()
    return " ".join(word for word in words if word not in RELEASE_WORDS)


def schedule_days(drug: Drug) -> frozenset[str]:
    """
    Takes one resolved drug.
    Reads the named days of its schedule, such as Mon/Wed/Fri.
    Gives the three-letter day names, empty for a drug not on named days.
    """
    text = (drug["entry"].schedule_text or "").lower()
    return frozenset(day for day in DAY_TOKENS if day in text)


def is_split_schedule(first: Drug, second: Drug) -> bool:
    """
    Takes two resolved drugs with the same ingredient.
    Checks whether they are one regimen split across named days, such as warfarin 5 mg Mon/Wed/Fri and 2.5 mg on the other days.
    Gives True when both are on named days and the days do not overlap.
    """
    first_days, second_days = schedule_days(first), schedule_days(second)
    return bool(first_days) and bool(second_days) and not first_days & second_days


def grade_duplicates(alerts: Sequence[Alert], drugs: Sequence[Drug], knowledge: Knowledge, totals: Sequence[Mapping[str, Any]]) -> list[Alert]:
    """
    Takes the duplication alerts (shared ingredient or active metabolite), the resolved drugs, the knowledge table, and the per-ingredient totals.
    Drops a split named-day regimen, grades a duplicate D when it is hidden (different names for one drug, a combination product, or an active metabolite) or the combined dose passes the labeled maximum, and C when the same product was simply entered twice, and states the combined total.
    Gives the graded duplication alerts.
    """
    graded: list[Alert] = []
    for alert in alerts:
        names = [member.drug_name for member in alert.members]
        pair = [drug for drug in drugs if drug["display_name"] in names][:2]
        if len(pair) == 2 and pair[0]["display_name"] == pair[1]["display_name"]:
            pair = [drug for drug in drugs if drug["display_name"] == names[0]][:2]
        if len(pair) == 2 and is_split_schedule(pair[0], pair[1]):
            continue
        shared = sorted(set(drug_bases(pair[0])) & set(drug_bases(pair[1]))) if len(pair) == 2 else []
        counted = shared or sorted({base for drug in pair for base in drug_bases(drug)})
        rows = [row for row in totals if row["ingredient"] in counted]
        combined = " and ".join(f"{row['ingredient']} {row['text']}" for row in rows)
        over = [row for row in rows if (ceiling := ceiling_for(row["ingredient"], knowledge.ceilings)) and row["period"] == "day" and float(row["total"]) >= float(ceiling["max_mg_per_day"]) * 0.995]
        hidden = alert.risk == "active_metabolite" or (len(pair) == 2 and typed_name_key(pair[0]) != typed_name_key(pair[1]))
        grade = "D" if hidden or over else "C"
        ceiling_text = "".join(f"; {row['ingredient']} is at or above its labeled maximum of {format_amount(float(ceiling_for(row['ingredient'], knowledge.ceilings)['max_mg_per_day']), 'mg')}/day" for row in over)
        labelled = [f"{drug['display_name']} ({', '.join(drug_bases(drug))})" for drug in pair] if len(pair) == 2 else list(dict.fromkeys(names))
        if alert.risk == "active_metabolite":
            head = f"Duplicate: {labelled[0]} and {labelled[-1]}: one is the active metabolite of the other"
        elif hidden:
            head = f"Duplicate: {labelled[0]} and {labelled[-1]} are the same drug under different names"
        else:
            head = f"Duplicate: {labelled[0]} is entered on two lines"
        title = head + (f": combined {combined}" if combined else "") + ceiling_text
        basis = "Hidden duplication: the entries name one drug differently, so the doses add up unnoticed." if hidden else "The same product appears on two lines; the doses add up."
        graded.append(dataclasses.replace(
            alert, title=title, grade=grade, basis=basis, category="duplicate therapy", family="duplicate",
            mechanism="Both entries deliver the same active drug, so the patient gets the combined dose." + (" One is the active metabolite of the other." if alert.risk == "active_metabolite" else ""),
            action="Confirm whether both lines are meant. If one is a duplicate entry, remove it; if both are real, treat the combined total as the dose.",
        ))
    return graded
