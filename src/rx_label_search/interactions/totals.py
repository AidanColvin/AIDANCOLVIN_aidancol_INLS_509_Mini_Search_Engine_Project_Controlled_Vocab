"""Pure per-ingredient totals across a medication list: components split out, units normalized, weekly and named-day schedules kept weekly, opioid MME added up."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from rx_label_search.records import MedEntry

MASS_TO_MG: dict[str, float] = {"mg": 1.0, "mcg": 0.001, "g": 1000.0}
FENTANYL_PATCH_KEY = "fentanyl_transdermal_per_mcg_h"


@dataclass(frozen=True)
class EntryAmount:
    """One ingredient's amount from one entry, in a normalized unit and period."""

    ingredient: str
    amount: float
    unit: str
    period: str
    as_needed: bool
    display_name: str


def unit_class(unit: str | None) -> tuple[str, float] | None:
    """
    Takes a strength unit such as "mg", "mcg", "g", "mEq", "units", or "mcg/h".
    Maps mass units onto milligrams and keeps the others as they are.
    Gives the normalized unit and the factor to multiply by, or None for a unit with no total (mL, %).
    """
    if unit is None:
        return None
    if unit in MASS_TO_MG:
        return "mg", MASS_TO_MG[unit]
    if unit in ("mEq", "units", "mcg/h"):
        return unit, 1.0
    return None


def component_bases(entry: MedEntry, bases: Sequence[str]) -> tuple[str, ...]:
    """
    Takes an entry with written components, such as "hydrocodone" and "acetaminophen", and the resolved drug's base ingredients.
    Pairs each written component with the base ingredient it names, so a salt such as "tenofovir disoproxil fumarate" maps to "tenofovir disoproxil".
    Gives one base name per component in written order, or an empty tuple when any component cannot be paired.
    """
    paired: list[str] = []
    for component in entry.components:
        low = component.lower()
        match = next((base for base in bases if base == low or low.startswith(base) or base.startswith(low)), None)
        if match is None:
            return ()
        paired.append(match)
    return tuple(paired)


def per_dose_units(entry: MedEntry) -> float | None:
    """
    Takes one parsed entry.
    Works out how many dosing units are taken per day: the per-dose count times the times per day.
    Gives the units per day, or None when the frequency is unknown.
    """
    if entry.times_per_day is None:
        return None
    return entry.times_per_day * (entry.dose_count or 1.0)


def entry_amounts(entry: MedEntry, bases: Sequence[str], display_name: str) -> list[EntryAmount]:
    """
    Takes one parsed entry, its resolved base ingredients, and its display name.
    Computes each ingredient's amount: per day, per week for weekly or named-day schedules, or as a continuous mcg/h rate.
    Gives the amounts, one per ingredient (or one for a whole combination product whose components were not written), empty when no amount can be computed.
    """
    normalized = unit_class(entry.strength_unit)
    if normalized is None or entry.strength_value is None:
        return []
    unit, factor = normalized
    if unit == "mcg/h":
        return [EntryAmount(bases[0] if bases else entry.name_text, entry.strength_value, unit, "rate", entry.as_needed, display_name)]
    paired = component_bases(entry, bases) if entry.component_strengths else ()
    if paired:
        strengths = [(base, value * (unit_class(each_unit) or ("mg", 1.0))[1], (unit_class(each_unit) or ("mg", 1.0))[0]) for base, (value, each_unit) in zip(paired, entry.component_strengths)]
    elif len(bases) == 1:
        strengths = [(bases[0], entry.strength_value * factor, unit)]
    else:
        strengths = [("/".join(bases), entry.strength_value * factor, unit)]
    weekly = entry.days_per_week is not None and entry.days_per_week < 7
    amounts: list[EntryAmount] = []
    for ingredient, per_unit, each_unit in strengths:
        if weekly and entry.times_per_day is None:
            amounts.append(EntryAmount(ingredient, per_unit * (entry.dose_count or 1.0), each_unit, "week", entry.as_needed, display_name))
            continue
        if not paired and len(strengths) == 1 and entry.daily_total is not None:
            daily = entry.daily_total * factor
        else:
            units_per_day = per_dose_units(entry)
            if units_per_day is None:
                continue
            daily = per_unit * units_per_day
        if weekly:
            amounts.append(EntryAmount(ingredient, daily * (entry.days_per_week or 0.0), each_unit, "week", entry.as_needed, display_name))
        else:
            amounts.append(EntryAmount(ingredient, daily, each_unit, "day", entry.as_needed, display_name))
    return amounts


def format_amount(amount: float, unit: str) -> str:
    """
    Takes an amount and its normalized unit.
    Writes it the way a prescriber reads it: mg with thousands separators, micrograms below 1 mg, grams added in parentheses from 1,000 mg up.
    Gives the formatted amount.
    """
    if unit == "mg" and 0 < amount < 1:
        return f"{amount * 1000:g} mcg ({amount:g} mg)"
    if unit == "mg" and amount >= 1000:
        grams = amount / 1000
        return f"{amount:,.0f} mg ({grams:g} g)" if amount == int(amount) else f"{amount:,.1f} mg ({grams:g} g)"
    text = f"{amount:,.2f}".rstrip("0").rstrip(".")
    return f"{text} {unit}"


def molecule_totals(drugs: Sequence[Mapping[str, Any]], mme_factors: Mapping[str, float]) -> list[dict[str, Any]]:
    """
    Takes the resolved drugs and the MME conversion factors.
    Adds up each ingredient across every entry, keeping per-day, per-week, and continuous-rate amounts apart, and converts opioids to morphine milligram equivalents.
    Gives one row per ingredient and period with the total, its text, the entries it came from, whether any entry was as-needed (a maximum), and the MME when it is an opioid.
    """
    grouped: dict[tuple[str, str, str], list[EntryAmount]] = {}
    for drug in drugs:
        bases = tuple(drug["record"].get("base_ingredients", ()))
        for item in entry_amounts(drug["entry"], bases, drug["display_name"]):
            grouped.setdefault((item.ingredient, item.unit, item.period), []).append(item)
    rows: list[dict[str, Any]] = []
    for (ingredient, unit, period), items in sorted(grouped.items()):
        total = sum(item.amount for item in items)
        suffix = {"day": "/day", "week": "/week", "rate": " continuous"}[period]
        as_needed = any(item.as_needed for item in items)
        mme = opioid_mme(ingredient, total, unit, period, mme_factors)
        rows.append({
            "ingredient": ingredient,
            "total": round(total, 4),
            "unit": unit,
            "period": period,
            "text": f"{format_amount(total, unit)}{suffix}{' max' if as_needed else ''}",
            "entries": [item.display_name for item in items],
            "entry_count": len(items),
            "as_needed": as_needed,
            "mme": mme,
        })
    return rows


def opioid_mme(ingredient: str, total: float, unit: str, period: str, mme_factors: Mapping[str, float]) -> float | None:
    """
    Takes an ingredient, its total, unit, and period, and the CDC MME conversion factors.
    Converts a daily opioid amount in mg, or a fentanyl patch rate in mcg/h, to morphine milligram equivalents per day.
    Gives the MME, or None for a non-opioid or an amount that is not per day.
    """
    if ingredient == "fentanyl" and unit == "mcg/h":
        return round(total * mme_factors.get(FENTANYL_PATCH_KEY, 0.0), 1) or None
    if period != "day" or unit != "mg" or ingredient not in mme_factors:
        return None
    return round(total * mme_factors[ingredient], 1)


def total_mme(rows: Sequence[Mapping[str, Any]]) -> float | None:
    """
    Takes the per-ingredient total rows.
    Adds the MME of every opioid row.
    Gives the total MME, or None when no row is an opioid.
    """
    values = [row["mme"] for row in rows if row.get("mme")]
    return round(sum(values), 1) if values else None


def daily_mg(rows: Sequence[Mapping[str, Any]], ingredient: str) -> float | None:
    """
    Takes the per-ingredient total rows and one ingredient.
    Finds that ingredient's per-day total in mg.
    Gives the amount, or None when it has no per-day mg total.
    """
    for row in rows:
        if row["ingredient"] == ingredient and row["unit"] == "mg" and row["period"] == "day":
            return float(row["total"])
    return None
