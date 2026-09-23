"""Tests for the "Brand (generic) dose frequency = total" line form a prescriber writes (TEST_PACK.md run 2026-09-23_0648: 244 of 244 entries were "not found")."""

from __future__ import annotations

from rx_label_search.normalize.med_line_parser import parse_entry, split_brand_and_generic, split_stated_total


def test_stated_total_is_split_off_and_never_read_as_a_dose() -> None:
    """
    Takes no arguments.
    Parses a Xanax line whose stated total (3 mg/day) differs from its strength (1 mg); lists L01, L21.
    Gives nothing; asserts the strength is 1 mg, the name is the generic, and the total is kept as written.
    """
    entry = parse_entry("Xanax (alprazolam) 1 mg three times daily = 3 mg/day")
    assert (entry.name_text, entry.brand_text, entry.strength_value, entry.times_per_day, entry.daily_total) == ("alprazolam", "Xanax", 1.0, 3.0, 3.0)
    assert entry.stated_total == "3 mg/day"
    assert split_stated_total("Zoloft 50 mg") == ("Zoloft 50 mg", None)


def test_generic_in_parentheses_names_the_drug_and_generic_marker_means_brand_is_generic() -> None:
    """
    Takes no arguments.
    Splits a brand-and-generic line and a "(generic)" line; list L41.
    Gives nothing; asserts the generic is used, and "sertraline (generic)" has no brand.
    """
    assert split_brand_and_generic("Zoloft (sertraline) 50 mg once daily")[:2] == ("Zoloft", "sertraline")
    entry = parse_entry("sertraline (generic) 50 mg once daily = 50 mg/day")
    assert (entry.name_text, entry.brand_text) == ("sertraline", None)


def test_release_form_and_otc_words_leave_the_name() -> None:
    """
    Takes no arguments.
    Parses lines whose generic carries ER, OTC, or DR; lists L04, L24, L26.
    Gives nothing; asserts the clean generic name and the spelled-out release form.
    """
    lithium = parse_entry("Lithobid (lithium carbonate ER) 300 mg three times daily = 900 mg/day")
    assert (lithium.name_text, lithium.release_form, lithium.daily_total) == ("lithium carbonate", "extended-release", 900.0)
    assert parse_entry("Aleve (naproxen sodium OTC) 220 mg twice daily = 440 mg/day").name_text == "naproxen sodium"


def test_combination_strength_is_read_per_component() -> None:
    """
    Takes no arguments.
    Parses Norco, Sprintec, and Fioricet lines; lists L12, L20, L35.
    Gives nothing; asserts each component keeps its own strength and unit, and Fioricet's "max 6 tablets/day" sets six tablets a day.
    """
    norco = parse_entry("Norco (hydrocodone/acetaminophen) 10/325 mg four times daily = 40/1300 mg/day")
    assert norco.components == ("hydrocodone", "acetaminophen")
    assert norco.component_strengths == ((10.0, "mg"), (325.0, "mg"))
    sprintec = parse_entry("Sprintec (norgestimate/ethinyl estradiol) 0.25 mg/35 mcg once daily = 0.25 mg/35 mcg/day")
    assert sprintec.component_strengths == ((0.25, "mg"), (35.0, "mcg"))
    fioricet = parse_entry("Fioricet (butalbital/acetaminophen/caffeine) 50/325/40 mg 2 tablets every 4 hours as needed max 6 tablets/day = 300/1950/240 mg/day max")
    assert fioricet.as_needed and fioricet.dose_count == 2.0 and fioricet.times_per_day == 3.0


def test_named_days_and_weekly_schedules_stay_weekly() -> None:
    """
    Takes no arguments.
    Parses a Mon/Wed/Fri warfarin line and a once-weekly methotrexate line; lists L05, L10, L32.
    Gives nothing; asserts three days a week, and no daily total for the weekly drug.
    """
    warfarin = parse_entry("Coumadin (warfarin) 5 mg once daily Mon/Wed/Fri = 5 mg on those days")
    assert (warfarin.days_per_week, warfarin.schedule_text, warfarin.name_text) == (3.0, "Mon/Wed/Fri", "warfarin")
    methotrexate = parse_entry("Trexall (methotrexate) 15 mg once weekly = 15 mg/week")
    assert (methotrexate.daily_total, methotrexate.days_per_week) == (None, 1.0)


def test_as_needed_limits_set_the_daily_maximum() -> None:
    """
    Takes no arguments.
    Parses as-needed lines with "max N doses/day", "may repeat once", "no more than once daily", and "max N mg/day"; lists L02, L06, L16, L35.
    Gives nothing; asserts the daily maximum each implies.
    """
    assert parse_entry("Roxicodone (oxycodone IR) 10 mg every 4 hours as needed max 6 doses/day = 60 mg/day max").daily_total == 60.0
    assert parse_entry("Imitrex (sumatriptan) 50 mg as needed may repeat once after 2 hours = 100 mg/day max").daily_total == 100.0
    assert parse_entry("Viagra (sildenafil) 100 mg as needed no more than once daily = 100 mg/day max").daily_total == 100.0
    assert parse_entry("Maxalt (rizatriptan) 10 mg as needed may repeat after 2 hours max 30 mg/day = 30 mg/day max").daily_total == 30.0


def test_sprays_in_each_nostril_count_twice() -> None:
    """
    Takes no arguments.
    Parses a Flonase line of 2 sprays in each nostril; list L28.
    Gives nothing; asserts four sprays of 50 mcg, 200 mcg a day, nasal route.
    """
    entry = parse_entry("Flonase (fluticasone propionate nasal) 50 mcg per spray 2 sprays each nostril once daily = 200 mcg/day")
    assert (entry.name_text, entry.dose_count, entry.daily_total, entry.route) == ("fluticasone propionate", 4.0, 200.0, "nasal")


def test_units_beyond_mg_and_routes_are_read() -> None:
    """
    Takes no arguments.
    Parses IV grams, subcutaneous units, mEq, and a mcg/h patch; lists L10, L13, L23, L31.
    Gives nothing; asserts each unit, total, and route.
    """
    zosyn = parse_entry("Zosyn (piperacillin/tazobactam) 3.375 g IV every 6 hours = 13.5 g/day")
    assert (zosyn.strength_unit, zosyn.daily_total, zosyn.route) == ("g", 13.5, "intravenous")
    lantus = parse_entry("Lantus (insulin glargine) 40 units subcutaneous once daily at bedtime = 40 units/day")
    assert (lantus.name_text, lantus.strength_unit, lantus.daily_total) == ("insulin glargine", "units", 40.0)
    assert parse_entry("Klor-Con (potassium chloride ER) 20 mEq once daily = 20 mEq/day").strength_unit == "mEq"
    patch = parse_entry("Duragesic (fentanyl) 25 mcg/h transdermal patch one patch every 72 hours = 25 mcg/h continuous")
    assert (patch.name_text, patch.strength_unit, patch.daily_total) == ("fentanyl", "mcg/h", 25.0)
