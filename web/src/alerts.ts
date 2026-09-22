/**
 * Takes no arguments.
 * Sorts alerts, picks each alert's primary and additional evidence, and names its tier and icon; touches no fetch call and no DOM node.
 * Gives nothing; every exported function is called for its return value.
 */

import type { AlertMember, AlertRecord } from "./records.js";

// Strongest-to-weakest label section, from BUILD_PROMPT.md Section 4.2:
// "Use the member from the strongest section, in this order: contraindications,
// boxed_warning, warnings_and_cautions/warnings/precautions, drug_interactions."
const SECTION_STRENGTH_ORDER: readonly string[] = [
  "contraindications",
  "boxed_warning",
  "warnings_and_cautions",
  "warnings",
  "precautions",
  "drug_interactions",
];

const DUPLICATE_THERAPY_LABEL = "Duplicate therapy";
const DUPLICATION_SORT_RANK = 5;

/**
 * Takes one alert.
 * Ranks it for card ordering: its tier when it has one, otherwise last (duplication has no tier).
 * Gives the sort rank, 1-4 for a tiered alert or 5 for a duplication flag.
 */
function sortRank(alert: AlertRecord): number {
  return alert.tier ?? DUPLICATION_SORT_RANK;
}

/**
 * Takes the alerts from a check response, in API order.
 * Orders them by tier from 1 to 4 with duplication flags last, keeping API order within a tier.
 * Gives a new array; the input array is never mutated.
 */
export function sortAlerts(alerts: readonly AlertRecord[]): readonly AlertRecord[] {
  return alerts
    .map((alert, index) => ({ alert, index }))
    .sort((a, b) => sortRank(a.alert) - sortRank(b.alert) || a.index - b.index)
    .map((entry) => entry.alert);
}

/**
 * Takes one alert.
 * Names its tier line: "Duplicate therapy" for a duplication flag, its own tier_name otherwise.
 * Gives the display tier name, word for word except for the duplication override.
 */
export function alertDisplayTierName(alert: AlertRecord): string {
  return alert.kind === "duplication" ? DUPLICATE_THERAPY_LABEL : alert.tier_name;
}

/**
 * Takes one alert's members.
 * Joins every member's drug_name with a comma.
 * Gives the joined string, empty when there are no members.
 */
export function alertDrugNames(members: readonly AlertMember[]): string {
  return members.map((member) => member.drug_name).join(", ");
}

/**
 * Takes one alert's members.
 * Keeps only the members that carry a label sentence, per Section 4.2: "Skip any member whose section is empty."
 * Gives the members with a non-empty section, in their original order.
 */
export function membersWithEvidence(members: readonly AlertMember[]): readonly AlertMember[] {
  return members.filter((member) => member.section !== "");
}

/**
 * Takes the members that carry a label sentence.
 * Picks the one from the strongest section, falling back to the first when none matches the known order.
 * Gives that member, or undefined when there are no members with evidence.
 */
export function primaryEvidenceMember(members: readonly AlertMember[]): AlertMember | undefined {
  const withEvidence = membersWithEvidence(members);
  for (const section of SECTION_STRENGTH_ORDER) {
    const found = withEvidence.find((member) => member.section === section);
    if (found !== undefined) {
      return found;
    }
  }
  return withEvidence[0];
}

/**
 * Takes the members that carry a label sentence and the primary member already chosen from them.
 * Keeps the rest, for the "Show N more label sentences" expansion.
 * Gives the remaining members in their original order, empty when there is nothing more to show.
 */
export function additionalEvidenceMembers(members: readonly AlertMember[], primary: AlertMember | undefined): readonly AlertMember[] {
  const withEvidence = membersWithEvidence(members);
  if (primary === undefined) {
    return withEvidence;
  }
  return withEvidence.filter((member) => member !== primary);
}

export type AlertIconKey = "tier-1" | "tier-2" | "tier-3" | "tier-4" | "duplication";

/**
 * Takes one alert.
 * Picks which of the five card icons Section 4.2 names for it.
 * Gives the icon key: the duplication icon for a duplication flag, otherwise the icon for its tier (tier 4 when the tier is missing).
 */
export function alertIconKey(alert: AlertRecord): AlertIconKey {
  if (alert.kind === "duplication") {
    return "duplication";
  }
  const tier = alert.tier ?? 4;
  return tier === 1 ? "tier-1" : tier === 2 ? "tier-2" : tier === 3 ? "tier-3" : "tier-4";
}
