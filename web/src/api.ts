/**
 * Takes no arguments.
 * Fetches from /api/check and /api/search and validates each response's shape before returning it.
 * Gives nothing; every exported function is called for its return value or thrown error.
 */

import type {
  AlertMember,
  AlertRecord,
  AlertReference,
  CheckResponse,
  ComponentStrength,
  LabelNote,
  MedicationRow,
  MoleculeTotal,
  PdlaTag,
  SearchHit,
  SearchResponse,
  TermInfo,
  TermsOnlyResponse,
  UnresolvedEntry,
} from "./records.js";

const MAX_MEDICATION_TEXT_CHARS = 4000;

export class ApiHttpError extends Error {
  readonly status: number;
  readonly apiMessage: string;

  /**
   * Takes the response's HTTP status and the API's own error text, when it has one.
   * Builds an error carrying both, with a human-readable message.
   * Gives the constructed ApiHttpError.
   */
  constructor(httpStatus: number, apiMessage: string) {
    super(`API request failed with status ${httpStatus}: ${apiMessage}`);
    this.name = "ApiHttpError";
    this.status = httpStatus;
    this.apiMessage = apiMessage;
  }
}

export class ApiShapeError extends Error {
  /**
   * Takes a description of what was expected.
   * Builds an error for a response whose JSON shape does not match the API contract.
   * Gives the constructed ApiShapeError.
   */
  constructor(expected: string) {
    super(`API response did not match the expected shape: ${expected}`);
    this.name = "ApiShapeError";
  }
}

/**
 * Takes an unknown value and a label describing what it should be.
 * Checks whether it is a plain object (not null, not an array).
 * Gives the value narrowed to a record, or throws ApiShapeError.
 */
function asRecord(value: unknown, label: string): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ApiShapeError(`${label} must be an object`);
  }
  return value as Record<string, unknown>;
}

/**
 * Takes an unknown value and a label.
 * Checks whether it is a string.
 * Gives the string, or throws ApiShapeError.
 */
function asString(value: unknown, label: string): string {
  if (typeof value !== "string") {
    throw new ApiShapeError(`${label} must be a string`);
  }
  return value;
}

/**
 * Takes an unknown value and a label.
 * Checks whether it is a number.
 * Gives the number, or throws ApiShapeError.
 */
function asNumber(value: unknown, label: string): number {
  if (typeof value !== "number") {
    throw new ApiShapeError(`${label} must be a number`);
  }
  return value;
}

/**
 * Takes an unknown value, a label, and a converter for each element.
 * Checks whether it is an array and converts every element.
 * Gives the readonly array of converted elements, or throws ApiShapeError.
 */
function asArray<T>(value: unknown, label: string, convert: (item: unknown, index: number) => T): readonly T[] {
  if (!Array.isArray(value)) {
    throw new ApiShapeError(`${label} must be an array`);
  }
  return value.map((item, index) => convert(item, index));
}

/**
 * Takes an unknown value and a label.
 * Checks whether it is a string or null.
 * Gives the string or null, or throws ApiShapeError.
 */
function asNullableString(value: unknown, label: string): string | null {
  return value === null ? null : asString(value, label);
}

/**
 * Takes an unknown value and a label.
 * Checks whether it is a number or null.
 * Gives the number or null, or throws ApiShapeError.
 */
function asNullableNumber(value: unknown, label: string): number | null {
  return value === null ? null : asNumber(value, label);
}

/**
 * Takes an unknown value.
 * Validates it as one PdlaTag.
 * Gives the PdlaTag, or throws ApiShapeError.
 */
function toPdlaTag(value: unknown): PdlaTag {
  const record = asRecord(value, "pdla_tags[]");
  return {
    term_id: asString(record["term_id"], "pdla_tags[].term_id"),
    name: asString(record["name"], "pdla_tags[].name"),
  };
}

/**
 * Takes an unknown value.
 * Validates it as one label note: a term id and name, the label field it came from, and its sentence.
 * Gives the LabelNote, or throws ApiShapeError.
 */
function toLabelNote(value: unknown): LabelNote {
  const record = asRecord(value, "label_notes[]");
  return {
    term_id: asString(record["term_id"], "label_notes[].term_id"),
    name: asString(record["name"], "label_notes[].name"),
    field_name: asString(record["field_name"], "label_notes[].field_name"),
    sentence: asString(record["sentence"], "label_notes[].sentence"),
  };
}

/**
 * Takes an unknown value.
 * Validates it as one medication table row, treating the strength, frequency, and label-note fields as absent when an older server omits them.
 * Gives the MedicationRow, or throws ApiShapeError.
 */
function toMedicationRow(value: unknown): MedicationRow {
  const record = asRecord(value, "medication_table[]");
  const matchedName = record["matched_name"];
  return {
    as_entered: asString(record["as_entered"], "medication_table[].as_entered"),
    matched_name: matchedName === null ? null : asArray(matchedName, "medication_table[].matched_name", (item) => asString(item, "matched_name[]")),
    generic: asArray(record["generic"], "medication_table[].generic", (item) => asString(item, "generic[]")),
    base_ingredients: asArray(record["base_ingredients"], "medication_table[].base_ingredients", (item) => asString(item, "base_ingredients[]")),
    brand: asArray(record["brand"], "medication_table[].brand", (item) => asString(item, "brand[]")),
    fda_class: asString(record["fda_class"], "medication_table[].fda_class"),
    route: asArray(record["route"], "medication_table[].route", (item) => asString(item, "route[]")),
    dea_schedule: asNullableString(record["dea_schedule"], "medication_table[].dea_schedule"),
    strength: record["strength"] === undefined ? null : asNullableNumber(record["strength"], "medication_table[].strength"),
    times_per_day: record["times_per_day"] === undefined ? null : asNullableNumber(record["times_per_day"], "medication_table[].times_per_day"),
    daily_total: asNullableNumber(record["daily_total"], "medication_table[].daily_total"),
    daily_total_unit: asNullableString(record["daily_total_unit"], "medication_table[].daily_total_unit"),
    pdla_tags: asArray(record["pdla_tags"], "medication_table[].pdla_tags", toPdlaTag),
    label_notes: record["label_notes"] === undefined ? [] : asArray(record["label_notes"], "medication_table[].label_notes", toLabelNote),
    brand_typed: optionalString(record["brand_typed"], "medication_table[].brand_typed"),
    components: record["components"] === undefined ? [] : asArray(record["components"], "medication_table[].components", toComponentStrength),
    dose_count: optionalNumber(record["dose_count"], "medication_table[].dose_count"),
    days_per_week: optionalNumber(record["days_per_week"], "medication_table[].days_per_week"),
    schedule_text: optionalString(record["schedule_text"], "medication_table[].schedule_text"),
    as_needed: record["as_needed"] === true,
    release_form: optionalString(record["release_form"], "medication_table[].release_form"),
    no_label: record["no_label"] === true,
  };
}

/**
 * Takes an unknown value and a label for error messages.
 * Reads an optional string field, treating a missing field as null.
 * Gives the string or null, or throws ApiShapeError for any other type.
 */
function optionalString(value: unknown, label: string): string | null {
  return value === undefined ? null : asNullableString(value, label);
}

/**
 * Takes an unknown value and a label for error messages.
 * Reads an optional number field, treating a missing field as null.
 * Gives the number or null, or throws ApiShapeError for any other type.
 */
function optionalNumber(value: unknown, label: string): number | null {
  return value === undefined ? null : asNullableNumber(value, label);
}

/**
 * Takes an unknown value.
 * Validates it as one component strength of a combination product.
 * Gives the ComponentStrength, or throws ApiShapeError.
 */
function toComponentStrength(value: unknown): ComponentStrength {
  const record = asRecord(value, "components[]");
  return {
    name: asString(record["name"], "components[].name"),
    strength: asNumber(record["strength"], "components[].strength"),
    unit: asString(record["unit"], "components[].unit"),
  };
}

/**
 * Takes an unknown value.
 * Validates it as one per-ingredient total.
 * Gives the MoleculeTotal, or throws ApiShapeError.
 */
function toMoleculeTotal(value: unknown): MoleculeTotal {
  const record = asRecord(value, "molecule_totals[]");
  return {
    ingredient: asString(record["ingredient"], "molecule_totals[].ingredient"),
    text: asString(record["text"], "molecule_totals[].text"),
    period: asString(record["period"], "molecule_totals[].period"),
    entries: asArray(record["entries"], "molecule_totals[].entries", (item) => asString(item, "entries[]")),
    entry_count: asNumber(record["entry_count"], "molecule_totals[].entry_count"),
    as_needed: record["as_needed"] === true,
    mme: optionalNumber(record["mme"], "molecule_totals[].mme"),
  };
}

/**
 * Takes an unknown value.
 * Validates it as one alert reference.
 * Gives the AlertReference, or throws ApiShapeError.
 */
function toAlertReference(value: unknown): AlertReference {
  const record = asRecord(value, "references[]");
  return { label: asString(record["label"], "references[].label"), url: asString(record["url"], "references[].url") };
}

/**
 * Takes an unknown value.
 * Validates it as one alert member.
 * Gives the AlertMember, or throws ApiShapeError.
 */
function toAlertMember(value: unknown): AlertMember {
  const record = asRecord(value, "alerts[].members[]");
  return {
    drug_name: asString(record["drug_name"], "members[].drug_name"),
    set_id: asString(record["set_id"], "members[].set_id"),
    effective_time: asString(record["effective_time"], "members[].effective_time"),
    section: asString(record["section"], "members[].section"),
    sentence: asString(record["sentence"], "members[].sentence"),
    dailymed_url: asString(record["dailymed_url"], "members[].dailymed_url"),
  };
}

/**
 * Takes an unknown value.
 * Checks whether it is one of the three known alert kinds.
 * Gives the narrowed kind, or throws ApiShapeError.
 */
function toAlertKind(value: unknown): AlertRecord["kind"] {
  if (value === "group" || value === "pair" || value === "duplication" || value === "ceiling") {
    return value;
  }
  throw new ApiShapeError(`alerts[].kind must be "group", "pair", "duplication", or "ceiling"`);
}

/**
 * Takes an unknown value.
 * Validates it as one alert.
 * Gives the AlertRecord, or throws ApiShapeError.
 */
function toAlertRecord(value: unknown): AlertRecord {
  const record = asRecord(value, "alerts[]");
  return {
    kind: toAlertKind(record["kind"]),
    risk: asString(record["risk"], "alerts[].risk"),
    title: asString(record["title"], "alerts[].title"),
    tier: asNullableNumber(record["tier"], "alerts[].tier"),
    tier_name: asString(record["tier_name"], "alerts[].tier_name"),
    members: asArray(record["members"], "alerts[].members", toAlertMember),
    note: asString(record["note"], "alerts[].note"),
    grade: record["grade"] === undefined ? null : asNullableString(record["grade"], "alerts[].grade"),
    grade_basis: record["grade_basis"] === undefined ? null : asNullableString(record["grade_basis"], "alerts[].grade_basis"),
    category: optionalString(record["category"], "alerts[].category") ?? "",
    mechanism: optionalString(record["mechanism"], "alerts[].mechanism") ?? "",
    action: optionalString(record["action"], "alerts[].action") ?? "",
    includes: record["includes"] === undefined ? [] : asArray(record["includes"], "alerts[].includes", (item) => asString(item, "includes[]")),
    references: record["references"] === undefined ? [] : asArray(record["references"], "alerts[].references", toAlertReference),
    rulebook_rows: record["rulebook_rows"] === undefined ? [] : asArray(record["rulebook_rows"], "alerts[].rulebook_rows", (item) => asNumber(item, "rulebook_rows[]")),
  };
}

/**
 * Takes an unknown value.
 * Checks whether it is one of the two known unresolved-entry statuses.
 * Gives the narrowed status, or throws ApiShapeError.
 */
function toUnresolvedStatus(value: unknown): UnresolvedEntry["status"] {
  if (value === "unresolved" || value === "needs_confirmation") {
    return value;
  }
  throw new ApiShapeError(`unresolved_entries[].status must be "unresolved" or "needs_confirmation"`);
}

/**
 * Takes an unknown value.
 * Validates it as one unresolved entry.
 * Gives the UnresolvedEntry, or throws ApiShapeError.
 */
function toUnresolvedEntry(value: unknown): UnresolvedEntry {
  const record = asRecord(value, "unresolved_entries[]");
  return {
    raw_text: asString(record["raw_text"], "unresolved_entries[].raw_text"),
    status: toUnresolvedStatus(record["status"]),
    reason: asString(record["reason"], "unresolved_entries[].reason"),
    candidates: asArray(record["candidates"], "unresolved_entries[].candidates", (item) => asString(item, "candidates[]")),
  };
}

/**
 * Takes an unknown decoded JSON value.
 * Validates it as a full /api/check success response.
 * Gives the CheckResponse, or throws ApiShapeError.
 */
export function parseCheckResponse(value: unknown): CheckResponse {
  const record = asRecord(value, "check response");
  return {
    build_date: asString(record["build_date"], "build_date"),
    medication_table: asArray(record["medication_table"], "medication_table", toMedicationRow),
    alerts: asArray(record["alerts"], "alerts", toAlertRecord),
    molecule_totals: record["molecule_totals"] === undefined ? [] : asArray(record["molecule_totals"], "molecule_totals", toMoleculeTotal),
    total_mme: optionalNumber(record["total_mme"], "total_mme"),
    unresolved_entries: asArray(record["unresolved_entries"], "unresolved_entries", toUnresolvedEntry),
    no_warning_text: asString(record["no_warning_text"], "no_warning_text"),
    notice: asString(record["notice"], "notice"),
  };
}

/**
 * Takes an unknown value.
 * Validates it as one search hit.
 * Gives the SearchHit, or throws ApiShapeError.
 */
function toSearchHit(value: unknown): SearchHit {
  const record = asRecord(value, "hits[]");
  return {
    set_id: asString(record["set_id"], "hits[].set_id"),
    brand_name: asString(record["brand_name"], "hits[].brand_name"),
    generic_name: asString(record["generic_name"], "hits[].generic_name"),
    snippet: asString(record["snippet"], "hits[].snippet"),
    tags: asArray(record["tags"], "hits[].tags", (item) => asString(item, "tags[]")),
    effective_time: asString(record["effective_time"], "hits[].effective_time"),
    score: asNumber(record["score"], "hits[].score"),
  };
}

/**
 * Takes an unknown decoded JSON value.
 * Validates it as a full /api/search success response.
 * Gives the SearchResponse, or throws ApiShapeError.
 */
export function parseSearchResponse(value: unknown): SearchResponse {
  const record = asRecord(value, "search response");
  return {
    hits: asArray(record["hits"], "hits", toSearchHit),
    query: asString(record["query"], "query"),
    operator: asString(record["operator"], "operator"),
    build_date: asString(record["build_date"], "build_date"),
  };
}

/**
 * Takes an unknown value.
 * Validates it as one available term.
 * Gives the TermInfo, or throws ApiShapeError.
 */
function toTermInfo(value: unknown): TermInfo {
  const record = asRecord(value, "available_terms[]");
  return {
    term_id: asString(record["term_id"], "available_terms[].term_id"),
    name: asString(record["name"], "available_terms[].name"),
    property_group: asString(record["property_group"], "available_terms[].property_group"),
  };
}

/**
 * Takes an unknown decoded JSON value.
 * Validates it as a full /api/search?terms_only=1 response.
 * Gives the TermsOnlyResponse, or throws ApiShapeError.
 */
export function parseTermsOnlyResponse(value: unknown): TermsOnlyResponse {
  const record = asRecord(value, "terms_only response");
  return {
    build_date: asString(record["build_date"], "build_date"),
    available_terms: asArray(record["available_terms"], "available_terms", toTermInfo),
  };
}

/**
 * Takes a fetch Response that was not ok.
 * Reads its body as JSON and pulls out the "error" field when present.
 * Gives the ApiHttpError to throw, falling back to the status text when the body has no error field.
 */
async function errorFromResponse(response: Response): Promise<ApiHttpError> {
  try {
    const body: unknown = await response.json();
    const record = asRecord(body, "error response");
    const message = typeof record["error"] === "string" ? record["error"] : response.statusText;
    return new ApiHttpError(response.status, message);
  } catch {
    return new ApiHttpError(response.status, response.statusText);
  }
}

/**
 * Takes the medication list text, whether to use the RxNorm fallback, and an AbortSignal.
 * Sends POST /api/check and validates the response.
 * Gives the CheckResponse, or throws ApiHttpError, ApiShapeError, or the fetch call's own error.
 */
export async function fetchCheck(medications: string, useRxnorm: boolean, signal: AbortSignal): Promise<CheckResponse> {
  const response = await fetch("/api/check", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ medications, use_rxnorm: useRxnorm }),
    signal,
  });
  if (!response.ok) {
    throw await errorFromResponse(response);
  }
  const body: unknown = await response.json();
  return parseCheckResponse(body);
}

/**
 * Takes no arguments.
 * Reads the maximum medication text length the server accepts.
 * Gives that length, so the caller can check a joined list against it before sending.
 */
export function maxMedicationTextChars(): number {
  return MAX_MEDICATION_TEXT_CHARS;
}

export interface SearchParams {
  readonly q: string;
  readonly terms: readonly string[];
  readonly operator: "AND" | "OR";
  readonly limit: number;
}

/**
 * Takes the search parameters.
 * Builds the /api/search query string.
 * Gives the query string, without a leading "?".
 */
function buildSearchQueryString(params: SearchParams): string {
  const search = new URLSearchParams();
  search.set("q", params.q);
  search.set("operator", params.operator);
  search.set("limit", String(params.limit));
  for (const term of params.terms) {
    search.append("term", term);
  }
  return search.toString();
}

/**
 * Takes the search parameters and an AbortSignal.
 * Sends GET /api/search and validates the response.
 * Gives the SearchResponse, or throws ApiHttpError, ApiShapeError, or the fetch call's own error.
 */
export async function fetchSearch(params: SearchParams, signal: AbortSignal): Promise<SearchResponse> {
  const response = await fetch(`/api/search?${buildSearchQueryString(params)}`, { signal });
  if (!response.ok) {
    throw await errorFromResponse(response);
  }
  const body: unknown = await response.json();
  return parseSearchResponse(body);
}

/**
 * Takes no arguments.
 * Sends GET /api/search?terms_only=1 and validates the response.
 * Gives the TermsOnlyResponse, or throws ApiHttpError, ApiShapeError, or the fetch call's own error.
 */
export async function fetchTermsOnly(): Promise<TermsOnlyResponse> {
  const response = await fetch("/api/search?terms_only=1");
  if (!response.ok) {
    throw await errorFromResponse(response);
  }
  const body: unknown = await response.json();
  return parseTermsOnlyResponse(body);
}
