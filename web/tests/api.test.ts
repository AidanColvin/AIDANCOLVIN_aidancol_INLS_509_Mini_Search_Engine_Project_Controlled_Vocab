/**
 * Takes no arguments.
 * Tests the response validators in src/api.ts against real API shapes, including the trimmed BUILD_PROMPT.md Appendix B payload.
 * Gives nothing; each test function is run by node:test.
 */

import assert from "node:assert/strict";
import test from "node:test";

import { ApiShapeError, parseCheckResponse, parseSearchResponse, parseTermsOnlyResponse } from "../src/api.js";

// BUILD_PROMPT.md Appendix B, trimmed: the repo's own /api/check output for
// "OxyContin 20 mg bid, ..., dextroamphetamine 10 mg bid" against the fixture
// labels (build date 2026-09-21).
const APPENDIX_B_CHECK_RESPONSE: unknown = {
  build_date: "2026-09-21",
  medication_table: [
    {
      as_entered: "OxyContin 20 mg bid",
      matched_name: ["OxyContin", "OXYCODONE HYDROCHLORIDE"],
      generic: ["OXYCODONE HYDROCHLORIDE"],
      base_ingredients: ["oxycodone"],
      brand: ["OxyContin"],
      fda_class: "Not listed on label.",
      route: ["ORAL"],
      dea_schedule: "II",
      strength: null,
      times_per_day: null,
      daily_total: 40.0,
      daily_total_unit: "mg",
      pdla_tags: [
        { term_id: "T01", name: "Boxed Warning" },
        { term_id: "T02", name: "Oral Route" },
        { term_id: "T03", name: "Pediatric Indication" },
      ],
      label_notes: [],
    },
    {
      as_entered: "dextroamphetamine 10 mg bid",
      matched_name: null,
      generic: [],
      base_ingredients: [],
      brand: [],
      fda_class: "Not listed on label.",
      route: [],
      dea_schedule: null,
      strength: null,
      times_per_day: null,
      daily_total: 20.0,
      daily_total_unit: "mg",
      pdla_tags: [],
      label_notes: [],
    },
  ],
  alerts: [
    {
      kind: "group",
      risk: "T15",
      title: "CNS Depression Risk shared by 5 drugs",
      tier: 2,
      tier_name: "Boxed warning (heuristic)",
      members: [
        {
          drug_name: "OxyContin",
          set_id: "bfdfe235-d717-4855-a3c8-a13d26dadede",
          effective_time: "20260624",
          section: "boxed_warning",
          sentence: "Life-Threatening Respiratory Depression...",
          dailymed_url: "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=bfdfe235-d717-4855-a3c8-a13d26dadede",
        },
        {
          drug_name: "Ambien",
          set_id: "c36cadf4-65a4-4466-b409-c82020b42452",
          effective_time: "20250415",
          section: "warnings_and_cautions",
          sentence: "Risk increases with dose and use with other CNS depressants and alcohol.",
          dailymed_url: "https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=c36cadf4-65a4-4466-b409-c82020b42452",
        },
      ],
      note: "",
    },
  ],
  unresolved_entries: [
    {
      raw_text: "dextroamphetamine 10 mg bid",
      status: "needs_confirmation",
      reason: "two or more names are equally close",
      candidates: [
        "DEXTROAMPHETAMINE SACCHARATE → AMPHETAMINE ASPARTATE MONOHYDRATE, AMPHETAMINE SULFATE, DEXTROAMPHETAMINE SACCHARATE, DEXTROAMPHETAMINE SULFATE",
        "DEXTROAMPHETAMINE SULFATE → AMPHETAMINE ASPARTATE MONOHYDRATE, AMPHETAMINE SULFATE, DEXTROAMPHETAMINE SACCHARATE, DEXTROAMPHETAMINE SULFATE | DEXTROAMPHETAMINE SULFATE",
      ],
    },
  ],
  no_warning_text: "No warning found in the labels checked.",
  notice:
    'Results reflect FDA label text as of 2026-09-21. "No warning found" does not mean a combination is safe. This tool is not validated for clinical use and does not replace clinical judgment or a licensed drug interaction database.',
};

/**
 * Takes no arguments.
 * Parses the real Appendix B payload.
 * Gives nothing; asserts the parsed shape carries every field through, including a null matched_name.
 */
test("parseCheckResponse accepts the real Appendix B payload", () => {
  const parsed = parseCheckResponse(APPENDIX_B_CHECK_RESPONSE);
  assert.equal(parsed.build_date, "2026-09-21");
  assert.equal(parsed.medication_table.length, 2);
  assert.deepEqual(parsed.medication_table[0]?.matched_name, ["OxyContin", "OXYCODONE HYDROCHLORIDE"]);
  assert.equal(parsed.medication_table[1]?.matched_name, null);
  assert.equal(parsed.alerts.length, 1);
  assert.equal(parsed.alerts[0]?.members.length, 2);
  assert.equal(parsed.unresolved_entries[0]?.status, "needs_confirmation");
});

/**
 * Takes no arguments.
 * Parses a response missing the required "alerts" field.
 * Gives nothing; asserts ApiShapeError is thrown, not a silent default.
 */
test("parseCheckResponse throws ApiShapeError on a missing field", () => {
  const bad = { ...(APPENDIX_B_CHECK_RESPONSE as Record<string, unknown>) };
  delete bad["alerts"];
  assert.throws(() => parseCheckResponse(bad), ApiShapeError);
});

/**
 * Takes no arguments.
 * Parses a response whose alert kind is not one of the three known values.
 * Gives nothing; asserts ApiShapeError is thrown.
 */
test("parseCheckResponse throws ApiShapeError on an unknown alert kind", () => {
  const bad = {
    ...(APPENDIX_B_CHECK_RESPONSE as Record<string, unknown>),
    alerts: [{ ...(APPENDIX_B_CHECK_RESPONSE as { alerts: Record<string, unknown>[] }).alerts[0], kind: "unknown" }],
  };
  assert.throws(() => parseCheckResponse(bad), ApiShapeError);
});

/**
 * Takes no arguments.
 * Parses null and a plain string.
 * Gives nothing; asserts ApiShapeError is thrown for both.
 */
test("parseCheckResponse throws ApiShapeError on a non-object top level", () => {
  assert.throws(() => parseCheckResponse(null), ApiShapeError);
  assert.throws(() => parseCheckResponse("not an object"), ApiShapeError);
});

/**
 * Takes no arguments.
 * Parses a well-formed /api/search response.
 * Gives nothing; asserts every hit field is carried through.
 */
test("parseSearchResponse accepts a well-formed response", () => {
  const response = {
    hits: [
      {
        set_id: "5d536e88-62be-45bd-bd09-0efc53fe12b9",
        brand_name: "",
        generic_name: "cyclobenzaprine hydrochloride",
        snippet: "relief of muscle spasm",
        tags: ["T14", "T15"],
        effective_time: "20260909",
        score: 12.5,
      },
    ],
    query: "muscle spasm",
    operator: "AND",
    build_date: "2026-09-21",
  };
  const parsed = parseSearchResponse(response);
  assert.equal(parsed.hits.length, 1);
  assert.equal(parsed.hits[0]?.score, 12.5);
  assert.deepEqual(parsed.hits[0]?.tags, ["T14", "T15"]);
});

/**
 * Takes no arguments.
 * Parses a response whose "hits" field is not an array.
 * Gives nothing; asserts ApiShapeError is thrown.
 */
test("parseSearchResponse throws ApiShapeError when hits is not an array", () => {
  assert.throws(() => parseSearchResponse({ hits: "not an array", query: "", operator: "AND", build_date: "2026-09-21" }), ApiShapeError);
});

/**
 * Takes no arguments.
 * Parses a well-formed terms_only response.
 * Gives nothing; asserts every term field is carried through.
 */
test("parseTermsOnlyResponse accepts a well-formed response", () => {
  const response = {
    build_date: "2026-09-21",
    available_terms: [{ term_id: "T14", name: "Serotonin Syndrome Risk", property_group: "Interaction risk" }],
  };
  const parsed = parseTermsOnlyResponse(response);
  assert.equal(parsed.available_terms.length, 1);
  assert.equal(parsed.available_terms[0]?.term_id, "T14");
});
