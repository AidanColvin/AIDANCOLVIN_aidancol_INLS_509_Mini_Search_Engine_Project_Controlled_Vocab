/**
 * Takes no arguments.
 * Tests the pure formatting helpers in src/format.ts.
 * Gives nothing; each test function is run by node:test.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { formatBuildDate, formatDailyTotal, formatMatchedChain, pluralizeCount, sectionDisplayName } from "../src/format.js";

/**
 * Takes no arguments.
 * Checks every section value BUILD_PROMPT.md Section 4.2's table names, and one unknown value.
 * Gives nothing; asserts each mapping.
 */
test("sectionDisplayName maps every known section and falls back on an unknown one", () => {
  assert.equal(sectionDisplayName("contraindications"), "Contraindications");
  assert.equal(sectionDisplayName("boxed_warning"), "Boxed Warning");
  assert.equal(sectionDisplayName("warnings_and_cautions"), "Warnings and Precautions");
  assert.equal(sectionDisplayName("warnings"), "Warnings");
  assert.equal(sectionDisplayName("precautions"), "Precautions");
  assert.equal(sectionDisplayName("drug_interactions"), "Drug Interactions");
  assert.equal(sectionDisplayName("description"), "Description");
  assert.equal(sectionDisplayName("unknown_field"), "unknown_field");
});

/**
 * Takes no arguments.
 * Checks a whole number, a missing total, and a missing unit.
 * Gives nothing; asserts each formatted string.
 */
test("formatDailyTotal drops a trailing .0 and handles missing values", () => {
  assert.equal(formatDailyTotal(40, "mg"), "40 mg/day");
  assert.equal(formatDailyTotal(0.5, "mg"), "0.5 mg/day");
  assert.equal(formatDailyTotal(null, "mg"), "");
  assert.equal(formatDailyTotal(10, null), "10/day");
});

/**
 * Takes no arguments.
 * Checks singular and plural counts.
 * Gives nothing; asserts each pluralized string.
 */
test("pluralizeCount uses the singular only for exactly one", () => {
  assert.equal(pluralizeCount(1, "alert"), "1 alert");
  assert.equal(pluralizeCount(0, "alert"), "0 alerts");
  assert.equal(pluralizeCount(2, "alert"), "2 alerts");
});

/**
 * Takes no arguments.
 * Checks a multi-step chain and the empty case.
 * Gives nothing; asserts each joined string.
 */
test("formatMatchedChain joins with the arrow separator and handles the empty case", () => {
  assert.equal(formatMatchedChain(["OxyContin", "OXYCODONE HYDROCHLORIDE"]), "OxyContin → OXYCODONE HYDROCHLORIDE");
  assert.equal(formatMatchedChain([]), "");
});

/**
 * Takes no arguments.
 * Checks a well-formed ISO date and a value that is not one.
 * Gives nothing; asserts each formatted string.
 */
test("formatBuildDate formats an ISO date and passes through anything else unchanged", () => {
  assert.equal(formatBuildDate("2026-09-21"), "Sep 21, 2026");
  assert.equal(formatBuildDate("2026-01-05"), "Jan 5, 2026");
  assert.equal(formatBuildDate("not-a-date"), "not-a-date");
});
