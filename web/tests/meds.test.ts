/**
 * Takes no arguments.
 * Tests the pure medication-list helpers in src/meds.ts.
 * Gives nothing; each test function is run by node:test.
 */

import assert from "node:assert/strict";
import test from "node:test";

import {
  candidateLabel,
  countResolvedRows,
  findRowForLine,
  isSpellingCorrected,
  isWithinLengthLimit,
  joinMedicationLines,
  rowHeadlineName,
  splitEnteredText,
  splitPastedText,
  statusForLine,
} from "../src/meds.js";
import type { CheckResponse, MedicationRow, UnresolvedEntry } from "../src/records.js";

/**
 * Takes a set of field overrides.
 * Builds a minimal MedicationRow for a test, filling in safe defaults for the rest.
 * Gives the MedicationRow.
 */
function row(overrides: Partial<MedicationRow>): MedicationRow {
  return {
    as_entered: "test entry",
    matched_name: null,
    generic: [],
    base_ingredients: [],
    brand: [],
    fda_class: "Not listed on label.",
    route: [],
    dea_schedule: null,
    daily_total: null,
    daily_total_unit: null,
    pdla_tags: [],
    ...overrides,
  };
}

/**
 * Takes no arguments.
 * Checks commas, semicolons, and newlines as separators, and the empty case.
 * Gives nothing; asserts each split result.
 */
test("splitPastedText splits on commas, semicolons, and newlines and drops blanks", () => {
  assert.deepEqual(splitPastedText("a, b; c\nd,,"), ["a", "b", "c", "d"]);
  assert.deepEqual(splitPastedText(""), []);
  assert.deepEqual(splitPastedText("   "), []);
});

/**
 * Takes no arguments.
 * Checks the exact production bug report: five real drug names typed with only spaces between them, no comma, semicolon, or newline anywhere.
 * Gives nothing; asserts every drug survives as its own entry instead of collapsing into one unresolvable line.
 */
test("splitEnteredText splits bare drug names typed with only spaces, no digits anywhere", () => {
  assert.deepEqual(splitEnteredText("Zoloft Flexeril Xanax Ambien Adderall"), [
    "Zoloft",
    "Flexeril",
    "Xanax",
    "Ambien",
    "Adderall",
  ]);
});

/**
 * Takes no arguments.
 * Checks that a normal single-entry dose line, which always carries a digit for the strength or a frequency count, is left as one entry rather than being chopped into words.
 * Gives nothing; asserts the dose line survives whole.
 */
test("splitEnteredText leaves a single dose line with a digit intact", () => {
  assert.deepEqual(splitEnteredText("Lyrica 100 mg tid"), ["Lyrica 100 mg tid"]);
  assert.deepEqual(splitEnteredText("Lisinopril 10 mg once daily"), ["Lisinopril 10 mg once daily"]);
});

/**
 * Takes no arguments.
 * Checks a single bare word, real comma-separated entries, and blank input.
 * Gives nothing; asserts each case behaves the same as splitPastedText.
 */
test("splitEnteredText matches splitPastedText for single words, real separators, and blank input", () => {
  assert.deepEqual(splitEnteredText("Metformin"), ["Metformin"]);
  assert.deepEqual(splitEnteredText("Zoloft, Flexeril, Xanax"), ["Zoloft", "Flexeril", "Xanax"]);
  assert.deepEqual(splitEnteredText(""), []);
  assert.deepEqual(splitEnteredText("   "), []);
});

/**
 * Takes no arguments.
 * Checks joining several lines and the empty list.
 * Gives nothing; asserts each joined string.
 */
test("joinMedicationLines joins with newlines and handles the empty case", () => {
  assert.equal(joinMedicationLines(["a", "b"]), "a\nb");
  assert.equal(joinMedicationLines([]), "");
});

/**
 * Takes no arguments.
 * Checks text at, just under, and just over the 4,000-character limit.
 * Gives nothing; asserts each boundary.
 */
test("isWithinLengthLimit is inclusive of exactly 4000 characters", () => {
  assert.equal(isWithinLengthLimit("a".repeat(4000)), true);
  assert.equal(isWithinLengthLimit("a".repeat(4001)), false);
  assert.equal(isWithinLengthLimit(""), true);
});

/**
 * Takes no arguments.
 * Checks a typed name matching an own name, one that does not, and a null matched_name.
 * Gives nothing; asserts each result.
 */
test("isSpellingCorrected fires only when the typed name is not one of the row's own names", () => {
  const corrected = row({ matched_name: ["trazdone", "TRAZODONE HYDROCHLORIDE"], generic: ["TRAZODONE HYDROCHLORIDE"] });
  assert.equal(isSpellingCorrected(corrected), true);
  const exact = row({ matched_name: ["Trazodone"], generic: ["Trazodone"] });
  assert.equal(isSpellingCorrected(exact), false);
  const unresolved = row({ matched_name: null });
  assert.equal(isSpellingCorrected(unresolved), false);
});

/**
 * Takes no arguments.
 * Checks a row with a generic name, one with only a matched_name, and one with neither.
 * Gives nothing; asserts each headline.
 */
test("rowHeadlineName prefers the generic name, then matched_name, then as_entered", () => {
  assert.equal(rowHeadlineName(row({ generic: ["OXYCODONE HYDROCHLORIDE"] })), "oxycodone hydrochloride");
  assert.equal(rowHeadlineName(row({ generic: [], matched_name: ["Lisinopril"] })), "lisinopril");
  assert.equal(rowHeadlineName(row({ generic: [], matched_name: null, as_entered: "Unknown Drug" })), "unknown drug");
});

/**
 * Takes no arguments.
 * Checks a candidate with an arrow and one without.
 * Gives nothing; asserts each label.
 */
test("candidateLabel takes the part before the arrow and lowercases it", () => {
  assert.equal(candidateLabel("DEXTROAMPHETAMINE SACCHARATE → AMPHETAMINE ASPARTATE MONOHYDRATE, ..."), "dextroamphetamine saccharate");
  assert.equal(candidateLabel("Plain Name"), "plain name");
});

/**
 * Takes no arguments.
 * Checks finding a matching row, no match, and an empty row list.
 * Gives nothing; asserts each result.
 */
test("findRowForLine matches by as_entered exactly", () => {
  const rows = [row({ as_entered: "OxyContin 20 mg bid" }), row({ as_entered: "Ambien 10 mg qhs" })];
  assert.equal(findRowForLine(rows, "Ambien 10 mg qhs"), rows[1]);
  assert.equal(findRowForLine(rows, "not present"), undefined);
  assert.equal(findRowForLine([], "anything"), undefined);
});

/**
 * Takes no arguments.
 * Checks a mix of resolved and unresolved rows, and the empty case.
 * Gives nothing; asserts each count.
 */
test("countResolvedRows counts only rows with a non-null matched_name", () => {
  const rows = [row({ matched_name: ["a"] }), row({ matched_name: null }), row({ matched_name: ["b"] })];
  assert.equal(countResolvedRows(rows), 2);
  assert.equal(countResolvedRows([]), 0);
});

/**
 * Takes a set of field overrides.
 * Builds a minimal UnresolvedEntry for a test.
 * Gives the UnresolvedEntry.
 */
function unresolvedEntry(overrides: Partial<UnresolvedEntry>): UnresolvedEntry {
  return { raw_text: "test entry", status: "needs_confirmation", reason: "", candidates: [], ...overrides };
}

/**
 * Takes a set of field overrides.
 * Builds a minimal CheckResponse for a test.
 * Gives the CheckResponse.
 */
function checkResponse(overrides: Partial<CheckResponse>): CheckResponse {
  return {
    build_date: "2026-09-21",
    medication_table: [],
    alerts: [],
    unresolved_entries: [],
    no_warning_text: "No warning found in the labels checked.",
    notice: "",
    ...overrides,
  };
}

/**
 * Takes no arguments.
 * Checks a line whose medication_table row is unresolved (matched_name null) but which also has a matching unresolved_entries entry with candidates -- the real shape /api/check returns for a "needs_confirmation" line, since medication_table always carries one row per line.
 * Gives nothing; fails if the row branch wins over the unresolved branch.
 */
test("statusForLine prefers the unresolved entry over a null-matched_name row for the same line", () => {
  const line = "venlafaxine 75 mg daily";
  const response = checkResponse({
    medication_table: [row({ as_entered: line, matched_name: null })],
    unresolved_entries: [unresolvedEntry({ raw_text: line, candidates: ["venlafaxine → VENLAFAXINE HYDROCHLORIDE"] })],
  });
  const status = statusForLine(line, response);
  assert.ok("unresolved" in status, "expected the unresolved branch");
});

/**
 * Takes no arguments.
 * Checks a line whose row resolved cleanly, one that matches neither list, and a null response.
 * Gives nothing; asserts each branch.
 */
test("statusForLine picks the row when it resolved and falls back to pending otherwise", () => {
  const resolvedRow = row({ as_entered: "Lyrica 100 mg tid", matched_name: ["Lyrica", "PREGABALIN"] });
  const response = checkResponse({ medication_table: [resolvedRow] });
  assert.deepEqual(statusForLine("Lyrica 100 mg tid", response), { row: resolvedRow });
  assert.deepEqual(statusForLine("not in the response", response), { pending: true });
  assert.deepEqual(statusForLine("anything", null), { pending: true });
});
