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

export type GradeLetter = "A" | "B" | "C" | "D" | "E";

export interface AlertGrade {
  readonly letter: GradeLetter;
  readonly name: string;
  readonly meaning: string;
  readonly lexicomp: string;
  readonly rank: number;
}

// The five grades, worst first. Each is set by the FDA label itself: the
// section the evidence sentence sits in, and what the label says to do about
// using the drugs together. Each lines up with a published Lexicomp level.
export const GRADES: readonly AlertGrade[] = [
  { letter: "E", name: "Avoid combination", meaning: "The label says these drugs must not be used together.", lexicomp: "X", rank: 0 },
  { letter: "D", name: "Consider changing therapy", meaning: "A boxed warning, or the label says to avoid using them together.", lexicomp: "D", rank: 1 },
  { letter: "C", name: "Monitor closely", meaning: "A clinically significant warning in the label.", lexicomp: "C", rank: 2 },
  { letter: "B", name: "Monitor", meaning: "The label describes the interaction and says to monitor or adjust.", lexicomp: "C", rank: 3 },
  { letter: "A", name: "Minor", meaning: "The label notes the interaction and states no action.", lexicomp: "B", rank: 4 },
];

/**
 * Takes a grade letter.
 * Looks it up in the five-grade table.
 * Gives the AlertGrade, or undefined when the letter is not one of A to E.
 */
export function gradeByLetter(letter: string): AlertGrade | undefined {
  return GRADES.find((grade) => grade.letter === letter);
}

/**
 * Takes one alert.
 * Uses the grade the server assigned, falling back for an older response to the tier: 1 is E, 2 is D, 3 is C, 4 is A, and a duplication flag is C.
 * Gives the AlertGrade.
 */
export function alertGrade(alert: AlertRecord): AlertGrade {
  const assigned = alert.grade === null ? undefined : gradeByLetter(alert.grade);
  if (assigned !== undefined) {
    return assigned;
  }
  if (alert.kind === "duplication") {
    return GRADES[2] as AlertGrade;
  }
  const tier = alert.tier ?? 4;
  const letter = tier === 1 ? "E" : tier === 2 ? "D" : tier === 3 ? "C" : "A";
  return gradeByLetter(letter) as AlertGrade;
}

/**
 * Takes the alerts from a check response.
 * Counts how many fall in each of the five grades.
 * Gives the counts keyed by letter, zero for a grade with no alerts.
 */
export function gradeCounts(alerts: readonly AlertRecord[]): Readonly<Record<GradeLetter, number>> {
  const counts: Record<GradeLetter, number> = { A: 0, B: 0, C: 0, D: 0, E: 0 };
  for (const alert of alerts) {
    counts[alertGrade(alert).letter] += 1;
  }
  return counts;
}

export interface AlertExplanation {
  readonly title: string;
  readonly text: string;
  readonly sourceName: string | null;
  readonly sourceUrl: string | null;
}

// Plain-language explanations of each risk, each with a public source a
// reader can open. The label sentence on the card is the evidence; this
// says what the words mean.
const EXPLANATIONS: Readonly<Record<string, AlertExplanation>> = {
  T14: {
    title: "Serotonin syndrome",
    text: "Too much serotonin activity in the nervous system, most often when two or more serotonergic drugs are taken together. Signs include agitation, fast heartbeat, high temperature, sweating, and twitching muscles. It can be life-threatening.",
    sourceName: "MedlinePlus, National Library of Medicine",
    sourceUrl: "https://medlineplus.gov/ency/article/007272.htm",
  },
  T15: {
    title: "CNS depression",
    text: "Each of these drugs slows the central nervous system. Together the effect adds up: heavy sedation, slowed breathing, and a higher risk of overdose, especially when an opioid and a benzodiazepine are combined.",
    sourceName: "National Institute on Drug Abuse, NIH",
    sourceUrl: "https://nida.nih.gov/research-topics/opioids/benzodiazepines-opioids",
  },
  T16: {
    title: "QT prolongation",
    text: "Each of these drugs can delay the heart's electrical recovery after a beat, seen as a longer QT interval on an ECG. Together the delay can add up and trigger torsades de pointes, a dangerous heart rhythm.",
    sourceName: "National Heart, Lung, and Blood Institute, NIH",
    sourceUrl: "https://www.nhlbi.nih.gov/health/long-qt-syndrome",
  },
  T17: {
    title: "Contraindicated",
    text: "A contraindication is a specific situation in which a drug should not be used because it may be harmful. One of these labels names the other drug, or its class, as exactly that.",
    sourceName: "MedlinePlus, National Library of Medicine",
    sourceUrl: "https://medlineplus.gov/ency/article/002314.htm",
  },
  shared_ingredient: {
    title: "Same active ingredient",
    text: "Two entries contain the same active ingredient, so their daily amounts add together. Check that the combined total is what was intended.",
    sourceName: null,
    sourceUrl: null,
  },
  active_metabolite: {
    title: "Active metabolite",
    text: "The body turns one of these drugs into the other, so the two act as one drug at a higher dose than either alone.",
    sourceName: null,
    sourceUrl: null,
  },
};

/**
 * Takes one alert.
 * Looks up the plain-language explanation for its risk.
 * Gives the AlertExplanation, or null when the risk has none.
 */
export function alertExplanation(alert: AlertRecord): AlertExplanation | null {
  return EXPLANATIONS[alert.risk] ?? null;
}

/**
 * Takes the alerts from a check response, in API order.
 * Orders them worst grade first (E, D, C, B, A), keeping API order within a grade.
 * Gives a new array; the input array is never mutated.
 */
export function sortAlerts(alerts: readonly AlertRecord[]): readonly AlertRecord[] {
  return alerts
    .map((alert, index) => ({ alert, index }))
    .sort((a, b) => alertGrade(a.alert).rank - alertGrade(b.alert).rank || a.index - b.index)
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
