"""Pure heuristic tier assignment, based on the label section an alert's evidence came from."""

from __future__ import annotations

TIER_CONTRAINDICATED = 1
TIER_BOXED_WARNING = 2
TIER_WARNING = 3
TIER_INTERACTION_NOTE = 4
TIER_NAMES: dict[int, str] = {
    TIER_CONTRAINDICATED: "Contraindicated",
    TIER_BOXED_WARNING: "Boxed warning",
    TIER_WARNING: "Warning",
    TIER_INTERACTION_NOTE: "Interaction note",
}
_FIELD_TIERS: dict[str, int] = {
    "contraindications": TIER_CONTRAINDICATED,
    "boxed_warning": TIER_BOXED_WARNING,
    "warnings_and_cautions": TIER_WARNING,
    "warnings": TIER_WARNING,
    "precautions": TIER_WARNING,
    "drug_interactions": TIER_INTERACTION_NOTE,
}


def tier_for_field(field_name: str) -> int | None:
    """
    Takes the label field an alert's evidence sentence came from.
    Looks up the tier that field maps to.
    Gives the tier number, or None when the field is not one of the six mapped fields.
    """
    return _FIELD_TIERS.get(field_name)


def tier_name(tier: int | None) -> str:
    """
    Takes a tier number, or None.
    Looks up its display name.
    Gives the name, or "Unknown" when the tier is not one of the four defined tiers.
    """
    if tier is None:
        return "Unknown"
    return TIER_NAMES.get(tier, "Unknown")


def highest_tier(tiers: tuple[int | None, ...]) -> int | None:
    """
    Takes the tiers of every member sentence in a group alert.
    Finds the highest-priority tier, where a lower number is more severe.
    Gives that tier, or None when every member's tier is None.
    """
    known = [tier for tier in tiers if tier is not None]
    return min(known) if known else None
