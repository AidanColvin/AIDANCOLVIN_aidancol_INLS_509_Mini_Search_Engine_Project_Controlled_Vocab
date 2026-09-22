/**
 * Takes no arguments.
 * Tests the pure label-search helpers in src/search.ts.
 * Gives nothing; each test function is run by node:test.
 */

import assert from "node:assert/strict";
import test from "node:test";

import {
  groupTermsByPropertyGroup,
  hitTitle,
  orderTermsWithinGroup,
  queryWordsFromQuery,
  resolveTagNames,
  splitSnippetIntoSegments,
  splitTagsByActiveFilters,
  termIndentLevel,
  termsById,
} from "../src/search.js";
import type { SearchHit, TermInfo } from "../src/records.js";

/**
 * Takes a term id, name, and property group.
 * Builds a minimal TermInfo for a test.
 * Gives the TermInfo.
 */
function term(termId: string, termName: string, propertyGroup: string): TermInfo {
  return { term_id: termId, name: termName, property_group: propertyGroup };
}

/**
 * Takes no arguments.
 * Checks every narrower term MiniVocab Section 1 names, and one term with no parent.
 * Gives nothing; asserts each indent level.
 */
test("termIndentLevel flags exactly the narrower terms", () => {
  for (const narrower of ["T10", "T06", "T12", "T14", "T15", "T16", "T17"]) {
    assert.equal(termIndentLevel(narrower), 1, narrower);
  }
  assert.equal(termIndentLevel("T13"), 0);
  assert.equal(termIndentLevel("T01"), 0);
});

/**
 * Takes no arguments.
 * Checks that a broader term's children move to sit right after it, in their original relative order.
 * Gives nothing; asserts the reordered sequence.
 */
test("orderTermsWithinGroup places each narrower term after the broader term it narrows", () => {
  const terms = [
    term("T06", "Renal Dose Adjustment", "Dosing"),
    term("T11", "Organ Impairment Dose Adjustment", "Dosing"),
    term("T12", "Hepatic Dose Adjustment", "Dosing"),
  ];
  const ordered = orderTermsWithinGroup(terms);
  assert.deepEqual(
    ordered.map((t) => t.term_id),
    ["T11", "T06", "T12"],
  );
});

/**
 * Takes no arguments.
 * Checks a narrower term whose broader term is not in this group.
 * Gives nothing; asserts it keeps its original position instead of being dropped.
 */
test("orderTermsWithinGroup leaves a narrower term alone when its broader term is not in the group", () => {
  const terms = [term("T10", "Schedule II Controlled Substance", "DEA control")];
  assert.deepEqual(orderTermsWithinGroup(terms), terms);
});

/**
 * Takes no arguments.
 * Checks that groups are ordered by first appearance and each group's terms are internally ordered.
 * Gives nothing; asserts the grouped, ordered result.
 */
test("groupTermsByPropertyGroup orders groups by first appearance", () => {
  const terms = [
    term("T01", "Boxed Warning", "Safety signal"),
    term("T11", "Organ Impairment Dose Adjustment", "Dosing"),
    term("T04", "High-Frequency Adverse Effect", "Safety signal"),
    term("T06", "Renal Dose Adjustment", "Dosing"),
  ];
  const groups = groupTermsByPropertyGroup(terms);
  assert.deepEqual(
    groups.map((g) => g.propertyGroup),
    ["Safety signal", "Dosing"],
  );
  assert.deepEqual(
    groups[1]?.terms.map((t) => t.term_id),
    ["T11", "T06"],
  );
});

/**
 * Takes no arguments.
 * Checks an empty term list.
 * Gives nothing; asserts an empty result.
 */
test("groupTermsByPropertyGroup gives no groups for no terms", () => {
  assert.deepEqual(groupTermsByPropertyGroup([]), []);
});

/**
 * Takes no arguments.
 * Checks that termsById finds a known id and gives undefined for an unknown one.
 * Gives nothing; asserts each lookup.
 */
test("termsById builds a lookup by term id", () => {
  const t = term("T14", "Serotonin Syndrome Risk", "Interaction risk");
  const byId = termsById([t]);
  assert.equal(byId.get("T14"), t);
  assert.equal(byId.get("T99"), undefined);
});

/**
 * Takes no arguments.
 * Checks resolving a known and an unknown tag id.
 * Gives nothing; asserts each resolved name.
 */
test("resolveTagNames falls back to the raw id for an unknown tag", () => {
  const byId = termsById([term("T14", "Serotonin Syndrome Risk", "Interaction risk")]);
  assert.deepEqual(resolveTagNames(["T14", "T99"], byId), [
    { termId: "T14", name: "Serotonin Syndrome Risk" },
    { termId: "T99", name: "T99" },
  ]);
});

/**
 * Takes no arguments.
 * Checks splitting tags into matching and non-matching an active filter set, and the no-filter case.
 * Gives nothing; asserts each split.
 */
test("splitTagsByActiveFilters puts everything in rest when no filter is active", () => {
  const tags = [
    { termId: "T14", name: "Serotonin Syndrome Risk" },
    { termId: "T15", name: "CNS Depression Risk" },
  ];
  assert.deepEqual(splitTagsByActiveFilters(tags, ["T14"]), { matching: [tags[0]], rest: [tags[1]] });
  assert.deepEqual(splitTagsByActiveFilters(tags, []), { matching: [], rest: tags });
});

/**
 * Takes no arguments.
 * Checks splitting a query into lowercase words and the empty case.
 * Gives nothing; asserts each split.
 */
test("queryWordsFromQuery lowercases and splits on whitespace", () => {
  assert.deepEqual(queryWordsFromQuery("Muscle Spasm"), ["muscle", "spasm"]);
  assert.deepEqual(queryWordsFromQuery("   "), []);
  assert.deepEqual(queryWordsFromQuery(""), []);
});

/**
 * Takes no arguments.
 * Checks that words matching the query are marked bold and the rest are not, and the no-query case.
 * Gives nothing; asserts the segment list.
 */
test("splitSnippetIntoSegments marks only the query's words bold", () => {
  const segments = splitSnippetIntoSegments("relief of muscle spasm associated with acute pain", "muscle spasm");
  const bolded = segments.filter((s) => s.bold).map((s) => s.text);
  assert.deepEqual(bolded, ["muscle", "spasm"]);
  const joined = segments.map((s) => s.text).join("");
  assert.equal(joined, "relief of muscle spasm associated with acute pain");

  const noQuery = splitSnippetIntoSegments("some text", "");
  assert.deepEqual(noQuery, [{ text: "some text", bold: false }]);
});

/**
 * Takes a set of field overrides.
 * Builds a minimal SearchHit for a test.
 * Gives the SearchHit.
 */
function hit(overrides: Partial<SearchHit>): SearchHit {
  return {
    set_id: "set-1",
    brand_name: "",
    generic_name: "",
    snippet: "",
    tags: [],
    effective_time: "20260101",
    score: 1,
    ...overrides,
  };
}

/**
 * Takes no arguments.
 * Checks a brand that differs from the generic, a brand matching the generic ignoring case, and an empty brand.
 * Gives nothing; asserts each title.
 */
test("hitTitle falls back to the lowercase generic when the brand is empty or matches it", () => {
  const branded = hitTitle(hit({ brand_name: "OxyContin", generic_name: "OXYCODONE HYDROCHLORIDE" }));
  assert.deepEqual(branded, { primary: "OxyContin", primaryIsGeneric: false, secondaryGeneric: "OXYCODONE HYDROCHLORIDE" });

  const sameName = hitTitle(hit({ brand_name: "TRAZODONE HYDROCHLORIDE", generic_name: "trazodone hydrochloride" }));
  assert.deepEqual(sameName, { primary: "trazodone hydrochloride", primaryIsGeneric: true, secondaryGeneric: null });

  const noBrand = hitTitle(hit({ brand_name: "", generic_name: "GABAPENTIN" }));
  assert.deepEqual(noBrand, { primary: "gabapentin", primaryIsGeneric: true, secondaryGeneric: null });
});
