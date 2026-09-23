"""Tests for the class-level interaction rules (interactions/knowledge.py) and per-ingredient totals (interactions/totals.py), run against the real rule table."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rx_label_search.interactions.knowledge import (
    Knowledge,
    grade_duplicates,
    knowledge_alerts,
    member_matches,
    merge_label_alerts,
    molecule_count,
)
from rx_label_search.interactions.totals import molecule_totals, total_mme
from rx_label_search.normalize.med_line_parser import parse_entry
from rx_label_search.records import Alert, AlertEvidence

KNOWLEDGE = Knowledge(json.loads((Path(__file__).resolve().parent.parent / "data" / "reference" / "interaction_knowledge.json").read_text()))


def drug(line: str, bases: tuple[str, ...], name: str | None = None) -> dict[str, Any]:
    """
    Takes a medication line, its base ingredients, and an optional display name.
    Builds a resolved-drug entry like the checker's, with a stub record.
    Gives the drug dictionary.
    """
    entry = parse_entry(line)
    return {"display_name": name or entry.brand_text or entry.name_text, "entry": entry, "record": {"set_id": "", "effective_time": "", "base_ingredients": bases, "evidence": []}}


def run(*drugs: dict[str, Any]) -> list[Alert]:
    """
    Takes resolved drugs.
    Runs the knowledge rules with per-ingredient totals and no label evidence.
    Gives the alerts.
    """
    totals = molecule_totals(list(drugs), KNOWLEDGE.mme_factors)
    return knowledge_alerts(list(drugs), KNOWLEDGE, {}, totals)


def grades_for(alerts: list[Alert], rule_id: str) -> list[str]:
    """
    Takes alerts and a rule id.
    Collects the grades of the alerts from that rule.
    Gives the grade letters.
    """
    return [alert.grade or "" for alert in alerts if alert.rule_id == rule_id]


def test_member_matches_a_longer_salt_name() -> None:
    """
    Takes no arguments.
    Checks that a class member matches a base name it starts, and not a different drug that merely contains it.
    Gives nothing; asserts lithium matches lithium carbonate and venlafaxine does not match desvenlafaxine.
    """
    assert member_matches("lithium carbonate", frozenset({"lithium"}))
    assert not member_matches("desvenlafaxine", frozenset({"venlafaxine"}))


def test_generalization_rows_fire_on_drugs_outside_the_pack() -> None:
    """
    Takes no arguments.
    Runs rulebook rows 4, 17, 21, 32, 35, and 36 on drugs that TEST_PACK.md's 41 lists never use together (the pack's generalization check).
    Gives nothing; asserts each row fires at its grade.
    """
    assert "D" in grades_for(run(drug("Depakote (divalproex sodium) 500 mg twice daily", ("valproate",)), drug("Merrem (meropenem) 1 g IV every 8 hours", ("meropenem",))), "valproate_carbapenem")
    assert "E" in grades_for(run(drug("Zanaflex (tizanidine) 4 mg three times daily", ("tizanidine",)), drug("Cipro (ciprofloxacin) 500 mg twice daily", ("ciprofloxacin",))), "tizanidine_1a2")
    assert "C" in grades_for(run(drug("Tylenol with Codeine (acetaminophen/codeine) 300/30 mg every 6 hours", ("acetaminophen", "codeine")), drug("Paxil (paroxetine) 20 mg once daily", ("paroxetine",))), "prodrug_opioid_2d6")
    assert "D" in grades_for(run(drug("Levaquin (levofloxacin) 750 mg once daily", ("levofloxacin",)), drug("Deltasone (prednisone) 40 mg once daily", ("prednisone",))), "fluoroquinolone_steroid")
    sodium = run(drug("Microzide (hydrochlorothiazide) 25 mg once daily", ("hydrochlorothiazide",)), drug("Zoloft (sertraline) 100 mg once daily", ("sertraline",)), drug("Tegretol (carbamazepine) 200 mg twice daily", ("carbamazepine",)))
    assert "D" in grades_for(sodium, "hyponatremia")
    assert "E" in grades_for(run(drug("Adempas (riociguat) 1 mg three times daily", ("riociguat",)), drug("Imdur (isosorbide mononitrate ER) 30 mg once daily", ("isosorbide",))), "nitrate_pde5")


def test_one_combination_product_is_one_medicine_in_a_group_count() -> None:
    """
    Takes no arguments.
    Counts Adderall's two amphetamines, and Zoloft beside generic sertraline; lists L01, L41.
    Gives nothing; asserts each counts as one medicine, so no serotonin group is raised for Adderall alone.
    """
    assert molecule_count([(0, "amphetamine"), (0, "dextroamphetamine")]) == 1
    assert molecule_count([(0, "sertraline"), (1, "sertraline")]) == 1
    alerts = run(drug("Adderall (amphetamine/dextroamphetamine) 20 mg three times daily", ("amphetamine", "dextroamphetamine")))
    assert not grades_for(alerts, "serotonin")


def test_pair_hits_for_one_victim_merge_into_one_alert() -> None:
    """
    Takes no arguments.
    Runs warfarin with TMP-SMX and amiodarone; list L05.
    Gives nothing; asserts one grade-D alert names all three drugs and counts the two perpetrators.
    """
    alerts = run(
        drug("Coumadin (warfarin) 5 mg once daily", ("warfarin",)),
        drug("Bactrim DS (sulfamethoxazole/trimethoprim) 800/160 mg twice daily", ("sulfamethoxazole", "trimethoprim")),
        drug("Cordarone (amiodarone) 200 mg once daily", ("amiodarone",)),
    )
    merged = [alert for alert in alerts if alert.rule_id == "warfarin_potentiator"]
    assert len(merged) == 1 and merged[0].grade == "D"
    assert {member.drug_name for member in merged[0].members} == {"Coumadin", "Bactrim DS", "Cordarone"}
    assert "2 drugs that raise the INR" in merged[0].title


def test_dose_cap_raises_the_grade_only_above_the_cap() -> None:
    """
    Takes no arguments.
    Runs simvastatin 40 mg and 10 mg with diltiazem, whose label cap is 10 mg; lists L37, L39.
    Gives nothing; asserts D above the cap and C at it.
    """
    above = run(drug("Zocor (simvastatin) 40 mg once daily", ("simvastatin",)), drug("Cardizem CD (diltiazem ER) 240 mg once daily", ("diltiazem",)))
    at_cap = run(drug("Zocor (simvastatin) 10 mg once daily", ("simvastatin",)), drug("Cardizem CD (diltiazem ER) 240 mg once daily", ("diltiazem",)))
    assert grades_for(above, "simvastatin_dose_cap") == ["D"]
    assert grades_for(at_cap, "simvastatin_dose_cap") == ["C"]


def test_controls_raise_nothing_at_b_or_above() -> None:
    """
    Takes no arguments.
    Runs the two control lists' drugs; lists L11, L29.
    Gives nothing; asserts no alert at grade B or above.
    """
    l11 = run(*(drug(f"{name} 10 mg once daily", (name,)) for name in ("levothyroxine", "atorvastatin", "lisinopril", "escitalopram", "montelukast")))
    l29 = run(*(drug(f"{name} 10 mg once daily", (name,)) for name in ("amoxicillin", "loratadine", "montelukast", "amlodipine", "sertraline", "metformin")))
    assert [alert.grade for alert in [*l11, *l29] if alert.grade in ("B", "C", "D", "E")] == []


def test_totals_split_combinations_normalize_units_and_count_mme() -> None:
    """
    Takes no arguments.
    Totals Norco with Tylenol, Synthroid 0.1 mg with levothyroxine 100 mcg, named-day warfarin, and a fentanyl patch; lists L05, L12, L13, L41.
    Gives nothing; asserts 4,300 mg acetaminophen, 0.2 mg levothyroxine, 25 mg warfarin a week, and 60 MME for fentanyl 25 mcg/h.
    """
    drugs = [
        drug("Norco (hydrocodone/acetaminophen) 10/325 mg four times daily", ("acetaminophen", "hydrocodone")),
        drug("Tylenol (acetaminophen OTC) 500 mg 2 tablets three times daily", ("acetaminophen",)),
        drug("Synthroid (levothyroxine) 0.1 mg once daily", ("levothyroxine",)),
        drug("levothyroxine (generic) 100 mcg once daily", ("levothyroxine",)),
        drug("Coumadin (warfarin) 5 mg once daily Mon/Wed/Fri", ("warfarin",)),
        drug("Coumadin (warfarin) 2.5 mg once daily Tue/Thu/Sat/Sun", ("warfarin",)),
        drug("Duragesic (fentanyl) 25 mcg/h transdermal patch one patch every 72 hours", ("fentanyl",)),
    ]
    rows = {(row["ingredient"], row["period"]): row for row in molecule_totals(drugs, KNOWLEDGE.mme_factors)}
    assert rows[("acetaminophen", "day")]["total"] == 4300.0
    assert rows[("levothyroxine", "day")]["total"] == 0.2
    assert rows[("warfarin", "week")]["total"] == 25.0
    assert rows[("fentanyl", "rate")]["mme"] == 60.0
    assert total_mme(list(rows.values())) == 100.0


def test_ceiling_flags_above_and_notes_at_the_maximum() -> None:
    """
    Takes no arguments.
    Runs acetaminophen at 4,300 mg across two entries and sertraline at 200 mg; lists L12, L40.
    Gives nothing; asserts grade D above the ceiling and grade A at it.
    """
    above = run(drug("Norco (hydrocodone/acetaminophen) 10/325 mg four times daily", ("acetaminophen", "hydrocodone")), drug("Tylenol (acetaminophen) 500 mg 2 tablets three times daily", ("acetaminophen",)))
    at_max = run(drug("Zoloft (sertraline) 200 mg once daily", ("sertraline",)))
    assert [alert.grade for alert in above if alert.kind == "ceiling"] == ["D"]
    assert [alert.grade for alert in at_max if alert.kind == "ceiling"] == ["A"]


def duplication(first: str, second: str) -> Alert:
    """
    Takes two display names.
    Builds a shared-ingredient duplication alert naming them.
    Gives the Alert.
    """
    members = tuple(AlertEvidence(name, "", "", "", "", "https://dailymed.nlm.nih.gov/x") for name in (first, second))
    return Alert(kind="duplication", risk="shared_ingredient", title="t", tier=None, tier_name="", members=members, note="")


def test_hidden_duplicates_grade_d_and_split_schedules_are_dropped() -> None:
    """
    Takes no arguments.
    Grades Zoloft beside generic sertraline, Zyprexa entered twice, and a warfarin regimen split across named days; lists L01, L05, L41.
    Gives nothing; asserts D for the hidden duplicate, C for the repeated product, and no alert for the split schedule.
    """
    hidden = [drug("Zoloft (sertraline) 50 mg once daily", ("sertraline",)), drug("sertraline (generic) 50 mg once daily", ("sertraline",))]
    totals = molecule_totals(hidden, KNOWLEDGE.mme_factors)
    assert grade_duplicates([duplication("Zoloft", "sertraline")], hidden, KNOWLEDGE, totals)[0].grade == "D"
    same = [drug("Zyprexa (olanzapine) 10 mg once daily", ("olanzapine",)), drug("Zyprexa (olanzapine) 2.5 mg once daily", ("olanzapine",))]
    graded = grade_duplicates([duplication("Zyprexa", "Zyprexa")], same, KNOWLEDGE, molecule_totals(same, KNOWLEDGE.mme_factors))
    assert graded[0].grade == "C" and "12.5 mg/day" in graded[0].title
    split = [drug("Coumadin (warfarin) 5 mg once daily Mon/Wed/Fri", ("warfarin",)), drug("Coumadin (warfarin) 2.5 mg once daily Tue/Thu/Sat/Sun", ("warfarin",))]
    assert grade_duplicates([duplication("Coumadin", "Coumadin")], split, KNOWLEDGE, molecule_totals(split, KNOWLEDGE.mme_factors)) == []


def test_uncovered_label_group_becomes_a_grade_a_note() -> None:
    """
    Takes no arguments.
    Merges a label-only QT group that no class rule covers; list L22 (omeprazole in a label QT group).
    Gives nothing; asserts it is kept at grade A, never raised to B or above.
    """
    drugs = [drug("Prilosec (omeprazole) 20 mg once daily", ("omeprazole",)), drug("Singulair (montelukast) 10 mg once daily", ("montelukast",))]
    label = Alert(kind="group", risk="T16", title="QT Prolongation Risk shared by 2 drugs", tier=3, tier_name="", members=tuple(AlertEvidence(item["display_name"], "", "", "warnings", "QT.", "https://dailymed.nlm.nih.gov/x") for item in drugs), note="")
    merged = merge_label_alerts([], [label], drugs)
    assert [alert.grade for alert in merged] == ["A"]


def test_metformin_is_named_in_a_kidney_injury_alert_and_statin_alerts_name_myopathy() -> None:
    """
    Takes no arguments.
    Runs lisinopril, hydrochlorothiazide, ibuprofen, and metformin, then atorvastatin 80 mg with ketoconazole; rulebook rows 19 and 27, lists L04 and L21.
    Gives nothing; asserts metformin is listed in the grade-D kidney alert and the statin alert names myopathy.
    """
    kidney = run(
        drug("Zestril (lisinopril) 20 mg once daily", ("lisinopril",)),
        drug("Microzide (hydrochlorothiazide) 25 mg once daily", ("hydrochlorothiazide",)),
        drug("Motrin (ibuprofen) 800 mg three times daily", ("ibuprofen",)),
        drug("Glucophage (metformin) 1000 mg twice daily", ("metformin",)),
    )
    group = next(alert for alert in kidney if alert.rule_id == "kidney")
    assert group.grade == "D" and "Glucophage" in {member.drug_name for member in group.members} and "lactic acidosis" in group.mechanism
    statin = run(drug("Lipitor (atorvastatin) 80 mg once daily", ("atorvastatin",)), drug("Nizoral (ketoconazole) 200 mg once daily", ("ketoconazole",)))
    assert any("myopathy" in alert.title for alert in statin if alert.rule_id == "atorvastatin_strong_cyp3a4")
