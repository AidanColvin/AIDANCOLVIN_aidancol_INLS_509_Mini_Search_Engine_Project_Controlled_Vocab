/**
 * Takes no arguments.
 * Tests the pure alert-sorting and evidence-picking helpers in src/alerts.ts.
 * Gives nothing; each test function is run by node:test.
 */

import assert from "node:assert/strict";
import test from "node:test";

import {
  additionalEvidenceMembers,
  alertDisplayTierName,
  alertDrugNames,
  alertGrade,
  alertIconKey,
  gradeCounts,
  membersWithEvidence,
  primaryEvidenceMember,
  sortAlerts,
} from "../src/alerts.js";
import type { AlertMember, AlertRecord } from "../src/records.js";

/**
 * Takes field overrides.
 * Builds a minimal AlertMember for a test.
 * Gives the AlertMember.
 */
function member(overrides: Partial<AlertMember>): AlertMember {
  return {
    drug_name: "Drug",
    set_id: "set-1",
    effective_time: "20260101",
    section: "warnings",
    sentence: "A sentence.",
    dailymed_url: "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=set-1",
    ...overrides,
  };
}

/**
 * Takes field overrides.
 * Builds a minimal AlertRecord for a test.
 * Gives the AlertRecord.
 */
function alert(overrides: Partial<AlertRecord>): AlertRecord {
  return {
    kind: "group",
    risk: "T15",
    title: "Title",
    tier: 3,
    tier_name: "Warning (heuristic)",
    members: [member({})],
    note: "",
    grade: null,
    grade_basis: null,
    category: "",
    mechanism: "",
    action: "",
    includes: [],
    references: [],
    rulebook_rows: [],
    ...overrides,
  };
}

/**
 * Takes no arguments.
 * Checks grade ordering (E, D, C, B, A) with an ungraded duplication flag falling back to C alongside tier 3, and stable order within a grade.
 * Gives nothing; asserts the sorted order.
 */
test("sortAlerts orders by grade, an ungraded duplication falls back to C, and API order holds within a grade", () => {
  const a = alert({ tier: 3, title: "warning-a" });
  const b = alert({ tier: 1, title: "contraindicated" });
  const c = alert({ tier: null, kind: "duplication", title: "dup" });
  const d = alert({ tier: 3, title: "warning-b" });
  const sorted = sortAlerts([a, b, c, d]);
  assert.deepEqual(
    sorted.map((x) => x.title),
    ["contraindicated", "warning-a", "dup", "warning-b"],
  );
});

/**
 * Takes no arguments.
 * Checks that a server-assigned grade wins over the tier, and counts alerts per grade.
 * Gives nothing; asserts the grade letters and the counts.
 */
test("alertGrade prefers the server grade and gradeCounts tallies every grade", () => {
  const graded = alert({ tier: 3, grade: "E" });
  const fallback = alert({ tier: 2 });
  assert.equal(alertGrade(graded).letter, "E");
  assert.equal(alertGrade(fallback).letter, "D");
  assert.deepEqual(gradeCounts([graded, fallback, alert({ grade: "D" })]), { A: 0, B: 0, C: 0, D: 2, E: 1 });
});

/**
 * Takes no arguments.
 * Checks a duplication alert and a non-duplication alert.
 * Gives nothing; asserts each display name.
 */
test("alertDisplayTierName overrides only duplication alerts", () => {
  assert.equal(alertDisplayTierName(alert({ kind: "duplication", tier_name: "heuristic" })), "Duplicate therapy");
  assert.equal(alertDisplayTierName(alert({ kind: "group", tier_name: "Warning (heuristic)" })), "Warning (heuristic)");
});

/**
 * Takes no arguments.
 * Checks joining several members and the empty case.
 * Gives nothing; asserts each joined string.
 */
test("alertDrugNames joins member drug names with a comma", () => {
  assert.equal(alertDrugNames([member({ drug_name: "A" }), member({ drug_name: "B" })]), "A, B");
  assert.equal(alertDrugNames([]), "");
});

/**
 * Takes no arguments.
 * Checks that a drug on two lines appears once in the alert heading.
 * Gives nothing; asserts on the joined names.
 */
test("alertDrugNames names a drug entered on two lines once (L05's two Coumadin lines)", () => {
  assert.equal(alertDrugNames([member({ drug_name: "Coumadin" }), member({ drug_name: "Coumadin" }), member({ drug_name: "Bactrim DS" })]), "Coumadin, Bactrim DS");
});

/**
 * Takes no arguments.
 * Checks that a dose-ceiling alert keeps the grade the server gave it.
 * Gives nothing; asserts grade D.
 */
test("alertGrade uses a class-rule grade from the server for a dose-ceiling alert", () => {
  assert.equal(alertGrade(alert({ kind: "ceiling", grade: "D", tier: null })).letter, "D");
});

/**
 * Takes no arguments.
 * Checks a mix of members with and without a section.
 * Gives nothing; asserts only the ones with evidence remain.
 */
test("membersWithEvidence drops members with an empty section", () => {
  const withEvidence = member({ drug_name: "A", section: "warnings" });
  const without = member({ drug_name: "B", section: "" });
  assert.deepEqual(membersWithEvidence([withEvidence, without]), [withEvidence]);
});

/**
 * Takes no arguments.
 * Checks that the strongest section wins regardless of member order, and that a pair alert's empty-section second member is skipped.
 * Gives nothing; asserts the picked member.
 */
test("primaryEvidenceMember picks the strongest section and skips empty ones", () => {
  const warning = member({ drug_name: "A", section: "warnings" });
  const boxed = member({ drug_name: "B", section: "boxed_warning" });
  assert.equal(primaryEvidenceMember([warning, boxed]), boxed);

  const source = member({ drug_name: "Source", section: "contraindications" });
  const other = member({ drug_name: "Other", section: "", sentence: "" });
  assert.equal(primaryEvidenceMember([source, other]), source);

  assert.equal(primaryEvidenceMember([other]), undefined);
});

/**
 * Takes no arguments.
 * Checks that the primary member is excluded from the "more" list and the empty case.
 * Gives nothing; asserts each result.
 */
test("additionalEvidenceMembers excludes the chosen primary member", () => {
  const a = member({ drug_name: "A", section: "boxed_warning" });
  const b = member({ drug_name: "B", section: "warnings" });
  const c = member({ drug_name: "C", section: "" });
  const primary = primaryEvidenceMember([a, b, c]);
  assert.deepEqual(additionalEvidenceMembers([a, b, c], primary), [b]);
  assert.deepEqual(additionalEvidenceMembers([a, b, c], undefined), [a, b]);
});

/**
 * Takes no arguments.
 * Checks every tier and the duplication kind, and the null-tier fallback.
 * Gives nothing; asserts each icon key.
 */
test("alertIconKey picks the duplication icon or the tier icon, tier 4 as the fallback", () => {
  assert.equal(alertIconKey(alert({ kind: "pair", tier: 1 })), "tier-1");
  assert.equal(alertIconKey(alert({ kind: "group", tier: 2 })), "tier-2");
  assert.equal(alertIconKey(alert({ kind: "group", tier: 3 })), "tier-3");
  assert.equal(alertIconKey(alert({ kind: "group", tier: 4 })), "tier-4");
  assert.equal(alertIconKey(alert({ kind: "duplication", tier: null })), "duplication");
});
