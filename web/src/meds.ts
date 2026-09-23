/**
 * Takes no arguments.
 * Splits pasted medication text into entries, checks for a spelling correction, and formats candidate labels; touches no fetch call and no DOM node.
 * Gives nothing; every exported function is called for its return value.
 */

import type { CheckResponse, MedicationRow, UnresolvedEntry } from "./records.js";

const ENTRY_SEPARATORS = /[,;\n]+/;
const MAX_MEDICATION_TEXT_CHARS = 4000;
const CONTAINS_DIGIT = /\d/;

/**
 * Takes freshly pasted or typed medication text.
 * Splits it at commas, semicolons, and new lines, trimming and dropping empty pieces.
 * Gives the tuple of non-empty entries, in the order they appeared, empty for blank input.
 */
export function splitPastedText(text: string): readonly string[] {
  return text
    .split(ENTRY_SEPARATORS)
    .map((part) => part.trim())
    .filter((part) => part.length > 0);
}

/**
 * Takes one entry already split on commas, semicolons, and new lines.
 * Checks whether it has no digit anywhere and two or more whitespace-separated words, the signature of several bare drug names typed with only spaces between them rather than one dose line (a real dose line like "Lyrica 100 mg tid" always carries a digit).
 * Gives one entry per word when it matches that signature, the entry unchanged otherwise.
 */
function splitBareNamesWithoutDose(entry: string): readonly string[] {
  const words = entry.split(/\s+/).filter((word) => word.length > 0);
  if (words.length < 2 || CONTAINS_DIGIT.test(entry)) {
    return [entry];
  }
  return words;
}

/**
 * Takes freshly typed or pasted medication text, the same input splitPastedText takes.
 * Splits it at commas, semicolons, and new lines first, then, for any resulting entry that still reads as several bare drug names run together with only spaces (no digit, two or more words), splits that entry on whitespace too -- so "Zoloft Flexeril Xanax" typed with no separator does not silently collapse into one unresolvable entry that drops four of five medications.
 * Gives the tuple of non-empty entries, in the order they appeared, empty for blank input.
 */
export function splitEnteredText(text: string): readonly string[] {
  return splitPastedText(text).flatMap(splitBareNamesWithoutDose);
}

/**
 * Takes the current list of medication lines.
 * Joins them with newlines, the separator the API expects for POST /api/check.
 * Gives the joined text, empty when the list is empty.
 */
export function joinMedicationLines(lines: readonly string[]): string {
  return lines.join("\n");
}

/**
 * Takes the joined medication text the app is about to send.
 * Checks it against the server's maximum length.
 * Gives true when the text is within the limit, false when it would be rejected with a 413.
 */
export function isWithinLengthLimit(joinedText: string): boolean {
  return joinedText.length <= MAX_MEDICATION_TEXT_CHARS;
}

/**
 * Takes one medication table row.
 * Collects every own name the row carries: brand, generic, and base ingredient names, lowercased.
 * Gives the set of lowercase own names, empty when the row carries none.
 */
function rowOwnNamesLowercase(row: MedicationRow): ReadonlySet<string> {
  const names = [...row.brand, ...row.generic, ...row.base_ingredients];
  return new Set(names.map((ownName) => ownName.toLowerCase()));
}

/**
 * Takes one resolved medication table row.
 * Checks whether the first item in matched_name (the name the local matcher or RxNorm accepted) matches none of the row's own brand, generic, or base-ingredient names.
 * Gives true when the row should show the "Spelling corrected" tag, false when matched_name is null or the typed name is one of the row's own names.
 */
export function isSpellingCorrected(row: MedicationRow): boolean {
  if (row.matched_name === null || row.matched_name.length === 0) {
    return false;
  }
  const typedName = row.matched_name[0];
  if (typedName === undefined) {
    return false;
  }
  return !rowOwnNamesLowercase(row).has(typedName.toLowerCase());
}

/**
 * Takes one resolved medication table row.
 * Picks the generic name to show as the row's headline, lowercased.
 * Gives the first generic name lowercased, or the row's typed name lowercased when it has no generic name.
 */
export function rowHeadlineName(row: MedicationRow): string {
  const generic = row.generic[0];
  if (generic !== undefined) {
    return generic.toLowerCase();
  }
  if (row.matched_name !== null && row.matched_name.length > 0) {
    return String(row.matched_name[0]).toLowerCase();
  }
  return row.as_entered.toLowerCase();
}

/**
 * Takes one candidate string shaped "NAME → INGREDIENT SET" from an unresolved entry.
 * Splits off the part before the arrow and lowercases it.
 * Gives the lowercase name, or the whole candidate lowercased when it has no arrow.
 */
export function candidateLabel(candidate: string): string {
  const arrowIndex = candidate.indexOf("→");
  const namePart = arrowIndex === -1 ? candidate : candidate.slice(0, arrowIndex);
  return namePart.trim().toLowerCase();
}

export interface CandidateChoice {
  readonly label: string;
  readonly entryText: string;
}

/**
 * Takes one candidate string shaped "NAME → INGREDIENT SET".
 * Pulls out the ingredient set after the arrow, lowercased, unless it is missing or was truncated with "...".
 * Gives the ingredient names as a tuple, or an empty tuple when there is no usable set.
 */
function candidateIngredients(candidate: string): readonly string[] {
  const arrowIndex = candidate.indexOf("→");
  if (arrowIndex === -1) {
    return [];
  }
  const setPart = candidate.slice(arrowIndex + 1).trim();
  if (setPart.length === 0 || setPart.endsWith("...")) {
    return [];
  }
  return setPart.split(",").map((part) => part.trim().toLowerCase()).filter((part) => part.length > 0);
}

/**
 * Takes every candidate string for one unresolved entry.
 * Picks a visible label and the text to re-check for each: the name when the names already differ, otherwise the ingredient set, which is what actually tells same-named products apart.
 * Gives one CandidateChoice per candidate, in order.
 */
export function candidateChoices(candidates: readonly string[]): readonly CandidateChoice[] {
  const names = candidates.map(candidateLabel);
  const namesAreDistinct = new Set(names).size === names.length;
  return candidates.map((candidate, index) => {
    const name = names[index] ?? candidateLabel(candidate);
    const ingredients = candidateIngredients(candidate);
    if (namesAreDistinct || ingredients.length === 0) {
      return { label: name, entryText: name };
    }
    return { label: ingredients.join(" + "), entryText: ingredients.join(" / ") };
  });
}

/**
 * Takes the medication table rows and one medication line as the user typed it.
 * Finds the row whose as_entered text matches that line.
 * Gives the matching row, or undefined when no row's as_entered matches.
 */
export function findRowForLine(rows: readonly MedicationRow[], line: string): MedicationRow | undefined {
  return rows.find((row) => row.as_entered === line);
}

/**
 * Takes the resolved medication table rows.
 * Counts the rows whose matched_name is not null.
 * Gives the count of resolved rows.
 */
export function countResolvedRows(rows: readonly MedicationRow[]): number {
  return rows.filter((row) => row.matched_name !== null).length;
}

export type LineStatus =
  | { readonly row: MedicationRow }
  | { readonly unresolved: UnresolvedEntry }
  | { readonly pending: true };

/**
 * Takes one medication line as the user typed it and the current check response, when there is one.
 * Finds the unresolved entry for that line first, since medication_table also carries a row for an unresolved entry (with a null matched_name), then falls back to a resolved row.
 * Gives {row} when it resolved, {unresolved} when it needs a candidate or was not found, or {pending: true} when the response has not caught up to this line yet.
 */
export function statusForLine(line: string, response: CheckResponse | null): LineStatus {
  if (response === null) {
    return { pending: true };
  }
  const unresolved = response.unresolved_entries.find((entry) => entry.raw_text === line);
  if (unresolved !== undefined) {
    return { unresolved };
  }
  const row = response.medication_table.find((candidate) => candidate.as_entered === line);
  if (row !== undefined && row.matched_name !== null) {
    return { row };
  }
  return { pending: true };
}
